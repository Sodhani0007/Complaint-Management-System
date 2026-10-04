from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIExtraction(Base):
    """
    Optional client-supplied snapshot saved with a confirmed complaint.
    Not independent proof of an extraction attempt: server-owned provenance
    and a full change history remain future work.
    """

    __tablename__ = "ai_extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"))
    # Generic JSON, not Postgres's JSONB — the assignment allows MySQL OR
    # Postgres, and JSONB isn't portable across dialects. Generic JSON works
    # on both real backends and made this catchable in a quick SQLite smoke
    # test rather than only failing during the actual demo.
    extracted_json: Mapped[dict] = mapped_column(JSON)
    model_used: Mapped[str] = mapped_column(String(100))
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    complaint: Mapped["Complaint"] = relationship(back_populates="extractions")
