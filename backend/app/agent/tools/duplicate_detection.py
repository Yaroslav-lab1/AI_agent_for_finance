import hashlib
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.transactions import find_duplicate


def build_source_hash(amount: Decimal, operation_type: str, occurred_at: date, comment: str | None) -> str:
    normalized = f"{amount:.2f}|{operation_type}|{occurred_at.isoformat()}|{(comment or '').strip().lower()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DuplicateDetectorTool:
    async def detect(self, db: AsyncSession, user_id: UUID, source_hash: str, amount: Decimal, operation_type: str, occurred_at: date):
        return await find_duplicate(db, user_id, source_hash, amount, operation_type, occurred_at)
