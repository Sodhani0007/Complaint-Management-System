"""
Thin wrapper around the Groq chat models, isolating three concerns that
would otherwise leak into every node: (1) which model to call, (2) retrying
on transient network/rate-limit failures, (3) safely parsing JSON out of an
LLM response that might include stray prose or markdown fences despite being
told not to.

Why this file exists rather than calling ChatGroq directly in each node:
every node needs the same "call LLM, parse JSON, handle failure" pattern.
Without this wrapper, that logic would be copy-pasted into extract.py,
risk_classify.py, and every bonus-feature node — a classic case where
duplicated code becomes duplicated bugs the moment retry behavior needs to
change.
"""

import json
import logging
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings

logger = logging.getLogger(__name__)


class LLMJSONError(Exception):
    """Raised when the LLM response cannot be parsed as valid JSON after all retries."""


def _strip_markdown_fences(text: str) -> str:
    """LLMs frequently wrap JSON in ```json ... ``` even when told not to.
    Strip fences defensively rather than trusting the prompt alone."""
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return match.group(1) if match else text


def get_llm_client(model_name: str) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=model_name,
        temperature=0.1,  # low temperature: we want consistent structured extraction, not creativity
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )


def call_llm_for_json(
    system_prompt: str,
    user_prompt: str,
    model_name: str = settings.GROQ_EXTRACTION_MODEL,
    max_retries: int = settings.LLM_MAX_RETRIES,
) -> dict:
    """
    Calls the LLM and returns parsed JSON. Retries on both network failure
    AND malformed-JSON responses — these are different failure modes but
    both are worth one more attempt before giving up, since a single retry
    resolves the large majority of transient issues with either.
    """
    llm = get_llm_client(model_name)
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )
            raw_text = response.content.strip()
            cleaned = _strip_markdown_fences(raw_text)
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"LLM returned invalid JSON on attempt {attempt + 1}: {e}")
        except Exception as e:  # network errors, rate limits, timeouts
            last_error = e
            logger.warning(f"LLM call failed on attempt {attempt + 1}: {e}")
            time.sleep(2**attempt)  # exponential backoff: 1s, 2s, 4s...

    raise LLMJSONError(
        f"LLM failed to return valid JSON after {max_retries + 1} attempts. Last error: {last_error}"
    )
