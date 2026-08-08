"""
Request/response contracts for the confirmed-complaint API.

ComplaintCreate is intentionally stricter than ExtractedFields (Step above):
by the time a user hits "Save Complaint", product_name/batch/description are
no longer optional — this is where the "AI-assisted, human-verified" model
becomes enforced by the type system rather than just a UI convention.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.complaint import ComplaintStatus, Priority, Severity


class ComplaintBase(BaseModel):
    complaint_source: str | None = None
    customer_name: str | None = None
    complaint_type: str | None = None
    complaint_date: date | None = None
    quantity_affected: float | None = None
    severity: Severity | None = None
    priority: Priority | None = None


class ComplaintCreate(ComplaintBase):
    product_name: str = Field(min_length=1)
    batch_lot_number: str = Field(min_length=1)
    description: str = Field(min_length=1)
    manufacturing_date: date | None = None
    expiry_date: date | None = None

    # Carried forward from the /extract response so the AI audit trail can be
    # written at save-time — extraction itself is stateless and doesn't touch
    # the DB (see AI Requirements in the architecture doc), so the frontend
    # is the thing passing this back to us rather than us caching it server-side.
    ai_extraction_snapshot: dict | None = None
    ai_model_used: str | None = None
    ai_confidence: float | None = None

    @field_validator("expiry_date")
    @classmethod
    def expiry_after_manufacture(cls, v: date | None, info):
        mfg = info.data.get("manufacturing_date")
        if v and mfg and v < mfg:
            raise ValueError("expiry_date cannot be before manufacturing_date")
        return v


class ComplaintUpdate(ComplaintBase):
    status: ComplaintStatus | None = None


class ComplaintRead(ComplaintBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int | None
    product_id: int | None
    description: str | None
    ai_confidence: Decimal | None
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime


class ComplaintListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    severity: Severity | None = None
    status: ComplaintStatus | None = None
    product_id: int | None = None
