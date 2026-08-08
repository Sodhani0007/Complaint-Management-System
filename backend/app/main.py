"""
Application entrypoint. Kept intentionally thin: configure logging, create
the app, register CORS + routers + exception handlers. All real logic lives
in services/repositories/ai — main.py should never grow business logic.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

configure_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} starting in {settings.ENVIRONMENT} mode")

    # Model imports registered here (not at module top) so Base.metadata
    # actually knows about every table before create_all runs.
    from app.models import ai_extraction, batch, complaint, complaint_document, product  # noqa: F401

    # create_all is a demo/dev convenience — it only creates tables that
    # don't exist and never alters existing ones. A real production
    # deployment would use Alembic migrations (already in requirements.txt)
    # instead of this, since create_all can't handle schema changes safely.
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created")

    yield  # application runs here

    logger.info(f"{settings.APP_NAME} shutting down")


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}
