"""
Node: validate_extraction

Checks the extraction against two things: (1) required fields present and
non-null, (2) confidence above a minimum threshold. Does NOT itself decide
where to go next — that's the job of `decide_after_validation`, a separate
routing function registered as a conditional edge in graph.py. Keeping the
node (which mutates state) and the router (which only reads state and
returns a string) separate is a LangGraph convention worth following: nodes
update state, conditional-edge functions decide the next node name.
"""

from app.ai.prompts.extraction_prompt import REQUIRED_FIELDS
from app.ai.state import ComplaintGraphState

MIN_CONFIDENCE_THRESHOLD = 0.5
MAX_RETRIES = 2


def validate_extraction(state: ComplaintGraphState) -> dict:
    fields = state.get("extracted_fields") or {}
    confidence = state.get("extraction_confidence") or 0.0

    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]

    errors: list[str] = []
    if missing:
        errors.append(f"missing_required_fields: {', '.join(missing)}")
    if confidence < MIN_CONFIDENCE_THRESHOLD:
        errors.append(f"low_confidence: {confidence}")

    return {
        "validation_errors": missing,  # field names, not the formatted string — the retry prompt needs raw names
        "retry_count": state.get("retry_count", 0) + 1,
    }


def decide_after_validation(state: ComplaintGraphState) -> str:
    """
    Routing logic:
    - if required fields are missing AND we haven't hit the retry cap → loop back to extract_fields
    - otherwise (valid, or retries exhausted) → proceed to classify_risk,
      with `requires_manual_review` set so the frontend can flag remaining gaps
    """
    missing = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)

    if missing and retry_count <= MAX_RETRIES:
        return "retry"
    return "proceed"
