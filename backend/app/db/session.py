"""
Database engine and session factory.

Why this exists: FastAPI needs a fresh SQLAlchemy Session per request (never
a shared global session — that leads to cross-request state bugs and
connection leaks under concurrency). `get_db()` is a generator dependency:
FastAPI calls next() to get the session, runs the request, then calls next()
again on teardown to close it — even if the request raised an exception,
because the close() sits in `finally`.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # detects stale/dropped DB connections before using them
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
