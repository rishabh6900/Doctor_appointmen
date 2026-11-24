"""Appointment Model with Partial Unique Index for Zero Double-Booking."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Time,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_phone_number = Column(String(30), nullable=False, index=True)
    patient_name = Column(String(120), nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="RESTRICT"), nullable=False, index=True)
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(Time, nullable=False)
    status = Column(String(20), nullable=False, default="confirmed", index=True)  # confirmed, cancelled
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("status IN ('confirmed', 'cancelled')", name="check_valid_status"),
        # Partial unique index: Only one 'confirmed' appointment per doctor, date, and time.
        # Cancelled appointments are kept for history without blocking re-booking!
        Index(
            "uq_active_slot",
            "doctor_id",
            "appointment_date",
            "appointment_time",
            unique=True,
            sqlite_where=text("status = 'confirmed'"),
            postgresql_where=text("status = 'confirmed'"),
        ),
        Index("idx_patient_phone", "patient_phone_number"),
        Index("idx_doctor_date_status", "doctor_id", "appointment_date", "status"),
    )

    # Relationships
    doctor = relationship("Doctor", back_populates="appointments")

    def __repr__(self) -> str:
        return (
            f"<Appointment(id={self.id}, doctor_id={self.doctor_id}, "
            f"date={self.appointment_date}, time={self.appointment_time}, status='{self.status}')>"
        )
