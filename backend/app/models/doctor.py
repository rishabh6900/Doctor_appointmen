"""Doctor SQLAlchemy Model."""

from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), nullable=False, index=True)
    speciality = Column(String(80), nullable=False, index=True)
    experience_years = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    availabilities = relationship(
        "Availability",
        back_populates="doctor",
        cascade="all, delete-orphan",
        order_by="Availability.appointment_date, Availability.start_time",
    )
    appointments = relationship(
        "Appointment",
        back_populates="doctor",
        cascade="all, delete-orphan",
        order_by="Appointment.appointment_date, Appointment.appointment_time",
    )

    def __repr__(self) -> str:
        return f"<Doctor(id={self.id}, name='{self.name}', speciality='{self.speciality}')>"
