# Roadmap

Where this project is headed after the initial assignment submission. Rough priority order, not
committed dates.

## Near-term

- [ ] **Complaint Summary** (bonus AI feature) — new LangGraph node, reuses existing extracted
      description; cheapest to add, highest visible payoff in a demo
- [ ] **Duplicate Complaint Detection** (bonus AI feature) — batch-based DB query (already
      possible today via `count_prior_complaints_for_batch`) plus a text-similarity pass over
      descriptions
- [ ] Replace `Base.metadata.create_all` with proper Alembic migrations
- [ ] Backend test coverage beyond the current smoke tests — unit tests per service with a mocked
      repository, and a dedicated test for the LangGraph retry-loop routing logic

## Mid-term

- [ ] Authentication (`Depends(get_current_user)` — routers are already structured to accept it)
- [ ] Complaint list/detail view with `react-router` (currently single-route by design)
- [ ] Root Cause Recommendation and CAPA Recommendation bonus features
- [ ] Completeness Checker (deterministic + LLM hybrid, as designed in `docs/architecture.md`
      Step 12)

## Longer-term / stretch

- [ ] Semantic-similarity duplicate detection via embeddings, replacing/augmenting the keyword
      approach
- [ ] OCR for scanned/image PDFs (Tesseract or a cloud OCR API) — explicitly out of scope for the
      assignment but named as a known gap in `docs/architecture.md` Step 10
- [ ] Real-time complaint trend dashboard (aggregation across batches/products over time)
- [ ] Managed deployment (see `docs/DEPLOYMENT.md`) with production-grade Postgres, secrets
      vault, and CDN-served frontend
