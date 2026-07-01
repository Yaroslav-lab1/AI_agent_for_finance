import csv
from io import StringIO


class CsvInputTool:
    aliases = {
        "date": ["date", "дата", "occurred_at", "дата операции"],
        "amount": ["amount", "сумма", "sum", "сумма операции"],
        "comment": ["comment", "описание", "назначение", "merchant", "контрагент"],
        "type": ["type", "тип", "operation_type", "операция"],
        "category": ["category", "category_slug", "категория"],
    }
    category_aliases = {
        "cafes_and_restaurants": "restaurants",
        "cafe": "restaurants",
        "cafes": "restaurants",
        "restaurants": "restaurants",
        "groceries": "products",
        "grocery": "products",
        "supermarkets": "products",
        "products": "products",
        "transport": "transport",
        "entertainment": "entertainment",
        "health": "health",
        "transfers": "transfers",
        "transfer": "transfers",
        "salary": "salary",
        "other": "other",
    }

    def bytes_to_text(self, content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "cp1251"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Unsupported CSV encoding")

    def normalize(self, content: bytes) -> str:
        raw = self.bytes_to_text(content)
        sample = raw[:4096]
        delimiter = self.detect_delimiter(sample)
        reader = csv.DictReader(StringIO(raw), delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        columns = {name.lower().strip(): name for name in reader.fieldnames}

        def find(key: str) -> str | None:
            for alias in self.aliases[key]:
                if alias in columns:
                    return columns[alias]
            return None

        date_col = find("date")
        amount_col = find("amount")
        comment_col = find("comment")
        type_col = find("type")
        category_col = find("category")
        lines: list[str] = []
        for row in reader:
            if date_col and amount_col:
                kind = row.get(type_col or "", "") or ""
                comment = row.get(comment_col or "", "") or ""
                category = self.normalize_category(row.get(category_col or "", "") or "")
                category_part = f"category:{category}" if category else ""
                lines.append(f"{row[date_col]} {kind} {row[amount_col]} RUB {category_part} {comment}".strip())
            else:
                lines.append(" ".join(value for value in row.values() if value))
        if not lines:
            raise ValueError("CSV has no rows")
        return "\n".join(lines)

    def normalize_category(self, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
        known_categories = set(self.category_aliases.values())
        return self.category_aliases.get(normalized, normalized if normalized in known_categories else "")

    def detect_delimiter(self, sample: str) -> str:
        if not sample.strip():
            return ","
        try:
            return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
        except csv.Error:
            first_line = sample.splitlines()[0] if sample.splitlines() else sample
            counts = {delimiter: first_line.count(delimiter) for delimiter in (",", ";", "\t")}
            return max(counts, key=counts.get) if max(counts.values()) > 0 else ","
