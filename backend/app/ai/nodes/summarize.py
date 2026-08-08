"""
Complaint Summary — a genuine single-call LLM feature (unlike completeness,
there's no deterministic way to write good prose). Follows the exact same
call_llm_for_json + retry pattern as extract.py/risk_classify.py rather than
introducing a new calling convention for one feature.
"""

import logging

from app.ai.llm_client import LLMJSONError, call_llm_for_json
from app.ai.prompts.summary_prompt import SUMMARY_SYSTEM_PROMPT, build_summary_user_prompt
from app.config import settings

logger = logging.getLogger(__name__)


def generate_summary(complaint_data: dict) -> dict:
    try:
        result = call_llm_for_json(
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_prompt=build_summary_user_prompt(complaint_data),
            model_name=settings.GROQ_EXTRACTION_MODEL,
        )
    except LLMJSONError as e:
        logger.error(f"Summary generation LLM call failed entirely: {e}")
        # Product/batch/customer/severity are copied straight from the
        # complaint record, not AI-derived — no reason to drop them just
        # because the LLM call (which only produces the prose summary and
        # impact/next-step reasoning) failed.
        return {
            "summary": "insufficient_information",
            "product": complaint_data.get("product_name"),
            "batch": complaint_data.get("batch_lot_number"),
            "customer": complaint_data.get("customer_name"),
            "issue": complaint_data.get("complaint_type"),
            "severity": complaint_data.get("severity"),
            "potential_impact": "unavailable",
            "recommended_next_step": "Retry summary generation or write manually.",
            "confidence": 0.0,
        }

    return {
        "summary": result.get("summary", "insufficient_information"),
        "product": complaint_data.get("product_name"),
        "batch": complaint_data.get("batch_lot_number"),
        "customer": complaint_data.get("customer_name"),
        "issue": complaint_data.get("complaint_type"),
        "severity": complaint_data.get("severity"),
        "potential_impact": result.get("potential_impact", ""),
        "recommended_next_step": result.get("recommended_next_step", ""),
        "confidence": float(result.get("confidence", 0.0)),
    }
