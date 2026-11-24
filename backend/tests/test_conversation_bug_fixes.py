"""Comprehensive Regression Tests for All 12 CarePoint Conversational Bug Scenarios."""

import pytest
import time
from datetime import timedelta, time
from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.models.availability import Availability
from app.services.datetime_service import datetime_service
from app.voice.conversation_state import conversation_state_manager
from app.voice.session_manager import voice_session_manager
from app.voice.interaction_service import VoiceInteractionService


@pytest.fixture(autouse=True)
def seed_test_doctor(db_session: Session):
    """Seed verified doctor and schedule for test scenarios."""
    db_session.query(Availability).delete()
    db_session.query(Doctor).delete()
    db_session.commit()

    doc = Doctor(
        name="Dr. Priya Sharma",
        speciality="Cardiology",
        is_active=True,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    today = datetime_service.get_clinic_today()
    tomorrow = today + timedelta(days=1)

    avail = Availability(
        doctor_id=doc.id,
        appointment_date=tomorrow,
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration_min=30,
        availability_status="available",
    )
    db_session.add(avail)
    db_session.commit()

    return doc


class TestConversationBugFixes:
    """Covers all 12 mandatory scenarios defined in the Master Bug Investigation Prompt."""

    def test_scenario_1_new_appointment(self, db_session: Session):
        """Scenario 1: Caller: 'I want to book an appointment' -> Agent asks for doctor or specialty."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_1"

        res = service.interact("I want to book an appointment", session_id=session_id)
        assert res["session_id"] == session_id
        text = res["response_text"].lower()
        assert "doctor" in text or "speciality" in text or "specialty" in text

    def test_scenario_2_short_response(self, db_session: Session):
        """Scenario 2: Caller says 'New' to indicate booking intent without crashing or resetting."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_2"

        # Initial turn
        service.interact("Hello", session_id=session_id)
        # Short intent reply
        res = service.interact("new", session_id=session_id)
        text = res["response_text"].lower()
        assert "doctor" in text or "speciality" in text or "schedule" in text or "appointment" in text

    def test_scenario_3_date_retention(self, db_session: Session):
        """Scenario 3: Caller: 'Tomorrow at 4 PM', then Agent asks doctor, Caller: 'Dr. Priya' -> Retains tomorrow at 4 PM."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_3"

        # Turn 1: Date & Time provided first
        res1 = service.interact("Tomorrow at 4 PM", session_id=session_id)
        state1 = conversation_state_manager.get(session_id)
        assert state1 is not None
        assert state1.appointment_date is not None
        assert state1.appointment_time == "16:00"

        # Turn 2: Doctor provided
        res2 = service.interact("Dr. Priya", session_id=session_id)
        state2 = conversation_state_manager.get(session_id)
        assert state2.appointment_date == state1.appointment_date
        assert state2.appointment_time == "16:00"
        assert "Dr. Priya" in (state2.selected_doctor_name or "")

    def test_scenario_4_phone_number_collection(self, db_session: Session):
        """Scenario 4: Caller provides phone number -> Agent reads back and requests confirmation."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_4"

        service.interact("Tomorrow at 4 PM", session_id=session_id)
        service.interact("Dr. Priya", session_id=session_id)
        res = service.interact("My phone number is 9876543210", session_id=session_id)

        state = conversation_state_manager.get(session_id)
        assert state.patient_phone is not None
        assert state.pending_action == "AWAITING_PHONE_CONFIRMATION"
        assert "confirm" in res["response_text"].lower() or "correct" in res["response_text"].lower()

    def test_scenario_5_successful_booking(self, db_session: Session):
        """Scenario 5: Caller confirms phone and final booking -> Executes book_appointment once and returns reference."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_5"

        service.interact("Tomorrow at 4 PM", session_id=session_id)
        service.interact("Dr. Priya", session_id=session_id)
        service.interact("9876543210", session_id=session_id)
        # Confirm phone readback
        service.interact("Yes, that is correct", session_id=session_id)
        # Final booking confirmation
        res = service.interact("Yes, confirm the appointment", session_id=session_id)

        assert res["appointment_updated"] is True
        assert "book_appointment" in res["tools_called"]
        state = conversation_state_manager.get(session_id)
        assert state.booking_confirmation is True
        assert state.booked_appointment_id is not None
        assert f"#{state.booked_appointment_id}" in res["response_text"]

    def test_scenario_6_thank_you_after_booking(self, db_session: Session):
        """Scenario 6: Caller: 'Thank you' after booking -> Warm polite reply, MUST NOT ask for booking confirmation again."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_6"

        service.interact("Tomorrow at 4 PM", session_id=session_id)
        service.interact("Dr. Priya", session_id=session_id)
        service.interact("9876543210", session_id=session_id)
        service.interact("Yes", session_id=session_id)
        service.interact("Yes, confirm", session_id=session_id)

        # Subsequent turn: Caller expresses gratitude
        res = service.interact("Thank you so much!", session_id=session_id)
        text = res["response_text"].lower()
        assert "welcome" in text or "have a wonderful day" in text or "great day" in text
        # CRITICAL: Must not ask to confirm booking
        assert "shall i confirm" not in text
        assert "confirm this reservation" not in text

    def test_scenario_7_another_booking(self, db_session: Session):
        """Scenario 7: Caller: 'I want to book another appointment' -> Starts new booking without corrupting the completed one."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_7"

        # Complete initial booking
        service.interact("Tomorrow at 4 PM", session_id=session_id)
        service.interact("Dr. Priya", session_id=session_id)
        service.interact("9876543210", session_id=session_id)
        service.interact("Yes", session_id=session_id)
        res_book1 = service.interact("Yes, confirm", session_id=session_id)
        first_booking_id = conversation_state_manager.get(session_id).booked_appointment_id

        # Request another booking
        res2 = service.interact("I want to book another appointment", session_id=session_id)
        state = conversation_state_manager.get(session_id)
        assert state.booking_confirmation is False
        assert state.appointment_date is None
        assert state.appointment_time is None
        # Preserves patient phone
        assert state.patient_phone == "+919876543210"
        assert "doctor" in res2["response_text"].lower() or "speciality" in res2["response_text"].lower()

    def test_scenario_8_duplicate_transcript_deduplication(self, db_session: Session):
        """Scenario 8: Same finalized transcript delivered twice in rapid succession -> Deduplicated."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_8"

        res1 = service.interact("I need an appointment with Dr. Priya", session_id=session_id)
        # Immediate duplicate within 1.5 seconds
        res2 = service.interact("I need an appointment with Dr. Priya", session_id=session_id)

        assert res1["response_text"] == res2["response_text"]
        # Tools should not be re-executed for duplicate
        assert res2["tools_called"] == []

    def test_scenario_9_genuine_repeated_speech(self, db_session: Session):
        """Scenario 9: Caller genuinely says same words after deduplication window -> Processed normally."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_9"

        res1 = service.interact("Hello", session_id=session_id)
        state = conversation_state_manager.get(session_id)
        # Advance last processed time by 4.0 seconds to simulate natural pause beyond 3s window
        state.last_processed_time -= 4.0

        res2 = service.interact("Hello", session_id=session_id)
        assert res2["response_text"] is not None
        assert len(res2["response_text"]) > 5

    def test_scenario_10_independent_sessions(self, db_session: Session):
        """Scenario 10: Two callers in separate active sessions -> Strict state isolation."""
        service = VoiceInteractionService(db_session)
        session_a = "session_user_alpha"
        session_b = "session_user_beta"

        service.interact("Tomorrow at 4 PM with Dr. Priya", session_id=session_a)
        service.interact("My phone is 9876543210", session_id=session_a)

        service.interact("I want to check cardiology availability", session_id=session_b)

        state_a = conversation_state_manager.get(session_a)
        state_b = conversation_state_manager.get(session_b)

        assert state_a.patient_phone == "+919876543210"
        assert state_b.patient_phone is None
        assert state_b.appointment_time is None

    def test_scenario_11_availability_query(self, db_session: Session):
        """Scenario 11: Caller asks for doctor availability -> Calls check_doctor_availability."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_11"

        res = service.interact("What slots does Dr. Priya have tomorrow?", session_id=session_id)
        assert "check_doctor_availability" in res["tools_called"]
        state = conversation_state_manager.get(session_id)
        assert len(state.available_slots) > 0

    def test_scenario_12_cancellation_confirmation(self, db_session: Session):
        """Scenario 12: Caller requests cancellation -> Enforces confirmation before executing."""
        service = VoiceInteractionService(db_session)
        session_id = "test_scen_12"

        # 1. Book an initial appointment to cancel
        service.interact("Tomorrow at 4 PM", session_id=session_id)
        service.interact("Dr. Priya", session_id=session_id)
        service.interact("9876543210", session_id=session_id)
        service.interact("Yes", session_id=session_id)
        service.interact("Yes, confirm", session_id=session_id)

        # 2. Request cancellation
        res_cancel = service.interact("I want to cancel my appointment", session_id=session_id)
        state = conversation_state_manager.get(session_id)
        assert state.current_state == "CONFIRM_CANCELLATION"
        assert "cancel_appointment" in res_cancel["tools_called"]
        assert "are you sure" in res_cancel["response_text"].lower()

        # 3. Confirm cancellation
        res_conf = service.interact("Yes, please cancel it", session_id=session_id)
        assert state.cancellation_confirmation is True
        assert "cancelled" in res_conf["response_text"].lower()
