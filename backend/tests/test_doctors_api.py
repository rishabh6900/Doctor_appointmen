"""Tests for Doctor and Speciality REST APIs."""

from fastapi.testclient import TestClient


def test_list_doctors_empty(client: TestClient):
    """Test listing doctors when none exist."""
    response = client.get("/api/v1/doctors")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_doctors_seeded(client: TestClient, seeded_db):
    """Test listing doctors when seeded."""
    response = client.get("/api/v1/doctors")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 8
    assert len(data["items"]) == 8


def test_filter_doctors_by_speciality(client: TestClient, seeded_db):
    """Test filtering doctors by speciality (case-insensitive)."""
    response = client.get("/api/v1/doctors?speciality=cardiology")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for doc in data["items"]:
        assert doc["speciality"] == "Cardiology"


def test_search_doctors_by_name(client: TestClient, seeded_db):
    """Test search doctor query."""
    response = client.get("/api/v1/doctors?search=Elena")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Elena Rostova" in data["items"][0]["name"]


def test_get_doctor_by_id(client: TestClient, seeded_db):
    """Test retrieving doctor by valid ID."""
    response = client.get("/api/v1/doctors/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "name" in data
    assert "speciality" in data


def test_get_doctor_not_found(client: TestClient, seeded_db):
    """Test 404 response for non-existent doctor ID."""
    response = client.get("/api/v1/doctors/9999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_list_specialities(client: TestClient, seeded_db):
    """Test listing distinct specialties with doctor counts."""
    response = client.get("/api/v1/specialities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5

    spec_map = {item["speciality"]: item["doctor_count"] for item in data}
    assert "Cardiology" in spec_map
    assert spec_map["Cardiology"] == 2
    assert "Dermatology" in spec_map
    assert spec_map["Dermatology"] == 1
