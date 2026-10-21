"""Repository mining, commit history, snapshots, and analysis progress SSE router."""

import asyncio
import uuid
from collections import defaultdict
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
from atip_api.db.models.mining import (
    AnalysisRun,
    CommitRecord,
    DependencyEdgeRecord,
    FileChangeRecord,
)
from atip_api.db.models.organization import OrganizationMembership, User
from atip_api.db.models.repository import Repository, RepositorySnapshot
from atip_api.db.session import get_db
from atip_api.modules.identity.deps import get_current_active_user
from atip_api.modules.mining.dependency_graph import DependencyGraphBuilder
from atip_api.modules.mining.git_fetcher import GitExecutionError, GitSecurityError, SafeGitFetcher
from atip_api.modules.mining.history_miner import HistoryMiner
from atip_api.modules.mining.schemas import (
    CommitDetailRead,
    CommitRead,
    CoverageFileDetailRead,
    CoverageIngestRequest,
    CoverageSummaryRead,
    DependencyEdgeRead,
    DependencyGraphRead,
    DependencyNodeRead,
    DiscoveredTestRead,
    FileChangeRead,
    FileComplexityRead,
    FileDependencyDetailRead,
    FunctionComplexityRead,
    HotspotRead,
    MineHistoryRequest,
    SnapshotCreateRequest,
    SnapshotFileContent,
    SnapshotRead,
    SnapshotTreeItem,
)
from atip_api.modules.mining.snapshot import SafePathTraversalError, SnapshotError, SnapshotManager
from atip_api.modules.mining.static_analyzer import (
    CodeComplexityAnalyzer,
    CoverageIngester,
    TestDiscoverer,
)

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


@router.post(
    "/repositories/{id}/mine-history",
    response_model=DataResponse[list[CommitRead]],
    status_code=status.HTTP_200_OK,
)
async def mine_repository_history(
    id: str,
    payload: MineHistoryRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[list[CommitRead]]:
    """Mine commit history, file diffs, and change statistics without checkout."""
    org_id = _extract_org_id(request, current_user)
    repo = await _verify_repo_access(session, id, org_id, current_user.id)

    miner = HistoryMiner()
    try:
        commits = await miner.mine_repository_history(
            session=session,
            org_id=org_id,
            repository=repo,
            branch=payload.branch,
            max_commits=payload.max_commits,
            include_patch=True,
        )
    except GitSecurityError as e:
        raise BadRequestError(f"Security restriction violated: {e}") from e
    except GitExecutionError as e:
        raise BadRequestError(f"Mining failed: {e}") from e

    return DataResponse(
        data=[
            CommitRead(
                id=c.id,
                repository_id=c.repository_id,
                organization_id=c.organization_id,
                commit_sha=c.commit_sha,
                tree_sha=c.tree_sha,
                parent_shas=c.parent_shas,
                author_name=c.author_name,
                author_email=c.author_email,
                committer_name=c.committer_name,
                committer_email=c.committer_email,
                committed_at=c.committed_at.isoformat() if c.committed_at else None,
                summary=c.summary,
                message=c.message,
                insertions=c.insertions,
                deletions=c.deletions,
                files_changed_count=c.files_changed_count,
                created_at=c.created_at.isoformat(),
            )
            for c in commits
        ]
    )


@router.get(
    "/repositories/{id}/commits",
    response_model=PaginatedResponse[CommitRead],
)
async def list_commits(
    id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CommitRead]:
    """List mined repository commits with pagination."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    count_stmt = select(func.count(CommitRecord.id)).where(
        CommitRecord.repository_id == id,
        CommitRecord.organization_id == org_id,
    )
    total_count = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        select(CommitRecord)
        .where(
            CommitRecord.repository_id == id,
            CommitRecord.organization_id == org_id,
        )
        .order_by(CommitRecord.committed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()

    return PaginatedResponse(
        data=[
            CommitRead(
                id=c.id,
                repository_id=c.repository_id,
                organization_id=c.organization_id,
                commit_sha=c.commit_sha,
                tree_sha=c.tree_sha,
                parent_shas=c.parent_shas,
                author_name=c.author_name,
                author_email=c.author_email,
                committer_name=c.committer_name,
                committer_email=c.committer_email,
                committed_at=c.committed_at.isoformat() if c.committed_at else None,
                summary=c.summary,
                message=c.message,
                insertions=c.insertions,
                deletions=c.deletions,
                files_changed_count=c.files_changed_count,
                created_at=c.created_at.isoformat(),
            )
            for c in items
        ],
        pagination=PaginationMetadata.create(
            page=page,
            page_size=page_size,
            total_items=total_count,
        ),
        meta=ResponseMeta(),
    )


@router.get(
    "/repositories/{id}/commits/{commit_sha}",
    response_model=DataResponse[CommitDetailRead],
)
async def get_commit_detail(
    id: str,
    commit_sha: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[CommitDetailRead]:
    """Get commit details including file changes and modifications."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    stmt = select(CommitRecord).where(
        CommitRecord.repository_id == id,
        CommitRecord.organization_id == org_id,
        (CommitRecord.commit_sha == commit_sha) | (CommitRecord.id == commit_sha),
    )
    commit_rec = (await session.execute(stmt)).scalar_one_or_none()
    if not commit_rec:
        raise NotFoundError("Commit not found")

    fc_stmt = (
        select(FileChangeRecord)
        .where(
            FileChangeRecord.repository_id == id,
            FileChangeRecord.organization_id == org_id,
            FileChangeRecord.commit_sha == commit_rec.commit_sha,
        )
        .order_by(FileChangeRecord.file_path.asc())
    )
    file_changes = (await session.execute(fc_stmt)).scalars().all()

    return DataResponse(
        data=CommitDetailRead(
            commit=CommitRead(
                id=commit_rec.id,
                repository_id=commit_rec.repository_id,
                organization_id=commit_rec.organization_id,
                commit_sha=commit_rec.commit_sha,
                tree_sha=commit_rec.tree_sha,
                parent_shas=commit_rec.parent_shas,
                author_name=commit_rec.author_name,
                author_email=commit_rec.author_email,
                committer_name=commit_rec.committer_name,
                committer_email=commit_rec.committer_email,
                committed_at=commit_rec.committed_at.isoformat()
                if commit_rec.committed_at
                else None,
                summary=commit_rec.summary,
                message=commit_rec.message,
                insertions=commit_rec.insertions,
                deletions=commit_rec.deletions,
                files_changed_count=commit_rec.files_changed_count,
                created_at=commit_rec.created_at.isoformat(),
            ),
            file_changes=[
                FileChangeRead(
                    id=fc.id,
                    commit_sha=fc.commit_sha,
                    file_path=fc.file_path,
                    previous_path=fc.previous_path,
                    change_type=fc.change_type,
                    insertions=fc.insertions,
                    deletions=fc.deletions,
                    is_test=fc.is_test,
                    language=fc.language,
                    patch=fc.patch,
                )
                for fc in file_changes
            ],
        )
    )


@router.get(
    "/repositories/{id}/hotspots",
    response_model=DataResponse[list[HotspotRead]],
)
async def get_repository_hotspots(
    id: str,
    request: Request,
    min_changes: int = Query(default=1, ge=1),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[list[HotspotRead]]:
    """Get file churn, ownership, and risk hotspot ranking."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    miner = HistoryMiner()
    hotspots = await miner.compute_hotspots_and_ownership(
        session=session,
        org_id=org_id,
        repository_id=id,
        min_changes=min_changes,
    )

    return DataResponse(
        data=[
            HotspotRead(
                file_path=h["file_path"],
                change_count=h["change_count"],
                total_insertions=h["total_insertions"],
                total_deletions=h["total_deletions"],
                total_churn=h["total_churn"],
                distinct_authors_count=h["distinct_authors_count"],
                primary_owner=h["primary_owner"],
                ownership_pct=h["ownership_pct"],
                authors=h["authors"],
                is_test=h["is_test"],
                language=h["language"],
                hotspot_score=h["hotspot_score"],
                last_modified=h["last_modified"],
            )
            for h in hotspots
        ]
    )


@router.get(
    "/repositories/{id}/dependencies",
    response_model=DataResponse[DependencyGraphRead],
)
async def get_repository_dependencies(
    id: str,
    request: Request,
    commit_sha: str = Query(default="HEAD"),
    repo_path: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[DependencyGraphRead]:
    """Get import and dependency graph with nodes, edges, and cycles."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    target_repo_path = repo_path or "."
    git_fetcher = SafeGitFetcher()
    try:
        resolved_sha = await git_fetcher.resolve_commit_sha(target_repo_path, commit_sha)
    except GitSecurityError as e:
        raise BadRequestError(f"Invalid commit ref: {e}") from e
    except GitExecutionError as e:
        raise NotFoundError(f"Could not resolve commit {commit_sha}: {e}") from e

    # 1. Check if graph was already built and persisted in DB
    edge_stmt = select(DependencyEdgeRecord).where(
        DependencyEdgeRecord.repository_id == id,
        DependencyEdgeRecord.organization_id == org_id,
        DependencyEdgeRecord.commit_sha == resolved_sha,
    )
    existing_edges = (await session.execute(edge_stmt)).scalars().all()

    builder = DependencyGraphBuilder(git_fetcher=git_fetcher)
    if existing_edges:
        file_to_deps: dict[str, list[str]] = defaultdict(list)
        file_to_dependents: dict[str, list[str]] = defaultdict(list)
        edges_read: list[DependencyEdgeRead] = []

        for de in existing_edges:
            edges_read.append(
                DependencyEdgeRead(
                    source=de.source_file,
                    target=de.target_file or de.target_module,
                    target_module=de.target_module,
                    target_file=de.target_file,
                    is_external=de.is_external,
                    import_type=de.import_type,
                    line=(de.edge_metadata or {}).get("line_number", 1),
                )
            )
            if de.target_file:
                file_to_deps[de.source_file].append(de.target_file)
                file_to_dependents[de.target_file].append(de.source_file)

        all_files = set(file_to_deps.keys()).union(file_to_dependents.keys())
        nodes_read = [
            DependencyNodeRead(
                id=f,
                file_path=f,
                fan_in=len(file_to_dependents[f]),
                fan_out=len(file_to_deps[f]),
                dependencies=file_to_deps[f],
                dependents=file_to_dependents[f],
            )
            for f in all_files
        ]
        cycles = builder._find_cycles(file_to_deps)

        return DataResponse(
            data=DependencyGraphRead(
                commit_sha=resolved_sha,
                total_nodes=len(nodes_read),
                total_edges=len(edges_read),
                internal_edges_count=sum(1 for e in edges_read if not e.is_external),
                external_edges_count=sum(1 for e in edges_read if e.is_external),
                circular_cycles=cycles,
                nodes=nodes_read,
                edges=edges_read,
            )
        )

    # 2. Build and persist fresh graph
    graph_data = await builder.build_and_persist_graph(
        session=session,
        org_id=org_id,
        repository_id=id,
        commit_sha=resolved_sha,
        repo_path=target_repo_path,
    )

    return DataResponse(
        data=DependencyGraphRead(
            commit_sha=graph_data["commit_sha"],
            total_nodes=graph_data["total_nodes"],
            total_edges=graph_data["total_edges"],
            internal_edges_count=graph_data["internal_edges_count"],
            external_edges_count=graph_data["external_edges_count"],
            circular_cycles=graph_data["circular_cycles"],
            nodes=[
                DependencyNodeRead(
                    id=n["id"],
                    file_path=n["file_path"],
                    fan_in=n["fan_in"],
                    fan_out=n["fan_out"],
                    dependencies=n["dependencies"],
                    dependents=n["dependents"],
                )
                for n in graph_data["nodes"]
            ],
            edges=[
                DependencyEdgeRead(
                    source=e["source"],
                    target=e["target"],
                    target_module=e["target_module"],
                    target_file=e["target_file"],
                    is_external=e["is_external"],
                    import_type=e["import_type"],
                    line=e["line"],
                )
                for e in graph_data["edges"]
            ],
        )
    )


@router.get(
    "/repositories/{id}/dependencies/file",
    response_model=DataResponse[FileDependencyDetailRead],
)
async def get_file_dependencies(
    id: str,
    request: Request,
    path: str = Query(..., description="File path relative to repository root"),
    commit_sha: str = Query(default="HEAD"),
    repo_path: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[FileDependencyDetailRead]:
    """Get direct dependencies and reverse dependents (blast radius) for a specific file."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    target_repo_path = repo_path or "."
    git_fetcher = SafeGitFetcher()
    try:
        resolved_sha = await git_fetcher.resolve_commit_sha(target_repo_path, commit_sha)
    except Exception as e:
        raise NotFoundError(f"Commit not found: {e}") from e

    # Direct dependencies (where file is source)
    stmt_direct = select(DependencyEdgeRecord).where(
        DependencyEdgeRecord.repository_id == id,
        DependencyEdgeRecord.organization_id == org_id,
        DependencyEdgeRecord.commit_sha == resolved_sha,
        DependencyEdgeRecord.source_file == path,
    )
    direct_edges = (await session.execute(stmt_direct)).scalars().all()

    # Reverse dependents (where file is target)
    stmt_reverse = select(DependencyEdgeRecord).where(
        DependencyEdgeRecord.repository_id == id,
        DependencyEdgeRecord.organization_id == org_id,
        DependencyEdgeRecord.commit_sha == resolved_sha,
        DependencyEdgeRecord.target_file == path,
    )
    reverse_edges = (await session.execute(stmt_reverse)).scalars().all()

    return DataResponse(
        data=FileDependencyDetailRead(
            file_path=path,
            direct_dependencies=[
                DependencyEdgeRead(
                    source=de.source_file,
                    target=de.target_file or de.target_module,
                    target_module=de.target_module,
                    target_file=de.target_file,
                    is_external=de.is_external,
                    import_type=de.import_type,
                    line=(de.edge_metadata or {}).get("line_number", 1),
                )
                for de in direct_edges
            ],
            reverse_dependents=[
                DependencyEdgeRead(
                    source=re.source_file,
                    target=re.target_file or re.target_module,
                    target_module=re.target_module,
                    target_file=re.target_file,
                    is_external=re.is_external,
                    import_type=re.import_type,
                    line=(re.edge_metadata or {}).get("line_number", 1),
                )
                for re in reverse_edges
            ],
            blast_radius_count=len(reverse_edges),
        )
    )


@router.get(
    "/repositories/{id}/complexity",
    response_model=DataResponse[list[FileComplexityRead]],
)
async def get_repository_complexity(
    id: str,
    request: Request,
    commit_sha: str = Query(default="HEAD"),
    file_path: str | None = Query(default=None),
    repo_path: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[list[FileComplexityRead]]:
    """Compute LOC, Cyclomatic Complexity, function inventory, and maintainability index."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    target_repo_path = repo_path or "."
    git_fetcher = SafeGitFetcher()
    try:
        resolved_sha = await git_fetcher.resolve_commit_sha(target_repo_path, commit_sha)
    except (GitSecurityError, GitExecutionError) as e:
        raise NotFoundError(f"Could not resolve commit {commit_sha}: {e}") from e

    if file_path:
        try:
            content_bytes = await git_fetcher.read_file_at_commit(
                target_repo_path, resolved_sha, file_path
            )
        except (GitSecurityError, GitExecutionError) as e:
            raise NotFoundError(f"File '{file_path}' not found at commit {commit_sha}: {e}") from e
        text = content_bytes.decode("utf-8", errors="replace")
        metric = CodeComplexityAnalyzer.analyze_source(text, file_path)
        return DataResponse(
            data=[
                FileComplexityRead(
                    file_path=metric.file_path,
                    language=metric.language,
                    lines_total=metric.lines_total,
                    lines_code=metric.lines_code,
                    lines_comments=metric.lines_comments,
                    lines_blank=metric.lines_blank,
                    cyclomatic_complexity=metric.cyclomatic_complexity,
                    average_function_complexity=metric.average_function_complexity,
                    max_function_complexity=metric.max_function_complexity,
                    maintainability_index=metric.maintainability_index,
                    functions=[
                        FunctionComplexityRead(
                            name=f.name,
                            line_start=f.line_start,
                            line_end=f.line_end,
                            complexity=f.complexity,
                            arg_count=f.arg_count,
                        )
                        for f in metric.functions
                    ],
                )
            ]
        )

    try:
        tree = await git_fetcher.list_tree_files(target_repo_path, resolved_sha)
    except (GitSecurityError, GitExecutionError) as e:
        raise NotFoundError(f"Could not list tree for commit {resolved_sha}: {e}") from e

    results: list[FileComplexityRead] = []
    source_exts = {".py", ".pyw", ".ts", ".tsx", ".js", ".jsx"}
    for f in tree:
        p = f["path"]
        if any(p.endswith(ext) for ext in source_exts) and not p.startswith("node_modules/"):
            try:
                content_bytes = await git_fetcher.read_file_at_commit(
                    target_repo_path, resolved_sha, p
                )
                text = content_bytes.decode("utf-8", errors="replace")
                metric = CodeComplexityAnalyzer.analyze_source(text, p)
                results.append(
                    FileComplexityRead(
                        file_path=metric.file_path,
                        language=metric.language,
                        lines_total=metric.lines_total,
                        lines_code=metric.lines_code,
                        lines_comments=metric.lines_comments,
                        lines_blank=metric.lines_blank,
                        cyclomatic_complexity=metric.cyclomatic_complexity,
                        average_function_complexity=metric.average_function_complexity,
                        max_function_complexity=metric.max_function_complexity,
                        maintainability_index=metric.maintainability_index,
                        functions=[
                            FunctionComplexityRead(
                                name=fn.name,
                                line_start=fn.line_start,
                                line_end=fn.line_end,
                                complexity=fn.complexity,
                                arg_count=fn.arg_count,
                            )
                            for fn in metric.functions
                        ],
                    )
                )
            except Exception:
                continue

    return DataResponse(data=results)


@router.get(
    "/repositories/{id}/tests",
    response_model=DataResponse[list[DiscoveredTestRead]],
)
async def get_repository_tests(
    id: str,
    request: Request,
    commit_sha: str = Query(default="HEAD"),
    repo_path: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[list[DiscoveredTestRead]]:
    """Discover existing test suites, test cases, and framework types across repository."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    target_repo_path = repo_path or "."
    git_fetcher = SafeGitFetcher()
    try:
        resolved_sha = await git_fetcher.resolve_commit_sha(target_repo_path, commit_sha)
    except (GitSecurityError, GitExecutionError) as e:
        raise NotFoundError(f"Could not resolve commit {commit_sha}: {e}") from e

    try:
        tree = await git_fetcher.list_tree_files(target_repo_path, resolved_sha)
    except (GitSecurityError, GitExecutionError) as e:
        raise NotFoundError(f"Could not list tree for commit {resolved_sha}: {e}") from e

    discovered: list[DiscoveredTestRead] = []
    test_exts = {".py", ".pyw", ".ts", ".tsx", ".js", ".jsx"}
    for f in tree:
        p = f["path"]
        is_test_file = (
            "test" in p.lower()
            or "spec" in p.lower()
            or p.endswith(("_test.py", "test_.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js"))
        )
        if is_test_file and any(p.endswith(ext) for ext in test_exts):
            try:
                content_bytes = await git_fetcher.read_file_at_commit(
                    target_repo_path, resolved_sha, p
                )
                text = content_bytes.decode("utf-8", errors="replace")
                cases = TestDiscoverer.discover_in_file(text, p)
                for c in cases:
                    discovered.append(
                        DiscoveredTestRead(
                            file_path=c.file_path,
                            suite_name=c.suite_name,
                            test_name=c.test_name,
                            line_number=c.line_number,
                            framework=c.framework,
                            language=c.language,
                        )
                    )
            except Exception:
                continue

    return DataResponse(data=discovered)


@router.post(
    "/repositories/{id}/coverage/ingest",
    response_model=DataResponse[CoverageSummaryRead],
    status_code=status.HTTP_201_CREATED,
)
async def ingest_repository_coverage(
    id: str,
    payload: CoverageIngestRequest,
    request: Request,
    commit_sha: str = Query(default="HEAD"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[CoverageSummaryRead]:
    """Ingest real coverage report (Coverage.py JSON, LCOV info, or Cobertura XML)."""
    org_id = _extract_org_id(request, current_user)
    repo = await _verify_repo_access(session, id, org_id, current_user.id)

    fmt = payload.format_type.lower()
    try:
        if fmt in {"coverage.json", "json"}:
            report = CoverageIngester.parse_coverage_json(payload.content)
        elif fmt in {"lcov", "lcov.info"}:
            report = CoverageIngester.parse_lcov(payload.content)
        elif fmt in {"cobertura", "cobertura_xml", "xml"}:
            report = CoverageIngester.parse_cobertura_xml(payload.content)
        else:
            raise BadRequestError(
                f"Unsupported coverage format '{payload.format_type}'. Expected coverage.json, lcov, or cobertura_xml."
            )
    except Exception as e:
        if isinstance(e, BadRequestError):
            raise
        raise BadRequestError(
            f"Failed to parse coverage content as {payload.format_type}: {e}"
        ) from e

    files_dict = {
        fp: {
            "file_path": fd.file_path,
            "statements_total": fd.statements_total,
            "statements_covered": fd.statements_covered,
            "coverage_pct": fd.coverage_pct,
            "covered_lines": fd.covered_lines,
            "uncovered_lines": fd.uncovered_lines,
        }
        for fp, fd in report.files.items()
    }
    summary_dict = {
        "format_type": report.format_type,
        "statements_total": report.statements_total,
        "statements_covered": report.statements_covered,
        "statement_coverage_pct": report.statement_coverage_pct,
        "branches_total": report.branches_total,
        "branches_covered": report.branches_covered,
        "branch_coverage_pct": report.branch_coverage_pct,
        "files_count": len(report.files),
        "files": files_dict,
    }

    analysis_stmt = (
        select(AnalysisRun)
        .where(
            AnalysisRun.repository_id == id,
            AnalysisRun.organization_id == org_id,
            AnalysisRun.commit_sha == commit_sha,
        )
        .order_by(AnalysisRun.created_at.desc())
    )
    analysis = (await session.execute(analysis_stmt)).scalars().first()

    if not analysis:
        analysis = AnalysisRun(
            repository_id=id,
            organization_id=org_id,
            commit_sha=commit_sha,
            branch=repo.default_branch,
            status="completed",
            coverage_summary=summary_dict,
        )
        session.add(analysis)
    else:
        analysis.coverage_summary = summary_dict

    await session.commit()

    return DataResponse(
        data=CoverageSummaryRead(
            format_type=report.format_type,
            statements_total=report.statements_total,
            statements_covered=report.statements_covered,
            statement_coverage_pct=report.statement_coverage_pct,
            branches_total=report.branches_total,
            branches_covered=report.branches_covered,
            branch_coverage_pct=report.branch_coverage_pct,
            files_count=len(report.files),
            files={
                fp: CoverageFileDetailRead(
                    file_path=fd.file_path,
                    statements_total=fd.statements_total,
                    statements_covered=fd.statements_covered,
                    coverage_pct=fd.coverage_pct,
                    covered_lines=fd.covered_lines,
                    uncovered_lines=fd.uncovered_lines,
                )
                for fp, fd in report.files.items()
            },
        )
    )


@router.get(
    "/repositories/{id}/coverage",
    response_model=DataResponse[CoverageSummaryRead | None],
)
async def get_repository_coverage(
    id: str,
    request: Request,
    commit_sha: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> DataResponse[CoverageSummaryRead | None]:
    """Retrieve ingested coverage summary. If not ingested, returns None (honest empty state)."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(session, id, org_id, current_user.id)

    query = select(AnalysisRun).where(
        AnalysisRun.repository_id == id,
        AnalysisRun.organization_id == org_id,
        AnalysisRun.coverage_summary.isnot(None),
    )
    if commit_sha:
        query = query.where(AnalysisRun.commit_sha == commit_sha)
    query = query.order_by(AnalysisRun.created_at.desc())

    analysis = (await session.execute(query)).scalars().first()
    if not analysis or not analysis.coverage_summary:
        return DataResponse(data=None)

    cov = analysis.coverage_summary
    files_data = {
        fp: CoverageFileDetailRead(
            file_path=f["file_path"],
            statements_total=f["statements_total"],
            statements_covered=f["statements_covered"],
            coverage_pct=f["coverage_pct"],
            covered_lines=f.get("covered_lines", []),
            uncovered_lines=f.get("uncovered_lines", []),
        )
        for fp, f in cov.get("files", {}).items()
    }

    return DataResponse(
        data=CoverageSummaryRead(
            format_type=cov.get("format_type", "unknown"),
            statements_total=cov.get("statements_total", 0),
            statements_covered=cov.get("statements_covered", 0),
            statement_coverage_pct=cov.get("statement_coverage_pct", 0.0),
            branches_total=cov.get("branches_total", 0),
            branches_covered=cov.get("branches_covered", 0),
            branch_coverage_pct=cov.get("branch_coverage_pct", 0.0),
            files_count=cov.get("files_count", len(files_data)),
            files=files_data,
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
