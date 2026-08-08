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

    try:
        if file is not None:
            ext = os.path.splitext(file.filename or "")[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
                )
            file_bytes = await file.read()
            return extraction_service.extract_from_file(file_bytes, ext)

        return extraction_service.extract_from_text(text)

    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    except NoInputProvidedError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
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
