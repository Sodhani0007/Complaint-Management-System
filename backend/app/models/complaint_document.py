from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ComplaintDocument(Base):
    __tablename__ = "complaint_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    complaint: Mapped["Complaint"] = relationship(back_populates="documents")
