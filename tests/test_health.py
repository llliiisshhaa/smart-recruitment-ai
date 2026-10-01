"""
Tests for the /health endpoint and basic API availability.
Uses FastAPI TestClient to verify system health without requiring a live database.
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure the backend directory is on the Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_endpoint_returns_200():
    """
    Test that the /health endpoint responds with HTTP 200 and
    the expected JSON structure containing 'status' and 'database'.
    """
    response = client.get("/health")

    # Assert HTTP status is 200 OK
    assert response.status_code == 200

    data = response.json()

    # Assert 'status' key is present and marked 'ok'
    assert "status" in data
    assert data["status"] == "ok"

    # Assert 'database' key is present and has a valid state ('connected' or 'unavailable')
    assert "database" in data
    assert data["database"] in ("connected", "unavailable")


def test_root_endpoint():
    """
    Test that the root '/' endpoint returns HTTP 200 and greeting.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
