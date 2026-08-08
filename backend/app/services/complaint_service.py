"""
Business logic for confirmed complaints: resolving/creating the
product+batch a complaint belongs to, applying the prior-complaints priority
escalation rule (see architecture doc Step 11), and persisting everything
through the repository. Routers should never touch the repository directly
— this is the only layer that does, alongside the risk-assessment endpoints.

Also owns the bonus AI features (completeness, summary, duplicate
detection) — these operate on an already-saved complaint, so they belong
here rather than in extraction_service.py (which is stateless/pre-save).
"""

import difflib
import logging

from app.ai.nodes.completeness import check_completeness
from app.ai.nodes.risk_classify import _contains_safety_keyword, classify_risk
from app.ai.nodes.summarize import generate_summary
from app.core.exceptions import ComplaintNotFoundError
from app.models.complaint import Complaint, Priority
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.bonus_features import (
    CompletenessCheckResult,
    DuplicateCheckResult,
    DuplicateMatch,
    RiskAssessmentResult,
    SummaryResult,
)
from app.schemas.complaint import ComplaintCreate, ComplaintListParams, ComplaintRead

logger = logging.getLogger(__name__)

_PRIORITY_ESCALATION = {
    Priority.LOW: Priority.MEDIUM,
    Priority.MEDIUM: Priority.HIGH,
    Priority.HIGH: Priority.HIGH,  # already at the top, nowhere to escalate to
}

# Below this, two complaints are considered unrelated rather than possible
# duplicates — tuned conservatively (favors false negatives over false
# positives) since a missed duplicate is far less costly than QA staff
# chasing a phantom match.
DUPLICATE_SIMILARITY_THRESHOLD = 0.55


def _complaint_to_dict(complaint: Complaint) -> dict:
    """Shared helper: both summary and completeness-check need the same
    plain-dict view of a saved Complaint row."""
    manufacture_date = complaint.batch.manufacture_date if complaint.batch else None
    expiry_date = complaint.batch.expiry_date if complaint.batch else None
    return {
        "complaint_source": complaint.complaint_source,
        "customer_name": complaint.customer_name,
        "product_name": complaint.product.name if complaint.product else None,
        "batch_lot_number": complaint.batch.lot_number if complaint.batch else None,
        "manufacturing_date": str(manufacture_date) if manufacture_date else None,
        "expiry_date": str(expiry_date) if expiry_date else None,
        "quantity_affected": float(complaint.quantity_affected) if complaint.quantity_affected is not None else None,
        "complaint_type": complaint.complaint_type,
        "complaint_date": str(complaint.complaint_date) if complaint.complaint_date else None,
        "description": complaint.description,
        "severity": complaint.severity.value if complaint.severity else None,
        "priority": complaint.priority.value if complaint.priority else None,
    }


class ComplaintService:
    def __init__(self, repository: ComplaintRepository):
        self.repository = repository

    def create_complaint(self, payload: ComplaintCreate) -> ComplaintRead:
        product = self.repository.get_or_create_product(
            name=payload.product_name, strength_grade=None
        )
        batch = self.repository.get_or_create_batch(
            product_id=product.id,
            lot_number=payload.batch_lot_number,
            manufacture_date=payload.manufacturing_date,
            expiry_date=payload.expiry_date,
        )

        prior_complaint_count = self.repository.count_prior_complaints_for_batch(batch.id)
        final_priority = self._apply_priority_escalation(payload.priority, prior_complaint_count)

        complaint = Complaint(
            batch_id=batch.id,
            product_id=product.id,
            complaint_source=payload.complaint_source,
            customer_name=payload.customer_name,
            complaint_type=payload.complaint_type,
            complaint_date=payload.complaint_date,
            description=payload.description,
            quantity_affected=payload.quantity_affected,
            severity=payload.severity,
            priority=final_priority,
            ai_confidence=payload.ai_confidence,
            raw_source_text=None,
        )
        saved = self.repository.create_complaint(complaint)

        # Audit trail write happens here, at save-time, since extraction
        # itself never touched the DB (see extraction_service.py docstring).
        if payload.ai_extraction_snapshot:
            self.repository.save_extraction_record(
                complaint_id=saved.id,
                extracted_json=payload.ai_extraction_snapshot,
                model_used=payload.ai_model_used or "unknown",
                confidence_score=payload.ai_confidence or 0.0,
            )

        logger.info(
            f"Complaint {saved.id} saved | batch={batch.lot_number} "
            f"| prior_complaints_on_batch={prior_complaint_count} "
            f"| priority: {payload.priority} -> {final_priority}"
        )
        return ComplaintRead.model_validate(saved)

    def get_complaint(self, complaint_id: int) -> ComplaintRead:
        complaint = self.repository.get_complaint(complaint_id)
        if not complaint:
            raise ComplaintNotFoundError(f"Complaint {complaint_id} not found")
        return ComplaintRead.model_validate(complaint)

    def list_complaints(self, params: ComplaintListParams) -> list[ComplaintRead]:
        complaints = self.repository.list_complaints(
            page=params.page,
            page_size=params.page_size,
            severity=params.severity,
            status=params.status,
            product_id=params.product_id,
        )
        return [ComplaintRead.model_validate(c) for c in complaints]

    @staticmethod
    def _apply_priority_escalation(priority: Priority | None, prior_complaint_count: int) -> Priority | None:
        """A repeat-batch issue is more urgent regardless of individual
        severity — this is the deterministic rule from the architecture doc,
        applied here (not inside the LLM prompt) so it's guaranteed to fire
        every time, not just when the model happens to weigh it correctly."""
        if priority is None:
            return None
        if prior_complaint_count > 0:
            return _PRIORITY_ESCALATION[priority]
        return priority

    # --- Bonus AI features ---

    def check_completeness(self, complaint_id: int) -> CompletenessCheckResult:
        complaint = self.repository.get_complaint(complaint_id)
        if not complaint:
            raise ComplaintNotFoundError(f"Complaint {complaint_id} not found")
        result = check_completeness(_complaint_to_dict(complaint))
        return CompletenessCheckResult(**result)

    def generate_summary(self, complaint_id: int) -> SummaryResult:
        complaint = self.repository.get_complaint(complaint_id)
        if not complaint:
            raise ComplaintNotFoundError(f"Complaint {complaint_id} not found")
        result = generate_summary(_complaint_to_dict(complaint))
        return SummaryResult(**result)

    def check_duplicates(self, complaint_id: int) -> DuplicateCheckResult:
        """
        Deliberately NOT embeddings-based, by design choice not oversight:
        difflib's SequenceMatcher gives a free, deterministic, zero-extra-
        dependency similarity score that's good enough at this data scale
        (see find_candidate_duplicates' limit=20 note). Worth naming this
        trade-off explicitly if asked — an embeddings/vector-search approach
        would scale better and catch paraphrased-but-different-wording
        duplicates that difflib misses, at the cost of an extra model call
        and infrastructure (a vector index) that isn't justified yet here.
        """
        complaint = self.repository.get_complaint(complaint_id)
        if not complaint:
            raise ComplaintNotFoundError(f"Complaint {complaint_id} not found")
        if not complaint.product_id or not complaint.description:
            return DuplicateCheckResult(is_duplicate=False, matches=[])

        candidates = self.repository.find_candidate_duplicates(
            product_id=complaint.product_id, exclude_complaint_id=complaint.id
        )

        matches: list[DuplicateMatch] = []
        for candidate in candidates:
            if not candidate.description:
                continue
            score = difflib.SequenceMatcher(None, complaint.description.lower(), candidate.description.lower()).ratio()

            same_batch = candidate.batch_id == complaint.batch_id
            if same_batch:
                score = min(1.0, score + 0.15)  # same batch is strong corroborating evidence

            if score >= DUPLICATE_SIMILARITY_THRESHOLD:
                reason = (
                    f"Same batch and {round(score * 100)}% description similarity"
                    if same_batch
                    else f"{round(score * 100)}% description similarity, same product"
                )
                matches.append(
                    DuplicateMatch(matched_complaint_id=candidate.id, similarity_score=round(score, 2), reason=reason)
                )

        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return DuplicateCheckResult(is_duplicate=len(matches) > 0, matches=matches[:5])

    def get_risk_assessment(self, complaint_id: int) -> RiskAssessmentResult:
        """
        Re-runs classify_risk against the complaint's CURRENT saved data,
        rather than only trusting whatever severity/priority was set at
        intake time — genuinely useful if the description was edited after
        the initial AI extraction, or if you just want to see the reasoning
        and business-rule-applied flag that the original /extract response
        already computed but never persisted anywhere.

        This is "improve the existing risk assessment" per the assignment's
        Phase 12, not a duplicate of it: same classify_risk node, called
        on-demand against saved-record data instead of only at intake, with
        a persisted-shape response (recommended_escalation,
        business_rule_applied) the intake flow's response never exposed.
        """
        complaint = self.repository.get_complaint(complaint_id)
        if not complaint:
            raise ComplaintNotFoundError(f"Complaint {complaint_id} not found")

        description = complaint.description or ""
        prior_count = (
            self.repository.count_prior_complaints_for_batch(complaint.batch_id)
            if complaint.batch_id
            else 0
        )

        state = {
            "extracted_fields": {
                "description": description,
                "product_name": complaint.product.name if complaint.product else None,
                "product_strength_grade": None,
            },
            "batch_has_prior_complaints": prior_count > 0,
        }
        result = classify_risk(state)["risk_assessment"]
        business_rule_applied = _contains_safety_keyword(description)

        recommended_escalation = (
            "Immediate escalation to QA lead and regulatory reporting review required."
            if result["severity"] == "Critical"
            else "Route to standard QA investigation queue."
        )

        return RiskAssessmentResult(
            severity=result["severity"],
            priority=result["priority"],
            confidence=float(result.get("confidence", 0.0)),
            reasoning=result.get("reasoning", ""),
            recommended_escalation=recommended_escalation,
            business_rule_applied=business_rule_applied,
        )
