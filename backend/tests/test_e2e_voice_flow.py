"""Comprehensive End-to-End Voice Flow Acceptance Tests.

Tests the full conversational workflow covering:
1. Specialty & Doctor discovery
2. Slot retrieval
3. Verbal phone number readback validation
4. Final booking action confirmation
5. Zero double-booking prevention on reserved slot
6. Two-stage cancellation with disambiguation
"""

import pytest
from datetime import date, time, timedelta
from app.voice.tools.availability_tool import execute_check_doctor_availability
from app.voice.tools.booking_tool import execute_book_appointment
from app.voice.tools.cancellation_tool import execute_cancel_appointment
from app.models.doctor import Doctor
from app.models.availability import Availability


@pytest.fixture
def seeded_e2e_data(db_session):
    """Seed test doctor and availability matching schema."""
    doc = Doctor(
        name="Dr. Emily Voice",
        speciality="Dermatology",
        experience_years=10,
        description="Board certified dermatologist",
        is_active=True,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    target_date = date.today() + timedelta(days=1)
    # Seed availability for target_date and next day
    avail1 = Availability(
        doctor_id=doc.id,
        appointment_date=target_date,
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration_min=30,
        availability_status="available",
    )
    avail2 = Availability(
        doctor_id=doc.id,
        appointment_date=target_date + timedelta(days=1),
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration_min=30,
        availability_status="available",
    )
    db_session.add_all([avail1, avail2])
    db_session.commit()

    return doc, target_date


def test_e2e_full_conversational_booking_and_cancellation_flow(db_session, seeded_e2e_data):
    """
    Simulates complete spoken interaction:
    1. Patient asks for Dermatology availability.
    2. Voice tool checks availability and returns slots.
    3. Patient attempts booking without confirmation (rejected by server guard).
    4. Patient provides spoken phone number, confirms readback and action (booking succeeds).
    5. Another patient attempts booking the same slot (rejected: duplicate prevention).
    6. Patient cancels the appointment via spoken cancellation flow.
    7. Slot is freed back for availability.
    """
    doc, target_date = seeded_e2e_data
    date_str = target_date.isoformat()

    # Step 1: Check availability
    avail_result = execute_check_doctor_availability(
        db=db_session,
        speciality="Dermatology",
        appointment_date=date_str,
    )
    assert avail_result["status"] == "success"
    assert avail_result["count"] > 0
    # Structure: results[0]["schedules"][0]["time_slots"][0]
    first_schedule = avail_result["results"][0]["schedules"][0]
    assert len(first_schedule["time_slots"]) > 0
    selected_slot = first_schedule["time_slots"][0]  # e.g. "09:00"

    # Step 2: Attempt booking without verbal readback confirmation (MUST FAIL)
    unconfirmed_result = execute_book_appointment(
        db=db_session,
        patient_phone_number="9876543210",
        doctor_id=doc.id,
        appointment_date=date_str,
        appointment_time=selected_slot,
        phone_readback_confirmed=False,
        action_confirmed=True,
    )
    assert unconfirmed_result["status"] == "error"
    assert unconfirmed_result["code"] == "PHONE_READBACK_REQUIRED"

    # Step 3: Attempt booking without final action confirmation (MUST FAIL)
    no_action_result = execute_book_appointment(
        db=db_session,
        patient_phone_number="9876543210",
        doctor_id=doc.id,
        appointment_date=date_str,
        appointment_time=selected_slot,
        phone_readback_confirmed=True,
        action_confirmed=False,
    )
    assert no_action_result["status"] == "error"
    assert no_action_result["code"] == "ACTION_CONFIRMATION_REQUIRED"

    # Step 4: Spoken phone with words and full confirmation (MUST SUCCEED)
    booking_result = execute_book_appointment(
        db=db_session,
        patient_phone_number="nine eight seven six five four three two one zero",
        doctor_id=doc.id,
        appointment_date=date_str,
        appointment_time=selected_slot,
        patient_name="Alex Spoken Patient",
        phone_readback_confirmed=True,
        action_confirmed=True,
    )
    assert booking_result["status"] == "confirmed"
    booking_id = booking_result["booking_id"]
    assert "***" in booking_result["patient_phone_masked"]

    # Step 5: Duplicate booking attempt for the exact same slot (MUST FAIL WITH ALTERNATIVES)
    conflict_result = execute_book_appointment(
        db=db_session,
        patient_phone_number="+91 99999 88888",
        doctor_id=doc.id,
        appointment_date=date_str,
        appointment_time=selected_slot,
        patient_name="Second Patient",
        phone_readback_confirmed=True,
        action_confirmed=True,
    )
    assert conflict_result["status"] == "error"
    assert conflict_result["code"] == "SLOT_TAKEN"
    assert len(conflict_result["alternatives"]) > 0

    # Step 6: Spoken cancellation flow - Stage 1: Disambiguation or Confirmation check
    cancel_await_result = execute_cancel_appointment(
        db=db_session,
        patient_phone_number="9876543210",
        appointment_id=booking_id,
        phone_readback_confirmed=True,
        action_confirmed=False,
    )
    assert cancel_await_result["status"] == "awaiting_confirmation"

    # Step 7: Final confirmed cancellation execution
    cancel_success_result = execute_cancel_appointment(
        db=db_session,
        patient_phone_number="9876543210",
        appointment_id=booking_id,
        phone_readback_confirmed=True,
        action_confirmed=True,
    )
    assert cancel_success_result["status"] == "cancelled"
    assert cancel_success_result["appointment_id"] == booking_id

    # Step 8: Verify slot has been released back to availability
    recheck_avail = execute_check_doctor_availability(
        db=db_session,
        doctor_name=doc.name,
        appointment_date=date_str,
    )
    freed_slots = recheck_avail["results"][0]["schedules"][0]["time_slots"]
    assert selected_slot in freed_slots
