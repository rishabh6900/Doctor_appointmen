"""Tests for seed database functionality."""

from app.database.seed import seed_database
from app.models.doctor import Doctor
from app.models.availability import Availability
from app.models.appointment import Appointment


def test_seed_database_execution(db_session):
    """Test that seed_database populates doctors, availability, and sample appointments."""
    summary = seed_database(db_session, num_days=7)

    assert summary["doctors_total"] == 8
    assert summary["doctors_seeded"] == 8
    assert summary["availabilities_seeded"] > 0
    assert summary["sample_appointments_seeded"] == 2

    # Verify doctors exist
    doctors = db_session.query(Doctor).all()
    assert len(doctors) == 8

    # Verify availabilities exist
    availabilities = db_session.query(Availability).all()
    assert len(availabilities) > 0

    # Verify idempotency: running seed again should not duplicate doctors
    second_summary = seed_database(db_session, num_days=7)
    assert second_summary["doctors_seeded"] == 0
    assert second_summary["doctors_total"] == 8
