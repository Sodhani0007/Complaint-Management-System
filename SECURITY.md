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

- **No authentication is implemented.** Routers are structured so `Depends(get_current_user)`
  could be added without restructuring, but nothing gates access currently — do not deploy this
  publicly without adding auth first.
- **Secrets**: `GROQ_API_KEY` and `DATABASE_URL` must be supplied via environment variables /
  `.env` (never committed — see `.gitignore`). `.env.example` contains placeholders only.
- **File uploads**: validated for extension and size (`MAX_UPLOAD_SIZE_MB`), enforced via a
  streaming size check that aborts as soon as the limit is exceeded rather than buffering the
  whole file first — but uploaded content is not scanned for malicious payloads. Don't accept
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

## Supported Versions

This project does not currently maintain multiple release branches — security fixes apply to the
latest `main` only.
