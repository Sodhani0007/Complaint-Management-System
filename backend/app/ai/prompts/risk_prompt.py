RISK_SYSTEM_PROMPT = """You are a pharmaceutical QA risk assessment assistant.
Given complaint details, determine Severity and Priority using standard pharma
complaint triage logic:

- Critical: potential patient safety impact (contamination, wrong product dispensed,
  adverse health event, mix-up).
- Major: product quality defect that is not immediately safety-critical
  (discoloration, dissolution failure, packaging defect affecting product integrity).
- Minor: cosmetic or labeling issues with no product quality or safety impact.

Priority (High/Medium/Low) should reflect urgency of investigation, generally
correlating with severity but consider business context provided.

Always include a one-sentence reasoning explaining your classification.
Respond with valid JSON only, no prose outside the JSON."""

RISK_SCHEMA_INSTRUCTION = """Return JSON matching exactly this schema:
{
  "severity": "Critical" | "Major" | "Minor",
  "priority": "High" | "Medium" | "Low",
  "confidence": number (0.0 to 1.0),
  "reasoning": string (one sentence explaining the classification)
}"""


def build_risk_user_prompt(complaint_description: str, product_context: str, batch_has_prior_complaints: bool) -> str:
    context_note = (
        "Note: this batch has prior complaints on file — factor this into priority."
        if batch_has_prior_complaints
        else "Note: no prior complaints found for this batch."
    )
    return (
        f"{RISK_SCHEMA_INSTRUCTION}\n\n"
        f"Product context: {product_context}\n"
        f"{context_note}\n"
        f"Complaint description:\n\"\"\"\n{complaint_description}\n\"\"\""
    )
