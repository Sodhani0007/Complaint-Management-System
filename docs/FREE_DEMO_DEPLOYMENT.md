# Free demo deployment: Render + Neon

This guide describes the checked-in `render.yaml`. No cloud resources are created
by checking in the file. Use the free plans; the configuration includes no worker,
Redis instance, paid database, or purchased domain.

## Account setup and deployment

### Current demo

- Frontend: https://complaints-demo.onrender.com/
- API: https://complaints-api-jxuj.onrender.com
- Deployed branch: `feat/free-demo-deployment` (PR #1; not yet merged into `main`).
- Verified on 2026-10-04: readiness, demo login, synthetic complaint save,
  list/detail retrieval, batch priority escalation, and live Groq text extraction.
- Known limitation observed in the live test: the keyword safety rule can flag
  negated phrases such as "No injury or adverse event" as Critical. Human review
  remains necessary; negation-aware risk handling needs a dedicated follow-up.

The steps below describe the intended deployment from `main` after review.
The current demo uses the feature branch until that review and merge are complete.

1. Create/sign in to Neon and Render using your own accounts. Do not send API keys
   or database passwords in a chat or commit them to Git.
2. Create a **Free Neon PostgreSQL project**. Copy its connection string with TLS
   (`sslmode=require`). Use a direct connection for this single-instance demo,
   which also runs migrations at startup. `postgresql://...` is supported.
3. Merge the reviewed feature PR into `main` after CI passes. In Render, create a
   Blueprint from this repository, using `render.yaml` and the `main` branch.
4. For `complaints-api`, set `DATABASE_URL` to the Neon connection string.
   Set `GROQ_API_KEY` to your Groq key, or leave it empty for manual/sample mode.
   Set `CORS_ORIGINS` to a JSON array with the actual frontend origin, such as
   `["https://complaints-demo-xxxx.onrender.com"]`. No trailing slash.
5. For `complaints-demo`, set `VITE_API_BASE_URL` to the actual backend URL plus
   `/api/v1`, e.g. `https://complaints-api-xxxx.onrender.com/api/v1`.
   Render may add suffixes to names. Copy the assigned URLs, not these examples.
   If URLs are unavailable during creation, update these values after provisioning
   and redeploy both services; the frontend value is baked in at build time.
6. Verify the backend is **Free**, and no database or paid service is being
   provisioned by Render. Apply the Blueprint. The startup command runs Alembic
   and an idempotent synthetic seed before serving requests.
7. Optionally configure `ADMIN_EMAIL` and a unique `ADMIN_PASSWORD` of at least 16
   characters on the backend. Both must be set together. Restarting with a changed
   password updates its hash and revokes that account's sessions. Demo mode does
   not need an owner account. Disabling `DEMO_MODE` invalidates demo sessions.

## Acceptance checks after deployment

- `/health` returns 200; `/ready` returns 200 only when the DB and migration
  revision are available.
- The frontend landing page loads immediately. A sleeping backend shows a startup
  message, then enables Enter demo.
- Enter demo → Load synthetic sample → Save Complaint → Saved complaints →
  select the saved record. Its priority is Medium because DEMO-001 already has
  a complaint. Sample mode does not call AI or invent a confidence score.
- With a Groq key configured, upload a synthetic document and verify extraction,
  review, and save. Automated tests mock provider calls; they do not establish
  that your live key/model quota works.
- Sign out. Calling `/api/v1/complaints` without a token must return 401.
- Restart the backend; saved records and usage counters should remain in Neon.
- Record a short walkthrough, add the actual URL/video to the README, and create
  a release only after these checks pass.

## Limits and engineering choices

- Render free web services sleep after inactivity. This is not an always-available
  service. Do not add artificial keepalive traffic.
- Render's free PostgreSQL expires after 30 days. The Blueprint uses Neon instead;
  both providers still impose quotas.
- All users share synthetic data. Authentication gates access; this is **not tenant
  isolation**. Do not submit real complaint documents or personal information.
- Passwords use PBKDF2-SHA256, a random salt, and 600,000 iterations. Random session
  tokens are stored only as SHA-256 digests in the DB, expire after one hour by
  default, and live in browser memory. Refreshing the page requires sign-in.
- Self-registration, password recovery, and user-management UI are not implemented.
- Global budgets default to 30 AI endpoint invocations/day and 100 saves/day.
  Each login type allows 60 attempts/hour. Failed attempts consume quota; counters
  use UTC windows and survive restarts. One AI endpoint can make multiple model
  calls: these are not token or monetary spend limits.
- Extraction runs in a thread pool, without durable job recovery. Startup
  migration/seed assumes one instance; use a release job before adding replicas.
- Save-time audit snapshots are client-supplied and committed with the complaint.
  They are not tamper-proof records of every attempt. Server-side provenance is
  future work. No regulatory compliance claim is made.
- Documents are parsed in memory, not durably archived. Render's local filesystem
  must not be used for persistent uploads.

## Database migration and rollback

Fresh database: `alembic upgrade head` (also run by `python -m app.start`).
Existing pre-migration database: back it up and compare it to revision `0001`.
Only if it matches the original schema, run `alembic stamp 0001`, then
`alembic upgrade head`. Never stamp an unknown database blindly.

Before releasing, take an external `pg_dump` backup and restore it into a separate
test database. No backup service is configured here; do not claim cloud restores
are tested until you perform one.

To roll back the app, deploy the previous tested commit. Avoid automatic database
downgrades: downgrading 0002 deletes accounts, sessions, and quotas. Restore from
a verified backup if a schema rollback is required.

## Local verification

```bash
cd backend
pip install -r requirements.txt
# Configure .env from .env.example, then:
python -m app.start
```

Run `pytest tests -q` from backend. Tests ignore ordinary `DATABASE_URL` and use
disposable SQLite storage. `TEST_DATABASE_URL` explicitly opts into a **disposable**
PostgreSQL database: tests migrate and drop its app tables. CI runs both variants.

From frontend, run `npm ci`, `npm run build`, `npx playwright install chromium`,
and `npm run test:e2e`. Browser tests start their own servers on ports 8000/5173;
stop any existing servers first. On Windows they expect a repository-root `.venv`
with backend requirements. If Chromium cannot download, set
`PLAYWRIGHT_CHANNEL=msedge` to use an installed Edge browser in an isolated profile.

## References

- [Render free-tier limits](https://render.com/docs/free)
- [Render Blueprint schema](https://render.com/docs/blueprint-spec)
- [Neon plans](https://neon.com/pricing)
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
