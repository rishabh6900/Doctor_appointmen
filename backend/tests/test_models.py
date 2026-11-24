"""Tests verifying SQLAlchemy models, constraints, and the partial unique index."""

from datetime import date, time
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.doctor import Doctor
from app.models.availability import Availability
from app.models.appointment import Appointment


def test_doctor_creation(db_session):
    """Test doctor model persistence and retrieval."""
    doctor = Doctor(
        name="Dr. Test Specialist",
        speciality="Neurology",
        experience_years=10,
        description="Expert in cognitive health",
        is_active=True,
    )
    db_session.add(doctor)
    db_session.commit()

    retrieved = db_session.query(Doctor).filter_by(name="Dr. Test Specialist").first()
    assert retrieved is not None
    assert retrieved.speciality == "Neurology"
    assert retrieved.experience_years == 10
    assert repr(retrieved).startswith("<Doctor")


def test_availability_foreign_key_and_relationship(db_session):
    """Test availability linked to doctor."""
    doctor = Doctor(name="Dr. Availability Doc", speciality="Cardiology")
    db_session.add(doctor)
    db_session.commit()

    avail = Availability(
        doctor_id=doctor.id,
        appointment_date=date(2026, 12, 1),
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration_min=30,
    )
    db_session.add(avail)
    db_session.commit()

    assert len(doctor.availabilities) == 1
    assert doctor.availabilities[0].appointment_date == date(2026, 12, 1)


def test_partial_unique_index_prevents_double_booking(db_session):
    """Critical Test: uq_active_slot partial unique index prevents concurrent double bookings."""
    doctor = Doctor(name="Dr. Double Booking Test", speciality="Dermatology")
    db_session.add(doctor)
    db_session.commit()

    target_date = date(2026, 12, 15)
    target_time = time(10, 0)

    # First confirmed booking succeeds
    app1 = Appointment(
        patient_phone_number="+15551112222",
        doctor_id=doctor.id,
        appointment_date=target_date,
        appointment_time=target_time,
        status="confirmed",
    )
    db_session.add(app1)
    db_session.commit()

    # Second confirmed booking for same doctor, date and time MUST fail at database level
    app2 = Appointment(
        patient_phone_number="+15559998888",
        doctor_id=doctor.id,
        appointment_date=target_date,
        appointment_time=target_time,
        status="confirmed",
    )
    db_session.add(app2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_partial_unique_index_allows_rebooking_after_cancellation(db_session):
    """Critical Test: A cancelled appointment record DOES NOT block re-booking the same slot."""
    doctor = Doctor(name="Dr. Rebook Test", speciality="Pediatrics")
    db_session.add(doctor)
    db_session.commit()

    target_date = date(2026, 12, 20)
    target_time = time(11, 30)

    # First appointment is created and subsequently cancelled
    app1 = Appointment(
        patient_phone_number="+15551112222",
        doctor_id=doctor.id,
        appointment_date=target_date,
        appointment_time=target_time,
        status="cancelled",
    )
    db_session.add(app1)
    db_session.commit()

    # Second appointment for the same slot with status='confirmed' MUST succeed
    app2 = Appointment(
        patient_phone_number="+15553334444",
        doctor_id=doctor.id,
        appointment_date=target_date,
        appointment_time=target_time,
        status="confirmed",
    )
    db_session.add(app2)
    db_session.commit()

    active_apps = (
        db_session.query(Appointment)
        .filter_by(doctor_id=doctor.id, appointment_date=target_date, appointment_time=target_time)
        .all()
    )
    assert len(active_apps) == 2
    assert {a.status for a in active_apps} == {"cancelled", "confirmed"}
