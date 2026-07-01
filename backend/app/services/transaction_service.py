from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.duplicate_detection import build_source_hash
from app.models.enums import TransactionSource
from app.repositories.categories import get_category
from app.repositories.transactions import create_transaction, get_transaction_for_user, list_transactions
from app.schemas.transaction import TransactionCreate


async def create_manual_transaction(db: AsyncSession, user_id: UUID, data: TransactionCreate):
    category = await get_category(db, data.category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")
    source_hash = build_source_hash(data.amount, data.operation_type, data.occurred_at, data.comment)
    transaction = await create_transaction(
        db,
        user_id=user_id,
        amount=data.amount,
        operation_type=data.operation_type,
        category_id=data.category_id,
        occurred_at=data.occurred_at,
        comment=data.comment,
        source=TransactionSource.manual.value,
        source_hash=source_hash,
    )
    await db.commit()
    return transaction


async def update_transaction(db: AsyncSession, user_id: UUID, transaction_id: UUID, data: TransactionCreate):
    transaction = await get_transaction_for_user(db, transaction_id, user_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if not await get_category(db, data.category_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")
    transaction.amount = data.amount
    transaction.operation_type = data.operation_type
    transaction.category_id = data.category_id
    transaction.occurred_at = data.occurred_at
    transaction.comment = data.comment
    transaction.source_hash = build_source_hash(data.amount, data.operation_type, data.occurred_at, data.comment)
    await db.commit()
    await db.refresh(transaction, ["category"])
    return transaction


async def get_transactions(db: AsyncSession, user_id: UUID, limit: int, offset: int, **filters):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    items, total = await list_transactions(db, user_id, limit=limit, offset=offset, **filters)
    return items, total, limit, offset


async def delete_transaction(db: AsyncSession, user_id: UUID, transaction_id: UUID) -> None:
    transaction = await get_transaction_for_user(db, transaction_id, user_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    await db.delete(transaction)
    await db.commit()
