"""All tests use disposable databases; never use the developer's DATABASE_URL."""
import os
import tempfile
from pathlib import Path

import pytest

_temp = tempfile.TemporaryDirectory(prefix="complaints-tests-")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{Path(_temp.name) / 'test.db'}")
os.environ["DEMO_MODE"] = "true"
os.environ["GROQ_API_KEY"] = "test_key_for_ci"
os.environ["DEBUG"] = "false"
os.environ["ENVIRONMENT"] = "test"
os.environ["ADMIN_EMAIL"] = "owner@example.invalid"
os.environ["ADMIN_PASSWORD"] = "only-for-automated-tests"
os.environ["AI_REQUESTS_PER_DAY"] = "1000"
os.environ["COMPLAINTS_PER_DAY"] = "1000"


@pytest.fixture(scope="module")
def client():
    from alembic import command
    from alembic.config import Config
    from fastapi.testclient import TestClient

    from app.main import app
    from app.seed import seed

    config = Config("alembic.ini")
    command.upgrade(config, "head")
    seed()
    with TestClient(app) as client:
        session = client.post("/api/v1/auth/demo")
        assert session.status_code == 200
        client.headers["Authorization"] = f"Bearer {session.json()['access_token']}"
        yield client
    command.downgrade(config, "base")
    from app.db.session import engine
    engine.dispose()
