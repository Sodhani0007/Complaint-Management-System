"""
Shared state object threaded through every node in the extraction graph.

Why TypedDict (not a Pydantic model) here: LangGraph merges partial state
updates returned by each node into this dict on every step. TypedDict is
LangGraph's expected shape for that merge behavior; Pydantic models we
still use everywhere else (schemas, node I/O) to get validation, and convert
at the state boundary.
"""

from typing import TypedDict


class ComplaintGraphState(TypedDict, total=False):
    # --- input ---
    raw_input: str
    input_type: str  # 'pdf' | 'docx' | 'eml' | 'text'

    # --- extraction ---
    extracted_fields: dict | None
    extraction_confidence: float | None
    validation_errors: list[str]
    retry_count: int

    # --- risk classification ---
    risk_assessment: dict | None

    # --- routing / control flow ---
    requires_manual_review: bool

    # --- final assembled output returned to the API layer ---
    final_output: dict | None
