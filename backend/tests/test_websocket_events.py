"""Tests for Real-Time WebSocket Event Streaming."""

import pytest
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.doctor import Doctor
from app.models.availability import Availability


def test_websocket_connection_and_ping():
    """Verify WebSocket connects and responds to ping/pong protocol."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/events") as websocket:
        # Expect welcome message
        data = websocket.receive_json()
        assert data["event"] == "connected"
        assert "CarePoint" in data["data"]["message"]

        # Send ping
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"


def test_websocket_broadcasts_on_booking(client, db_session):
    """Verify that booking an appointment broadcasts an appointment_booked event."""
    # Create doctor and availability matching actual SQLAlchemy model schema
    doctor = Doctor(
        name="Dr. WS Broadcast Test",
        speciality="Cardiology",
        experience_years=8,
        description="Cardiac specialist for broadcast tests",
        is_active=True,
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)

    target_date = date.today() + timedelta(days=2)
    avail = Availability(
        doctor_id=doctor.id,
        appointment_date=target_date,
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration_min=30,
        availability_status="available",
    )
    db_session.add(avail)
    db_session.commit()

    test_client = TestClient(app)
    with test_client.websocket_connect("/api/v1/ws/events") as websocket:
        # Welcome message
        welcome = websocket.receive_json()
        assert welcome["event"] == "connected"

        # Book an appointment via REST API
        booking_payload = {
            "doctor_id": doctor.id,
            "appointment_date": target_date.isoformat(),
            "appointment_time": "10:00",
            "patient_name": "WebSocket Test Patient",
            "patient_phone_number": "+91 98765 43210",
            "phone_readback_confirmed": True,
            "action_confirmed": True,
        }
        resp = test_client.post("/api/v1/appointments", json=booking_payload)
        assert resp.status_code == 201

        # The WebSocket client must receive the real-time broadcast
        broadcast_msg = websocket.receive_json()
        assert broadcast_msg["event"] == "appointment_booked"
        assert broadcast_msg["data"]["doctor_id"] == doctor.id
        assert broadcast_msg["data"]["appointment_time"] == "10:00"
        assert "***" in broadcast_msg["data"]["patient_phone_masked"]
