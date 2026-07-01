from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass
class ExtractedTransaction:
    amount: str
    date: str
    operation_type: str | None
    comment: str
    category: str | None = None
    confidence: Decimal = Decimal("0.80")
    raw_payload: dict = field(default_factory=dict)


@dataclass
class AgentCandidate:
    amount: Decimal
    operation_type: str
    category_slug: str
    category_id: UUID
    occurred_at: date
    comment: str
    confidence: Decimal
    duplicate_status: str
    duplicate_transaction_id: UUID | None
    source_hash: str
    raw_payload: dict
