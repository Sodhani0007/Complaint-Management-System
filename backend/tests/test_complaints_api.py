"""
Smoke tests covering the flows manually verified during development:
app boot, table creation, and the priority-escalation business rule. Not
exhaustive coverage — a starting point CI can actually run, matching what
was already proven to work by hand (see repo history / demo video for the
manual verification this was derived from).
"""

import os

os.environ.setdefault("GROQ_API_KEY", "test_key_for_ci")
os.environ.setdefault("DATABASE_URL", "sqlite:///./ci_test.db")

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.models import ai_extraction, batch, complaint, complaint_document, product  # noqa: F401


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_routes_registered(client):
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/api/v1/complaints/extract" in paths
    assert "/api/v1/complaints" in paths
    assert "/api/v1/complaints/{complaint_id}" in paths


def test_complaint_not_found_returns_404(client):
    response = client.get("/api/v1/complaints/999999")
    assert response.status_code == 404


def test_create_complaint_and_priority_escalation(client):
    payload = {
        "product_name": "Test Product 500mg",
        "batch_lot_number": "TEST-BATCH-001",
        "description": "Sample complaint description for automated testing.",
        "severity": "Major",
        "priority": "Medium",
    }

    first = client.post("/api/v1/complaints", json=payload)
    assert first.status_code == 201
    assert first.json()["priority"] == "Medium"

    # Second complaint on the same batch should escalate priority
    second = client.post("/api/v1/complaints", json=payload)
    assert second.status_code == 201
    assert second.json()["priority"] == "High"


def test_create_complaint_missing_required_field_returns_422(client):
    payload = {"product_name": "Test Product", "batch_lot_number": "TEST-BATCH-002"}  # missing description
    response = client.post("/api/v1/complaints", json=payload)
    assert response.status_code == 422
