"""Repository management router."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.core.errors import NotFoundError
from atip_api.core.pagination import PaginationMetadata, PaginationParams, get_pagination_params
from atip_api.core.responses import DataResponse, PaginatedResponse
from atip_api.db.models import ExecutionJob, JobStatus, JobType, Repository
from atip_api.db.session import get_db
from atip_api.modules.repositories.schemas import (
    BranchSummary,
    RepositoryRead,
    RepositorySyncResponse,
)

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("", response_model=PaginatedResponse[RepositoryRead])
async def list_repositories(
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[RepositoryRead]:
    """List repositories connected to the active organization."""
    stmt = select(Repository).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(stmt)
    repos = result.scalars().all()

    items = [
        RepositoryRead(
            id=r.id,
            name=r.name,
            full_name=r.full_name,
            default_branch=r.default_branch,
            is_private=r.is_private,
            clone_url=r.clone_url,
            language=r.language,
            last_synced_at=r.last_synced_at,
            created_at=r.created_at,
        )
        for r in repos
    ]

    return PaginatedResponse(
        data=items,
        pagination=PaginationMetadata.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=len(items),
        ),
    )


@router.get("/{id}", response_model=DataResponse[RepositoryRead])
async def get_repository(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> DataResponse[RepositoryRead]:
    """Get single repository by ID."""
    stmt = select(Repository).where(Repository.id == id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError(f"Repository '{id}' not found")

    return DataResponse(
        data=RepositoryRead(
            id=repo.id,
            name=repo.name,
            full_name=repo.full_name,
            default_branch=repo.default_branch,
            is_private=repo.is_private,
            clone_url=repo.clone_url,
            language=repo.language,
            last_synced_at=repo.last_synced_at,
            created_at=repo.created_at,
        )
    )


@router.post("/{id}/sync", response_model=DataResponse[RepositorySyncResponse])
async def sync_repository(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DataResponse[RepositorySyncResponse]:
    """Trigger background repository sync from GitHub."""
    stmt = select(Repository).where(Repository.id == id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError(f"Repository '{id}' not found")

    job_id = f"job_sync_{uuid.uuid4().hex[:12]}"
    job = ExecutionJob(
        id=job_id,
        organization_id=repo.organization_id,
        repository_id=repo.id,
        job_type=JobType.REPO_MINING,
        status=JobStatus.QUEUED,
        progress_pct=0,
        current_step="Queued for sync",
    )
    db.add(job)
    await db.flush()

    return DataResponse(
        data=RepositorySyncResponse(
            repository_id=repo.id,
            status="queued",
            job_id=job.id,
            message="Repository sync dispatched to mining worker",
        )
    )


@router.get("/{id}/branches", response_model=DataResponse[list[BranchSummary]])
async def list_branches(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> DataResponse[list[BranchSummary]]:
    """List available branches for repository."""
    stmt = select(Repository).where(Repository.id == id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError(f"Repository '{id}' not found")

    branches = [
        BranchSummary(name=repo.default_branch, commit_sha="HEAD", is_default=True),
    ]
    return DataResponse(data=branches)
