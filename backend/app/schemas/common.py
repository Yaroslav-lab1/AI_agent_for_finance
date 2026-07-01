from decimal import Decimal


def money_to_str(value: Decimal | int | float | None) -> str:
    if value is None:
        return "0.00"
    return f"{Decimal(value):.2f}"
