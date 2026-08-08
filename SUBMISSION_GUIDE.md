# Submission Guide

A practical checklist for taking the repo from "built" to "submitted." Follow in order.

## 1. Get it running on your machine

```bash
unzip complaint-management-system.zip
cd complaint-management-system
```

Get a free Groq API key at https://console.groq.com if you don't have one yet.

```bash
echo "GROQ_API_KEY=your_real_key_here" > .env
docker compose up --build
```

Open http://localhost — you should see the two-pane form. Open http://localhost:8000/docs —
you should see Swagger UI. If either fails, check `README.md` → "Known limitations" first, then
`docker compose logs backend` for the actual error.

If you don't have Docker, use the "Running locally without Docker" section in `README.md`
instead (venv + `uvicorn` for backend, `npm run dev` for frontend, two terminals).

## 2. Smoke-test it yourself before recording anything

Walk through this once, live, before the camera is rolling:

- [ ] Drag `sample_data/complaint_email_discoloration.eml` into the AI panel → confirm fields populate
- [ ] Paste the contents of `sample_data/complaint_text_adverse_event.txt` → confirm it comes back **Critical** severity
- [ ] Upload `sample_data/complaint_pdf_packaging_defect.pdf` → confirm PDF text extracts correctly
- [ ] Edit a populated field by hand → confirm it's editable
- [ ] Click Save → confirm the success message and a real complaint ID
- [ ] Submit the *same* adverse-event text a second time (same batch/lot number) → confirm priority is now **High** (the escalation rule)
- [ ] Try an empty/garbage upload → confirm you get an error message, not a blank screen or crash

If any of these don't work exactly as described, fix it before recording — better to catch it now than live on camera or in the interview.

## 3. Personalize the placeholders

Two things I deliberately left as placeholders since I don't know your details:

```bash
# LICENSE — replace [Your Name]
# then set your real git identity for future commits:
git config user.name "Your Actual Name"
git config user.email "you@youremail.com"
```

## 4. Push to GitHub

```bash
# create an empty repo on github.com first (no README/license — you already have those), then:
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

Check that GitHub Actions runs and passes (Actions tab) — it's already been verified locally
(lint + tests + frontend build all genuinely pass), so a green check here confirms nothing broke
in the copy.

## 5. Record the two required videos

**Video 1 — Feature demo (5–10 min):** walk through the checklist from Step 2 above, narrating
what you're doing and why it matters (e.g., "this priority escalation reflects that a repeat
complaint on the same batch is more urgent regardless of individual severity — that's a
deterministic business rule, not something I'm trusting the LLM to always get right").

**Video 2 — Code walkthrough (5–10 min):** trace one request end-to-end, out loud —
`AIAssistantPanel.tsx` → `extractionSlice` thunk → `api/client.ts` → FastAPI router →
`extraction_service.py` → `graph.py`'s node sequence → back to the populated form. Use the
"why it exists" explanations from the build process (this conversation) as your script, but say
them in your own words — you should be able to, since the module docstrings throughout the code
already carry that reasoning.

## 6. Fill in the README's placeholder sections

Before submitting, replace the placeholder blocks in `README.md`:
- `## Screenshots` — add real screenshots of the empty form and a populated one
- `## Demo Video` — add the actual links to both videos from Step 5

## 7. Final check before you submit

- [ ] `.env` is NOT committed (check `git status` — it should be gitignored)
- [ ] GitHub Actions shows green
- [ ] Both video links work and are set to at least "unlisted," not private
- [ ] The submission form has the repo link, not a zip

## If you get asked to modify something live in the interview

This is explicitly called out in the assignment as something they may do. A few safe, well-
scoped things to have ready as talking points if asked "can you add X":
- Add a new required field to the form → touches `FormSections.tsx`, `types/complaint.ts`,
  `ExtractedFields` schema, and the extraction prompt schema — know that chain
- Swap the LLM provider → `app/ai/llm_client.py` is the only file that should need to change
- Add a new bonus AI feature → new node in `app/ai/nodes/`, wire into `graph.py`, new prompt file,
  matches the pattern of everything already there (see `docs/architecture.md` Step 12 for the
  designs of the ones not yet built)
