from decimal import Decimal
from uuid import UUID

import pytest

from app.agent.llm_client import OllamaLLMClient, OpenAICompatibleLLMClient, create_llm_client, MockLLMClient, transactions_from_json_content
from app.agent.pipeline import AgentPipeline
from app.agent.schemas import ExtractedTransaction
from app.core.config import get_settings
from app.agent.tools.categorization import CategoryClassifierTool, OperationTypeResolverTool
from app.agent.tools.csv_input import CsvInputTool
from app.agent.tools.image_ocr import ImageOcrTool
from app.agent.tools.normalization import AmountNormalizerTool, DateNormalizerTool
from app.agent.tools.text_input import TextInputTool


def test_amount_normalizer_comma_decimal():
    assert AmountNormalizerTool().normalize("349,90 ₽") == Decimal("349.90")
    assert AmountNormalizerTool().normalize("-100") == Decimal("100.00")


def test_amount_normalizer_invalid():
    with pytest.raises(ValueError):
        AmountNormalizerTool().normalize("not money")


def test_date_normalizer_ru_and_iso():
    tool = DateNormalizerTool()
    assert tool.normalize("01.07.2026").isoformat() == "2026-07-01"
    assert tool.normalize("2026-07-01").isoformat() == "2026-07-01"


def test_text_input_rejects_empty():
    with pytest.raises(ValueError):
        TextInputTool().normalize(" \n ")


def test_csv_input_utf8_and_cp1251():
    tool = CsvInputTool()
    utf8 = "Дата;Сумма;Описание\n01.07.2026;349,90;Перекрёсток\n".encode()
    assert "Перекрёсток" in tool.normalize(utf8)
    cp1251 = "Дата;Сумма;Описание\n02.07.2026;220,00;Метро\n".encode("cp1251")
    assert "Метро" in tool.normalize(cp1251)

def test_csv_input_normalizes_demo_bank_export_categories():
    content = (
        "date,amount,type,category,comment\n"
        "2026-06-01,125000.00,income,salary,Зарплата за май\n"
        "2026-06-02,2430.50,expense,groceries,\"Пятёрочка, продукты\"\n"
        "2026-06-03,890.00,expense,cafes_and_restaurants,Кофе и обед\n"
    ).encode()
    normalized = CsvInputTool().normalize(content)
    assert "category:salary Зарплата за май" in normalized
    assert "category:products Пятёрочка, продукты" in normalized
    assert "category:restaurants Кофе и обед" in normalized


def test_csv_input_delimiter_fallback():
    tool = CsvInputTool()
    assert tool.detect_delimiter("date,amount,type\n2026-06-01,100.00,income") == ","


def test_category_classifier_and_type_resolver():
    assert CategoryClassifierTool().classify("Перекрёсток", "expense") == "products"
    assert CategoryClassifierTool().classify("Метро", "expense") == "transport"
    assert CategoryClassifierTool().classify("Непонятно", "expense") == "other"
    assert OperationTypeResolverTool().resolve("Зачисление зарплата", None) == "income"
    assert OperationTypeResolverTool().resolve("Списание покупка", None) == "expense"


@pytest.mark.asyncio
async def test_mock_llm_extracts_transactions():
    rows = await MockLLMClient().extract("01.07.2026 Списание 349,90 RUB Перекрёсток")
    assert len(rows) == 1
    assert rows[0].operation_type == "expense"


def test_openai_client_parses_json_content():
    payload = OpenAICompatibleLLMClient._parse_json_content(
        '```json\n{"transactions":[{"amount":"359.00","date":"2026-07-01","operation_type":"expense","category":"restaurants","comment":"Rostics","confidence":"0.92"}]}\n```'
    )
    assert payload["transactions"][0]["amount"] == "359.00"
    assert payload["transactions"][0]["category"] == "restaurants"


def test_structured_json_content_to_transactions():
    rows = transactions_from_json_content(
        '{"transactions":[{"amount":"984.00","date":"2026-07-01","operation_type":"expense","category":"other","comment":"VY_8025_KCO_6","confidence":"0.88"}]}'
    )
    assert len(rows) == 1
    assert rows[0].amount == "984.00"
    assert rows[0].category == "other"
    assert rows[0].operation_type == "expense"


def test_structured_json_content_ignores_text_around_json():
    rows = transactions_from_json_content(
        'Result:\n{"transactions":[{"amount":"153.98","date":"2026-07-01","operation_type":"expense","category":"products","comment":"Magnit","confidence":"0.90"}]}\nDone.'
    )
    assert len(rows) == 1
    assert rows[0].amount == "153.98"
    assert rows[0].comment == "Magnit"


def test_openai_provider_requires_api_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        create_llm_client()
    monkeypatch.setattr(settings, "llm_provider", "mock")


def test_ollama_provider_factory(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(settings, "llm_model", "qwen3.5:9b")
    monkeypatch.setattr(settings, "ollama_base_url", "http://localhost:11434")
    client = create_llm_client()
    assert isinstance(client, OllamaLLMClient)
    assert client.model == "qwen3.5:9b"
    monkeypatch.setattr(settings, "llm_provider", "mock")


@pytest.mark.asyncio
async def test_image_payload_is_ocr_text_before_llm(db_session, monkeypatch):
    captured = {}

    class CapturingLLMClient:
        async def extract(self, text: str):
            captured["text"] = text
            return [
                ExtractedTransaction(
                    amount="153.98",
                    date="2026-07-01",
                    operation_type="expense",
                    category="products",
                    comment="Magnit",
                )
            ]

    monkeypatch.setattr(
        ImageOcrTool,
        "extract_text",
        lambda self, content, content_type=None: "  Card MIR-8487\nPurchase 153.98 RUB Magnit  ",
    )
    pipeline = AgentPipeline(llm_client=CapturingLLMClient())
    candidates = await pipeline.run(
        db_session,
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        source_type="image",
        payload=b"fake-image",
        content_type="image/png",
    )

    assert captured["text"] == "Card MIR-8487\nPurchase 153.98 RUB Magnit"
    assert len(candidates) == 1
    assert candidates[0].amount == Decimal("153.98")
    assert candidates[0].category_slug == "products"
