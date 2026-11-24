"""Tests for the /api/v1/voice/interact conversational endpoint."""

from fastapi.testclient import TestClient


def test_voice_interact_availability(client: TestClient, seeded_db):
    """Test voice interact handles availability inquiry."""
    payload = {
        "message": "Is Dr. Sarah Jenkins available tomorrow?",
        "history": [],
    }
    response = client.post("/api/v1/voice/interact", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "response_text" in data
    assert len(data["response_text"]) > 10
    assert "check_doctor_availability" in data["tools_called"]


def test_voice_interact_emergency_safeguard(client: TestClient, seeded_db):
    """Test voice interact immediately diverts medical emergencies."""
    payload = {
        "message": "I am having severe chest pain and difficulty breathing!",
    }
    response = client.post("/api/v1/voice/interact", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "emergency" in data["response_text"].lower() or "112" in data["response_text"] or "911" in data["response_text"]
    assert data["appointment_updated"] is False


def test_voice_interact_general_greeting(client: TestClient, seeded_db):
    """Test voice interact welcomes callers politely."""
    payload = {
        "message": "Hello, good morning!",
    }
    response = client.post("/api/v1/voice/interact", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["response_text"]) > 5
