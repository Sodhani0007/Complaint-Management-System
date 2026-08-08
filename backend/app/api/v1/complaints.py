"""
HTTP layer only: parse the request, call the service, shape the response.
No business logic and no direct DB/repository access should ever land here
— see complaint_service.py and extraction_service.py for that.
"""

import logging
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_complaint_service, get_extraction_service
from app.core.exceptions import (
    ComplaintNotFoundError,
    FileTooLargeError,
    InvalidBatchReferenceError,
    NoInputProvidedError,
    UnsupportedFileTypeError,
)
from app.schemas.bonus_features import (
    CompletenessCheckResult,
    DuplicateCheckResult,
    RiskAssessmentResult,
    SummaryResult,
)
from app.schemas.complaint import ComplaintCreate, ComplaintListParams, ComplaintRead
from app.schemas.extraction import ExtractionResponse
from app.services.complaint_service import ComplaintService
from app.services.document_service import SUPPORTED_EXTENSIONS
from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.post("/extract", response_model=ExtractionResponse)
async def extract_complaint(
    file: UploadFile | None = File(default=None),
    text: str | None = None,
    extraction_service: ExtractionService = Depends(get_extraction_service),
):
    if file is None and not text:
        raise HTTPException(status_code=400, detail="Either 'file' or 'text' must be provided")

    # Validated before the try block on purpose — this used to raise
    # HTTPException from inside the try/except below, where the bare
    # `except Exception` handler was catching it (HTTPException IS an
    # Exception) and converting a deliberate 400 into a misleading 502.
    # Caught by test_extract_from_file_rejects_unsupported_extension.
    ext = os.path.splitext(file.filename or "")[1].lower() if file is not None else None
    if file is not None and ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    try:
        if file is not None:
            # Read in bounded chunks and abort as soon as the limit is
            # exceeded, rather than reading the whole file into memory
            # first and rejecting it afterward — the previous version did
            # exactly that, which meant an oversized upload was fully
            # buffered before extraction_service ever got a chance to
            # reject it. A malicious multi-GB upload would have consumed
            # memory regardless of the eventual 413.
            max_bytes = extraction_service.max_upload_bytes
            chunk_size = 1024 * 1024  # 1MB
            chunks: list[bytes] = []
            total_read = 0
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_read += len(chunk)
                if total_read > max_bytes:
                    raise FileTooLargeError(f"File exceeds {max_bytes // (1024 * 1024)}MB limit")
                chunks.append(chunk)
            file_bytes = b"".join(chunks)
            return extraction_service.extract_from_file(file_bytes, ext)

        return extraction_service.extract_from_text(text)

    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    except NoInputProvidedError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during extraction")
        raise HTTPException(status_code=502, detail="AI extraction service unavailable, please try again") from e


@router.post("", response_model=ComplaintRead, status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    service: ComplaintService = Depends(get_complaint_service),
):
    try:
        return service.create_complaint(payload)
    except InvalidBatchReferenceError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/{complaint_id}", response_model=ComplaintRead)
def get_complaint(complaint_id: int, service: ComplaintService = Depends(get_complaint_service)):
    try:
        return service.get_complaint(complaint_id)
    except ComplaintNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("", response_model=list[ComplaintRead])
def list_complaints(
    params: ComplaintListParams = Depends(),
    service: ComplaintService = Depends(get_complaint_service),
):
    return service.list_complaints(params)


# --- Bonus AI features — all operate on an already-saved complaint ---


@router.post("/{complaint_id}/completeness-check", response_model=CompletenessCheckResult)
def completeness_check(complaint_id: int, service: ComplaintService = Depends(get_complaint_service)):
    try:
        return service.check_completeness(complaint_id)
    except ComplaintNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{complaint_id}/summary", response_model=SummaryResult)
def complaint_summary(complaint_id: int, service: ComplaintService = Depends(get_complaint_service)):
    try:
        return service.generate_summary(complaint_id)
    except ComplaintNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{complaint_id}/duplicate-check", response_model=DuplicateCheckResult)
def duplicate_check(complaint_id: int, service: ComplaintService = Depends(get_complaint_service)):
    try:
        return service.check_duplicates(complaint_id)
    except ComplaintNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{complaint_id}/risk-assessment", response_model=RiskAssessmentResult)
def risk_assessment(complaint_id: int, service: ComplaintService = Depends(get_complaint_service)):
    try:
        return service.get_risk_assessment(complaint_id)
    except ComplaintNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
