"""
Format-specific text extraction, isolated from the AI pipeline per the
architecture doc's Step 10 design: every format funnels down to a plain
string, so extract_fields (the LangGraph node) never needs to know or care
whether the source was a PDF, an email, or pasted text.
"""

import email
import logging
from email import policy
from io import BytesIO

import docx
from pypdf import PdfReader

from app.core.exceptions import UnsupportedFileTypeError

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".eml"}


def parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    # Text-based PDFs only, per the assignment's explicit note that
    # production-grade OCR is not required — scanned/image PDFs will yield
    # an empty or near-empty string here, which validate_extraction will
    # correctly flag as low-confidence/missing-fields rather than crash on.
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def parse_docx(file_bytes: bytes) -> str:
    document = docx.Document(BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs).strip()


def parse_eml(file_bytes: bytes) -> str:
    msg = email.message_from_bytes(file_bytes, policy=policy.default)
    subject = msg.get("subject", "")
    sender = msg.get("from", "")
    body = msg.get_body(preferencelist=("plain",))
    body_text = body.get_content() if body else ""
    return f"From: {sender}\nSubject: {subject}\n\n{body_text}".strip()


def parse_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace").strip()


_PARSERS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".eml": parse_eml,
    ".txt": parse_txt,
}


def parse_document(file_bytes: bytes, file_extension: str) -> tuple[str, str]:
    """Returns (extracted_text, input_type). Raises UnsupportedFileTypeError
    for anything outside SUPPORTED_EXTENSIONS — caught at the API layer and
    turned into a 400, not a 500."""
    ext = file_extension.lower()
    if ext not in _PARSERS:
        raise UnsupportedFileTypeError(f"Unsupported file type: {ext}")

    text = _PARSERS[ext](file_bytes)
    input_type = ext.lstrip(".")
    return text, input_type
