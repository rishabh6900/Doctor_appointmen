"""Tests for AppointmentService booking, cancellation, and guardrails."""

from datetime import date, time, timedelta
import pytest
from app.services.appointment_service import AppointmentService, BookingError
from app.models.appointment import Appointment


def test_successful_booking(db_session, seeded_db):
    """Test complete booking flow with confirmations."""
    service = AppointmentService(db_session)
    target_date = service.get_clinic_today() + timedelta(days=4)

    result = service.book_appointment(
        patient_phone="+15551234567",
        doctor_id=1,
        appointment_date=target_date,
        appointment_time=time(10, 30),
        patient_name="John Doe",
        phone_readback_confirmed=True,
        action_confirmed=True,
    )

    assert result["status"] == "confirmed"
    assert result["booking_id"] is not None
    assert result["patient_phone_number"] == "+15551234567"
    assert result["appointment_time"] == "10:30"

    # Verify persistence
    saved = db_session.query(Appointment).filter_by(id=result["booking_id"]).first()
    assert saved is not None
    assert saved.status == "confirmed"


def test_booking_requires_phone_readback_guard(db_session, seeded_db):
    """Server guard: booking without confirmed readback must fail."""
    service = AppointmentService(db_session)
    target_date = service.get_clinic_today() + timedelta(days=4)

    with pytest.raises(BookingError) as exc_info:
        service.book_appointment(
            patient_phone="+15551234567",
            doctor_id=1,
            appointment_date=target_date,
            appointment_time=time(11, 0),
            phone_readback_confirmed=False,
            action_confirmed=True,
        )
    assert exc_info.value.code == "PHONE_READBACK_REQUIRED"


def test_booking_requires_action_confirmation_guard(db_session, seeded_db):
    """Server guard: booking without patient verbal confirmation must fail."""
    service = AppointmentService(db_session)
    target_date = service.get_clinic_today() + timedelta(days=4)

    with pytest.raises(BookingError) as exc_info:
        service.book_appointment(
            patient_phone="+15551234567",
            doctor_id=1,
            appointment_date=target_date,
            appointment_time=time(11, 0),
            phone_readback_confirmed=True,
            action_confirmed=False,
        )
    assert exc_info.value.code == "ACTION_CONFIRMATION_REQUIRED"


def test_duplicate_booking_prevention(db_session, seeded_db):
    """Test that a patient cannot book multiple appointments with the same doctor on the same date."""
    service = AppointmentService(db_session)
    # Select a target date that is not a Sunday
    target_date = service.get_clinic_today() + timedelta(days=2)
    if target_date.weekday() == 6:
        target_date += timedelta(days=1)

    # First booking
    service.book_appointment(
        patient_phone="+15551234567",
        doctor_id=1,
        appointment_date=target_date,
        appointment_time=time(9, 30),
        phone_readback_confirmed=True,
        action_confirmed=True,
    )

    # Second booking for same doctor & date at different time
    with pytest.raises(BookingError) as exc_info:
        service.book_appointment(
            patient_phone="+15551234567",
            doctor_id=1,
            appointment_date=target_date,
            appointment_time=time(14, 0),
            phone_readback_confirmed=True,
            action_confirmed=True,
        )
    assert exc_info.value.code == "DUPLICATE_BOOKING"


def test_cancellation_flow(db_session, seeded_db):
    """Test patient appointment cancellation with phone lookup."""
    service = AppointmentService(db_session)
    target_date = service.get_clinic_today() + timedelta(days=6)

    # Book an appointment first
    booking = service.book_appointment(
        patient_phone="+15557778888",
        doctor_id=2,
        appointment_date=target_date,
        appointment_time=time(11, 0),
        phone_readback_confirmed=True,
        action_confirmed=True,
    )

    # Cancel it
    cancel_result = service.cancel_appointment(
        patient_phone="+15557778888",
        appointment_id=booking["booking_id"],
        phone_readback_confirmed=True,
        action_confirmed=True,
    )
    assert cancel_result["status"] == "cancelled"

    # Verify status in database
    app = db_session.query(Appointment).filter_by(id=booking["booking_id"]).first()
    assert app.status == "cancelled"
