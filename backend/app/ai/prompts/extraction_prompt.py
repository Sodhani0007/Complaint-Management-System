"""
Prompts for the field-extraction agent. Kept as plain functions (not
hardcoded strings inline in the node) so the fallback/retry prompt can be
generated dynamically from the actual missing fields, per complaint.
"""

EXTRACTION_SYSTEM_PROMPT = """You are a pharmaceutical quality assurance data extraction assistant.
Extract structured complaint information from the provided document or text.
Only extract information explicitly present in the source — never invent or guess values.
If a field is not present in the source, return null for it.
Always respond with valid JSON only. No prose, no explanation, no markdown code fences."""

EXTRACTION_SCHEMA_INSTRUCTION = """Return JSON matching exactly this schema:
{
  "complaint_source": string|null,
  "customer_name": string|null,
  "product_name": string|null,
  "product_strength_grade": string|null,
  "batch_lot_number": string|null,
  "manufacturing_date": string|null (format YYYY-MM-DD),
  "expiry_date": string|null (format YYYY-MM-DD),
  "quantity_affected": number|null,
  "complaint_type": string|null,
  "complaint_date": string|null (format YYYY-MM-DD),
  "description": string|null,
  "confidence": number (0.0 to 1.0 — your own confidence in this extraction overall)
}"""

REQUIRED_FIELDS = ["product_name", "batch_lot_number", "description"]


def build_extraction_user_prompt(raw_input: str) -> str:
    return f"{EXTRACTION_SCHEMA_INSTRUCTION}\n\nDocument:\n\"\"\"\n{raw_input}\n\"\"\""


def build_extraction_retry_prompt(raw_input: str, missing_fields: list[str]) -> str:
    """
    Used when validate_extraction finds required fields still missing after
    the first attempt. Re-reading with a targeted instruction performs
    noticeably better than a generic "try again" — pointing the model at
    exactly what to look for narrows its search within the document.
    """
    return (
        f"Your previous extraction was missing or invalid for: {', '.join(missing_fields)}.\n"
        f"Re-read the document carefully and look again specifically for these fields.\n"
        f"Return the FULL corrected JSON object (not just the missing fields), "
        f"same schema as before.\n\n"
        f"{EXTRACTION_SCHEMA_INSTRUCTION}\n\nDocument:\n\"\"\"\n{raw_input}\n\"\"\""
    )
