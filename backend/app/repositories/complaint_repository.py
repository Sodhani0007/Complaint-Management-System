"""
Repository layer: SQLAlchemy queries only. No business rules live here —
e.g. "does this batch have prior complaints" is a query this repository
answers, but "should that escalate priority" is a decision made in
services/complaint_service.py. This split is what makes the service layer
unit-testable with a mocked repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_extraction import AIExtraction
from app.models.batch import Batch
from app.models.complaint import Complaint, ComplaintStatus, Severity
from app.models.product import Product


class ComplaintRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- products / batches ---

    def get_or_create_product(self, name: str, strength_grade: str | None) -> Product:
        stmt = select(Product).where(Product.name == name)
        product = self.db.execute(stmt).scalar_one_or_none()
        if product:
            return product
        product = Product(name=name, strength_grade=strength_grade)
        self.db.add(product)
        self.db.flush()  # assigns product.id without committing the transaction yet
        return product

    def get_or_create_batch(self, product_id: int, lot_number: str, manufacture_date, expiry_date) -> Batch:
        stmt = select(Batch).where(Batch.product_id == product_id, Batch.lot_number == lot_number)
        batch = self.db.execute(stmt).scalar_one_or_none()
        if batch:
            return batch
        batch = Batch(
            product_id=product_id,
            lot_number=lot_number,
            manufacture_date=manufacture_date,
            expiry_date=expiry_date,
        )
        self.db.add(batch)
        self.db.flush()
        return batch

    def count_prior_complaints_for_batch(self, batch_id: int) -> int:
        stmt = select(Complaint).where(Complaint.batch_id == batch_id)
        return len(self.db.execute(stmt).scalars().all())

    # --- complaints ---

    def create_complaint(self, complaint: Complaint) -> Complaint:
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def get_complaint(self, complaint_id: int) -> Complaint | None:
        return self.db.get(Complaint, complaint_id)

    def list_complaints(
        self,
        page: int,
        page_size: int,
        severity: Severity | None = None,
        status: ComplaintStatus | None = None,
        product_id: int | None = None,
    ) -> list[Complaint]:
        stmt = select(Complaint)
        if severity:
            stmt = stmt.where(Complaint.severity == severity)
        if status:
            stmt = stmt.where(Complaint.status == status)
        if product_id:
            stmt = stmt.where(Complaint.product_id == product_id)
        stmt = stmt.order_by(Complaint.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(self.db.execute(stmt).scalars().all())

    # --- AI extraction audit trail ---

    def save_extraction_record(
        self, complaint_id: int | None, extracted_json: dict, model_used: str, confidence_score: float
    ) -> AIExtraction:
        record = AIExtraction(
            complaint_id=complaint_id,
            extracted_json=extracted_json,
            model_used=model_used,
            confidence_score=confidence_score,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
