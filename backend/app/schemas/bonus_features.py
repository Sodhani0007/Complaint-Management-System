"""
Structured output schemas for the bonus AI features. Every feature returns
one of these — never free-form text — per the "no hallucinated prose"
requirement. Kept in their own file rather than extension.py/complaint.py
since these are a genuinely separate concern (on-demand AI insights on an
already-saved complaint, not the intake flow itself).
"""

from pydantic import BaseModel, Field


class CompletenessCheckResult(BaseModel):
    is_complete: bool
    missing_fields: list[str] = []
    warnings: list[str] = []
    suggested_next_action: str
    confidence: float = Field(ge=0.0, le=1.0)


class SummaryResult(BaseModel):
    summary: str
    product: str | None = None
    batch: str | None = None
    customer: str | None = None
    issue: str | None = None
    severity: str | None = None
    potential_impact: str
    recommended_next_step: str
    confidence: float = Field(ge=0.0, le=1.0)


class DuplicateMatch(BaseModel):
    matched_complaint_id: int
    similarity_score: float = Field(ge=0.0, le=1.0)
    reason: str


class DuplicateCheckResult(BaseModel):
    is_duplicate: bool
    matches: list[DuplicateMatch] = []


class RiskAssessmentResult(BaseModel):
    """Extends what classify_risk already produces with a persisted,
    retrievable shape — see complaint_service.get_risk_assessment."""

    severity: str
    priority: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    recommended_escalation: str
    business_rule_applied: bool
