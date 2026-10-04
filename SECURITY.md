# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately rather than
opening a public issue — email the maintainer or use GitHub's private vulnerability reporting
feature on this repository.

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce
- Any relevant logs or screenshots

## Known Security Considerations for This Project

This is a demo/assignment project, not a hardened production system. Notably:

- **Authentication**: complaint endpoints require expiring bearer sessions. Public demo access
  is explicitly enabled through `DEMO_MODE` and shares synthetic records among visitors.
  There is no organization isolation. Do not use the demo for real customer data.
- **Secrets**: `GROQ_API_KEY` and `DATABASE_URL` must be supplied via environment variables /
  `.env` (never committed — see `.gitignore`). `.env.example` contains placeholders only.
- **File uploads**: the entire request is bounded before parsing (upload limit plus 1 MB for
  multipart overhead), and the file is checked again against `MAX_UPLOAD_SIZE_MB`. Extracted
  text is capped before model calls. Content is not scanned for malicious payloads. Don't accept
  uploads from untrusted sources in a production deployment without adding that.
- **Prompt injection**: complaint descriptions and other extracted text are interpolated directly
  into LLM prompts (`app/ai/prompts/*.py`) with no sanitization beyond triple-quote fencing, which
  is not a robust defense. A malicious complaint description could attempt to influence the LLM's
  severity/priority classification or summary output via injected instructions. Blast radius is
  partially contained by Pydantic schema validation on the LLM's structured output (it can't
  return anything outside the defined shape) and by the deterministic safety-keyword rule in
  `risk_classify.py`, which overrides the LLM's severity/priority regardless of what it was
  manipulated into saying — but this is not a complete mitigation. Not fixed in this pass;
  documenting honestly rather than claiming it's handled.
- **CORS**: `CORS_ORIGINS` defaults to localhost dev origins; update this before deploying.
- **Usage**: database-backed global quotas survive restarts. Failed calls count, and one
  visitor can exhaust the shared allowance. These limits do not replace provider quotas.
- **Audit**: extraction snapshots are client-supplied at save time, not independent evidence
  of every extraction attempt. A future server-side provenance feature is required for that.

## Supported Versions

This project does not currently maintain multiple release branches — security fixes apply to the
latest `main` only.
