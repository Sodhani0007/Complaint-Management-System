# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Planned
- Root Cause Recommendation (bonus feature — see `docs/architecture.md` Step 12)
- CAPA Recommendation (bonus feature)
- Alembic migrations to replace `Base.metadata.create_all`
- Authentication

## [0.2.0] — 2026-08-08

### Added
- **Completeness Checker**: deterministic required-fields check + optional LLM qualitative
  warnings pass, `POST /complaints/{id}/completeness-check`
- **Complaint Summary**: LLM-generated summary for QA review, explicit `"insufficient_information"`
  fallback rather than fabricating, `POST /complaints/{id}/summary`
- **Duplicate Complaint Detection**: same-product candidate search + `difflib.SequenceMatcher`
  similarity scoring, same-batch boost, `POST /complaints/{id}/duplicate-check`
- **Risk Assessment re-run**: on-demand re-invocation of the existing `classify_risk` node against
  a complaint's current saved data, exposing reasoning and the safety-keyword business-rule flag
  that intake-time classification never persisted, `POST /complaints/{id}/risk-assessment`
- **Frontend**: `InsightsPanel` component — four expand/collapse sections below the saved
  complaint form, each independently loadable with skeleton loading states and retry-on-error
- 18 backend tests total (up from 5), covering happy path, missing data, LLM failure, and the
  safety-keyword override for every bonus feature, LLM calls mocked throughout

### Fixed
- Migrated off `gemma2-9b-it` (deprecated by Groq 10/08/2025) and `llama-3.3-70b-versatile`
  (deprecated 08/16/2026) to `openai/gpt-oss-20b` / `openai/gpt-oss-120b`
- `extraction_service.py` was hardcoding `model_used` as a literal string instead of reading from
  settings — fixed to reflect the actual configured model

## [0.1.0] — 2026-08-08

Initial working version of the AI-Powered Customer Complaint Management System, built for the
AIVOA AI Product Engineer internship assignment.

### Added
- **Backend foundation**: FastAPI app, SQLAlchemy models (`Product`, `Batch`, `Complaint`,
  `ComplaintDocument`, `AIExtraction`), Pydantic schemas, config via `pydantic-settings`
- **LangGraph AI pipeline**: extraction → validation (with retry loop) → risk classification →
  finalize, backed by Groq (`openai/gpt-oss-20b` extraction, `openai/gpt-oss-120b` reasoning — updated post-launch after Groq deprecated the original models)
- **Deterministic safety-net rule**: safety-keyword complaints are force-classified as Critical
  severity regardless of LLM output
- **Document parsing**: PDF, DOCX, EML, TXT → plain text feeding the same extraction pipeline
- **FastAPI routes**: `/api/v1/complaints/extract`, `/api/v1/complaints` (create/get/list)
- **Business rule**: priority auto-escalates when a batch already has a prior complaint on file
- **React + Redux frontend**: two-pane intake UI matching the reference design — Log Complaint
  form (4 sections) and AI Complaint Intake Assistant panel (upload/paste, progress, chat-style
  status messages)
- **Sample data**: three fabricated complaint documents (email, pasted text, PDF) covering
  different severity levels for demo purposes
- **Docker support**: Dockerfiles for both services, `docker-compose.yml` wiring Postgres +
  backend + frontend
- **CI**: GitHub Actions running backend lint (ruff) + tests (pytest) and frontend build + type
  check on every push/PR
- **Docs**: full architecture writeup (`docs/architecture.md`), deployment guide, git workflow
  reference

### Known limitations
- OCR limited to text-based PDFs (no scanned-document support, per assignment scope)
- No authentication implemented yet
- Only 2 of 6 designed bonus AI features are scoped for implementation next (Summary, Duplicate
  Detection) — see `docs/architecture.md` Step 12 for the prioritization reasoning
