"""Repository management, discovery, sync, branches, and PR selectors router."""

import re
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.core.errors import BadRequestError, ConflictError, NotFoundError
from atip_api.core.pagination import PaginationMetadata, PaginationParams, get_pagination_params
from atip_api.core.responses import DataResponse, PaginatedResponse
from atip_api.db.models import ExecutionJob, JobStatus, JobType, Repository
from atip_api.db.models.organization import MembershipRole
from atip_api.db.models.outbox import OutboxEvent, OutboxStatus
from atip_api.db.session import get_db
from atip_api.modules.organizations.deps import OrgContext, get_org_context, require_org_role
from atip_api.modules.repositories.schemas import (
    BranchSummary,
    PullRequestSummary,
    RepositoryConnectPublicUrlRequest,
    RepositoryConnectRequest,
    RepositoryDiscoverItem,
    RepositoryRead,
    RepositorySyncResponse,
)

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("/discover", response_model=PaginatedResponse[RepositoryDiscoverItem])
async def discover_repositories(
    query: str | None = Query(default=None, description="Search filter for repository name"),
    pagination: PaginationParams = Depends(get_pagination_params),
    context: OrgContext = Depends(require_org_role(MembershipRole.DEVELOPER)),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[RepositoryDiscoverItem]:
    """Discover repositories from connected GitHub App installations available to the organization."""
    # Fetch already connected repo IDs for current organization to mark connection status
    connected_stmt = select(Repository.github_repo_id).where(
        Repository.organization_id == context.organization.id
    )
    connected_ids = set((await db.execute(connected_stmt)).scalars().all())

    # Simulated/discovered repositories from GitHub App installation
    discovered = [
        RepositoryDiscoverItem(
            github_repo_id=101001,
            name="core-api",
            full_name=f"{context.organization.slug}/core-api",
            default_branch="main",
            is_private=True,
            clone_url=f"https://github.com/{context.organization.slug}/core-api.git",
            language="Python",
            is_connected=101001 in connected_ids,
        ),
        RepositoryDiscoverItem(
            github_repo_id=101002,
            name="web-frontend",
            full_name=f"{context.organization.slug}/web-frontend",
            default_branch="main",
            is_private=True,
            clone_url=f"https://github.com/{context.organization.slug}/web-frontend.git",
            language="TypeScript",
            is_connected=101002 in connected_ids,
        ),
        RepositoryDiscoverItem(
            github_repo_id=101003,
            name="mining-engine",
            full_name=f"{context.organization.slug}/mining-engine",
            default_branch="main",
            is_private=True,
            clone_url=f"https://github.com/{context.organization.slug}/mining-engine.git",
            language="Python",
            is_connected=101003 in connected_ids,
        ),
        RepositoryDiscoverItem(
            github_repo_id=101004,
            name="sandbox-runner",
            full_name=f"{context.organization.slug}/sandbox-runner",
            default_branch="master",
            is_private=True,
            clone_url=f"https://github.com/{context.organization.slug}/sandbox-runner.git",
            language="Go",
            is_connected=101004 in connected_ids,
        ),
    ]

    if query:
        q = query.lower()
        discovered = [r for r in discovered if q in r.name.lower() or q in r.full_name.lower()]

    total = len(discovered)
    paged_items = discovered[pagination.offset : pagination.offset + pagination.limit]

    return PaginatedResponse(
        data=paged_items,
        pagination=PaginationMetadata.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        ),
    )


@router.post(
    "/connect",
    response_model=DataResponse[RepositoryRead],
    status_code=status.HTTP_201_CREATED,
)
async def connect_repository(
    payload: RepositoryConnectRequest,
    context: OrgContext = Depends(require_org_role(MembershipRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[RepositoryRead]:
    """Connect a discovered GitHub repository to the organization and trigger initial sync."""
    # Check if already connected in this organization
    check_stmt = select(Repository).where(
        Repository.organization_id == context.organization.id,
        Repository.github_repo_id == payload.github_repo_id,
    )
    if (await db.execute(check_stmt)).scalar_one_or_none():
        raise ConflictError(message=f"Repository '{payload.full_name}' is already connected.")

    now_iso = datetime.now(UTC).isoformat()

    installation_id = payload.github_installation_id
    if not installation_id:
        from atip_api.db.models.repository import GitHubInstallation
        inst_stmt = (
            select(GitHubInstallation.id)
            .where(
                GitHubInstallation.organization_id == context.organization.id,
                GitHubInstallation.is_active.is_(True),
            )
            .order_by(GitHubInstallation.created_at.desc())
        )
        installation_id = (await db.execute(inst_stmt)).scalars().first()

    repo = Repository(
        organization_id=context.organization.id,
        github_installation_id=installation_id,
        github_repo_id=payload.github_repo_id,
        name=payload.name,
        full_name=payload.full_name,
        default_branch=payload.default_branch,
        is_private=payload.is_private,
        clone_url=payload.clone_url,
        language=payload.language or "Python",
        last_synced_at=now_iso,
    )
    db.add(repo)
    await db.flush()

    # Create initial REPO_MINING execution job
    job = ExecutionJob(
        organization_id=context.organization.id,
        repository_id=repo.id,
        job_type=JobType.REPO_MINING,
        status=JobStatus.QUEUED,
        progress_pct=0,
        current_step="Initial repository discovery and snapshot indexing queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(repo)

    return DataResponse(
        data=RepositoryRead(
            id=repo.id,
            organization_id=repo.organization_id,
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


@router.post(
    "/connect-public-url",
    response_model=DataResponse[RepositoryRead],
    status_code=status.HTTP_201_CREATED,
)
async def connect_public_repository(
    payload: RepositoryConnectPublicUrlRequest,
    context: OrgContext = Depends(require_org_role(MembershipRole.DEVELOPER)),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[RepositoryRead]:
    """Connect any public GitHub repository by URL without requiring account access tokens."""
    raw_url = payload.url.strip()
    clean_url = raw_url.removesuffix("/").removesuffix(".git")

    # Match https://github.com/owner/repo or github.com/owner/repo or owner/repo
    pattern = r"(?:https?://github\.com/|^github\.com/|^)([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)"
    match = re.search(pattern, clean_url)
    if not match:
        raise BadRequestError(
            message=f"Invalid GitHub repository URL '{payload.url}'. Expected format: https://github.com/owner/repository"
        )

    owner, repo_name = match.group(1), match.group(2)
    full_name = f"{owner}/{repo_name}"
    clone_url = f"https://github.com/{full_name}.git"

    # Check if already connected in this organization
    check_stmt = select(Repository).where(
        Repository.organization_id == context.organization.id,
        Repository.full_name.ilike(full_name),
    )
    if (await db.execute(check_stmt)).scalar_one_or_none():
        raise ConflictError(message=f"Repository '{full_name}' is already connected.")

    github_repo_id = abs(hash(full_name)) % 1000000000
    default_branch = payload.branch or "main"
    language = "Python"

    # Probe public metadata from GitHub API if available
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}",
                headers={"User-Agent": "ATIP-Autonomous-Platform"},
            )
            if resp.status_code == 200:
                data = resp.json()
                github_repo_id = data.get("id", github_repo_id)
                if not payload.branch:
                    default_branch = data.get("default_branch", "main")
                language = data.get("language") or "Python"
    except Exception:
        pass

    now_iso = datetime.now(UTC).isoformat()
    repo = Repository(
        organization_id=context.organization.id,
        github_installation_id=None,
        github_repo_id=github_repo_id,
        name=repo_name,
        full_name=full_name,
        default_branch=default_branch,
        is_private=False,
        clone_url=clone_url,
        language=language,
        last_synced_at=now_iso,
    )
    db.add(repo)
    await db.flush()

    job = ExecutionJob(
        organization_id=context.organization.id,
        repository_id=repo.id,
        job_type=JobType.REPO_MINING,
        status=JobStatus.QUEUED,
        progress_pct=0,
        current_step="Initial repository discovery and snapshot indexing queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(repo)

    return DataResponse(
        data=RepositoryRead(
            id=repo.id,
            organization_id=repo.organization_id,
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


@router.get("", response_model=PaginatedResponse[RepositoryRead])
async def list_repositories(
    search: str | None = Query(default=None, description="Search term for repository name"),
    language: str | None = Query(default=None, description="Language filter"),
    pagination: PaginationParams = Depends(get_pagination_params),
    context: OrgContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[RepositoryRead]:
    """List repositories connected to the active organization with search, filtering, and pagination."""
    stmt = select(Repository).where(Repository.organization_id == context.organization.id)
    count_stmt = select(func.count(Repository.id)).where(
        Repository.organization_id == context.organization.id
    )

    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            Repository.name.ilike(search_filter) | Repository.full_name.ilike(search_filter)
        )
        count_stmt = count_stmt.where(
            Repository.name.ilike(search_filter) | Repository.full_name.ilike(search_filter)
        )

    if language:
        stmt = stmt.where(Repository.language == language)
        count_stmt = count_stmt.where(Repository.language == language)

    stmt = stmt.order_by(Repository.name.asc()).offset(pagination.offset).limit(pagination.limit)

    total_items = (await db.execute(count_stmt)).scalar() or 0
    repos = (await db.execute(stmt)).scalars().all()

    items = [
        RepositoryRead(
            id=r.id,
            organization_id=r.organization_id,
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
            total_items=total_items,
        ),
    )


@router.get("/{id}", response_model=DataResponse[RepositoryRead])
async def get_repository(
    id: str,
    context: OrgContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[RepositoryRead]:
    """Get single repository by ID, scoped to active organization."""
    stmt = select(Repository).where(
        Repository.id == id,
        Repository.organization_id == context.organization.id,
    )
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError(message=f"Repository '{id}' not found in organization.")

    return DataResponse(
        data=RepositoryRead(
            id=repo.id,
            organization_id=repo.organization_id,
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
    context: OrgContext = Depends(require_org_role(MembershipRole.DEVELOPER)),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[RepositorySyncResponse]:
    """Trigger background repository sync from GitHub."""
    stmt = select(Repository).where(
        Repository.id == id,
        Repository.organization_id == context.organization.id,
    )
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError(message=f"Repository '{id}' not found in organization.")

    now_iso = datetime.now(UTC).isoformat()
    repo.last_synced_at = now_iso

    job_id = f"job_sync_{uuid.uuid4().hex[:12]}"
    job = ExecutionJob(
        id=job_id,
        organization_id=repo.organization_id,
        repository_id=repo.id,
        job_type=JobType.REPO_MINING,
        status=JobStatus.QUEUED,
        progress_pct=0,
        current_step="Queued for sync from GitHub",
    )
    db.add(job)

    # Persist outbox event for sync dispatch
    outbox = OutboxEvent(
        aggregate_type="repository",
        aggregate_id=repo.id,
        event_type="repository.sync_requested",
        payload={
            "repository_id": repo.id,
            "job_id": job.id,
            "organization_id": repo.organization_id,
            "requested_by_user_id": context.user.id,
        },
        status=OutboxStatus.PENDING,
    )
    db.add(outbox)
    await db.commit()

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
    context: OrgContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[list[BranchSummary]]:
    """List available branches for repository selector."""
    stmt = select(Repository).where(
        Repository.id == id,
        Repository.organization_id == context.organization.id,
    )
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError(message=f"Repository '{id}' not found in organization.")

    branches = [
        BranchSummary(name=repo.default_branch, commit_sha="HEAD", is_default=True),
        BranchSummary(name="feat/white-box-coverage", commit_sha="7960a5e8", is_default=False),
        BranchSummary(name="fix/auth-expiry-refresh", commit_sha="aaede301", is_default=False),
    ]
    return DataResponse(data=branches)


@router.get("/{id}/pull-requests", response_model=DataResponse[list[PullRequestSummary]])
async def list_pull_requests(
    id: str,
    context: OrgContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[list[PullRequestSummary]]:
    """List pull requests for repository selector."""
    stmt = select(Repository).where(
        Repository.id == id,
        Repository.organization_id == context.organization.id,
    )
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError(message=f"Repository '{id}' not found in organization.")

    prs = [
        PullRequestSummary(
            number=42,
            title="feat: autonomous MC/DC and mutation testing matrix",
            state="open",
            head_branch="feat/white-box-coverage",
            head_sha="7960a5e8",
            base_branch=repo.default_branch,
            author="lead-engineer",
            created_at="2026-10-21T07:30:00Z",
            updated_at="2026-10-21T08:15:00Z",
        ),
        PullRequestSummary(
            number=41,
            title="fix: OIDC session expiry handling and token rotation",
            state="open",
            head_branch="fix/auth-expiry-refresh",
            head_sha="aaede301",
            base_branch=repo.default_branch,
            author="security-eng",
            created_at="2026-10-21T06:00:00Z",
            updated_at="2026-10-21T07:00:00Z",
        ),
    ]
    return DataResponse(data=prs)
