"""Single-instance free-tier launcher: migrate, seed, then serve.

For multiple replicas, move migrations and bootstrap into a release job.
"""
import os
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config

from app.seed import seed

if __name__ == "__main__":
    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    seed()
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
