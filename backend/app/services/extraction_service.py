"""
Orchestrates the /complaints/extract flow: parse the uploaded document (or
use pasted text directly) -> invoke the LangGraph pipeline -> return a
response the frontend can render into the form.

This service is deliberately stateless with respect to the DB — no
complaint exists yet at this point, so nothing is persisted here. That's
also why it doesn't take a repository/db session at all, unlike
ComplaintService below.
"""

import logging
import uuid

from app.ai.graph import run_extraction_pipeline
from app.core.exceptions import FileTooLargeError, NoInputProvidedError
from app.schemas.extraction import ExtractedFields, ExtractionResponse
from app.services.document_service import parse_document

logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(self, max_upload_size_mb: int):
        self.max_upload_bytes = max_upload_size_mb * 1024 * 1024

    def extract_from_file(self, file_bytes: bytes, file_extension: str) -> ExtractionResponse:
        if len(file_bytes) > self.max_upload_bytes:
            raise FileTooLargeError(f"File exceeds {self.max_upload_bytes // (1024*1024)}MB limit")

        text, input_type = parse_document(file_bytes, file_extension)
        if not text:
            logger.warning(f"Parsed document produced empty text (type={input_type})")
        return self._run_pipeline(text, input_type)

    def extract_from_text(self, text: str) -> ExtractionResponse:
        if not text or not text.strip():
            raise NoInputProvidedError("No text provided for extraction")
        return self._run_pipeline(text, input_type="text")

    def _run_pipeline(self, raw_input: str, input_type: str) -> ExtractionResponse:
        result = run_extraction_pipeline(raw_input=raw_input, input_type=input_type)

        logger.info(
            f"Extraction complete | input_type={input_type} "
            f"| confidence={result.get('extraction_confidence')} "
            f"| requires_manual_review={result.get('requires_manual_review')}"
        )

        return ExtractionResponse(
            extraction_id=str(uuid.uuid4()),
            fields=ExtractedFields(**result["fields"]),
            confidence_score=result.get("extraction_confidence", 0.0),
            model_used="gemma2-9b-it",
            missing_required_fields=result.get("missing_required_fields", []),
        )
