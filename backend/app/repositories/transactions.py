from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.transaction import Transaction


async def create_transaction(db: AsyncSession, **values) -> Transaction:
    transaction = Transaction(**values)
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction, ["category"])
    return transaction


def _filters(
    user_id: UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    operation_type: str | None = None,
    category_id: UUID | None = None,
    search: str | None = None,
):
    filters = [Transaction.user_id == user_id]
    if date_from:
        filters.append(Transaction.occurred_at >= date_from)
    if date_to:
        filters.append(Transaction.occurred_at <= date_to)
    if operation_type:
        filters.append(Transaction.operation_type == operation_type)
    if category_id:
        filters.append(Transaction.category_id == category_id)
    if search:
        filters.append(Transaction.comment.ilike(f"%{search}%"))
    return and_(*filters)


async def list_transactions(db: AsyncSession, user_id: UUID, limit: int = 50, offset: int = 0, **kwargs):
    where = _filters(user_id, **kwargs)
    total = await db.scalar(select(func.count()).select_from(Transaction).where(where))
    rows = await db.scalars(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(where)
        .order_by(Transaction.occurred_at.desc(), Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(rows.all()), int(total or 0)


async def get_transaction_for_user(db: AsyncSession, transaction_id: UUID, user_id: UUID) -> Transaction | None:
    return await db.scalar(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    )


async def find_duplicate(db: AsyncSession, user_id: UUID, source_hash: str, amount: Decimal, operation_type: str, occurred_at: date):
    exact = await db.scalar(select(Transaction).where(Transaction.user_id == user_id, Transaction.source_hash == source_hash))
    if exact:
        return "exact_duplicate", exact.id
    possible = await db.scalar(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.amount == amount,
            Transaction.operation_type == operation_type,
            Transaction.occurred_at == occurred_at,
        )
    )
    if possible:
        return "possible_duplicate", possible.id
    return "none", None
