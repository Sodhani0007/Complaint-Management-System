from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = (UniqueConstraint("product_id", "lot_number", name="uq_product_lot"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    lot_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    manufacture_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="batches")
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="batch")
