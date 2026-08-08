"""
Node: classify_risk

Calls the LLM for severity/priority, then applies a deterministic safety-net
rule ON TOP of the LLM output: if the description contains explicit safety
keywords, severity is force-set to Critical regardless of what the model
returned. This is a deliberate design decision (see architecture doc, Step
11) — an LLM should never be the sole gate on a safety-critical
classification in a regulated domain. The business rule is intentionally
simple and auditable (keyword match), not another AI call, precisely because
it needs to be a hard guarantee, not a probabilistic one.
"""

import logging

from app.ai.llm_client import LLMJSONError, call_llm_for_json
from app.ai.prompts.risk_prompt import RISK_SYSTEM_PROMPT, build_risk_user_prompt
from app.ai.state import ComplaintGraphState
from app.config import settings

logger = logging.getLogger(__name__)

SAFETY_KEYWORDS = [
    "adverse event",
    "allergic reaction",
    "contamination",
    "contaminated",
    "hospitalization",
    "anaphyla",
    "wrong product",
    "mix-up",
    "mix up",
]


def _contains_safety_keyword(description: str) -> bool:
    text = description.lower()
    return any(kw in text for kw in SAFETY_KEYWORDS)


def classify_risk(state: ComplaintGraphState) -> dict:
    fields = state.get("extracted_fields") or {}
    description = fields.get("description") or ""
    product_context = f"{fields.get('product_name', 'unknown product')} ({fields.get('product_strength_grade', 'n/a')})"

    # NOTE: batch history lookup (prior complaints on this batch) happens in
    # the service layer before the graph is invoked and is passed in via
    # state — kept out of this node so the AI layer has no direct DB access,
    # preserving the layering from the architecture doc (Step 7).
    batch_has_prior_complaints = state.get("batch_has_prior_complaints", False)

    try:
        result = call_llm_for_json(
            system_prompt=RISK_SYSTEM_PROMPT,
            user_prompt=build_risk_user_prompt(description, product_context, batch_has_prior_complaints),
            model_name=settings.GROQ_REASONING_MODEL,
        )
    except LLMJSONError as e:
        logger.error(f"Risk classification LLM call failed entirely: {e}")
        result = {
            "severity": "Major",  # fail toward caution, never toward under-classifying
            "priority": "Medium",
            "confidence": 0.0,
            "reasoning": "AI classification unavailable — defaulted to Major/Medium pending manual review.",
        }

    if _contains_safety_keyword(description):
        result["severity"] = "Critical"
        result["priority"] = "High"
        result["reasoning"] = (
            "Escalated to Critical/High by business rule: description contains a safety-relevant keyword. "
            + result.get("reasoning", "")
        )

    return {"risk_assessment": result}
