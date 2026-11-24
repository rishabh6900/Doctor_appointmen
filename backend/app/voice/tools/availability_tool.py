"""Tool 1: check_doctor_availability function tool for Pipecat / Gemini."""

from datetime import date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.services.availability_service import AvailabilityService

CHECK_AVAILABILITY_SCHEMA = {
    "name": "check_doctor_availability",
    "description": (
        "Check available doctors and unbooked consultation time slots by doctor name, "
        "medical speciality, or date. Always use this tool when the patient asks about "
        "doctor schedules or wants to find an appointment slot."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "doctor_name": {
                "type": "string",
                "description": "Optional doctor name to search for (e.g. 'Dr. Sarah Jenkins' or 'Sarah')",
            },
            "speciality": {
                "type": "string",
                "description": "Optional medical speciality (e.g. 'Cardiology', 'Dermatology', 'Pediatrics')",
            },
            "appointment_date": {
                "type": "string",
                "description": "Target calendar date in YYYY-MM-DD format. If patient says 'tomorrow', compute the date relative to today's date.",
            },
        },
        "required": [],
    },
}


def execute_check_doctor_availability(
    db: Session,
    doctor_name: Optional[str] = None,
    speciality: Optional[str] = None,
    appointment_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute availability search against backend services."""
    service = AvailabilityService(db)

    target_d = None
    if appointment_date:
        try:
            target_d = date.fromisoformat(appointment_date)
        except ValueError:
            target_d = None

    results = service.search_availability(
        doctor_name=doctor_name,
        speciality=speciality,
        target_date=target_d,
        days_ahead=5,
    )

    if not results:
        # Check alternative upcoming slots
        return {
            "status": "none_found",
            "message": "No available appointments found matching your criteria.",
            "suggestion": "Please check another date or ask for all available specialties.",
            "results": [],
        }

    return {
        "status": "success",
        "count": len(results),
        "results": results,
    }
