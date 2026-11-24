"""Database seed script for realistic clinical test data."""

import logging
from datetime import date, time, timedelta, datetime
import pytz
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import Base, engine, SessionLocal
from app.models.doctor import Doctor
from app.models.availability import Availability
from app.models.appointment import Appointment

logger = logging.getLogger(__name__)


INITIAL_DOCTORS = [
    {
        "name": "Dr. Sarah Jenkins",
        "speciality": "Cardiology",
        "experience_years": 14,
        "description": "Board-certified cardiologist specializing in preventive cardiology, heart rhythm disorders, and hypertension management.",
        "is_active": True,
    },
    {
        "name": "Dr. Marcus Vance",
        "speciality": "Cardiology",
        "experience_years": 9,
        "description": "Cardiologist focused on interventional cardiology, coronary artery disease, and lipid management.",
        "is_active": True,
    },
    {
        "name": "Dr. Elena Rostova",
        "speciality": "Dermatology",
        "experience_years": 11,
        "description": "Dermatologist with expertise in medical dermatology, eczema, acne, skin cancer screenings, and mole evaluations.",
        "is_active": True,
    },
    {
        "name": "Dr. David Kim",
        "speciality": "Pediatrics",
        "experience_years": 16,
        "description": "Senior pediatrician offering comprehensive childhood care, routine well-child exams, and adolescent medicine.",
        "is_active": True,
    },
    {
        "name": "Dr. Priya Patel",
        "speciality": "Pediatrics",
        "experience_years": 8,
        "description": "Pediatrician specializing in pediatric allergy management, childhood asthma, and developmental milestones.",
        "is_active": True,
    },
    {
        "name": "Dr. Robert Chen",
        "speciality": "Orthopedics",
        "experience_years": 18,
        "description": "Orthopedic specialist focusing on joint pain, sports injuries, knee and shoulder health, and fracture rehabilitation.",
        "is_active": True,
    },
    {
        "name": "Dr. Lisa Morales",
        "speciality": "General Medicine",
        "experience_years": 12,
        "description": "Primary care physician providing preventive annual health screenings, diabetes management, and chronic disease wellness.",
        "is_active": True,
    },
    {
        "name": "Dr. James Wilson",
        "speciality": "Neurology",
        "experience_years": 15,
        "description": "Neurologist evaluating migraine and chronic headache conditions, peripheral neuropathy, and cognitive disorders.",
        "is_active": True,
    },
]


def seed_database(db: Session, num_days: int = 14) -> dict:
    """Populate database with doctors, availability windows, and initial sample appointments."""
    bind = db.get_bind()
    Base.metadata.create_all(bind=bind)

    # 1. Seed Doctors if not already present
    existing_doctors = db.query(Doctor).all()
    doctor_map = {d.name: d for d in existing_doctors}

    seeded_doctors_count = 0
    for doc_data in INITIAL_DOCTORS:
        if doc_data["name"] not in doctor_map:
            doctor = Doctor(**doc_data)
            db.add(doctor)
            db.flush()
            doctor_map[doctor.name] = doctor
            seeded_doctors_count += 1

    db.commit()

    # 2. Seed Availability Windows for the next num_days
    try:
        tz = pytz.timezone(settings.iana_timezone)
    except pytz.UnknownTimeZoneError:
        tz = pytz.timezone("Asia/Kolkata")
    today = datetime.now(tz).date()

    doctors = list(doctor_map.values())
    start_time_obj = time(9, 0)
    end_time_obj = time(17, 0)

    # Fetch existing availability records in one query to avoid 100+ separate roundtrips
    existing_avail = set(
        db.query(Availability.doctor_id, Availability.appointment_date).all()
    )

    new_availabilities = []
    for day_offset in range(num_days):
        current_date = today + timedelta(days=day_offset)
        # Skip Sundays
        if current_date.weekday() == 6:
            continue

        for doctor in doctors:
            if not doctor.is_active:
                continue
            if (doctor.id, current_date) not in existing_avail:
                new_availabilities.append(
                    Availability(
                        doctor_id=doctor.id,
                        appointment_date=current_date,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        slot_duration_min=settings.DEFAULT_SLOT_DURATION_MIN,
                        availability_status="available",
                    )
                )

    seeded_availabilities_count = len(new_availabilities)
    if new_availabilities:
        db.bulk_save_objects(new_availabilities)
        db.commit()

    # 3. Seed a few sample appointments for realism and testing
    sample_appointments_count = 0
    if len(doctors) >= 2:
        # Sample appointment 1 for tomorrow with Dr. Sarah Jenkins
        doc_sarah = doctor_map.get("Dr. Sarah Jenkins")
        target_date_1 = today + timedelta(days=1)
        if doc_sarah:
            app_1_exists = (
                db.query(Appointment)
                .filter(
                    Appointment.doctor_id == doc_sarah.id,
                    Appointment.appointment_date == target_date_1,
                    Appointment.appointment_time == time(10, 0),
                    Appointment.status == "confirmed",
                )
                .first()
            )
            if not app_1_exists:
                app_1 = Appointment(
                    patient_phone_number="+15551234567",
                    patient_name="John Doe",
                    doctor_id=doc_sarah.id,
                    appointment_date=target_date_1,
                    appointment_time=time(10, 0),
                    status="confirmed",
                )
                db.add(app_1)
                sample_appointments_count += 1

        # Sample appointment 2 with Dr. David Kim
        doc_david = doctor_map.get("Dr. David Kim")
        target_date_2 = today + timedelta(days=2)
        if doc_david:
            app_2_exists = (
                db.query(Appointment)
                .filter(
                    Appointment.doctor_id == doc_david.id,
                    Appointment.appointment_date == target_date_2,
                    Appointment.appointment_time == time(14, 0),
                    Appointment.status == "confirmed",
                )
                .first()
            )
            if not app_2_exists:
                app_2 = Appointment(
                    patient_phone_number="+15559876543",
                    patient_name="Alice Smith",
                    doctor_id=doc_david.id,
                    appointment_date=target_date_2,
                    appointment_time=time(14, 0),
                    status="confirmed",
                )
                db.add(app_2)
                sample_appointments_count += 1

    db.commit()

    return {
        "doctors_total": db.query(Doctor).count(),
        "doctors_seeded": seeded_doctors_count,
        "availabilities_seeded": seeded_availabilities_count,
        "sample_appointments_seeded": sample_appointments_count,
    }


if __name__ == "__main__":
    db = SessionLocal()
    try:
        result = seed_database(db)
        print(f"Seed complete: {result}")
    finally:
        db.close()
