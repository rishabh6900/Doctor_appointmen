"""REST API tests for Availability, Appointments, and Dashboard Stats."""

from datetime import date, timedelta
from fastapi.testclient import TestClient


def test_get_availability_endpoint(client: TestClient, seeded_db):
    """Test GET /api/v1/availability."""
    response = client.get("/api/v1/availability?speciality=Cardiology")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["count"] >= 1


def test_book_appointment_endpoint_success(client: TestClient, seeded_db):
    """Test POST /api/v1/appointments."""
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    payload = {
        "patient_phone_number": "+15551239999",
        "patient_name": "API Tester",
        "doctor_id": 1,
        "appointment_date": tomorrow,
        "appointment_time": "11:30:00",
        "phone_readback_confirmed": True,
        "action_confirmed": True,
    }
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["booking_id"] is not None


def test_book_appointment_slot_conflict(client: TestClient, seeded_db):
    """Test POST /api/v1/appointments returns 409 when slot is taken."""
    tomorrow = (date.today() + timedelta(days=3)).isoformat()
    payload = {
        "patient_phone_number": "+15551231111",
        "doctor_id": 1,
        "appointment_date": tomorrow,
        "appointment_time": "14:00:00",
        "phone_readback_confirmed": True,
        "action_confirmed": True,
    }
    # First booking succeeds
    r1 = client.post("/api/v1/appointments", json=payload)
    assert r1.status_code == 201

    # Second booking for same slot with different patient returns 409 Conflict
    payload2 = dict(payload, patient_phone_number="+15551232222")
    r2 = client.post("/api/v1/appointments", json=payload2)
    assert r2.status_code == 409
    err = r2.json()["detail"]
    assert err["code"] == "SLOT_TAKEN"
    assert len(err["alternatives"]) > 0


def test_cancel_appointment_endpoint(client: TestClient, seeded_db):
    """Test POST /api/v1/appointments/{id}/cancel."""
    tomorrow = (date.today() + timedelta(days=4)).isoformat()
    book_payload = {
        "patient_phone_number": "+15554445555",
        "doctor_id": 2,
        "appointment_date": tomorrow,
        "appointment_time": "15:00:00",
        "phone_readback_confirmed": True,
        "action_confirmed": True,
    }
    r_book = client.post("/api/v1/appointments", json=book_payload)
    app_id = r_book.json()["booking_id"]

    cancel_payload = {
        "patient_phone_number": "+15554445555",
        "phone_readback_confirmed": True,
        "action_confirmed": True,
    }
    r_cancel = client.post(f"/api/v1/appointments/{app_id}/cancel", json=cancel_payload)
    assert r_cancel.status_code == 200
    assert r_cancel.json()["status"] == "cancelled"


def test_dashboard_stats_endpoint(client: TestClient, seeded_db):
    """Test GET /api/v1/dashboard/stats."""
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_doctors"] == 8
    assert data["active_doctors"] == 8
    assert data["total_appointments"] >= 2
    assert "recent_activity" in data
    assert isinstance(data["recent_activity"], list)
