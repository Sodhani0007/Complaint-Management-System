from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings, settings
from app.core.security import consume_quota, issue_session, token_digest, utcnow
from app.db.session import SessionLocal
from app.main import app
from app.models.auth import AuthSession, User
from app.models.complaint import Complaint
from app.seed import seed


def test_unauthenticated_access_is_rejected(client):
    with TestClient(app) as anonymous:
        for method, path in [("get", "/api/v1/complaints"), ("get", "/api/v1/complaints/1"),
                             ("post", "/api/v1/complaints"), ("post", "/api/v1/complaints/extract"),
                             ("post", "/api/v1/complaints/1/summary")]:
            assert getattr(anonymous, method)(path).status_code == 401


def test_seed_is_idempotent_and_readiness_checks_migrations(client):
    with SessionLocal() as db:
        before = db.scalar(select(func.count()).select_from(Complaint))
    seed()
    seed()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Complaint)) == before
    assert client.get("/ready").status_code == 200


def test_owner_login_logout_and_token_storage(client):
    with TestClient(app) as owner:
        assert owner.post("/api/v1/auth/login", json={"email": settings.ADMIN_EMAIL, "password": "wrong"}).status_code == 401
        result = owner.post("/api/v1/auth/login", json={
            "email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD})
        assert result.status_code == 200
        assert result.headers["cache-control"] == "no-store"
        token = result.json()["access_token"]
        with SessionLocal() as db:
            assert db.get(AuthSession, token) is None
            assert db.get(AuthSession, token_digest(token)) is not None
        owner.headers["Authorization"] = f"Bearer {token}"
        assert owner.get("/api/v1/auth/me").json()["role"] == "admin"
        assert owner.post("/api/v1/auth/logout").status_code == 204
        assert owner.get("/api/v1/complaints").status_code == 401


def test_expiry_and_read_only_role_are_enforced(client):
    with SessionLocal() as db:
        viewer = User(email="viewer@example.invalid", role="viewer", active=True)
        db.add(viewer)
        db.commit()
        token = issue_session(db, viewer)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/complaints", headers=headers).status_code == 200
    assert client.post("/api/v1/complaints", json={}, headers=headers).status_code == 403
    assert client.post("/api/v1/complaints/extract", data={"text": "sample"}, headers=headers).status_code == 403
    with SessionLocal.begin() as db:
        db.get(AuthSession, token_digest(token)).expires_at = utcnow() - timedelta(seconds=1)
    assert client.get("/api/v1/complaints", headers=headers).status_code == 401


def test_disabling_demo_revokes_existing_demo_access(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert client.get("/api/v1/complaints").status_code == 401
    assert client.post("/api/v1/auth/demo").status_code == 404


def test_quota_persists_across_database_sessions(client):
    with SessionLocal() as db:
        consume_quota(db, "test-persisted", 1)
    with SessionLocal() as db:
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as raised:
            consume_quota(db, "test-persisted", 1)
        assert raised.value.status_code == 429
        assert int(raised.value.headers["Retry-After"]) > 0


def test_zero_ai_quota_prevents_provider_calls(client, monkeypatch):
    monkeypatch.setattr(settings, "AI_REQUESTS_PER_DAY", 0)
    with patch("app.services.extraction_service.run_extraction_pipeline") as pipeline:
        response = client.post("/api/v1/complaints/extract", data={"text": "synthetic"})
    assert response.status_code == 429
    pipeline.assert_not_called()


def test_audit_failure_rolls_back_complaint(client):
    with SessionLocal() as db:
        before = db.scalar(select(func.count()).select_from(Complaint))
    with patch("app.repositories.complaint_repository.ComplaintRepository.save_extraction_record",
               side_effect=RuntimeError("simulated audit storage failure")):
        with pytest.raises(RuntimeError):
            client.post("/api/v1/complaints", json={
                "product_name": "Atomic test", "batch_lot_number": "ATOMIC", "description": "synthetic",
                "ai_extraction_snapshot": {"description": "original synthetic"}})
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Complaint)) == before


def test_text_is_in_body_and_query_text_is_not_accepted(client):
    assert client.post("/api/v1/complaints/extract", params={"text": "legacy"}).status_code == 400
    with patch("app.services.extraction_service.run_extraction_pipeline", return_value={
        "fields": {"description": "Synthetic body"}, "extraction_confidence": 0.5
    }) as pipeline:
        response = client.post("/api/v1/complaints/extract", data={"text": "Synthetic body"})
        assert response.status_code == 200
        pipeline.assert_called_once_with(raw_input="Synthetic body", input_type="text")


def test_production_rejects_debug_and_short_owner_password():
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", DEBUG=True)
    with pytest.raises(ValueError):
        Settings(ADMIN_EMAIL="owner@example.invalid", ADMIN_PASSWORD="short")


def test_quota_is_atomic_under_concurrent_requests(client):
    from concurrent.futures import ThreadPoolExecutor
    from fastapi import HTTPException

    def attempt(_):
        with SessionLocal() as db:
            try:
                consume_quota(db, "concurrent-test", 3)
                return 200
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=6) as pool:
        statuses = list(pool.map(attempt, range(12)))
    assert statuses.count(200) == 3
    assert statuses.count(429) == 9


def test_chunked_request_body_is_bounded_before_parsing(client):
    from app.core.http_limits import BodyLimitMiddleware
    from fastapi import FastAPI
    small_app = FastAPI()
    small_app.add_middleware(BodyLimitMiddleware, max_bytes=5)
    with TestClient(small_app) as limited:
        response = limited.post("/", content=iter([b"123", b"456"]),
                                headers={"Content-Type": "application/octet-stream"})
        assert response.status_code == 413


def test_schema_matches_migrations(client):
    from alembic import command
    from alembic.config import Config
    command.check(Config("alembic.ini"))


def test_pdf_sample_still_parses_after_dependency_upgrade():
    from pathlib import Path
    from app.services.document_service import parse_document
    text, kind = parse_document(
        Path("../sample_data/complaint_pdf_packaging_defect.pdf").read_bytes(), ".pdf")
    assert kind == "pdf"
    assert len(text.strip()) > 50
