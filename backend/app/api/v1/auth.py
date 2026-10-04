from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    bearer,
    consume_quota,
    current_user,
    issue_session,
    token_digest,
    verify_password,
)
from app.db.session import get_db
from app.models.auth import AuthSession, User

router = APIRouter(prefix="/auth", tags=["authentication"])
# Same work for nonexistent usernames, without generating a new hash per request.
_DUMMY_HASH = "pbkdf2_sha256$600000$dummy$" + "0" * 64


class Login(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=256)


@router.get("/config")
def auth_config():
    return {"demo_enabled": settings.DEMO_MODE, "live_ai_enabled": bool(settings.GROQ_API_KEY)}


@router.post("/login")
def login(payload: Login, response: Response, db: Session = Depends(get_db)):
    consume_quota(db, "password-logins", 60, hourly=True)
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    valid = verify_password(payload.password, user.password_hash if user and user.password_hash else _DUMMY_HASH)
    if not valid or user is None or not user.active:
        raise HTTPException(401, "Invalid email or password")
    response.headers["Cache-Control"] = "no-store"
    return issue_session(db, user)


@router.post("/demo")
def demo_login(response: Response, db: Session = Depends(get_db)):
    if not settings.DEMO_MODE:
        raise HTTPException(404, "Demo access is disabled")
    consume_quota(db, "demo-logins", 60, hourly=True)
    user = db.scalar(select(User).where(User.email == "demo@example.invalid", User.role == "demo"))
    if user is None or not user.active:
        raise HTTPException(503, "Demo data has not been initialized")
    response.headers["Cache-Control"] = "no-store"
    return issue_session(db, user)


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"email": user.email, "role": user.role}


@router.post("/logout", status_code=204)
def logout(
    user: User = Depends(current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_digest(credentials.credentials)))
    db.commit()
