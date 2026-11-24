"""Tool 3: cancel_appointment function tool for Pipecat / Gemini."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.services.appointment_service import AppointmentService, BookingError

CANCEL_APPOINTMENT_SCHEMA = {
    "name": "cancel_appointment",
    "description": (
        "Cancel an existing appointment. First call this with the patient's phone number "
        "to search for matching appointments. If multiple appointments are returned, ask the "
        "patient which one they want to cancel. Once confirmed, call again with appointment_id "
        "and action_confirmed=True."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "patient_phone_number": {
                "type": "string",
                "description": "Patient's spoken phone number.",
            },
            "appointment_id": {
                "type": "integer",
                "description": "Specific appointment ID to cancel. Required if multiple appointments exist.",
            },
            "phone_readback_confirmed": {
                "type": "boolean",
                "description": "Must be True if the phone number was read back and confirmed.",
            },
            "action_confirmed": {
                "type": "boolean",
                "description": "Must be True ONLY if patient explicitly gave final confirmation to cancel.",
            },
        },
        "required": ["patient_phone_number", "phone_readback_confirmed", "action_confirmed"],
    },
}


def execute_cancel_appointment(
    db: Session,
    patient_phone_number: str,
    appointment_id: Optional[int] = None,
    phone_readback_confirmed: bool = False,
    action_confirmed: bool = False,
) -> Dict[str, Any]:
    """Execute cancellation with multi-stage disambiguation and confirmation."""
    service = AppointmentService(db)

    try:
        result = service.cancel_appointment(
            patient_phone=patient_phone_number,
            appointment_id=appointment_id,
            phone_readback_confirmed=phone_readback_confirmed,
            action_confirmed=action_confirmed,
        )
        return result
    except BookingError as exc:
        return {
            "status": "error",
            "code": exc.code,
            "message": exc.message,
        }
