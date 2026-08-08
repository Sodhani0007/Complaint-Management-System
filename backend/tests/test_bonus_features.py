"""
Tests for the bonus AI features: Completeness Checker, Complaint Summary,
Duplicate Detection.

Per the assignment's own testing requirement, LLM calls are mocked rather
than hitting the live Groq API — this sandbox in particular can't reach
api.groq.com at all, but even outside this sandbox, unit tests shouldn't
depend on a live network call and a real API key to pass. Completeness
Checker's core logic needs no mock since its required-fields determination
is deterministic; only its optional qualitative-warnings LLM pass is mocked.
"""

import os
from unittest.mock import patch

os.environ.setdefault("GROQ_API_KEY", "test_key_for_ci")
os.environ.setdefault("DATABASE_URL", "sqlite:///./ci_test_bonus.db")

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.models import ai_extraction, batch, complaint, complaint_document, product  # noqa: F401

COMPLETE_PAYLOAD = {
    "complaint_source": "Email",
    "customer_name": "Dr. Test",
    "product_name": "Test Product 500mg",
    "batch_lot_number": "BONUS-BATCH-001",
    "manufacturing_date": "2026-01-01",
    "expiry_date": "2028-01-01",
    "quantity_affected": 5,
    "complaint_type": "Discoloration",
    "complaint_date": "2026-08-01",
    "description": "Tablets show discoloration in several units from this batch.",
    "severity": "Major",
    "priority": "Medium",
}

INCOMPLETE_PAYLOAD = {
    "product_name": "Sparse Product",
    "batch_lot_number": "BONUS-BATCH-002",
    "description": "Minor issue noted.",
}


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


# --- Completeness Checker ---


def test_completeness_check_complete_complaint(client):
    with patch("app.ai.nodes.completeness.call_llm_for_json", return_value={"warnings": []}):
        created = client.post("/api/v1/complaints", json=COMPLETE_PAYLOAD)
        cid = created.json()["id"]
        response = client.post(f"/api/v1/complaints/{cid}/completeness-check")

    assert response.status_code == 200
    body = response.json()
    assert body["is_complete"] is True
    assert body["missing_fields"] == []
    assert body["confidence"] == 1.0


def test_completeness_check_incomplete_complaint_flags_missing_fields(client):
    created = client.post("/api/v1/complaints", json=INCOMPLETE_PAYLOAD)
    cid = created.json()["id"]
    # No LLM patch needed here: an incomplete complaint should short-circuit
    # before ever calling the LLM (see check_completeness — the optional
    # warnings pass only runs when is_complete is already True).
    response = client.post(f"/api/v1/complaints/{cid}/completeness-check")

    assert response.status_code == 200
    body = response.json()
    assert body["is_complete"] is False
    assert "Manufacturing Date" in body["missing_fields"]
    assert "Quantity Affected" in body["missing_fields"]


def test_completeness_check_nonexistent_complaint_returns_404(client):
    response = client.post("/api/v1/complaints/999999/completeness-check")
    assert response.status_code == 404


def test_completeness_check_llm_warning_failure_is_non_fatal(client):
    """If the optional LLM warnings pass fails, the deterministic result
    should still return successfully rather than the whole request failing."""
    with patch("app.ai.nodes.completeness.call_llm_for_json", side_effect=Exception("simulated LLM outage")):
        created = client.post("/api/v1/complaints", json=COMPLETE_PAYLOAD)
        cid = created.json()["id"]
        response = client.post(f"/api/v1/complaints/{cid}/completeness-check")

    assert response.status_code == 200
    assert response.json()["is_complete"] is True
    assert response.json()["warnings"] == []


# --- Complaint Summary ---


def test_summary_happy_path_with_mocked_llm(client):
    mocked_llm_response = {
        "summary": "Customer reported discoloration in a batch of tablets.",
        "potential_impact": "Possible quality defect requiring batch review.",
        "recommended_next_step": "Escalate to batch investigation.",
        "confidence": 0.88,
    }
    with patch("app.ai.nodes.summarize.call_llm_for_json", return_value=mocked_llm_response):
        created = client.post("/api/v1/complaints", json=COMPLETE_PAYLOAD)
        cid = created.json()["id"]
        response = client.post(f"/api/v1/complaints/{cid}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == mocked_llm_response["summary"]
    assert body["confidence"] == 0.88
    assert body["product"] == "Test Product 500mg"


def test_summary_llm_failure_degrades_gracefully(client):
    from app.ai.llm_client import LLMJSONError

    with patch("app.ai.nodes.summarize.call_llm_for_json", side_effect=LLMJSONError("simulated failure")):
        created = client.post("/api/v1/complaints", json=COMPLETE_PAYLOAD)
        cid = created.json()["id"]
        response = client.post(f"/api/v1/complaints/{cid}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == "insufficient_information"
    assert body["confidence"] == 0.0
    # Deterministic fields should still be populated even though the LLM failed
    assert body["product"] == "Test Product 500mg"


def test_summary_nonexistent_complaint_returns_404(client):
    response = client.post("/api/v1/complaints/999999/summary")
    assert response.status_code == 404


# --- Duplicate Detection ---


def test_duplicate_detection_finds_similar_complaint_same_batch(client):
    payload_a = dict(COMPLETE_PAYLOAD, batch_lot_number="DUP-BATCH-001")
    payload_b = dict(
        COMPLETE_PAYLOAD,
        batch_lot_number="DUP-BATCH-001",
        description="Tablets showing discoloration found in several units from this same batch.",
        customer_name="Different Customer",
    )

    client.post("/api/v1/complaints", json=payload_a)
    created_b = client.post("/api/v1/complaints", json=payload_b)
    cid_b = created_b.json()["id"]

    response = client.post(f"/api/v1/complaints/{cid_b}/duplicate-check")

    assert response.status_code == 200
    body = response.json()
    assert body["is_duplicate"] is True
    assert len(body["matches"]) >= 1
    assert body["matches"][0]["similarity_score"] > 0.5


def test_duplicate_detection_no_match_for_unrelated_complaint(client):
    payload = dict(
        COMPLETE_PAYLOAD,
        batch_lot_number="UNIQUE-BATCH-999",
        description="Completely unrelated issue about a broken cap on the bottle, nothing to do with tablets.",
    )
    created = client.post("/api/v1/complaints", json=payload)
    cid = created.json()["id"]

    response = client.post(f"/api/v1/complaints/{cid}/duplicate-check")

    assert response.status_code == 200
    # First complaint ever created for this product+batch combination in
    # this test — no prior complaints exist to match against.
    assert response.json()["is_duplicate"] is False


def test_duplicate_detection_nonexistent_complaint_returns_404(client):
    response = client.post("/api/v1/complaints/999999/duplicate-check")
    assert response.status_code == 404


# --- Risk Assessment (re-assessment endpoint) ---


def test_risk_assessment_returns_llm_classification_with_reasoning(client):
    mocked_llm_response = {
        "severity": "Major",
        "priority": "Medium",
        "confidence": 0.82,
        "reasoning": "Discoloration suggests a possible formulation defect, not immediately safety-critical.",
    }
    with patch("app.ai.nodes.risk_classify.call_llm_for_json", return_value=mocked_llm_response):
        created = client.post("/api/v1/complaints", json=COMPLETE_PAYLOAD)
        cid = created.json()["id"]
        response = client.post(f"/api/v1/complaints/{cid}/risk-assessment")

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] == "Major"
    assert body["business_rule_applied"] is False
    assert "formulation defect" in body["reasoning"]
    assert body["recommended_escalation"] == "Route to standard QA investigation queue."


def test_risk_assessment_safety_keyword_forces_critical_regardless_of_llm(client):
    """The deterministic safety-net rule must override the LLM's output even
    on this re-assessment path, not just at initial intake — this is the
    whole point of it being a hard rule instead of a prompt instruction."""
    payload = dict(
        COMPLETE_PAYLOAD,
        batch_lot_number="RISK-BATCH-001",
        description="Patient reported a severe allergic reaction after taking this product.",
    )
    mocked_llm_response = {
        "severity": "Minor",  # deliberately wrong, to prove the business rule overrides it
        "priority": "Low",
        "confidence": 0.5,
        "reasoning": "Isolated report, low apparent severity.",
    }
    with patch("app.ai.nodes.risk_classify.call_llm_for_json", return_value=mocked_llm_response):
        created = client.post("/api/v1/complaints", json=payload)
        cid = created.json()["id"]
        response = client.post(f"/api/v1/complaints/{cid}/risk-assessment")

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] == "Critical"
    assert body["priority"] == "High"
    assert body["business_rule_applied"] is True
    assert body["recommended_escalation"] == "Immediate escalation to QA lead and regulatory reporting review required."


def test_risk_assessment_nonexistent_complaint_returns_404(client):
    response = client.post("/api/v1/complaints/999999/risk-assessment")
    assert response.status_code == 404
