"""
Application entrypoint. Kept intentionally thin: configure logging, create
the app, register CORS + routers + exception handlers. All real logic lives
in services/repositories/ai — main.py should never grow business logic.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import api_router
from app.config import settings
from app.core.http_limits import BodyLimitMiddleware
from app.core.logging import configure_logging
from app.db.session import engine

configure_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} starting in {settings.ENVIRONMENT} mode")

    # Register relationships before serving requests. Migration imports also
    # register the full schema independently of application startup.
    from app.models import ai_extraction, auth, batch, complaint, complaint_document, product  # noqa: F401

    # Schema changes are explicit Alembic migrations, run before serving traffic.

    yield  # application runs here

    logger.info(f"{settings.APP_NAME} shutting down")


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

app.add_middleware(BodyLimitMiddleware, max_bytes=(settings.MAX_UPLOAD_SIZE_MB + 1) * 1024 * 1024)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.middleware("http")
async def response_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}


@app.get("/ready")
def readiness_check():
    try:
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            connection.execute(text("SELECT id FROM users LIMIT 1"))
        if revision != "0002":
            raise HTTPException(503, "Database migrations are not current")
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Database unavailable or not migrated") from exc
    return {"status": "ready"}
