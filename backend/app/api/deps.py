"""
Central place for FastAPI Depends() providers. Routers depend on these
functions, never construct services/repositories themselves — this is what
makes it possible to override get_db in tests (e.g. point it at an in-memory
SQLite session) without touching a single router.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.repositories.complaint_repository import ComplaintRepository
from app.services.complaint_service import ComplaintService
from app.services.extraction_service import ExtractionService


def get_complaint_repository(db: Session = Depends(get_db)) -> ComplaintRepository:
    return ComplaintRepository(db)


def get_complaint_service(
    repository: ComplaintRepository = Depends(get_complaint_repository),
) -> ComplaintService:
    return ComplaintService(repository)


def get_extraction_service() -> ExtractionService:
    return ExtractionService(max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB)
