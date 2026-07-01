from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_serializer


class SummaryResponse(BaseModel):
    income_total: Decimal
    expense_total: Decimal
    balance: Decimal

    @field_serializer("income_total", "expense_total", "balance")
    def serialize_money(self, value: Decimal) -> str:
        return f"{value:.2f}"


class ExpenseByCategoryResponse(BaseModel):
    category_id: UUID
    category_slug: str
    category_name: str
    amount: Decimal

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return f"{value:.2f}"
