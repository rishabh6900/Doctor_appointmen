"""Availability REST endpoints."""

from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.availability_service import AvailabilityService

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Search doctor availability and unbooked time slots",
)
def get_availability(
    doctor_name: Optional[str] = Query(None, description="Doctor name search query"),
    speciality: Optional[str] = Query(None, description="Medical speciality filter (e.g. Cardiology)"),
    appointment_date: Optional[date] = Query(None, description="Target calendar date (YYYY-MM-DD)"),
    days_ahead: int = Query(7, ge=1, le=30, description="Days ahead to inspect"),
    db: Session = Depends(get_db),
):
    """Retrieve available doctors and their open consultation slots."""
    service = AvailabilityService(db)
    results = service.search_availability(
        doctor_name=doctor_name,
        speciality=speciality,
        target_date=appointment_date,
        days_ahead=days_ahead,
    )
    return {"results": results, "count": len(results)}


@router.get(
    "/doctor/{doctor_id}/slots",
    status_code=status.HTTP_200_OK,
    summary="Get free slots for a specific doctor on a given date",
)
def get_doctor_slots(
    doctor_id: int,
    appointment_date: date = Query(..., description="Target date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Retrieve unbooked time slots for a specific doctor."""
    service = AvailabilityService(db)
    slots = service.get_available_slots(doctor_id, appointment_date)
    return {
        "doctor_id": doctor_id,
        "appointment_date": appointment_date.isoformat(),
        "available_slots": slots,
        "count": len(slots),
    }
