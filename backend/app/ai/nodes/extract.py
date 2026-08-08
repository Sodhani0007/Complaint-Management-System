"""
Node: extract_fields

Calls the LLM to pull structured fields out of raw_input. On the first call
uses the standard prompt; if this is a retry pass (retry_count > 0), it uses
the targeted retry prompt instead, built from the missing fields the
previous validate_extraction pass found. This is the node that actually
implements the "retry loop" described in the architecture doc — the routing
decision itself lives in validate_extraction's conditional edge, not here.
"""

import logging

from app.ai.llm_client import LLMJSONError, call_llm_for_json
from app.ai.prompts.extraction_prompt import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_retry_prompt,
    build_extraction_user_prompt,
)
from app.ai.state import ComplaintGraphState
from app.config import settings

logger = logging.getLogger(__name__)


def extract_fields(state: ComplaintGraphState) -> dict:
    raw_input = state["raw_input"]
    retry_count = state.get("retry_count", 0)
    validation_errors = state.get("validation_errors", [])

    if retry_count > 0 and validation_errors:
        user_prompt = build_extraction_retry_prompt(raw_input, validation_errors)
    else:
        user_prompt = build_extraction_user_prompt(raw_input)

    try:
        result = call_llm_for_json(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model_name=settings.GROQ_EXTRACTION_MODEL,
        )
    except LLMJSONError as e:
        # Total LLM failure (not a validation issue) — return an empty
        # extraction with zero confidence rather than raising, so the graph
        # can route to manual review gracefully instead of the whole
        # request 500ing.
        logger.error(f"Extraction LLM call failed entirely: {e}")
        return {
            "extracted_fields": {},
            "extraction_confidence": 0.0,
        }

    confidence = result.pop("confidence", 0.0)
    return {
        "extracted_fields": result,
        "extraction_confidence": float(confidence),
    }
