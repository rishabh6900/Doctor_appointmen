"""Appointment repository for database queries and mutations."""

from datetime import date, time, datetime
from typing import List, Optional, Tuple
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session
from app.models.appointment import Appointment
from app.models.doctor import Doctor


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Retrieve an appointment by primary key."""
        return self.db.query(Appointment).filter(Appointment.id == appointment_id).first()

    def get_active_slot_appointment(
        self,
        doctor_id: int,
        appointment_date: date,
        appointment_time: time,
    ) -> Optional[Appointment]:
        """Check if a confirmed appointment already occupies this exact slot."""
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appointment_date,
                Appointment.appointment_time == appointment_time,
                Appointment.status == "confirmed",
            )
            .first()
        )

    def find_duplicate_booking(
        self,
        patient_phone: str,
        doctor_id: int,
        appointment_date: date,
    ) -> Optional[Appointment]:
        """Check if the same patient already has a confirmed booking with this doctor on this date."""
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.patient_phone_number == patient_phone,
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appointment_date,
                Appointment.status == "confirmed",
            )
            .first()
        )

    def find_patient_appointments(
        self,
        patient_phone: str,
        status: Optional[str] = "confirmed",
        future_only: bool = True,
        clinic_today: Optional[date] = None,
    ) -> List[Appointment]:
        """Retrieve appointments matching a patient phone number."""
        query = self.db.query(Appointment).filter(
            Appointment.patient_phone_number == patient_phone
        )

        if status:
            query = query.filter(Appointment.status == status)

        if future_only and clinic_today:
            query = query.filter(Appointment.appointment_date >= clinic_today)

        return (
            query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
            .all()
        )

    def list_appointments(
        self,
        doctor_id: Optional[int] = None,
        patient_phone: Optional[str] = None,
        appointment_date: Optional[date] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Appointment], int]:
        """List appointments with filtering and pagination."""
        query = self.db.query(Appointment)

        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)
        if patient_phone:
            query = query.filter(Appointment.patient_phone_number == patient_phone)
        if appointment_date:
            query = query.filter(Appointment.appointment_date == appointment_date)
        if status:
            query = query.filter(Appointment.status == status)

        total = query.count()
        appointments = (
            query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return appointments, total

    def create(self, appointment: Appointment) -> Appointment:
        """Add and commit an appointment record."""
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def cancel(self, appointment: Appointment) -> Appointment:
        """Mark appointment status as cancelled and commit."""
        appointment.status = "cancelled"
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def get_dashboard_metrics(self) -> dict:
        """Aggregate high-level clinical operational statistics."""
        total_doctors = self.db.query(Doctor).count()
        active_doctors = self.db.query(Doctor).filter(Doctor.is_active.is_(True)).count()

        total_appointments = self.db.query(Appointment).count()
        confirmed_appointments = (
            self.db.query(Appointment).filter(Appointment.status == "confirmed").count()
        )
        cancelled_appointments = (
            self.db.query(Appointment).filter(Appointment.status == "cancelled").count()
        )

        recent_appointments = (
            self.db.query(Appointment)
            .order_by(Appointment.created_at.desc())
            .limit(10)
            .all()
        )

        return {
            "total_doctors": total_doctors,
            "active_doctors": active_doctors,
            "total_appointments": total_appointments,
            "confirmed_appointments": confirmed_appointments,
            "cancelled_appointments": cancelled_appointments,
            "recent_activity": recent_appointments,
        }
