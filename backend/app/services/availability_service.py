"""Doctor Availability and Slot Generation Service."""

from datetime import date, time, datetime, timedelta
from typing import List, Optional, Dict, Any
import pytz
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.doctor import Doctor
from app.models.availability import Availability
from app.models.appointment import Appointment
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.appointment_repository import AppointmentRepository


class AvailabilityService:
    def __init__(self, db: Session):
        self.db = db
        self.doctor_repo = DoctorRepository(db)
        self.appointment_repo = AppointmentRepository(db)
        try:
            self.tz = pytz.timezone(settings.iana_timezone)
        except pytz.UnknownTimeZoneError:
            self.tz = pytz.timezone("Asia/Kolkata")

    def get_clinic_today(self) -> date:
        """Get today's calendar date in the clinic timezone."""
        return datetime.now(self.tz).date()

    def generate_slots_from_window(
        self,
        start_time: time,
        end_time: time,
        slot_duration_min: int = 30,
    ) -> List[time]:
        """Generate discrete time slots across an availability window."""
        slots = []
        current_dt = datetime.combine(date.today(), start_time)
        end_dt = datetime.combine(date.today(), end_time)
        step = timedelta(minutes=slot_duration_min)

        while current_dt + step <= end_dt:
            slots.append(current_dt.time())
            current_dt += step

        return slots

    def get_available_slots(
        self,
        doctor_id: int,
        target_date: date,
    ) -> List[str]:
        """Calculate unbooked 30-minute slots for a given doctor on a specific date."""
        # Retrieve doctor's schedule window for this date
        availability = (
            self.db.query(Availability)
            .filter(
                Availability.doctor_id == doctor_id,
                Availability.appointment_date == target_date,
                Availability.availability_status == "available",
            )
            .first()
        )
        if not availability:
            return []

        # Generate all valid candidate slots
        all_candidate_slots = self.generate_slots_from_window(
            availability.start_time,
            availability.end_time,
            availability.slot_duration_min,
        )

        # Retrieve existing confirmed appointments for this doctor and date
        confirmed_appointments = (
            self.db.query(Appointment.appointment_time)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == target_date,
                Appointment.status == "confirmed",
            )
            .all()
        )
        booked_times = {app[0] for app in confirmed_appointments}

        # Filter out booked slots
        free_slots = [
            slot.strftime("%H:%M")
            for slot in all_candidate_slots
            if slot not in booked_times
        ]
        return free_slots

    def search_availability(
        self,
        doctor_name: Optional[str] = None,
        speciality: Optional[str] = None,
        target_date: Optional[date] = None,
        days_ahead: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Search availability across doctors, specialties, and dates.
        Returns structured results with doctor details and available slots.
        """
        clinic_today = self.get_clinic_today()
        search_date = target_date or clinic_today

        # Query matching doctors
        doctors, _ = self.doctor_repo.list_doctors(
            speciality=speciality,
            search=doctor_name,
            is_active=True,
            limit=10,
        )

        results = []
        for doc in doctors:
            doc_availability = []

            # Check slots for search_date up to search_date + days_ahead
            num_days_to_check = 1 if target_date else days_ahead
            for offset in range(num_days_to_check):
                check_date = search_date + timedelta(days=offset)
                if check_date.weekday() == 6:  # Skip Sundays
                    continue

                free_slots = self.get_available_slots(doc.id, check_date)
                if free_slots:
                    doc_availability.append({
                        "date": check_date.isoformat(),
                        "time_slots": free_slots,
                    })

            if doc_availability:
                results.append({
                    "doctor_id": doc.id,
                    "doctor_name": doc.name,
                    "speciality": doc.speciality,
                    "experience_years": doc.experience_years,
                    "schedules": doc_availability,
                })

        return results

    def find_alternative_slots(
        self,
        doctor_id: int,
        target_date: date,
        days_window: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find alternative slots for the same doctor across nearby dates."""
        alternatives = []
        for offset in range(1, days_window + 1):
            next_date = target_date + timedelta(days=offset)
            if next_date.weekday() == 6:
                continue
            slots = self.get_available_slots(doctor_id, next_date)
            if slots:
                alternatives.append({
                    "date": next_date.isoformat(),
                    "time_slots": slots[:4],  # Return up to 4 convenient options
                })
        return alternatives
