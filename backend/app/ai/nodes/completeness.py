"""
Completeness Checker — deliberately NOT an LLM call for the core
is_complete/missing_fields determination. A required-fields check is a
correctness-critical, deterministic question ("is batch_lot_number null or
not?") — asking an LLM to answer it would trade a 100%-reliable check for a
probabilistic one with no upside. This mirrors the same reasoning as the
risk_classify.py safety-keyword rule: use AI where judgment is genuinely
needed, use plain code where it isn't.

The `warnings` list is softer, more qualitative territory (e.g. "description
is very short for a Critical-severity complaint") where a lightweight LLM
pass genuinely adds value beyond what a rule can express — that part is
optional and best-effort; if it fails, the deterministic result still
returns correctly.
"""

import logging

from app.ai.llm_client import call_llm_for_json
from app.config import settings

logger = logging.getLogger(__name__)

REQUIRED_FOR_COMPLETENESS = [
    "complaint_source",
    "customer_name",
    "product_name",
    "batch_lot_number",
    "manufacturing_date",
    "expiry_date",
    "quantity_affected",
    "complaint_type",
    "complaint_date",
    "description",
    "severity",
    "priority",
]

FIELD_LABELS = {
    "complaint_source": "Complaint Source",
    "customer_name": "Customer Name",
    "product_name": "Product Name",
    "batch_lot_number": "Batch/Lot Number",
    "manufacturing_date": "Manufacturing Date",
    "expiry_date": "Expiry Date",
    "quantity_affected": "Quantity Affected",
    "complaint_type": "Complaint Type",
    "complaint_date": "Complaint Date",
    "description": "Detailed Complaint Description",
    "severity": "Initial Severity",
    "priority": "Priority",
}

_WARNING_SYSTEM_PROMPT = """You are a pharmaceutical QA assistant reviewing a complaint record
for completeness. Fields already confirmed present are given — do not comment on missing fields,
only note if any PRESENT field looks unusually thin or vague for its purpose (e.g. a one-word
description on a Critical complaint). If everything looks reasonable, return an empty warnings list.
Never invent information not present. Respond with valid JSON only: {"warnings": [string, ...]}"""


def check_completeness(complaint_data: dict) -> dict:
    missing = [
        FIELD_LABELS[f] for f in REQUIRED_FOR_COMPLETENESS if not complaint_data.get(f)
    ]
    is_complete = len(missing) == 0

    warnings: list[str] = []
    if is_complete:
        # Only worth the LLM call when the deterministic check already
        # passes — no point qualitatively reviewing a record we already
        # know is missing required data.
        try:
            present_fields = {k: v for k, v in complaint_data.items() if v is not None}
            result = call_llm_for_json(
                system_prompt=_WARNING_SYSTEM_PROMPT,
                user_prompt=f"Complaint fields:\n{present_fields}",
                model_name=settings.GROQ_EXTRACTION_MODEL,
                max_retries=1,  # this is a nice-to-have, not worth the full retry budget
            )
            warnings = result.get("warnings", [])
        except Exception as e:
            # Deliberately broad: this pass is optional/best-effort (see
            # module docstring) — ANY failure here (LLMJSONError, a network
            # error that somehow escapes the client wrapper, a KeyError on
            # unexpected response shape) should degrade to "no warnings"
            # rather than take down the whole completeness-check endpoint.
            logger.warning(f"Completeness warning-check LLM call failed (non-fatal): {e}")
            warnings = []

    suggested_action = (
        "Ready for QA triage assignment."
        if is_complete and not warnings
        else "Review flagged fields before triage."
        if is_complete
        else f"Request missing information before proceeding: {', '.join(missing)}."
    )

    return {
        "is_complete": is_complete,
        "missing_fields": missing,
        "warnings": warnings,
        "suggested_next_action": suggested_action,
        # Always 1.0: the missing-fields determination is deterministic code,
        # not a probabilistic AI guess — there's nothing to be uncertain about.
        "confidence": 1.0,
    }
