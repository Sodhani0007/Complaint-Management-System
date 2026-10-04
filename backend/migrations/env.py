from alembic import context
from sqlalchemy import create_engine

from app.config import settings
from app.db.base import Base
from app.models import ai_extraction, auth, batch, complaint, complaint_document, product  # noqa: F401

target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()

