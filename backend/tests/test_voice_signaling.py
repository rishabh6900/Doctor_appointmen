"""Tests for WebRTC voice signaling endpoints."""

from fastapi.testclient import TestClient
from app.voice.session_manager import voice_session_manager


def test_list_voice_sessions_endpoint(client: TestClient):
    """Test GET /api/v1/voice/sessions."""
    voice_session_manager.create_session("api-test-call-1")
    response = client.get("/api/v1/voice/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert any(s["session_id"] == "api-test-call-1" for s in data["sessions"])


def test_end_voice_session_endpoint(client: TestClient):
    """Test POST /api/v1/voice/sessions/{id}/end."""
    voice_session_manager.create_session("api-test-call-end")
    response = client.post("/api/v1/voice/sessions/api-test-call-end/end")
    assert response.status_code == 200
    assert response.json()["status"] == "ended"


def test_end_nonexistent_voice_session_returns_404(client: TestClient):
    """Test 404 response when ending an unknown session."""
    response = client.post("/api/v1/voice/sessions/non-existent-session-id/end")
    assert response.status_code == 404
