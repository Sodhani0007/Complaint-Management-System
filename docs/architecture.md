# AI-Powered Customer Complaint Management System — Architecture

---

## STEP 3 — Software Architecture

### High-Level Architecture

```
┌─────────────────┐      HTTPS/REST       ┌──────────────────────┐
│   React + Redux   │ ───────────────────▶ │      FastAPI          │
│   (Vite frontend)  │ ◀─────────────────── │   (backend service)   │
└─────────────────┘        JSON            └──────────┬───────────┘
                                                        │
                                    ┌───────────────────┼───────────────────┐
                                    ▼                   ▼                   ▼
                         ┌──────────────────┐ ┌──────────────────┐ ┌───────────────┐
                         │  LangGraph Agent  │ │  PostgreSQL/MySQL │ │  File Storage  │
                         │  (extraction,     │ │  (complaints,      │ │  (uploaded docs│
                         │  risk, bonus AI)  │ │  products, batches)│ │  — local/S3)   │
                         └────────┬─────────┘ └──────────────────┘ └───────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Groq API        │
                         │  openai/gpt-oss-20b/    │
                         │  llama-3.3-70b     │
                         └──────────────────┘
```

**Flow in one sentence:** user uploads/pastes a complaint → React sends it to FastAPI → FastAPI invokes a LangGraph agent → agent calls Groq LLMs through a series of nodes (extract → validate → classify risk → [bonus nodes]) → structured JSON returns → FastAPI persists it → React fills the form for human review → user edits/confirms → saved to DB.

### Low-Level Architecture (request lifecycle)

1. User drops PDF/email or pastes text in `AI Complaint Intake Assistant` panel
2. React dispatches `extractComplaint` thunk → `POST /api/v1/complaints/extract`
3. FastAPI `complaints` router validates upload (size/type) → calls `extraction_service`
4. `extraction_service` builds initial LangGraph state → invokes graph
5. Graph runs: `parse_document` → `extract_fields` → `validate_extraction` → `classify_risk` → (optional bonus nodes: `check_duplicates`, `check_completeness`) → `finalize`
6. Each node calls Groq via LangChain's Groq chat wrapper, with structured-output parsing + retry
7. Final state returned as Pydantic model → FastAPI returns JSON to frontend
8. Redux stores the extraction result → form auto-populates with `AWAITING → filled` transition, editable
9. User reviews/edits → clicks "Save Complaint" → `POST /api/v1/complaints`
10. FastAPI persists to DB (complaint + link to product/batch) → returns saved record with ID

### Folder Structure

```
complaint-management-system/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entrypoint
│   │   ├── config.py                # settings (env vars, pydantic-settings)
│   │   ├── api/
│   │   │   ├── deps.py              # dependency injection (db session, etc.)
│   │   │   └── v1/
│   │   │       ├── complaints.py    # complaint routes
│   │   │       ├── ai.py            # AI-only routes (extract, chat, bonus features)
│   │   │       └── router.py        # aggregates routers
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── complaint.py
│   │   │   ├── product.py
│   │   │   └── batch.py
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── complaint.py
│   │   │   └── extraction.py
│   │   ├── repositories/            # DB access layer (query logic)
│   │   │   └── complaint_repository.py
│   │   ├── services/                # business logic layer
│   │   │   ├── extraction_service.py
│   │   │   ├── complaint_service.py
│   │   │   └── document_service.py  # file parsing (pdf/docx/eml/txt)
│   │   ├── ai/
│   │   │   ├── graph.py             # LangGraph definition (nodes + edges)
│   │   │   ├── state.py             # TypedDict / Pydantic graph state
│   │   │   ├── nodes/
│   │   │   │   ├── extract.py
│   │   │   │   ├── validate.py
│   │   │   │   ├── risk_classify.py
│   │   │   │   ├── duplicate_check.py
│   │   │   │   ├── completeness_check.py
│   │   │   │   └── summarize.py
│   │   │   ├── prompts/
│   │   │   │   ├── extraction_prompt.py
│   │   │   │   ├── risk_prompt.py
│   │   │   │   └── ...
│   │   │   └── llm_client.py        # Groq client wrapper w/ retry
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── base.py
│   │   └── core/
│   │       ├── logging.py
│   │       └── exceptions.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   └── ComplaintIntakePage.tsx
│   │   ├── components/
│   │   │   ├── ComplaintForm/
│   │   │   ├── AIAssistantPanel/
│   │   │   ├── FileUpload/
│   │   │   └── common/              # Button, Card, Input, Badge, etc.
│   │   ├── store/
│   │   │   ├── store.ts
│   │   │   └── slices/
│   │   │       ├── complaintSlice.ts
│   │   │       └── extractionSlice.ts
│   │   ├── hooks/
│   │   ├── api/
│   │   │   └── client.ts            # axios instance + API calls
│   │   ├── types/
│   │   └── styles/
│   ├── package.json
│   └── vite.config.ts
│
├── sample_data/                     # fabricated complaint PDFs/emails for demo
├── docker-compose.yml
└── README.md
```

### Deployment Architecture (kept simple, on purpose)

```
docker-compose:
  frontend  → nginx serving Vite build (or `npm run dev` for local demo)
  backend   → uvicorn/FastAPI container
  db        → postgres container with volume
```

For an internship submission, Docker Compose running locally is enough — don't over-engineer with Kubernetes/cloud infra. If asked "how would you deploy this in production," the answer is: containerize each service, put FastAPI behind a load balancer, managed Postgres (RDS/Cloud SQL), frontend on a CDN (S3+CloudFront or Vercel), secrets in a vault, not `.env` files.

---

## STEP 4 — Database Design

### ER Diagram

```
┌────────────────┐        ┌────────────────┐        ┌────────────────┐
│    products     │        │     batches     │        │   complaints    │
├────────────────┤        ├────────────────┤        ├────────────────┤
│ id (PK)         │───┐    │ id (PK)         │───┐    │ id (PK)          │
│ name            │   └───▶│ product_id (FK) │   └───▶│ batch_id (FK)    │
│ strength_grade  │        │ lot_number      │        │ product_id (FK)  │
│ created_at      │        │ manufacture_date│        │ complaint_source │
└────────────────┘        │ expiry_date     │        │ customer_name    │
                            │ created_at      │        │ complaint_type   │
                            └────────────────┘        │ complaint_date   │
                                                        │ description      │
                                                        │ quantity_affected│
                                                        │ severity         │
                                                        │ priority         │
                                                        │ ai_confidence    │
                                                        │ status           │
                                                        │ raw_source_text  │
                                                        │ created_at       │
                                                        │ updated_at       │
                                                        └────────┬─────────┘
                                                                 │
                                                        ┌────────▼─────────┐
                                                        │ complaint_documents│
                                                        ├──────────────────┤
                                                        │ id (PK)           │
                                                        │ complaint_id (FK) │
                                                        │ file_name         │
                                                        │ file_path         │
                                                        │ file_type         │
                                                        │ uploaded_at       │
                                                        └──────────────────┘

                                                        ┌──────────────────┐
                                                        │  ai_extractions   │
                                                        ├──────────────────┤
                                                        │ id (PK)           │
                                                        │ complaint_id (FK) │
                                                        │ extracted_json    │
                                                        │ model_used        │
                                                        │ confidence_score  │
                                                        │ created_at        │
                                                        └──────────────────┘
```

### Tables & Relationships

- `products` 1---N `batches` (a product has many batches/lots)
- `batches` 1---N `complaints` (a batch can have multiple complaints — this is what enables duplicate/pattern detection)
- `complaints` 1---N `complaint_documents` (a complaint can have multiple attached files)
- `complaints` 1---N `ai_extractions` (keep every AI extraction attempt as an audit record — regulated data, per Step 1's audit-trail point, never overwrite silently)

### Why this shape

Rather than one flat `complaints` table with a `product_name` text field, normalizing into `products` → `batches` → `complaints` is what actually enables the **Duplicate Complaint Detection** bonus feature — you can query "how many complaints exist for batch X" directly instead of fuzzy-matching text.

### SQL (PostgreSQL)

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    strength_grade VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE batches (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    lot_number VARCHAR(100) NOT NULL,
    manufacture_date DATE,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, lot_number)
);
CREATE INDEX idx_batches_lot_number ON batches(lot_number);

CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES batches(id),
    product_id INTEGER REFERENCES products(id),
    complaint_source VARCHAR(100),
    customer_name VARCHAR(255),
    complaint_type VARCHAR(100),
    complaint_date DATE,
    description TEXT,
    quantity_affected NUMERIC(10,2),
    severity VARCHAR(20),          -- 'Critical' | 'Major' | 'Minor'
    priority VARCHAR(20),          -- 'High' | 'Medium' | 'Low'
    ai_confidence NUMERIC(4,3),
    status VARCHAR(30) DEFAULT 'Pending Triage',
    raw_source_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_complaints_batch_id ON complaints(batch_id);
CREATE INDEX idx_complaints_severity ON complaints(severity);
CREATE INDEX idx_complaints_status ON complaints(status);

CREATE TABLE complaint_documents (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ai_extractions (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
    extracted_json JSONB,   -- MySQL equivalent: JSON (see note below)
    model_used VARCHAR(100),
    confidence_score NUMERIC(4,3),
    created_at TIMESTAMP DEFAULT NOW()
);
```

Normalized to 3NF; `extracted_json` as JSONB/JSON is a deliberate denormalization exception — raw AI output is inherently variable-shaped, and a JSON column lets you query it later without a rigid schema while the reviewed/confirmed fields still live in proper typed columns on `complaints`. **Portability note:** the ORM model actually uses SQLAlchemy's generic `JSON` type rather than Postgres-specific `JSONB`, since the assignment allows either MySQL or Postgres and `JSONB` isn't valid on MySQL/SQLite — caught this during a smoke test against SQLite before it became a demo-day surprise.

---

## STEP 5 — API Design

### `POST /api/v1/complaints/extract`
**Purpose:** Run AI extraction on an uploaded document or pasted text — does NOT save to DB yet.
**Input (multipart/form-data):**
```json
{ "file": "<binary, optional>", "text": "<string, optional — one of file/text required>" }
```
**Output 200:**
```json
{
  "extraction_id": "temp-uuid",
  "fields": {
    "complaint_source": "Email",
    "customer_name": "Dr. R. Mehta",
    "product_name": "Amoxicillin 500mg",
    "product_strength_grade": "500mg",
    "batch_lot_number": "AMX-2026-0731",
    "manufacturing_date": "2026-01-15",
    "expiry_date": "2028-01-15",
    "quantity_affected": 12,
    "complaint_type": "Discoloration",
    "complaint_date": "2026-08-05",
    "description": "Customer reports yellow discoloration in 12 tablets from the batch.",
    "initial_severity": "Major",
    "priority": "High"
  },
  "confidence_score": 0.87,
  "model_used": "openai/gpt-oss-20b"
}
```
**Validation:** file type in {pdf, docx, txt, eml}, max 10MB. Either `file` or `text` required, not neither.
**Error cases:** `400` unsupported file type / no input provided, `413` file too large, `422` LLM returned unparseable output after retries, `502` Groq API unreachable.

### `POST /api/v1/complaints`
**Purpose:** Save a reviewed/confirmed complaint.
**Input:** the (possibly human-edited) fields object from above, plus `extraction_id` for audit linkage.
**Output 201:** the saved complaint record with generated `id` and `status: "Pending Triage"`.
**Validation:** required fields (product_name, batch_lot_number, description) must be non-empty; dates must be valid and expiry ≥ manufacture.
**Error cases:** `400` validation failure with field-level messages, `409` if batch reference invalid.

### `GET /api/v1/complaints/{id}`
Fetch a single complaint. `404` if not found.

### `GET /api/v1/complaints`
List/paginate complaints, filterable by `severity`, `status`, `product_id`. Query params: `page`, `page_size`, `severity`, `status`.

### `POST /api/v1/complaints/{id}/risk-assessment`
**Purpose:** Re-run or fetch the AI Copilot Risk Assessment for a complaint (severity/priority reasoning + confidence).
**Output:**
```json
{
  "severity": "Major",
  "priority": "High",
  "confidence": 0.87,
  "reasoning": "Discoloration suggests possible stability/formulation issue affecting patient safety.",
  "business_rules_applied": ["batch_has_prior_complaints: false"]
}
```

### `POST /api/v1/complaints/{id}/chat`
**Purpose:** AI Assistant chat panel — ask questions about a specific complaint.
**Input:** `{ "message": "why was this marked high priority?" }`
**Output:** `{ "response": "..." }`

### Bonus feature endpoints (all follow the same shape)
- `POST /api/v1/complaints/{id}/duplicate-check` → list of possibly-duplicate complaint IDs + similarity score
- `POST /api/v1/complaints/{id}/completeness-check` → list of missing/weak fields
- `POST /api/v1/complaints/{id}/root-cause-suggestion` → suggested root cause text
- `POST /api/v1/complaints/{id}/capa-suggestion` → suggested CAPA text
- `POST /api/v1/complaints/{id}/summary` → 2-3 sentence complaint summary

Every AI endpoint returns `confidence_score` and `model_used` — this is a deliberate pattern, not repetition, because it's what lets the frontend show "AI-generated, please verify" honestly, matching the regulated-data trust model from Step 1.

---

## STEP 6 — React Frontend Design

### Pages
- `ComplaintIntakePage` — the single main page (matches the two-pane reference UI)

### Components
```
ComplaintForm/
  ComplaintForm.tsx          # orchestrates the 4 sections
  OriginCustomerSection.tsx
  ProductBatchSection.tsx
  ComplaintDetailsSection.tsx
  AssessmentPrioritySection.tsx
  FormField.tsx               # reusable labeled input w/ "Awaiting AI extraction..." placeholder state

AIAssistantPanel/
  AIAssistantPanel.tsx
  FileDropzone.tsx
  PasteTextInput.tsx
  ExtractionProgress.tsx      # progress bar + status text
  ChatBox.tsx

common/
  Button.tsx, Card.tsx, Input.tsx, Select.tsx, Badge.tsx (for severity/priority pills), Spinner.tsx
```

### Redux Store
```
store/
  complaintSlice   → { formData, status: 'idle'|'saving'|'saved'|'error', savedComplaint }
  extractionSlice  → { status: 'idle'|'uploading'|'extracting'|'done'|'error', progress, extractedFields, confidenceScore }
  chatSlice        → { messages[], status }
```

`extractionSlice` and `complaintSlice` are deliberately separate — extraction is a transient AI process with its own loading/error lifecycle, while `complaintSlice` is the actual form-of-record the user edits and saves. Merging them would make it hard to let the user edit AI output without it looking like "the extraction changed."

### Hooks
- `useComplaintForm()` — wraps form state + validation
- `useFileUpload()` — drag/drop + progress
- `useDebounce()` — for any live-typed paste-text extraction trigger

### Forms & Validation
Client-side validation via `react-hook-form` + `zod` schema mirroring the backend Pydantic schema (single source of truth conceptually, duplicated intentionally front/back since you never trust client-side-only validation for regulated data).

### Routing
Single route for this assignment (`/`) is honestly fine — don't over-build routing for a one-page demo. If asked, mention `react-router` would be added for a complaint list/detail view in a real product.

### Responsive / Loading / Error States
- Loading: skeleton/placeholder text ("Awaiting AI extraction...") exactly as shown in reference UI, progress bar during extraction
- Error: inline banner in AI panel ("Couldn't read this file — try a different format" ) rather than a silent failure or raw stack trace
- Responsive: two-pane layout collapses to stacked single column under ~768px

Dark mode: optional, skip unless time remains — not worth the risk of shallow, half-themed implementation given limited scope.

---

## STEP 7 — FastAPI Backend Design

### Layering (Clean Architecture, lightweight version)
```
Router (api/v1/*.py)       → HTTP concerns only: parse request, call service, return response
Service (services/*.py)     → business logic: orchestrates repository + AI calls
Repository (repositories/*) → DB queries only, no business logic
Models (models/*.py)        → SQLAlchemy ORM
Schemas (schemas/*.py)      → Pydantic request/response contracts
```

This separation is what lets you answer "how would you test this" cleanly — services can be unit-tested with a mocked repository and a mocked LangGraph call, without spinning up a DB.

### Dependency Injection
FastAPI's `Depends()` for DB session (`get_db`) and service instances — makes swapping a real DB for a test SQLite trivial.

```python
# api/deps.py
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_complaint_service(db: Session = Depends(get_db)) -> ComplaintService:
    return ComplaintService(ComplaintRepository(db))
```

### Logging
Structured logging (`logging` + JSON formatter) at service boundaries: log every AI call's latency, model used, and confidence — this becomes genuinely useful evidence in your demo video ("here's the log showing the LangGraph run").

### Configuration
`pydantic-settings` reading from `.env`: `GROQ_API_KEY`, `DATABASE_URL`, `MAX_UPLOAD_SIZE_MB`, `CORS_ORIGINS`. Never hardcode the Groq key — this is a near-guaranteed interview question.

### Authentication (future-ready, not implemented)
No auth required for this assignment, but structure the routers so a `Depends(get_current_user)` could be inserted later without restructuring — i.e., don't couple `user_id` logic into business logic that doesn't need it yet.

---

## STEP 8 — AI Architecture (LangGraph)

### Why LangGraph over simple prompt chaining?

A simple chain (`prompt1 → LLM → prompt2 → LLM`) can't easily do three things this project genuinely needs:
1. **Conditional branching** — e.g., if extraction confidence is low, route to a re-prompt/clarification path instead of blindly continuing to risk classification on bad data.
2. **Explicit, inspectable state** — LangGraph's shared state object means every node's output is visible and debuggable, which matters when you need to explain "why did it classify this as Major" in your interview.
3. **Retryable, composable nodes** — bonus features (duplicate check, completeness check, summary) can be added as new graph nodes/branches without restructuring the whole pipeline, versus a linear chain where every addition means rewriting the sequence.

### Graph Design

**State** (shared across all nodes):
```python
class ComplaintGraphState(TypedDict):
    raw_input: str                    # extracted text from doc, or pasted text
    input_type: str                   # 'pdf' | 'email' | 'text'
    extracted_fields: dict | None
    extraction_confidence: float | None
    validation_errors: list[str]
    retry_count: int
    risk_assessment: dict | None
    duplicate_matches: list | None
    completeness_issues: list | None
    summary: str | None
    final_output: dict | None
```

**Nodes & Edges:**
```
START
  → parse_document          (if input_type == pdf/email: extract raw text)
  → extract_fields           (LLM call: text → structured JSON)
  → validate_extraction      (schema check + confidence threshold)
      ├─(low confidence, retry_count < 2)→ extract_fields   [retry loop]
      ├─(low confidence, retry_count ≥ 2)→ flag_for_manual_review → END
      └─(valid)→ classify_risk
  → classify_risk            (LLM call + business rules → severity/priority)
  → [optional parallel-ish bonus nodes, triggered by separate endpoints, not the main flow]:
       check_duplicates, check_completeness, generate_summary
  → finalize                 (assemble final_output)
END
```

The extraction retry loop is the key design decision — rather than accepting whatever the LLM returns, `validate_extraction` checks confidence and required-field presence, and can loop back to `extract_fields` with an amended prompt (e.g., "you missed batch_lot_number, look again") up to 2 times before falling back to marking fields for manual entry. This is exactly the kind of thing that's hard to express cleanly in a linear chain and easy in a graph.

### Memory
No long-term memory needed for this assignment (each complaint extraction is independent) — but the chat endpoint (`/complaints/{id}/chat`) keeps a short conversation buffer scoped to that complaint's context (its extracted fields + description) so the AI Assistant can answer follow-up questions coherently.

### Decision Making / Confidence
Confidence score comes from two sources combined: (a) the LLM is prompted to self-report a 0-1 confidence per extraction, and (b) a rule-based check — how many required fields came back non-null/non-placeholder. Relying on LLM self-reported confidence alone is unreliable, so blend it with the deterministic completeness signal.

### Retries & Fallbacks
- LLM call failures (network/rate-limit): exponential backoff retry (2 attempts) at the `llm_client.py` level
- Malformed JSON output: re-prompt once with "your last output wasn't valid JSON, return ONLY valid JSON matching this schema"
- Total failure after retries: return partial extraction with `status: "manual_review_required"` rather than a 500 error — the form just shows more empty fields for the human to fill in, which is a graceful degradation, not a crash

---

## STEP 9 — Prompt Design

### Extraction Agent

**System Prompt:**
```
You are a pharmaceutical quality assurance data extraction assistant.
Extract structured complaint information from the provided document or text.
Only extract information explicitly present in the source — never invent values.
If a field is not present, return null for it. Always respond with valid JSON only, no prose, no markdown fences.
```

**Developer Prompt (schema instruction):**
```
Return JSON matching exactly this schema:
{
  "complaint_source": string|null,
  "customer_name": string|null,
  "product_name": string|null,
  "product_strength_grade": string|null,
  "batch_lot_number": string|null,
  "manufacturing_date": string|null (YYYY-MM-DD),
  "expiry_date": string|null (YYYY-MM-DD),
  "quantity_affected": number|null,
  "complaint_type": string|null,
  "complaint_date": string|null (YYYY-MM-DD),
  "description": string|null,
  "confidence": number (0.0-1.0, your own confidence in this extraction)
}
```

**User Prompt:** the raw document/email text, wrapped: `Document:\n"""\n{raw_input}\n"""`

**Fallback Prompt** (used on retry after validation failure):
```
Your previous extraction was missing or invalid for: {missing_fields}.
Re-read the document carefully and look again specifically for these fields.
Return the FULL corrected JSON object (not just the missing fields), same schema as before.
```

### Risk Classification Agent

**System Prompt:**
```
You are a pharmaceutical QA risk assessment assistant. Given complaint details, determine
Severity (Critical/Major/Minor) and Priority (High/Medium/Low) following standard pharma
complaint triage logic: Critical = potential patient safety impact (contamination, wrong
product, adverse event); Major = product quality defect not immediately safety-critical
(discoloration, dissolution failure, packaging defect affecting product integrity);
Minor = cosmetic/labeling issues with no product quality impact.
Always explain your reasoning in one sentence. Respond with valid JSON only.
```

**Output Schema:**
```json
{ "severity": "Major", "priority": "High", "confidence": 0.9, "reasoning": "..." }
```

### Output Parsing & Validation
All LLM JSON output is parsed with a Pydantic model (`ExtractionResult`, `RiskAssessmentResult`). Parsing failure triggers the fallback prompt path described in Step 8, not a crash.

---

## STEP 10 — OCR / Document Extraction Strategy

Production OCR isn't required, so design for the common cases cleanly rather than building a robust OCR pipeline:

- **`.txt` / pasted text** → used directly, no parsing needed
- **`.eml`** → parsed with Python's `email` stdlib module to pull sender, subject, and body text
- **`.pdf`** → text extracted with `pypdf` or `pdfplumber` (text-based PDFs only — since this covers your own fabricated sample PDFs, that's sufficient; note this explicitly as a known limitation for scanned/image PDFs)
- **`.docx`** → `python-docx` to pull paragraph text
- **Images** (if you demo one) → mention that a production version would add an OCR step (e.g., Tesseract or a cloud OCR API) before the same extraction pipeline; not implementing it, just naming it, is enough per the assignment note

This all lives in `document_service.py` as a `parse_document(file) -> str` function feeding into the LangGraph `parse_document` node — same downstream extraction pipeline regardless of input type, which is the actual point: format-specific parsing is isolated from the AI logic.

---

## STEP 11 — Risk Classification Design

- **Severity**: Critical / Major / Minor, driven by the LLM using the rubric in the Step 9 prompt (safety impact vs. quality defect vs. cosmetic)
- **Priority**: High / Medium / Low — derived from severity **plus** a business rule: if `batch_id` already has ≥1 prior complaint on file, bump priority up one level (a repeat-batch issue is more urgent regardless of individual severity)
- **Business Rules** (deterministic, sit alongside the LLM call, not inside the prompt):
  - prior complaints on same batch → priority escalation
  - complaint_type contains safety keywords (e.g., "adverse event", "allergic reaction") → force severity = Critical regardless of LLM output (a hard safety net, LLM output should never be the sole gate on a safety-critical classification)
- **Confidence**: shown to the user directly in the UI (e.g., "87% confidence") so it's clear this is AI-assisted, not AI-decided — consistent with the human-in-the-loop principle from Step 1
- **"Why AI predicted this"**: the `reasoning` string from the risk prompt is surfaced in the UI next to the severity/priority badges — this single design choice is what makes the AI Copilot feel trustworthy rather than a black box, and it's explicitly named in the reference UI ("AI Copilot Risk Assessment")

---

## STEP 12 — Bonus AI Features Design

Recommend implementing **2** well rather than all 6 shallowly (per the earlier scope note). Suggested priority order and why:

1. **Complaint Summary** — cheapest to build (one more LangGraph node, reuses existing extracted data), highest visible payoff in the demo video
2. **Duplicate Complaint Detection** — most product-relevant given the domain, and it's a great interview talking point (`SELECT * FROM complaints WHERE batch_id = ?` plus a semantic-similarity pass over description text using simple embedding cosine similarity, or even just keyword overlap if time is tight)

Design for all 6, but only build the top 2 fully:

| Feature | Approach |
|---|---|
| Complaint Summary | LLM node, 2-3 sentence summary of `description` |
| Root Cause Recommendation | LLM node, prompted with description + product context, returns hypothesis + disclaimer ("suggested, not confirmed") |
| Duplicate Detection | DB query on `batch_id` + text similarity on `description` (embeddings optional/stretch) |
| CAPA Recommendation | LLM node, given root cause + severity, suggests a corrective/preventive action draft |
| AI Risk Classification | Already core (Step 11) |
| Completeness Checker | Deterministic + LLM hybrid: checks which schema fields are null/low-confidence, returns a list with why each matters |

---

## STEP 13 — UI/UX Design Direction

Treat this as a QA/regulatory tool, not a consumer app — the visual language should read as **precise and trustworthy**, not playful. A few concrete decisions to carry into the actual build (we'll firm these up with the frontend-design process once we start coding the UI, rather than freezing them here):

- **Color palette**: neutral grays/whites as the base (matches reference screenshot), a single confident accent (blue reads as "clinical/trustworthy" in enterprise healthcare tooling — avoid anything playful/saturated), severity badges using semantic color (red=Critical, amber=Major, gray=Minor) since that mapping is instantly scannable and matches how QA staff actually triage visually
- **Typography**: Google Inter as mandated, using weight (500/600 for labels, 400 for body) rather than color for hierarchy, keeping the form dense-but-legible like the reference
- **Spacing**: generous section spacing (matches the reference UI's numbered sections), tight field-label spacing within a section
- **Cards**: two flat elevated panels (form left, AI assistant right) exactly as shown
- **Buttons**: primary (Save Complaint) filled, secondary (Reset Form) outlined — standard, don't overdesign
- **Icons**: minimal — upload cloud icon, sparkle for AI, send arrow for chat — matches reference
- **Accessibility**: visible focus states, sufficient contrast on placeholder text, labels properly associated with inputs (not just visually adjacent)
- **Microinteractions**: the extraction progress bar filling + field-by-field placeholder-to-value transition is the single moment worth polishing — it's the "wow" moment of the whole demo video

---

**Architecture design complete.** Next is Step 14: production code, generated module by module, starting with the backend foundation (config, DB models, then the LangGraph extraction pipeline) — I'll pause after each module for your review rather than dumping it all at once.
