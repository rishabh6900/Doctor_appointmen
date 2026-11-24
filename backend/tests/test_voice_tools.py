"""Tests for Pipecat Voice Function Calling Tools and Schemas."""

from datetime import date, timedelta
from app.voice.tools import (
    VOICE_TOOLS,
    CHECK_AVAILABILITY_SCHEMA,
    BOOK_APPOINTMENT_SCHEMA,
    CANCEL_APPOINTMENT_SCHEMA,
    execute_check_doctor_availability,
    execute_book_appointment,
    execute_cancel_appointment,
)
from app.voice.prompts import get_system_prompt


def test_voice_tool_schemas_structure():
    """Verify all 3 voice tools have valid names, descriptions, and parameter definitions."""
    assert len(VOICE_TOOLS) == 3
    names = {tool["name"] for tool in VOICE_TOOLS}
    assert names == {"check_doctor_availability", "book_appointment", "cancel_appointment"}

    for tool in VOICE_TOOLS:
        assert "description" in tool
        assert "parameters" in tool
        assert tool["parameters"]["type"] == "object"
        assert "properties" in tool["parameters"]


def test_system_prompt_generation():
    """Verify system prompt includes clinic name, date, and emergency safety instructions."""
    prompt = get_system_prompt(date(2026, 11, 24))
    assert "CarePoint Health Medical Clinic" in prompt
    assert "Tuesday, November 24, 2026" in prompt
    assert "EMERGENCY" in prompt
    assert "112 or 911" in prompt


def test_execute_check_doctor_availability_tool(db_session, seeded_db):
    """Test voice tool check_doctor_availability."""
    result = execute_check_doctor_availability(
        db=db_session,
        speciality="Cardiology",
    )
    assert result["status"] == "success"
    assert result["count"] >= 1
    assert "results" in result


def test_execute_book_appointment_tool_success(db_session, seeded_db):
    """Test voice tool book_appointment with confirmed guards."""
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    result = execute_book_appointment(
        db=db_session,
        patient_phone_number="+919876543210",
        doctor_id=1,
        appointment_date=tomorrow,
        appointment_time="10:00",
        patient_name="Voice Test Patient",
        phone_readback_confirmed=True,
        action_confirmed=True,
    )
    assert result["status"] == "confirmed"
    assert result["booking_id"] is not None
    assert "successfully booked" in result["message"]


def test_execute_book_appointment_tool_guards_refusal(db_session, seeded_db):
    """Test voice tool book_appointment refuses when guards are False."""
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    result = execute_book_appointment(
        db=db_session,
        patient_phone_number="+919876543210",
        doctor_id=1,
        appointment_date=tomorrow,
        appointment_time="10:00",
        phone_readback_confirmed=False,
        action_confirmed=False,
    )
    assert result["status"] == "error"
    assert result["code"] == "PHONE_READBACK_REQUIRED"


def test_execute_cancel_appointment_tool(db_session, seeded_db):
    """Test voice tool cancel_appointment."""
    tomorrow = (date.today() + timedelta(days=3)).isoformat()
    # Book first
    book_res = execute_book_appointment(
        db=db_session,
        patient_phone_number="+919876543210",
        doctor_id=2,
        appointment_date=tomorrow,
        appointment_time="11:00",
        phone_readback_confirmed=True,
        action_confirmed=True,
    )
    booking_id = book_res["booking_id"]

    # Cancel via voice tool
    cancel_res = execute_cancel_appointment(
        db=db_session,
        patient_phone_number="+919876543210",
        appointment_id=booking_id,
        phone_readback_confirmed=True,
        action_confirmed=True,
    )
    assert cancel_res["status"] == "cancelled"
    assert cancel_res["appointment_id"] == booking_id
