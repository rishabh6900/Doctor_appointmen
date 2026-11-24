"""Tool 2: book_appointment function tool for Pipecat / Gemini."""

from datetime import date, time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.services.appointment_service import AppointmentService, BookingError

BOOK_APPOINTMENT_SCHEMA = {
    "name": "book_appointment",
    "description": (
        "Book a confirmed appointment for a patient. CRITICAL: You must only call this tool "
        "AFTER you have read back the phone number to the patient, obtained their confirmation "
        "(phone_readback_confirmed=True), and obtained their final verbal confirmation of the "
        "appointment details (action_confirmed=True)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "patient_phone_number": {
                "type": "string",
                "description": "The patient's telephone number spoken during the conversation.",
            },
            "doctor_id": {
                "type": "integer",
                "description": "The numeric ID of the doctor.",
            },
            "appointment_date": {
                "type": "string",
                "description": "Appointment date in YYYY-MM-DD format.",
            },
            "appointment_time": {
                "type": "string",
                "description": "Appointment time in HH:MM format (e.g. '10:00' or '14:30').",
            },
            "patient_name": {
                "type": "string",
                "description": "Optional patient full name if provided.",
            },
            "phone_readback_confirmed": {
                "type": "boolean",
                "description": "Must be True ONLY if you read back the phone number and patient confirmed it.",
            },
            "action_confirmed": {
                "type": "boolean",
                "description": "Must be True ONLY if patient explicitly said yes to booking this specific slot.",
            },
        },
        "required": [
            "patient_phone_number",
            "doctor_id",
            "appointment_date",
            "appointment_time",
            "phone_readback_confirmed",
            "action_confirmed",
        ],
    },
}


def execute_book_appointment(
    db: Session,
    patient_phone_number: str,
    doctor_id: int,
    appointment_date: str,
    appointment_time: str,
    patient_name: Optional[str] = None,
    phone_readback_confirmed: bool = False,
    action_confirmed: bool = False,
) -> Dict[str, Any]:
    """Execute appointment booking against transactional backend services."""
    service = AppointmentService(db)

    try:
        app_date = date.fromisoformat(appointment_date)
    except ValueError:
        return {
            "status": "error",
            "code": "INVALID_DATE_FORMAT",
            "message": f"Invalid date format '{appointment_date}'. Please provide YYYY-MM-DD.",
        }

    try:
        # Parse time HH:MM or HH:MM:SS
        parts = [int(p) for p in appointment_time.split(":")[:2]]
        app_time = time(parts[0], parts[1])
    except Exception:
        return {
            "status": "error",
            "code": "INVALID_TIME_FORMAT",
            "message": f"Invalid time format '{appointment_time}'. Please provide HH:MM.",
        }

    try:
        result = service.book_appointment(
            patient_phone=patient_phone_number,
            doctor_id=doctor_id,
            appointment_date=app_date,
            appointment_time=app_time,
            patient_name=patient_name,
            phone_readback_confirmed=phone_readback_confirmed,
            action_confirmed=action_confirmed,
        )
        return result
    except BookingError as exc:
        return {
            "status": "error",
            "code": exc.code,
            "message": exc.message,
            "alternatives": exc.alternatives,
        }
