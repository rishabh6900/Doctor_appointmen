"""Tests for AvailabilityService slot generation and searches."""

from datetime import date, time, timedelta
from app.services.availability_service import AvailabilityService
from app.models.appointment import Appointment


def test_slot_generation_window(db_session):
    """Test carving a schedule window into discrete 30-minute slots."""
    service = AvailabilityService(db_session)
    slots = service.generate_slots_from_window(
        start_time=time(9, 0),
        end_time=time(11, 0),
        slot_duration_min=30,
    )
    assert len(slots) == 4
    assert slots == [time(9, 0), time(9, 30), time(10, 0), time(10, 30)]


def test_get_available_slots_filters_booked(db_session, seeded_db):
    """Test that confirmed booked slots are excluded from availability."""
    service = AvailabilityService(db_session)
    target_date = service.get_clinic_today() + timedelta(days=3)

    # Initially doctor 1 has open slots
    initial_slots = service.get_available_slots(doctor_id=1, target_date=target_date)
    assert "09:30" in initial_slots

    # Book 09:30 slot
    app = Appointment(
        patient_phone_number="+15558889999",
        doctor_id=1,
        appointment_date=target_date,
        appointment_time=time(9, 30),
        status="confirmed",
    )
    db_session.add(app)
    db_session.commit()

    # Query again: 09:30 must be gone
    updated_slots = service.get_available_slots(doctor_id=1, target_date=target_date)
    assert "09:30" not in updated_slots
    assert len(updated_slots) == len(initial_slots) - 1


def test_search_availability_by_speciality(db_session, seeded_db):
    """Test searching availability by medical specialty."""
    service = AvailabilityService(db_session)
    results = service.search_availability(speciality="Cardiology", days_ahead=3)
    assert len(results) >= 1
    for r in results:
        assert r["speciality"] == "Cardiology"
        assert len(r["schedules"]) > 0


def test_find_alternative_slots(db_session, seeded_db):
    """Test finding alternative appointment slots."""
    service = AvailabilityService(db_session)
    target_date = service.get_clinic_today() + timedelta(days=2)
    alternatives = service.find_alternative_slots(doctor_id=1, target_date=target_date)
    assert isinstance(alternatives, list)
    assert len(alternatives) > 0
    assert "date" in alternatives[0]
    assert "time_slots" in alternatives[0]
