"""
Schemas for the AI extraction flow — what the LLM must return, and what the
API returns to the frontend before anything is saved to the DB.

Why these are separate from schemas/complaint.py: an extraction result is
provisional (unconfirmed, AI-generated, possibly wrong) while a Complaint is
confirmed data. Mixing them would blur "AI said" and "human confirmed",
which is the exact distinction the whole product is built around.
"""

from datetime import date

from pydantic import BaseModel, Field, field_validator


class ExtractedFields(BaseModel):
    """
    Mirrors the LLM's required JSON schema (see ai/prompts/extraction_prompt.py).
    Every field is optional at this layer on purpose — the LLM may legitimately
    not find a value, and we'd rather surface `null` to the reviewer than have
    a validation error hide the whole extraction.
    """

    complaint_source: str | None = None
    customer_name: str | None = None
    product_name: str | None = None
    product_strength_grade: str | None = None
    batch_lot_number: str | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    quantity_affected: float | None = None
    complaint_type: str | None = None
    complaint_date: date | None = None
    description: str | None = None
    initial_severity: str | None = None
    priority: str | None = None

    @field_validator("expiry_date")
    @classmethod
    def expiry_after_manufacture(cls, v: date | None, info):
        mfg = info.data.get("manufacturing_date")
        if v and mfg and v < mfg:
            raise ValueError("expiry_date cannot be before manufacturing_date")
        return v


class ExtractionResponse(BaseModel):
    extraction_id: str
    fields: ExtractedFields
    confidence_score: float = Field(ge=0.0, le=1.0)
    model_used: str
    missing_required_fields: list[str] = []


class ExtractionRequest(BaseModel):
    """Used only for the text-paste path; file uploads go through FastAPI's
    UploadFile, not JSON, so this schema doesn't cover that branch."""

    text: str = Field(min_length=1, max_length=20000)
