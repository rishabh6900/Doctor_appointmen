"""Appointment business logic: atomic booking, cancellation, and validation."""

import logging
from datetime import date, time, datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import pytz
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from app.core.config import settings
from app.core.phone_utils import (
    normalize_spoken_phone_number,
    format_phone_for_speech,
    mask_phone_number,
)
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.services.availability_service import AvailabilityService

logger = logging.getLogger(__name__)


class BookingError(Exception):
    """Base business error for booking operations."""
    def __init__(self, code: str, message: str, alternatives: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.alternatives = alternatives or []


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.doctor_repo = DoctorRepository(db)
        self.appointment_repo = AppointmentRepository(db)
        self.availability_service = AvailabilityService(db)
        try:
            self.tz = pytz.timezone(settings.iana_timezone)
        except pytz.UnknownTimeZoneError:
            self.tz = pytz.timezone("Asia/Kolkata")

    def get_clinic_today(self) -> date:
        """Current date in clinic timezone."""
        return datetime.now(self.tz).date()

    def book_appointment(
        self,
        patient_phone: str,
        doctor_id: int,
        appointment_date: date,
        appointment_time: time,
        patient_name: Optional[str] = None,
        phone_readback_confirmed: bool = True,
        action_confirmed: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute an atomic appointment booking.

        Enforces:
        1. Phone validation & normalization to E.164
        2. Verbal confirmation guardrails
        3. Active doctor verification
        4. Date boundary validation (cannot book in the past)
        5. Duplicate booking prevention (same patient, doctor, and date)
        6. Slot availability validation
        7. Database-level partial unique index concurrency protection
        """
        # 1. Server-side confirmation guards
        if not phone_readback_confirmed:
            raise BookingError(
                code="PHONE_READBACK_REQUIRED",
                message="Patient phone number has not been read back and confirmed verbally.",
            )
        if not action_confirmed:
            raise BookingError(
                code="ACTION_CONFIRMATION_REQUIRED",
                message="Patient has not provided final verbal confirmation for this booking.",
            )

        # 2. Phone validation
        is_valid, e164_phone, phone_err = normalize_spoken_phone_number(patient_phone)
        if not is_valid:
            raise BookingError(code="INVALID_PHONE_NUMBER", message=phone_err)

        # 3. Doctor validation
        doctor = self.doctor_repo.get_active_by_id(doctor_id)
        if not doctor:
            raise BookingError(
                code="DOCTOR_NOT_FOUND",
                message=f"Doctor with ID {doctor_id} is inactive or does not exist.",
            )

        # 4. Date validation
        clinic_today = self.get_clinic_today()
        if appointment_date < clinic_today:
            raise BookingError(
                code="PAST_DATE_NOT_ALLOWED",
                message="Cannot book appointments in the past.",
            )

        # 5. Duplicate booking check: Same patient, doctor, and date
        existing_dup = self.appointment_repo.find_duplicate_booking(
            patient_phone=e164_phone,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
        )
        if existing_dup:
            raise BookingError(
                code="DUPLICATE_BOOKING",
                message=(
                    f"Patient already holds an active appointment with {doctor.name} "
                    f"on {appointment_date.isoformat()} at {existing_dup.appointment_time.strftime('%H:%M')}."
                ),
            )

        # 6. Slot availability validation
        available_slots = self.availability_service.get_available_slots(doctor_id, appointment_date)
        slot_str = appointment_time.strftime("%H:%M")
        if slot_str not in available_slots:
            alternatives = self.availability_service.find_alternative_slots(doctor_id, appointment_date)
            raise BookingError(
                code="SLOT_TAKEN",
                message=f"The selected time slot {slot_str} on {appointment_date} is no longer available.",
                alternatives=alternatives,
            )

        # 7. Atomic database transaction with unique index collision safety
        appointment = Appointment(
            patient_phone_number=e164_phone,
            patient_name=patient_name.strip() if patient_name else None,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status="confirmed",
        )

        try:
            saved_appointment = self.appointment_repo.create(appointment)
        except (IntegrityError, OperationalError):
            self.db.rollback()
            alternatives = self.availability_service.find_alternative_slots(doctor_id, appointment_date)
            raise BookingError(
                code="SLOT_TAKEN",
                message=f"The slot {slot_str} was just reserved by another patient.",
                alternatives=alternatives,
            )

        return {
            "status": "confirmed",
            "booking_id": saved_appointment.id,
            "patient_phone_number": e164_phone,
            "patient_phone_masked": mask_phone_number(e164_phone),
            "phone_speech_format": format_phone_for_speech(e164_phone),
            "patient_name": saved_appointment.patient_name,
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "speciality": doctor.speciality,
            "appointment_date": appointment_date.isoformat(),
            "appointment_time": slot_str,
            "message": (
                f"Appointment successfully booked with {doctor.name} for "
                f"{appointment_date.strftime('%A, %B %d, %Y')} at {slot_str}."
            ),
        }

    def cancel_appointment(
        self,
        patient_phone: str,
        appointment_id: Optional[int] = None,
        phone_readback_confirmed: bool = True,
        action_confirmed: bool = True,
    ) -> Dict[str, Any]:
        """
        Two-stage cancellation engine:
        - If multiple appointments match and appointment_id is omitted, returns disambiguation list.
        - Once confirmed, executes soft cancellation by setting status='cancelled'.
        """
        # Validate phone number
        is_valid, e164_phone, phone_err = normalize_spoken_phone_number(patient_phone)
        if not is_valid:
            raise BookingError(code="INVALID_PHONE_NUMBER", message=phone_err)

        clinic_today = self.get_clinic_today()
        matching_appointments = self.appointment_repo.find_patient_appointments(
            patient_phone=e164_phone,
            status="confirmed",
            future_only=True,
            clinic_today=clinic_today,
        )

        if not matching_appointments:
            return {
                "status": "none_found",
                "patient_phone_masked": mask_phone_number(e164_phone),
                "message": "No active future appointments found matching this phone number.",
                "appointments": [],
            }

        # Stage 1: Disambiguation if multiple exist and no specific ID was given
        if len(matching_appointments) > 1 and not appointment_id:
            return {
                "status": "multiple_found",
                "patient_phone_masked": mask_phone_number(e164_phone),
                "message": (
                    f"Found {len(matching_appointments)} appointments for this number. "
                    "Please specify which appointment you would like to cancel."
                ),
                "appointments": [
                    {
                        "appointment_id": app.id,
                        "doctor_name": app.doctor.name,
                        "speciality": app.doctor.speciality,
                        "date": app.appointment_date.isoformat(),
                        "time": app.appointment_time.strftime("%H:%M"),
                    }
                    for app in matching_appointments
                ],
            }

        # Identify target appointment
        target_app = None
        if appointment_id:
            for app in matching_appointments:
                if app.id == appointment_id:
                    target_app = app
                    break
            if not target_app:
                raise BookingError(
                    code="APPOINTMENT_NOT_FOUND",
                    message=f"No confirmed future appointment with ID {appointment_id} found for this phone number.",
                )
        else:
            target_app = matching_appointments[0]

        # Confirmation guardrails
        if not phone_readback_confirmed:
            raise BookingError(
                code="PHONE_READBACK_REQUIRED",
                message="Patient phone number must be read back and verbally confirmed before cancellation.",
            )
        if not action_confirmed:
            return {
                "status": "awaiting_confirmation",
                "appointment_id": target_app.id,
                "doctor_name": target_app.doctor.name,
                "date": target_app.appointment_date.isoformat(),
                "time": target_app.appointment_time.strftime("%H:%M"),
                "message": (
                    f"Please confirm: Do you want to cancel your appointment with "
                    f"{target_app.doctor.name} on {target_app.appointment_date} at "
                    f"{target_app.appointment_time.strftime('%H:%M')}?"
                ),
            }

        # Execute cancellation
        cancelled_app = self.appointment_repo.cancel(target_app)

        return {
            "status": "cancelled",
            "appointment_id": cancelled_app.id,
            "patient_phone_masked": mask_phone_number(e164_phone),
            "doctor_name": cancelled_app.doctor.name,
            "speciality": cancelled_app.doctor.speciality,
            "appointment_date": cancelled_app.appointment_date.isoformat(),
            "appointment_time": cancelled_app.appointment_time.strftime("%H:%M"),
            "message": (
                f"Appointment with {cancelled_app.doctor.name} on "
                f"{cancelled_app.appointment_date} has been successfully cancelled."
            ),
        }
