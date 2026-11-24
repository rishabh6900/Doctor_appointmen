"""Doctor Availability Schedule Model."""

from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_min = Column(Integer, nullable=False, default=30)
    availability_status = Column(String(20), nullable=False, default="available")  # available, on_leave, busy

    # Constraints
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="check_end_after_start"),
        CheckConstraint("slot_duration_min > 0", name="check_positive_slot_duration"),
        Index("idx_doctor_date", "doctor_id", "appointment_date"),
    )

    # Relationships
    doctor = relationship("Doctor", back_populates="availabilities")

    def __repr__(self) -> str:
        return (
            f"<Availability(id={self.id}, doctor_id={self.doctor_id}, "
            f"date={self.appointment_date}, {self.start_time}-{self.end_time})>"
        )
