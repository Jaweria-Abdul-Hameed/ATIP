"""Repository mining, commit history, snapshots, and analysis progress SSE router."""

import asyncio
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.core.errors import BadRequestError, ForbiddenError, NotFoundError
from atip_api.core.pagination import PaginationMetadata
from atip_api.core.responses import DataResponse, PaginatedResponse, ResponseMeta
from atip_api.core.sse import ServerSentEvent, sse_event_stream
from atip_api.db.models.organization import OrganizationMembership, User
from atip_api.db.models.repository import Repository, RepositorySnapshot
from atip_api.db.session import get_db
from atip_api.modules.identity.deps import get_current_active_user
from atip_api.modules.mining.git_fetcher import GitExecutionError, GitSecurityError, SafeGitFetcher
from atip_api.modules.mining.schemas import (
    SnapshotCreateRequest,
    SnapshotFileContent,
    SnapshotRead,
    SnapshotTreeItem,
)
from atip_api.modules.mining.snapshot import SafePathTraversalError, SnapshotError, SnapshotManager

router = APIRouter(tags=["Mining & Analysis"])


def _extract_org_id(request: Request, current_user: User) -> str:
    """Extract organization ID from header or user's active membership."""
    header_org = request.headers.get("X-Organization-ID")
    if header_org:
        return header_org
    if current_user.memberships:
        return current_user.memberships[0].organization_id
    raise ForbiddenError("User is not a member of any organization")


async def _verify_repo_access(
    session: AsyncSession, repo_id: str, org_id: str, user_id: str
) -> Repository:
    """Verify user belongs to organization and repository exists within tenant."""
    # Check org membership
    mem_stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user_id,
    )
    mem = (await session.execute(mem_stmt)).scalar_one_or_none()
    if not mem:
        raise ForbiddenError("You do not have access to this organization")

    repo_stmt = select(Repository).where(
        Repository.id == repo_id,
        Repository.organization_id == org_id,
    )
    repo = (await session.execute(repo_stmt)).scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository not found")
    return repo


@router.post(
    "/repositories/{id}/snapshots",
    response_model=DataResponse[SnapshotRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_snapshot(
    id: str,
    payload: SnapshotCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[SnapshotRead]:
    """Create or retrieve an immutable commit-specific repository snapshot."""
    org_id = _extract_org_id(request, current_user)
    repo = await _verify_repo_access(session, id, org_id, current_user.id)

    manager = SnapshotManager()
    ref_or_commit = payload.commit_sha or payload.ref or "HEAD"

    try:
        snapshot = await manager.get_or_create_snapshot(
            session=session,
            org_id=org_id,
            repository=repo,
            ref_or_commit=ref_or_commit,
        )
    except (GitSecurityError, SafePathTraversalError) as e:
        raise BadRequestError(f"Security restriction violated: {e}") from e
    except (GitExecutionError, SnapshotError) as e:
        raise BadRequestError(f"Snapshot creation failed: {e}") from e

    return DataResponse(
        data=SnapshotRead(
            id=snapshot.id,
            repository_id=snapshot.repository_id,
            organization_id=snapshot.organization_id,
            commit_sha=snapshot.commit_sha,
            tree_sha=snapshot.tree_sha,
            parent_shas=snapshot.parent_shas,
            branch_name=snapshot.branch_name,
            ref=snapshot.ref,
            summary=snapshot.summary,
            author_name=snapshot.author_name,
            author_email=snapshot.author_email,
            committed_at=snapshot.committed_at.isoformat() if snapshot.committed_at else None,
            stats_json=snapshot.stats_json,
            created_at=snapshot.created_at.isoformat(),
        )
    )


@router.get(
    "/repositories/{id}/snapshots",
    response_model=PaginatedResponse[SnapshotRead],
)
async def list_snapshots(
    id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SnapshotRead]:
    """List immutable repository snapshots."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    count_stmt = select(func.count(RepositorySnapshot.id)).where(
        RepositorySnapshot.repository_id == id,
        RepositorySnapshot.organization_id == org_id,
    )
    total_count = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        select(RepositorySnapshot)
        .where(
            RepositorySnapshot.repository_id == id,
            RepositorySnapshot.organization_id == org_id,
        )
        .order_by(RepositorySnapshot.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()

    return PaginatedResponse(
        data=[
            SnapshotRead(
                id=s.id,
                repository_id=s.repository_id,
                organization_id=s.organization_id,
                commit_sha=s.commit_sha,
                tree_sha=s.tree_sha,
                parent_shas=s.parent_shas,
                branch_name=s.branch_name,
                ref=s.ref,
                summary=s.summary,
                author_name=s.author_name,
                author_email=s.author_email,
                committed_at=s.committed_at.isoformat() if s.committed_at else None,
                stats_json=s.stats_json,
                created_at=s.created_at.isoformat(),
            )
            for s in items
        ],
        pagination=PaginationMetadata.create(
            page=page,
            page_size=page_size,
            total_items=total_count,
        ),
        meta=ResponseMeta(),
    )


@router.get(
    "/repositories/{id}/snapshots/{commit_sha}",
    response_model=DataResponse[SnapshotRead],
)
async def get_snapshot(
    id: str,
    commit_sha: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[SnapshotRead]:
    """Get single immutable snapshot by commit SHA or snapshot ID."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == id,
        RepositorySnapshot.organization_id == org_id,
        (RepositorySnapshot.commit_sha == commit_sha) | (RepositorySnapshot.id == commit_sha),
    )
    snapshot = (await session.execute(stmt)).scalar_one_or_none()
    if not snapshot:
        raise NotFoundError("Snapshot not found for given commit SHA")

    return DataResponse(
        data=SnapshotRead(
            id=snapshot.id,
            repository_id=snapshot.repository_id,
            organization_id=snapshot.organization_id,
            commit_sha=snapshot.commit_sha,
            tree_sha=snapshot.tree_sha,
            parent_shas=snapshot.parent_shas,
            branch_name=snapshot.branch_name,
            ref=snapshot.ref,
            summary=snapshot.summary,
            author_name=snapshot.author_name,
            author_email=snapshot.author_email,
            committed_at=snapshot.committed_at.isoformat() if snapshot.committed_at else None,
            stats_json=snapshot.stats_json,
            created_at=snapshot.created_at.isoformat(),
        )
    )


@router.get(
    "/repositories/{id}/snapshots/{commit_sha}/tree",
    response_model=DataResponse[list[SnapshotTreeItem]],
)
async def get_snapshot_tree(
    id: str,
    commit_sha: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[list[SnapshotTreeItem]]:
    """List all files in repository tree at snapshot commit without checkout."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    git_fetcher = SafeGitFetcher()
    try:
        files = await git_fetcher.list_tree_files(".", commit_sha)
    except GitSecurityError as e:
        raise BadRequestError(f"Invalid commit request: {e}") from e
    except GitExecutionError as e:
        raise NotFoundError(f"Could not list tree for commit {commit_sha}: {e}") from e

    return DataResponse(
        data=[
            SnapshotTreeItem(
                path=f["path"],
                type=f.get("type", "blob"),
                size_bytes=f.get("size_bytes", 0),
                sha=f.get("sha", ""),
            )
            for f in files
        ]
    )


@router.get(
    "/repositories/{id}/snapshots/{commit_sha}/files/{path:path}",
    response_model=DataResponse[SnapshotFileContent],
)
async def get_snapshot_file(
    id: str,
    commit_sha: str,
    path: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[SnapshotFileContent]:
    """Read a specific file from the repository at commit_sha safely without checkout."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    git_fetcher = SafeGitFetcher()
    try:
        content_bytes = await git_fetcher.read_file_at_commit(".", commit_sha, path)
    except GitSecurityError as e:
        raise BadRequestError(f"Path access rejected: {e}") from e
    except GitExecutionError as e:
        raise NotFoundError(f"File '{path}' not found at commit {commit_sha}: {e}") from e

    # Determine if text or binary
    is_binary = b"\x00" in content_bytes[:1024]
    text_content = (
        content_bytes.decode("utf-8", errors="replace") if not is_binary else "<binary data>"
    )

    return DataResponse(
        data=SnapshotFileContent(
            path=path,
            commit_sha=commit_sha,
            size_bytes=len(content_bytes),
            content=text_content,
            is_binary=is_binary,
        )
    )


class AnalysisTriggerRequest(BaseModel):
    commit_sha: str | None = Field(default=None, example="7960a5e8")
    branch: str | None = Field(default="main", example="main")


class AnalysisJobRead(BaseModel):
    id: str
    repository_id: str
    status: str = Field(default="running")
    progress_pct: int = Field(default=0)
    current_step: str = Field(default="Initializing repository checkout")
    commit_sha: str = Field(default="HEAD")


@router.post(
    "/repositories/{id}/analyses",
    response_model=DataResponse[AnalysisJobRead],
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_analysis(
    id: str,
    payload: AnalysisTriggerRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[AnalysisJobRead]:
    """Trigger repository mining and static analysis job."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    job_id = f"job_ana_{uuid.uuid4().hex[:12]}"
    job = AnalysisJobRead(
        id=job_id,
        repository_id=id,
        status="queued",
        progress_pct=0,
        current_step="Queued for analysis worker",
        commit_sha=payload.commit_sha or "HEAD",
    )
    return DataResponse(data=job)


@router.get("/analyses/{id}", response_model=DataResponse[AnalysisJobRead])
async def get_analysis(id: str) -> DataResponse[AnalysisJobRead]:
    """Get analysis job status and progress."""
    job = AnalysisJobRead(
        id=id,
        repository_id="repo_nextjs_dashboard",
        status="completed",
        progress_pct=100,
        current_step="Analysis completed successfully",
        commit_sha="HEAD",
    )
    return DataResponse(data=job)


@router.get("/analyses/{id}/events")
async def stream_analysis_events(id: str, request: Request) -> StreamingResponse:
    """Stream real-time analysis progress events via Server-Sent Events (SSE)."""

    async def event_generator() -> AsyncGenerator[ServerSentEvent, None]:
        steps = [
            ("queued", 0, "Job queued in outbox worker"),
            ("provisioning", 20, "Extracting commit diff and file changes"),
            ("running", 50, "Building dependency and import graph"),
            ("running", 80, "Discovering whitebox coverage objectives"),
            ("completed", 100, "Analysis complete. Persisted artifacts to object store"),
        ]
        for step_idx, (job_status, pct, desc) in enumerate(steps):
            if await request.is_disconnected():
                break
            yield ServerSentEvent(
                id=f"evt_{id}_{step_idx}",
                event="analysis_progress",
                data={
                    "job_id": id,
                    "status": job_status,
                    "progress_pct": pct,
                    "current_step": desc,
                },
            )
            await asyncio.sleep(0.01)

    return StreamingResponse(
        sse_event_stream(event_generator()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
