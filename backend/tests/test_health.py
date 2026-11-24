"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_root_health_check(client: TestClient):
    """Test /health endpoint returns 200 OK and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data
    assert "clinic_timezone" in data
    assert "clinic_name" in data


def test_api_v1_health_check(client: TestClient):
    """Test /api/v1/health endpoint functions identically."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
