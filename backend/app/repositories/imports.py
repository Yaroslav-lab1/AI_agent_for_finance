from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_audit_log import AgentAuditLog
from app.models.import_candidate import ImportCandidate
from app.models.import_job import ImportJob


async def create_job(db: AsyncSession, user_id: UUID, source_type: str) -> ImportJob:
    job = ImportJob(user_id=user_id, source_type=source_type, status="pending")
    db.add(job)
    await db.flush()
    return job


async def get_job_for_user(db: AsyncSession, job_id: UUID, user_id: UUID) -> ImportJob | None:
    return await db.scalar(
        select(ImportJob).options(selectinload(ImportJob.candidates).selectinload(ImportCandidate.category)).where(
            ImportJob.id == job_id,
            ImportJob.user_id == user_id,
        )
    )


async def get_candidate_for_user(db: AsyncSession, candidate_id: UUID, user_id: UUID) -> ImportCandidate | None:
    return await db.scalar(
        select(ImportCandidate).options(selectinload(ImportCandidate.category)).where(
            ImportCandidate.id == candidate_id,
            ImportCandidate.user_id == user_id,
        )
    )


async def add_candidate(db: AsyncSession, **values) -> ImportCandidate:
    candidate = ImportCandidate(**values)
    db.add(candidate)
    await db.flush()
    await db.refresh(candidate, ["category"])
    return candidate


async def add_audit_log(db: AsyncSession, **values) -> AgentAuditLog:
    log = AgentAuditLog(**values)
    db.add(log)
    await db.flush()
    return log
