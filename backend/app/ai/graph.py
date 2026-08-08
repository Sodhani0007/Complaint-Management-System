"""
Graph wiring: this is the file that actually justifies "why LangGraph"
in the architecture doc. The conditional edge from validate_extraction is
the part a simple linear chain can't express cleanly — it lets the graph
loop back to extract_fields on a bad extraction, up to MAX_RETRIES times,
before falling through to risk classification regardless.

    START
      -> extract_fields
      -> validate_extraction --(retry)--> extract_fields   [loop]
                              --(proceed)--> classify_risk
      -> classify_risk
      -> finalize
      -> END
"""

from langgraph.graph import END, START, StateGraph

from app.ai.nodes.extract import extract_fields
from app.ai.nodes.finalize import finalize
from app.ai.nodes.risk_classify import classify_risk
from app.ai.nodes.validate import decide_after_validation, validate_extraction
from app.ai.state import ComplaintGraphState


def build_complaint_graph():
    graph = StateGraph(ComplaintGraphState)

    graph.add_node("extract_fields", extract_fields)
    graph.add_node("validate_extraction", validate_extraction)
    graph.add_node("classify_risk", classify_risk)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "extract_fields")
    graph.add_edge("extract_fields", "validate_extraction")

    graph.add_conditional_edges(
        "validate_extraction",
        decide_after_validation,
        {
            "retry": "extract_fields",
            "proceed": "classify_risk",
        },
    )

    graph.add_edge("classify_risk", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


# Compiled once at import time — compiling is relatively expensive and the
# graph structure never changes at runtime, so this is a module-level
# singleton rather than rebuilt per-request.
complaint_graph = build_complaint_graph()


def run_extraction_pipeline(raw_input: str, input_type: str, batch_has_prior_complaints: bool = False) -> dict:
    """Entry point called by extraction_service.py. Keeps the service layer
    from needing to know anything about LangGraph's invoke() signature or
    initial-state shape."""
    initial_state: ComplaintGraphState = {
        "raw_input": raw_input,
        "input_type": input_type,
        "retry_count": 0,
        "validation_errors": [],
        "batch_has_prior_complaints": batch_has_prior_complaints,
    }
    result_state = complaint_graph.invoke(initial_state)
    return result_state["final_output"]
