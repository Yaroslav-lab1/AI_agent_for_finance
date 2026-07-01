from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, uuid_pk


class AgentAuditLog(TimestampMixin, Base):
    __tablename__ = "agent_audit_logs"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    import_job_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("import_jobs.id", ondelete="SET NULL"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
