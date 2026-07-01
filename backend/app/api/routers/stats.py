from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.stats import ExpenseByCategoryResponse, SummaryResponse
from app.services.stats_service import expenses_by_category, summary


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=SummaryResponse)
async def summary_endpoint(
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    income, expense, balance = await summary(db, current_user.id, date_from, date_to)
    return SummaryResponse(income_total=income, expense_total=expense, balance=balance)


@router.get("/expenses-by-category", response_model=list[ExpenseByCategoryResponse])
async def expenses_by_category_endpoint(
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await expenses_by_category(db, current_user.id, date_from, date_to)
    return [
        ExpenseByCategoryResponse(category_id=row[0], category_slug=row[1], category_name=row[2], amount=row[3])
        for row in rows
    ]
