"""Idempotent bootstrap for the single shared demo. Never deletes complaint data."""

from sqlalchemy import select

from app.config import settings
from app.core.security import hash_password, verify_password
from app.db.session import SessionLocal
from app.models import ai_extraction, complaint_document  # noqa: F401
from app.models.auth import User
from app.models.batch import Batch
from app.models.complaint import Complaint, Priority, Severity
from app.models.product import Product


def seed() -> None:
    with SessionLocal.begin() as db:
        if settings.ADMIN_EMAIL:
            email = settings.ADMIN_EMAIL.strip().lower()
            if email == "demo@example.invalid":
                raise ValueError("ADMIN_EMAIL cannot be the reserved demo address")
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                db.add(User(email=email, role="admin", password_hash=hash_password(settings.ADMIN_PASSWORD)))
            elif not user.password_hash or not verify_password(settings.ADMIN_PASSWORD, user.password_hash):
                user.password_hash = hash_password(settings.ADMIN_PASSWORD)
                # Password rotation revokes outstanding sessions.
                from sqlalchemy import delete

                from app.models.auth import AuthSession
                db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))

        if not settings.DEMO_MODE:
            return
        if db.scalar(select(User).where(User.email == "demo@example.invalid")) is None:
            db.add(User(email="demo@example.invalid", role="demo", password_hash=None))
        product = db.scalar(select(Product).where(Product.name == "Demo Vitamin Tablets (synthetic)"))
        if product is None:
            product = Product(name="Demo Vitamin Tablets (synthetic)")
            db.add(product)
            db.flush()
        batch = db.scalar(select(Batch).where(Batch.product_id == product.id, Batch.lot_number == "DEMO-001"))
        if batch is None:
            batch = Batch(product_id=product.id, lot_number="DEMO-001")
            db.add(batch)
            db.flush()
        if db.scalar(select(Complaint.id).where(Complaint.batch_id == batch.id).limit(1)) is None:
            db.add(Complaint(product_id=product.id, batch_id=batch.id, customer_name="Synthetic Customer",
                             description="Synthetic example: damaged outer packaging; tablets appear intact.",
                             severity=Severity.MINOR, priority=Priority.LOW, complaint_source="Demo"))


if __name__ == "__main__":
    seed()
