"""
Node: finalize

Assembles the graph's scattered state pieces into the single JSON shape the
API layer (and eventually the frontend form) actually consumes. Nothing
downstream of the graph should need to know about retry_count,
validation_errors, or other internal bookkeeping fields — this node is the
boundary that hides that internal state.
"""

from app.ai.nodes.validate import REQUIRED_FIELDS
from app.ai.state import ComplaintGraphState


def finalize(state: ComplaintGraphState) -> dict:
    fields = state.get("extracted_fields") or {}
    risk = state.get("risk_assessment") or {}
    still_missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]

    final_output = {
        "fields": {
            **fields,
            "initial_severity": risk.get("severity"),
            "priority": risk.get("priority"),
        },
        "extraction_confidence": state.get("extraction_confidence", 0.0),
        "risk_confidence": risk.get("confidence", 0.0),
        "risk_reasoning": risk.get("reasoning", ""),
        "requires_manual_review": bool(still_missing),
        "missing_required_fields": still_missing,
    }
    return {"final_output": final_output, "requires_manual_review": bool(still_missing)}
