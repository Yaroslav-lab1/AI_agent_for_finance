from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, Base, TimestampMixin, uuid_pk


class ImportCandidate(TimestampMixin, Base):
    __tablename__ = "import_candidates"
    __table_args__ = (
        Index("ix_import_candidates_job", "import_job_id"),
        Index("ix_import_candidates_user_status", "user_id", "status"),
    )

    id = uuid_pk()
    import_job_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("categories.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))
    duplicate_status: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    duplicate_transaction_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    job = relationship("ImportJob", back_populates="candidates")
    category = relationship("Category")
