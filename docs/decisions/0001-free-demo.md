# ADR 0001: A shared demo on free hosting

Status: accepted for the portfolio demo, not for a multi-tenant production service.

## Context

The project needs a public demonstration without a hosting budget. The backend
can sleep or restart, and AI use has provider limits. The original repository
provides intake functionality but no authentication or schema migration history.

## Decision

Keep the FastAPI application modular and deploy one instance. Use PostgreSQL for
records, hashed opaque sessions, and atomic usage counters. Use Alembic migrations
and a repeatable synthetic seed. Ship a static landing page and a sample workflow
that needs no AI key. Supply a declarative Render Blueprint with Neon configured
separately, and require CI before automatic deployments.

Sessions are kept in browser memory to avoid long-lived credentials in browser
storage or reliance on third-party cookies between frontend/backend origins.
Refreshing requires login. Public demo access uses an explicitly enabled shared
account; it must never be represented as organization isolation.

## Consequences

Cold starts remain visible. Quotas survive process restarts but a global quota
can be exhausted by one visitor. Quota consumption precedes work, so failed
requests count. Document parsing runs off the event loop, but jobs do not survive
a restart. This is an honest, affordable demonstration of the current architecture.

Before handling real customer data: add organizations and record-level policy,
server-owned extraction records, upload scanning/retention, account management,
durable jobs, and verified backups. Before scaling replicas: serialize migrations
in a release job and add concurrency coverage for product/batch creation.
