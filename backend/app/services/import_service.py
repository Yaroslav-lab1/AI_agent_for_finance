from time import perf_counter
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.pipeline import AgentPipeline
from app.agent.tools.duplicate_detection import build_source_hash
from app.models.enums import CandidateStatus, ImportJobStatus, TransactionSource
from app.repositories.categories import get_category
from app.repositories.imports import add_audit_log, add_candidate, create_job, get_candidate_for_user, get_job_for_user
from app.repositories.transactions import create_transaction
from app.schemas.imports import CandidateUpdateRequest


SOURCE_TO_TRANSACTION = {
    "text": TransactionSource.ai_text.value,
    "csv": TransactionSource.ai_csv.value,
    "image": TransactionSource.ai_image.value,
}


async def create_import(
    db: AsyncSession,
    user_id: UUID,
    source_type: str,
    payload: str | bytes,
    content_type: str | None = None,
    pipeline: AgentPipeline | None = None,
):
    job = await create_job(db, user_id, source_type)
    started = perf_counter()
    input_size = len(payload.encode("utf-8") if isinstance(payload, str) else payload)
    try:
        job.status = ImportJobStatus.processing.value
        candidates = await (pipeline or AgentPipeline()).run(db, user_id, source_type, payload, content_type)
        saved = []
        for candidate in candidates:
            saved.append(
                await add_candidate(
                    db,
                    import_job_id=job.id,
                    user_id=user_id,
                    category_id=candidate.category_id,
                    amount=candidate.amount,
                    operation_type=candidate.operation_type,
                    occurred_at=candidate.occurred_at,
                    comment=candidate.comment,
                    confidence=candidate.confidence,
                    duplicate_status=candidate.duplicate_status,
                    duplicate_transaction_id=candidate.duplicate_transaction_id,
                    status=CandidateStatus.new.value,
                    raw_payload=candidate.raw_payload,
                )
            )
        job.candidates_count = len(saved)
        job.status = ImportJobStatus.needs_review.value
        await add_audit_log(
            db,
            user_id=user_id,
            import_job_id=job.id,
            source_type=source_type,
            status="success",
            input_size_bytes=input_size,
            candidates_count=len(saved),
            duration_ms=int((perf_counter() - started) * 1000),
        )
        await db.commit()
        await db.refresh(job)
        for item in saved:
            await db.refresh(item, ["category"])
        return job, saved
    except Exception as exc:
        job.status = ImportJobStatus.failed.value
        job.error_message = str(exc)[:1000]
        await add_audit_log(
            db,
            user_id=user_id,
            import_job_id=job.id,
            source_type=source_type,
            status="failed",
            input_size_bytes=input_size,
            duration_ms=int((perf_counter() - started) * 1000),
            error_code=exc.__class__.__name__,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=job.error_message) from exc


async def get_import(db: AsyncSession, user_id: UUID, job_id: UUID):
    job = await get_job_for_user(db, job_id, user_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return job


async def update_candidate(db: AsyncSession, user_id: UUID, candidate_id: UUID, data: CandidateUpdateRequest):
    candidate = await get_candidate_for_user(db, candidate_id, user_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    if candidate.status not in {CandidateStatus.new.value, CandidateStatus.edited.value}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Finalized candidate cannot be edited")
    if not await get_category(db, data.category_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")
    candidate.amount = data.amount
    candidate.operation_type = data.operation_type
    candidate.category_id = data.category_id
    candidate.occurred_at = data.occurred_at
    candidate.comment = data.comment
    candidate.status = CandidateStatus.edited.value
    await db.commit()
    await db.refresh(candidate, ["category"])
    return candidate


async def confirm_import(db: AsyncSession, user_id: UUID, job_id: UUID, candidate_ids: list[UUID], reject_other_candidates: bool):
    job = await get_import(db, user_id, job_id)
    selected = set(candidate_ids)
    created = []
    for candidate in job.candidates:
        if candidate.id in selected and candidate.status != CandidateStatus.confirmed.value:
            source_hash = build_source_hash(candidate.amount, candidate.operation_type, candidate.occurred_at, candidate.comment)
            created.append(
                await create_transaction(
                    db,
                    user_id=user_id,
                    amount=candidate.amount,
                    operation_type=candidate.operation_type,
                    category_id=candidate.category_id,
                    occurred_at=candidate.occurred_at,
                    comment=candidate.comment,
                    source=SOURCE_TO_TRANSACTION[job.source_type],
                    source_hash=source_hash,
                )
            )
            candidate.status = CandidateStatus.confirmed.value
        elif reject_other_candidates and candidate.status in {CandidateStatus.new.value, CandidateStatus.edited.value}:
            candidate.status = CandidateStatus.rejected.value
    if all(candidate.status in {CandidateStatus.confirmed.value, CandidateStatus.rejected.value} for candidate in job.candidates):
        job.status = ImportJobStatus.completed.value
    await db.commit()
    for transaction in created:
        await db.refresh(transaction, ["category"])
    return created
