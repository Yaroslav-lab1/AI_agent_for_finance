from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.imports import (
    CandidateUpdateRequest,
    ConfirmImportRequest,
    ConfirmImportResponse,
    ImportCandidateResponse,
    ImportPreviewResponse,
    TextImportRequest,
)
from app.services.import_service import confirm_import, create_import, get_import, update_candidate


router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/text", response_model=ImportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def import_text_endpoint(payload: TextImportRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    job, candidates = await create_import(db, current_user.id, "text", payload.text)
    return ImportPreviewResponse(job=job, candidates=candidates)


@router.post("/csv", response_model=ImportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def import_csv_endpoint(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    job, candidates = await create_import(db, current_user.id, "csv", await file.read(), file.content_type)
    return ImportPreviewResponse(job=job, candidates=candidates)


@router.post("/image", response_model=ImportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def import_image_endpoint(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    job, candidates = await create_import(db, current_user.id, "image", await file.read(), file.content_type)
    return ImportPreviewResponse(job=job, candidates=candidates)


@router.get("/{job_id}", response_model=ImportPreviewResponse)
async def get_import_endpoint(job_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = await get_import(db, current_user.id, job_id)
    return ImportPreviewResponse(job=job, candidates=job.candidates)


@router.patch("/candidates/{candidate_id}", response_model=ImportCandidateResponse)
async def patch_candidate_endpoint(
    candidate_id: UUID,
    payload: CandidateUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_candidate(db, current_user.id, candidate_id, payload)


@router.post("/{job_id}/confirm", response_model=ConfirmImportResponse, status_code=status.HTTP_201_CREATED)
async def confirm_import_endpoint(
    job_id: UUID,
    payload: ConfirmImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = await confirm_import(db, current_user.id, job_id, payload.candidate_ids, payload.reject_other_candidates)
    return ConfirmImportResponse(created_transactions=created)
