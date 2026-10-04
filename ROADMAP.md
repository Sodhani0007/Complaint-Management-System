# Roadmap

Where this project is headed after the initial assignment submission. Rough priority order, not
committed dates.

## Near-term

- [ ] Root Cause Recommendation (bonus AI feature)
- [ ] CAPA Recommendation (bonus AI feature)
- [x] Replace `Base.metadata.create_all` with Alembic migrations
- [ ] Backend test coverage beyond the current smoke/bonus-feature tests — a dedicated test for
      the LangGraph retry-loop routing logic in the extraction pipeline itself

## Mid-term

- [x] Authentication with expiring database-backed sessions and explicit shared demo access
- [x] Basic complaint inbox/detail view (latest 20 records)
- [ ] URL routing, search/filtering, and full pagination for the inbox
- [ ] Organization isolation and investigator/manager permissions
- [ ] Assignment, investigation notes, resolution, reopening, and audit events
- [ ] Durable extraction jobs with retry/recovery
- [ ] Versioned AI evaluation dataset and measured quality report
- [ ] Completeness Checker's optional LLM warnings pass — currently best-effort/silent on failure;
      consider surfacing "warnings unavailable" in the UI rather than silently returning empty

## Longer-term / stretch

- [ ] Semantic-similarity duplicate detection via embeddings, replacing/augmenting the keyword
      approach
- [ ] OCR for scanned/image PDFs (Tesseract or a cloud OCR API) — explicitly out of scope for the
      assignment but named as a known gap in `docs/architecture.md` Step 10
- [ ] Real-time complaint trend dashboard (aggregation across batches/products over time)
- [ ] Managed deployment (see `docs/DEPLOYMENT.md`) with production-grade Postgres, secrets
      vault, and CDN-served frontend
