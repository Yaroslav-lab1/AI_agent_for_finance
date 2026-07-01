import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


class AmountNormalizerTool:
    def normalize(self, value: str) -> Decimal:
        cleaned = re.sub(r"[^\d,.\-]", "", value).replace(" ", "")
        if cleaned.count(",") == 1 and cleaned.count(".") == 0:
            cleaned = cleaned.replace(",", ".")
        elif cleaned.count(",") > 0 and cleaned.count(".") > 0:
            cleaned = cleaned.replace(",", "")
        try:
            amount = abs(Decimal(cleaned)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Invalid amount") from exc
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return amount


class DateNormalizerTool:
    def normalize(self, value: str) -> date:
        value = value.strip()
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass
        raise ValueError("Invalid date")
