"""Regression cases for the live demo's negated safety-event escalation."""

from unittest.mock import patch

import pytest

from app.ai.nodes.risk_classify import _contains_safety_keyword, classify_risk


@pytest.mark.parametrize("description", [
    "Dented outer cartons. No injury or adverse event.",
    "No adverse events reported.",
    "NO ALLERGIC REACTION WAS OBSERVED.",
    "No evidence of contamination; cosmetic damage only.",
    "No injury, allergic reaction, or adverse event.",
    "No hospitalization or anaphylaxis",
])
def test_explicit_denial_does_not_trigger_keyword_override(description):
    assert not _contains_safety_keyword(description)


@pytest.mark.parametrize("description", [
    "Patient suffered an allergic reaction.",
    "Suspected contamination.",
    "Contamination cannot be ruled out.",
    "No evidence that contamination can be ruled out.",
    "No improvement after an adverse event.",
    "Not only contamination but also wrong product.",
    "No adverse event. Contamination was detected.",
    "Contamination detected. No adverse event.",
    "No allergic reaction, but an adverse event occurred.",
    "No contamination was reported initially, but contamination was later confirmed.",
    "The product was contaminated.",
    "Anaphylactic shock reported.",
])
def test_positive_or_uncertain_safety_mentions_still_escalate(description):
    assert _contains_safety_keyword(description)


@pytest.mark.parametrize("severity,priority", [("Minor", "Low"), ("Critical", "High")])
def test_denial_preserves_model_assessment_instead_of_forcing_downgrade(severity, priority):
    assessment = {"severity": severity, "priority": priority, "confidence": 0.9, "reasoning": "Model assessment."}
    with patch("app.ai.nodes.risk_classify.call_llm_for_json", return_value=assessment):
        result = classify_risk({"extracted_fields": {"description": "No injury or adverse event."}})
    assert result["risk_assessment"] == assessment


def test_reassessment_endpoint_uses_same_negation_rule(client):
    created = client.post("/api/v1/complaints", json={
        "product_name": "Synthetic test product",
        "batch_lot_number": "NEGATION-001",
        "description": "Dented outer carton. No injury or adverse event.",
    })
    assert created.status_code == 201
    with patch("app.ai.nodes.risk_classify.call_llm_for_json", return_value={
        "severity": "Minor", "priority": "Low", "confidence": 0.9, "reasoning": "Cosmetic damage only.",
    }):
        response = client.post(f"/api/v1/complaints/{created.json()['id']}/risk-assessment")
    assert response.status_code == 200
    assert response.json()["severity"] == "Minor"
    assert response.json()["business_rule_applied"] is False
