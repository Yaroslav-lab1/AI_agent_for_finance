from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_client import LLMClient, create_llm_client
from app.agent.schemas import AgentCandidate
from app.agent.tools.categorization import CategoryClassifierTool, OperationTypeResolverTool
from app.agent.tools.csv_input import CsvInputTool
from app.agent.tools.duplicate_detection import DuplicateDetectorTool, build_source_hash
from app.agent.tools.image_ocr import ImageOcrTool
from app.agent.tools.normalization import AmountNormalizerTool, DateNormalizerTool
from app.agent.tools.text_input import TextInputTool
from app.repositories.categories import get_category_by_slug


class AgentPipeline:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or create_llm_client()
        self.text_tool = TextInputTool()
        self.csv_tool = CsvInputTool()
        self.image_tool = ImageOcrTool()
        self.amount_tool = AmountNormalizerTool()
        self.date_tool = DateNormalizerTool()
        self.type_tool = OperationTypeResolverTool()
        self.category_tool = CategoryClassifierTool()
        self.duplicate_tool = DuplicateDetectorTool()

    async def run(
        self,
        db: AsyncSession,
        user_id: UUID,
        source_type: str,
        payload: str | bytes,
        content_type: str | None = None,
    ) -> list[AgentCandidate]:
        normalized_text = self._normalize_source_payload(source_type, payload, content_type)
        extracted = await self.llm_client.extract(normalized_text)
        candidates: list[AgentCandidate] = []
        for item in extracted:
            amount = self.amount_tool.normalize(item.amount)
            occurred_at = self.date_tool.normalize(item.date)
            operation_type = self.type_tool.resolve(item.comment, item.operation_type)
            category_slug = self.category_tool.classify(item.comment, operation_type, item.category)
            category = await get_category_by_slug(db, category_slug) or await get_category_by_slug(db, "other")
            if category is None:
                raise ValueError("Categories are not seeded")
            comment = item.comment[:500]
            source_hash = build_source_hash(amount, operation_type, occurred_at, comment)
            duplicate_status, duplicate_transaction_id = await self.duplicate_tool.detect(
                db, user_id, source_hash, amount, operation_type, occurred_at
            )
            confidence = min(max(item.confidence, Decimal("0.00")), Decimal("1.00"))
            candidates.append(
                AgentCandidate(
                    amount=amount,
                    operation_type=operation_type,
                    category_slug=category.slug,
                    category_id=category.id,
                    occurred_at=occurred_at,
                    comment=comment,
                    confidence=confidence,
                    duplicate_status=duplicate_status,
                    duplicate_transaction_id=duplicate_transaction_id,
                    source_hash=source_hash,
                    raw_payload=item.raw_payload,
                )
            )
        return candidates

    def _normalize_source_payload(self, source_type: str, payload: str | bytes, content_type: str | None = None) -> str:
        if source_type == "text":
            return self.text_tool.normalize(str(payload))
        elif source_type == "csv":
            return self.csv_tool.normalize(payload if isinstance(payload, bytes) else str(payload).encode())
        elif source_type == "image":
            ocr_text = self.image_tool.extract_text(payload if isinstance(payload, bytes) else str(payload).encode(), content_type)
            return self.text_tool.normalize(ocr_text)
        else:
            raise ValueError("Unsupported import source")
