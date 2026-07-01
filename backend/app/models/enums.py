from enum import StrEnum


class OperationType(StrEnum):
    income = "income"
    expense = "expense"


class TransactionSource(StrEnum):
    manual = "manual"
    ai_text = "ai_text"
    ai_csv = "ai_csv"
    ai_image = "ai_image"


class ImportSource(StrEnum):
    text = "text"
    csv = "csv"
    image = "image"


class ImportJobStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    needs_review = "needs_review"
    completed = "completed"
    failed = "failed"


class DuplicateStatus(StrEnum):
    none = "none"
    possible_duplicate = "possible_duplicate"
    exact_duplicate = "exact_duplicate"


class CandidateStatus(StrEnum):
    new = "new"
    edited = "edited"
    confirmed = "confirmed"
    rejected = "rejected"
