from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction


def _period_filters(user_id: UUID, date_from: date | None, date_to: date | None):
    filters = [Transaction.user_id == user_id]
    if date_from:
        filters.append(Transaction.occurred_at >= date_from)
    if date_to:
        filters.append(Transaction.occurred_at <= date_to)
    return filters


async def summary(db: AsyncSession, user_id: UUID, date_from: date | None = None, date_to: date | None = None):
    filters = _period_filters(user_id, date_from, date_to)
    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(case((Transaction.operation_type == "income", Transaction.amount), else_=0)), 0),
                func.coalesce(func.sum(case((Transaction.operation_type == "expense", Transaction.amount), else_=0)), 0),
            ).where(*filters)
        )
    ).one()
    income = Decimal(row[0]).quantize(Decimal("0.01"))
    expense = Decimal(row[1]).quantize(Decimal("0.01"))
    return income, expense, (income - expense).quantize(Decimal("0.01"))


async def expenses_by_category(db: AsyncSession, user_id: UUID, date_from: date | None = None, date_to: date | None = None):
    filters = _period_filters(user_id, date_from, date_to)
    filters.append(Transaction.operation_type == "expense")
    rows = await db.execute(
        select(Category.id, Category.slug, Category.name, func.coalesce(func.sum(Transaction.amount), 0))
        .join(Category, Category.id == Transaction.category_id)
        .where(*filters)
        .group_by(Category.id, Category.slug, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    return rows.all()
