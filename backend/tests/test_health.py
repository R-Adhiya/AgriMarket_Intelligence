"""
Phase 1 tests — health endpoint verification.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_contains_status():
    response = client.get("/api/health")
    data = response.json()
    assert "status" in data


def test_health_status_is_healthy():
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_service_name():
    response = client.get("/api/health")
    data = response.json()
    assert data["service"] == "AgriMarket Intelligence API"
