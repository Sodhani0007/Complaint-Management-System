import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Severity(str, enum.Enum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"


class Priority(str, enum.Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ComplaintStatus(str, enum.Enum):
    PENDING_TRIAGE = "Pending Triage"
    UNDER_INVESTIGATION = "Under Investigation"
    CLOSED = "Closed"


class Complaint(Base):
    """
    The central record of the system. Deliberately uses Python enums (not
    free-text strings) for severity/priority/status — this is what stops
    "critical", "Critical", "CRITICAL" from silently becoming three different
    values in the DB, which would break every downstream query and chart.
    """

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("batches.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))

    complaint_source: Mapped[str | None] = mapped_column(String(100))
    customer_name: Mapped[str | None] = mapped_column(String(255))
    complaint_type: Mapped[str | None] = mapped_column(String(100))
    complaint_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    quantity_affected: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    severity: Mapped[Severity | None] = mapped_column(Enum(Severity, native_enum=False))
    priority: Mapped[Priority | None] = mapped_column(Enum(Priority, native_enum=False))
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, native_enum=False), default=ComplaintStatus.PENDING_TRIAGE
    )
    raw_source_text: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    batch: Mapped["Batch"] = relationship(back_populates="complaints")
    documents: Mapped[list["ComplaintDocument"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    extractions: Mapped[list["AIExtraction"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
