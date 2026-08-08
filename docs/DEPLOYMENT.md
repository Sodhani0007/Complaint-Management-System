# Deployment Guide

This project has three deployable pieces — frontend (static build), backend (FastAPI), and a
database — plus the AI layer, which runs in-process inside the backend rather than as a separate
service (see `docs/architecture.md` Step 3).

## Option A — Docker (all-in-one, recommended for a demo)

The whole stack (Postgres + backend + frontend/nginx) runs from a single command locally or on
any VM/host that can run Docker:

```bash
echo "GROQ_API_KEY=your_key_here" > .env
docker compose up --build
```

For a cloud VM (e.g. a single DigitalOcean droplet, EC2 instance, or similar), this is the
lowest-effort path: install Docker, copy the repo, run the same command, put a reverse proxy or
the cloud provider's load balancer in front of port 80.

## Option B — Split deployment (frontend / backend / DB on separate platforms)

This is closer to how you'd actually run this in production, and worth understanding even if you
demo with Option A.

### Frontend → Vercel

The frontend is a static Vite build, which Vercel handles natively.

1. Import the repo into Vercel, set the **root directory** to `frontend/`
2. Build command: `npm run build` · Output directory: `dist`
3. Set an environment variable pointing the frontend at your deployed backend URL (currently the
   app relies on a `/api` proxy — for a split deployment, add a `VITE_API_BASE_URL` env var and
   update `src/api/client.ts`'s `baseURL` to read from it via `import.meta.env`)

### Backend → Render or Railway

Both platforms can build directly from the `backend/Dockerfile`.

**Render:**
1. New → Web Service → connect the repo, set root directory to `backend/`
2. Render detects the `Dockerfile` automatically
3. Set environment variables: `GROQ_API_KEY`, `DATABASE_URL` (see below), `CORS_ORIGINS` (your
   Vercel frontend URL)

**Railway:**
1. New Project → Deploy from GitHub repo → select `backend/` as the service root
2. Railway also builds from the `Dockerfile` directly
3. Same environment variables as above

Either platform: after deploy, confirm `GET /health` responds and `/docs` renders Swagger UI.

### Database → managed Postgres

Both Render and Railway offer a managed Postgres add-on with one click — provision it, copy the
connection string into your backend service's `DATABASE_URL` (SQLAlchemy format:
`postgresql+psycopg2://user:password@host:port/dbname`).

Don't reuse `Base.metadata.create_all` as your migration strategy against a real managed database
long-term — see the note in `app/main.py` and the Roadmap for the Alembic migration path.

### AI Service

There isn't a separate AI service to deploy — the LangGraph pipeline executes inside the backend
process and calls out to Groq's hosted API. The only thing to configure is `GROQ_API_KEY` as an
environment variable on whichever platform hosts the backend.

## Environment variables reference

| Variable | Where it's used | Notes |
|---|---|---|
| `GROQ_API_KEY` | backend | required, never commit a real value |
| `DATABASE_URL` | backend | SQLAlchemy connection string |
| `GROQ_EXTRACTION_MODEL` | backend | defaults to `openai/gpt-oss-20b` (updated after Groq deprecated gemma2-9b-it) |
| `GROQ_REASONING_MODEL` | backend | defaults to `openai/gpt-oss-120b` (updated after Groq deprecated llama-3.3-70b-versatile) |
| `CORS_ORIGINS` | backend | must include your deployed frontend's origin |
| `VITE_API_BASE_URL` | frontend | only needed for split deployment (Option B) |

## Post-deploy checklist

- [ ] `GET /health` returns `200`
- [ ] `/docs` renders Swagger UI
- [ ] CORS origin list includes the actual deployed frontend URL, not just `localhost`
- [ ] `.env` / secrets are set via the platform's environment variable UI, never committed
- [ ] Uploading one of the `sample_data/` files through the deployed frontend round-trips
      correctly end to end
