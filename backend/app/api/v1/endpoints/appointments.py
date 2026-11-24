"""Appointment REST endpoints for booking, listing, and cancellation."""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.appointment_repository import AppointmentRepository
from app.services.appointment_service import AppointmentService, BookingError
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentListResponse,
    AppointmentDetailResponse,
)
from app.schemas.dashboard import (
    CancelAppointmentRequest,
    CancelAppointmentResponse,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Book a doctor appointment",
)
def book_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
):
    """Book an appointment with atomic slot reservation and duplicate checks."""
    service = AppointmentService(db)
    try:
        result = service.book_appointment(
            patient_phone=payload.patient_phone_number,
            doctor_id=payload.doctor_id,
            appointment_date=payload.appointment_date,
            appointment_time=payload.appointment_time,
            patient_name=payload.patient_name,
            phone_readback_confirmed=payload.phone_readback_confirmed,
            action_confirmed=payload.action_confirmed,
        )
        return result
    except BookingError as exc:
        status_code = status.HTTP_400_BAD_REQUEST
        if exc.code == "SLOT_TAKEN" or exc.code == "DUPLICATE_BOOKING":
            status_code = status.HTTP_409_CONFLICT
        elif exc.code == "INVALID_PHONE_NUMBER":
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif exc.code == "DOCTOR_NOT_FOUND":
            status_code = status.HTTP_404_NOT_FOUND

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
                "alternatives": exc.alternatives,
            },
        )


@router.get(
    "",
    response_model=AppointmentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List appointments with filtering and pagination",
)
def list_appointments(
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    patient_phone: Optional[str] = Query(None, description="Filter by exact phone number"),
    appointment_date: Optional[date] = Query(None, description="Filter by date"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (confirmed/cancelled)"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
):
    """Retrieve appointments matching query filters."""
    repo = AppointmentRepository(db)
    appointments, total = repo.list_appointments(
        doctor_id=doctor_id,
        patient_phone=patient_phone,
        appointment_date=appointment_date,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return AppointmentListResponse(total=total, items=appointments)


@router.get(
    "/{appointment_id}",
    response_model=AppointmentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get appointment details by ID",
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full appointment details including doctor metadata."""
    repo = AppointmentRepository(db)
    appointment = repo.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found.",
        )

    return AppointmentDetailResponse(
        id=appointment.id,
        patient_phone_number=appointment.patient_phone_number,
        patient_name=appointment.patient_name,
        doctor_id=appointment.doctor_id,
        doctor_name=appointment.doctor.name,
        speciality=appointment.doctor.speciality,
        appointment_date=appointment.appointment_date,
        appointment_time=appointment.appointment_time,
        status=appointment.status,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )


@router.post(
    "/{appointment_id}/cancel",
    response_model=CancelAppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel an appointment",
)
def cancel_appointment(
    appointment_id: int,
    payload: CancelAppointmentRequest,
    db: Session = Depends(get_db),
):
    """Cancel an existing appointment after patient confirmation."""
    service = AppointmentService(db)
    try:
        result = service.cancel_appointment(
            patient_phone=payload.patient_phone_number,
            appointment_id=appointment_id,
            phone_readback_confirmed=payload.phone_readback_confirmed,
            action_confirmed=payload.action_confirmed,
        )
        return result
    except BookingError as exc:
        status_code = status.HTTP_400_BAD_REQUEST
        if exc.code == "APPOINTMENT_NOT_FOUND":
            status_code = status.HTTP_404_NOT_FOUND
        elif exc.code == "INVALID_PHONE_NUMBER":
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "message": exc.message},
        )
