from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionListResponse, TransactionResponse
from app.services.transaction_service import create_manual_transaction, delete_transaction, get_transactions, update_transaction


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction_endpoint(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_manual_transaction(db, current_user.id, payload)


@router.get("", response_model=TransactionListResponse)
async def list_transactions_endpoint(
    date_from: date | None = None,
    date_to: date | None = None,
    operation_type: str | None = Query(default=None, pattern="^(income|expense)$"),
    category_id: UUID | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total, limit, offset = await get_transactions(
        db,
        current_user.id,
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        operation_type=operation_type,
        category_id=category_id,
        search=search,
    )
    return TransactionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction_endpoint(
    transaction_id: UUID,
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_transaction(db, current_user.id, transaction_id, payload)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction_endpoint(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_transaction(db, current_user.id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
