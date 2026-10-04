"""Opaque bearer sessions; only token digests are persisted in the database."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.auth import AuthSession, UsageBucket, User

bearer = HTTPBearer(auto_error=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    _, iterations, salt, expected = encoded.split("$")
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
    return hmac.compare_digest(expected, actual)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_session(db: Session, user: User) -> dict:
    token = secrets.token_urlsafe(32)
    expires = utcnow() + timedelta(minutes=settings.SESSION_TTL_MINUTES)
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= utcnow()))
    db.add(AuthSession(token_hash=token_digest(token), user_id=user.id, expires_at=expires))
    db.commit()
    return {"access_token": token, "token_type": "bearer", "role": user.role,
            "expires_in": settings.SESSION_TTL_MINUTES * 60}


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(401, "Session expired or invalid. Please sign in.",
                                 headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unauthorized
    session = db.get(AuthSession, token_digest(credentials.credentials))
    if session is None or session.expires_at <= utcnow():
        raise unauthorized
    user = db.get(User, session.user_id)
    if user is None or not user.active or (user.role == "demo" and not settings.DEMO_MODE):
        raise unauthorized
    return user


def consume_quota(db: Session, scope: str, limit: int, *, hourly: bool = False) -> None:
    """Atomic conditional update: simultaneous requests cannot exceed the cap.

    Failed requests intentionally consume quota too. Counters survive restarts.
    Global limits protect the free demo even when callers rotate IPs/sessions.
    """
    now = utcnow()
    start = now.replace(minute=0, second=0, microsecond=0) if hourly else now.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    expires = start + (timedelta(hours=1) if hourly else timedelta(days=1))
    key = f"{scope}:{start.isoformat()}"
    db.execute(delete(UsageBucket).where(UsageBucket.expires_at <= now))
    if db.get(UsageBucket, key) is None:
        try:
            with db.begin_nested():
                db.add(UsageBucket(key=key, count=0, expires_at=expires))
                db.flush()
        except IntegrityError:
            pass  # Another transaction inserted this bucket first.
    result = db.execute(update(UsageBucket).where(
        UsageBucket.key == key, UsageBucket.count < limit
    ).values(count=UsageBucket.count + 1))
    db.commit()
    if result.rowcount != 1:
        raise HTTPException(429, "Demo usage limit reached. Try again after the quota resets.",
                            headers={"Retry-After": str(max(1, int((expires - now).total_seconds())))})


def allow_write(user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
    if user.role not in {"admin", "demo"}:
        raise HTTPException(403, "This account has read-only access")
    consume_quota(db, "complaint-writes", settings.COMPLAINTS_PER_DAY)
    return user


def allow_ai(user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
    if user.role not in {"admin", "demo"}:
        raise HTTPException(403, "This account has read-only access")
    if not settings.GROQ_API_KEY:
        raise HTTPException(503, "Live AI is unavailable. Use the synthetic sample or enter fields manually.")
    consume_quota(db, "ai", settings.AI_REQUESTS_PER_DAY)
    return user
