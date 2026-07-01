import json
import re
from datetime import date
from decimal import Decimal

import httpx

from app.core.config import get_settings
from app.agent.schemas import ExtractedTransaction


TRANSACTION_EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "amount": {"type": "string"},
                    "date": {"type": "string"},
                    "operation_type": {"type": "string", "enum": ["income", "expense"]},
                    "category": {
                        "type": "string",
                        "enum": [
                            "products",
                            "transport",
                            "restaurants",
                            "entertainment",
                            "health",
                            "transfers",
                            "salary",
                            "other",
                        ],
                    },
                    "comment": {"type": "string"},
                    "confidence": {"type": "string"},
                },
                "required": ["amount", "date", "operation_type", "category", "comment", "confidence"],
            },
        }
    },
    "required": ["transactions"],
}


class LLMClient:
    async def extract(self, text: str) -> list[ExtractedTransaction]:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    line_pattern = re.compile(
        r"(?P<date>\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2}).*?"
        r"(?P<kind>Списание|Оплата|Покупка|Зачисление|Поступление|Зарплата|income|expense)?\s*"
        r"(?P<amount>-?\d+[\s\d]*(?:[,.]\d{1,2})?)\s*(?:RUB|₽|руб\.?)?\s*(?P<comment>.*)",
        re.IGNORECASE,
    )

    async def extract(self, text: str) -> list[ExtractedTransaction]:
        results: list[ExtractedTransaction] = []
        for line in [item.strip() for item in text.splitlines() if item.strip()]:
            match = self.line_pattern.search(line)
            if not match:
                continue
            kind = (match.group("kind") or "").lower()
            op_type = "income" if any(word in kind for word in ["зачис", "поступ", "зарп", "income"]) else "expense"
            comment = match.group("comment").strip(" -;,\t") or line
            results.append(
                ExtractedTransaction(
                    amount=match.group("amount"),
                    date=match.group("date"),
                    operation_type=op_type,
                    comment=comment[:500],
                    confidence=Decimal("0.90"),
                    raw_payload={"line": line},
                )
            )
        return results


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def extract(self, text: str) -> list[ExtractedTransaction]:
        content = await self._request(text)
        return transactions_from_json_content(content)

    async def _request(self, text: str) -> str:
        today = date.today().isoformat()
        system_prompt = transaction_extraction_system_prompt()
        user_prompt = transaction_extraction_user_payload(text, today)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
                    ],
                    "temperature": 0,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "transaction_extraction", "schema": TRANSACTION_EXTRACTION_SCHEMA},
                    },
                },
            )
            response.raise_for_status()
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Unexpected LLM response format") from exc

    @staticmethod
    def _parse_json_content(content: str) -> dict:
        return parse_json_content(content)

    @staticmethod
    def _confidence(value: object) -> Decimal:
        return parse_confidence(value)


class OllamaLLMClient(LLMClient):
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 120,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def extract(self, text: str) -> list[ExtractedTransaction]:
        content = await self._request(text)
        return transactions_from_json_content(content)

    async def _request(self, text: str) -> str:
        today = date.today().isoformat()
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "think": False,
                    "format": TRANSACTION_EXTRACTION_SCHEMA,
                    "options": {"temperature": 0},
                    "messages": [
                        {"role": "system", "content": transaction_extraction_system_prompt()},
                        {"role": "user", "content": json.dumps(transaction_extraction_user_payload(text, today), ensure_ascii=False)},
                    ],
                },
            )
            response.raise_for_status()
        data = response.json()
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise ValueError("Unexpected Ollama response format") from exc


def transaction_extraction_system_prompt() -> str:
    return (
        "You are a deterministic parser of Russian bank notifications for a personal finance app. "
        "Return only JSON that matches the provided schema. Do not add markdown or explanations. "
        "Extract only real money movement transactions. Ignore balances, card numbers, account numbers, "
        "phone numbers, notification header times, and technical identifiers unless useful in a merchant comment. "
        "If a transaction has a time but no date, use current_date. Amount must be a positive decimal string with dot "
        "as separator and two decimal digits. operation_type must be income or expense. category must be one of: "
        "products, transport, restaurants, entertainment, health, transfers, salary, other. Purchases, payments, "
        "card debits, and SBP purchases are expenses. Incoming transfers, deposits, and salary are income. "
        "For OCR text from screenshots, reconstruct wrapped notification lines before extracting. "
        "Examples: Rostics, KFC, Burger King, cafes and restaurants -> restaurants; Магнит, Пятерочка, Перекресток -> products."
    )


def transaction_extraction_user_payload(text: str, current_date: str) -> dict:
    return {
        "current_date": current_date,
        "input_text": text,
        "instructions": [
            "Return JSON only.",
            "The top-level object must contain transactions.",
            "Use current_date when the source contains only time like 16:20.",
            "Ignore text after Баланс when it is only account balance.",
        ],
        "example": {
            "transactions": [
                {
                    "amount": "359.00",
                    "date": current_date,
                    "operation_type": "expense",
                    "category": "restaurants",
                    "comment": "Rostics_74022053",
                    "confidence": "0.90",
                }
            ]
        },
    }


def transactions_from_json_content(content: str) -> list[ExtractedTransaction]:
    payload = parse_json_content(content)
    rows = payload.get("transactions", [])
    if not isinstance(rows, list):
        raise ValueError("LLM response must contain a transactions array")

    transactions: list[ExtractedTransaction] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        amount = str(row.get("amount", "")).strip()
        occurred_at = str(row.get("date", "")).strip()
        comment = str(row.get("comment", "")).strip()
        operation_type = str(row.get("operation_type", "")).strip().lower() or None
        category = str(row.get("category", "")).strip().lower() or None
        confidence = parse_confidence(row.get("confidence", "0.70"))
        if not amount or not occurred_at or not comment:
            continue
        transactions.append(
            ExtractedTransaction(
                amount=amount,
                date=occurred_at,
                operation_type=operation_type,
                comment=comment,
                category=category,
                confidence=confidence,
                raw_payload=row,
            )
        )
    return transactions


def parse_json_content(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("LLM response JSON must be an object")
    return payload


def parse_confidence(value: object) -> Decimal:
    try:
        confidence = Decimal(str(value))
    except Exception:
        confidence = Decimal("0.70")
    return min(max(confidence, Decimal("0.00")), Decimal("1.00"))


def create_llm_client() -> LLMClient:
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    if provider == "mock":
        return MockLLMClient()
    if provider in {"openai", "openai-compatible"}:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAICompatibleLLMClient(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            base_url=settings.openai_base_url,
            timeout_seconds=settings.openai_request_timeout_seconds,
        )
    if provider in {"ollama", "qwen", "qwen3.5"}:
        return OllamaLLMClient(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            timeout_seconds=settings.ollama_request_timeout_seconds,
        )
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
