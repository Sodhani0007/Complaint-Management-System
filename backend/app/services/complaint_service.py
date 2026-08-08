"""
Business logic for confirmed complaints: resolving/creating the
product+batch a complaint belongs to, applying the prior-complaints priority
escalation rule (see architecture doc Step 11), and persisting everything
through the repository. Routers should never touch the repository directly
— this is the only layer that does, alongside the risk-assessment endpoints.
"""

import logging

from app.core.exceptions import ComplaintNotFoundError
from app.models.complaint import Complaint, Priority
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.complaint import ComplaintCreate, ComplaintListParams, ComplaintRead

logger = logging.getLogger(__name__)

_PRIORITY_ESCALATION = {
    Priority.LOW: Priority.MEDIUM,
    Priority.MEDIUM: Priority.HIGH,
    Priority.HIGH: Priority.HIGH,  # already at the top, nowhere to escalate to
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
