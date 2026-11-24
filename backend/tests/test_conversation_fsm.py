"""Comprehensive acceptance tests for Stateful Conversation Management and FSM flow."""

import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.voice.conversation_state import conversation_state_manager
from app.voice.fsm_engine import FSMEngine
from app.services.datetime_service import datetime_service


def test_one_time_greeting_never_repeats(db_session, seeded_db):
    """Verify the welcome greeting is spoken only once and never repeated mid-call."""
    session_id = "test-greeting-session"
    conversation_state_manager.remove(session_id)
    state = conversation_state_manager.get_or_create(session_id)
    fsm = FSMEngine(db=db_session, state=state)

    # Turn 1: Initial caller opening
    t1 = fsm.process_turn("Hello")
    assert state.greeting_sent is True
    assert "Welcome to CarePoint Health Medical Clinic" in t1["response_text"]

    # Turn 2: Mid-call hello
    t2 = fsm.process_turn("Hello")
    assert "Welcome to CarePoint Health Medical Clinic" not in t2["response_text"]
    assert "How can I help you" in t2["response_text"] or "assist" in t2["response_text"]

    conversation_state_manager.remove(session_id)


def test_full_contextual_multi_turn_booking_flow(db_session, seeded_db):
    """
    Test the multi-turn conversational references:
    'Cardiologist' -> 'Tomorrow' -> 'At 9 AM' -> 'Yeh 7860634479' -> 'Yes, but it's zero, not O' -> 'Yes confirm'
    """
    session_id = "test-multi-turn-flow"
    conversation_state_manager.remove(session_id)
    state = conversation_state_manager.get_or_create(session_id)
    fsm = FSMEngine(db=db_session, state=state)

    # Turn 1: Speciality specification
    t1 = fsm.process_turn("I want to see a cardiologist")
    assert state.requested_speciality == "Cardiology"
    assert state.pending_action == "AWAITING_DATE"
    assert "date" in t1["response_text"].lower()

    # Turn 2: Short answer 'Tomorrow'
    t2 = fsm.process_turn("Tomorrow")
    tomorrow_iso = (datetime_service.get_clinic_today() + timedelta(days=1)).isoformat()
    assert state.appointment_date == tomorrow_iso
    assert state.requested_speciality == "Cardiology"
    assert state.selected_doctor_name is not None
    assert state.pending_action == "AWAITING_TIME"
    assert "slots" in t2["response_text"].lower() or "which time" in t2["response_text"].lower()

    # Turn 3: Short answer 'At 9'
    t3 = fsm.process_turn("At 9 AM")
    assert state.appointment_time == "09:00"
    assert state.appointment_date == tomorrow_iso
    assert state.pending_action == "AWAITING_PHONE"
    assert "phone" in t3["response_text"].lower() or "telephone" in t3["response_text"].lower()

    # Turn 4: Spoken phone with conversational prefix 'Yeh 7860634479'
    t4 = fsm.process_turn("Yeh 7860634479")
    assert state.patient_phone == "+917860634479"
    assert state.pending_action == "AWAITING_PHONE_CONFIRMATION"
    assert "7-8-6-0-6-3-4-4-7-9" in t4["response_text"]
    assert "Is that correct?" in t4["response_text"]

    # Turn 5: Correction 'Yes, but it's zero, not O'
    t5 = fsm.process_turn("Yes, but it's zero, not O")
    assert state.phone_confirmed is True
    assert state.pending_action == "AWAITING_BOOKING_CONFIRMATION"
    assert "confirm" in t5["response_text"].lower()
    assert state.selected_doctor_name in t5["response_text"]

    # Turn 6: Final verbal confirmation
    t6 = fsm.process_turn("Yes please confirm")
    assert state.current_state == "BOOKING_SUCCESS"
    assert state.booking_confirmation is True
    assert state.booked_appointment_id is not None
    assert t6["appointment_updated"] is True
    assert f"#{state.booked_appointment_id}" in t6["response_text"]

    conversation_state_manager.remove(session_id)


def test_unsupported_speciality_refusal(db_session, seeded_db):
    """Verify clinic refuses non-existent specialties and never hallucinates doctors."""
    session_id = "test-unsupported-spec"
    conversation_state_manager.remove(session_id)
    state = conversation_state_manager.get_or_create(session_id)
    fsm = FSMEngine(db=db_session, state=state)

    res = fsm.process_turn("I need an appointment with a psychologist")
    assert "does not currently offer" in res["response_text"]
    assert "psychologist" in res["response_text"].lower()
    assert "Cardiology" in res["response_text"]

    conversation_state_manager.remove(session_id)


def test_emergency_divert(db_session, seeded_db):
    """Verify life-threatening symptoms trigger immediate emergency diversion."""
    session_id = "test-emergency-divert"
    conversation_state_manager.remove(session_id)
    state = conversation_state_manager.get_or_create(session_id)
    fsm = FSMEngine(db=db_session, state=state)

    res = fsm.process_turn("I am experiencing severe chest pain and shortness of breath")
    assert state.current_state == "EMERGENCY_DIVERT"
    assert "112" in res["response_text"] or "911" in res["response_text"]
    assert "emergency room" in res["response_text"]

    conversation_state_manager.remove(session_id)
