"""Immutable commit-specific repository snapshot service and safe file reader."""

import logging
import tarfile
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.config import get_settings
from atip_api.db.models.repository import Repository, RepositorySnapshot
from atip_api.modules.mining.git_fetcher import SafeGitFetcher

logger = logging.getLogger(__name__)


class SnapshotError(Exception):
    """Raised when snapshot operations fail."""

    pass


class SafePathTraversalError(SnapshotError):
    """Raised when an attempt to escape the sandbox root is detected."""

    pass


@dataclass(frozen=True)
class SnapshotFileItem:
    path: str
    type: str  # "blob" | "tree"
    size_bytes: int
    sha: str


class SafeSnapshotReader:
    """Safe reader for extracted repository snapshot trees."""

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()
        if not self.root_path.exists() or not self.root_path.is_dir():
            raise SnapshotError(f"Snapshot directory does not exist: {self.root_path}")

    def safe_resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path within the snapshot root, preventing path traversal."""
        raw = relative_path.replace("\\", "/").strip()
        if not raw:
            raise SafePathTraversalError("Empty path is invalid")

        if raw.startswith("/") or raw.startswith("-") or (len(raw) > 1 and raw[1] == ":"):
            raise SafePathTraversalError(f"Absolute or unsafe path not permitted: {relative_path}")

        parts = raw.split("/")
        if ".." in parts or any(p.startswith("-") for p in parts):
            raise SafePathTraversalError(f"Path traversal sequence detected: {relative_path}")

        target = (self.root_path / raw).resolve()

        # Strict containment check
        try:
            target.relative_to(self.root_path)
        except ValueError as err:
            raise SafePathTraversalError(
                f"Path {relative_path} resolves outside snapshot root {self.root_path}"
            ) from err

        return target

    def read_text(self, relative_path: str, max_bytes: int = 10 * 1024 * 1024) -> str:
        """Read text file safely."""
        target = self.safe_resolve_path(relative_path)
        if not target.is_file():
            raise SnapshotError(f"File not found or is not a regular file: {relative_path}")

        size = target.stat().st_size
        if size > max_bytes:
            raise SnapshotError(f"File size {size} exceeds limit {max_bytes} bytes")

        return target.read_text(encoding="utf-8", errors="replace")

    def read_bytes(self, relative_path: str, max_bytes: int = 10 * 1024 * 1024) -> bytes:
        """Read binary file safely."""
        target = self.safe_resolve_path(relative_path)
        if not target.is_file():
            raise SnapshotError(f"File not found or is not a regular file: {relative_path}")

        size = target.stat().st_size
        if size > max_bytes:
            raise SnapshotError(f"File size {size} exceeds limit {max_bytes} bytes")

        return target.read_bytes()

    def list_files(self) -> list[SnapshotFileItem]:
        """List all files in the snapshot root."""
        items: list[SnapshotFileItem] = []
        for p in self.root_path.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(self.root_path)).replace("\\", "/")
                items.append(
                    SnapshotFileItem(
                        path=rel,
                        type="blob",
                        size_bytes=p.stat().st_size,
                        sha="",
                    )
                )
        return items


class SnapshotManager:
    """Manages immutable commit snapshots, safe fetch, and storage."""

    def __init__(
        self,
        base_storage_dir: str | Path | None = None,
        git_fetcher: SafeGitFetcher | None = None,
    ):
        settings = get_settings()
        self.base_storage_dir = Path(
            base_storage_dir or getattr(settings, "SNAPSHOT_STORAGE_PATH", "data/snapshots")
        ).resolve()
        self.git_fetcher = git_fetcher or SafeGitFetcher()

    def _get_snapshot_archive_path(self, org_id: str, repo_id: str, commit_sha: str) -> Path:
        return self.base_storage_dir / org_id / repo_id / f"{commit_sha}.tar.gz"

    def _get_snapshot_extract_path(self, org_id: str, repo_id: str, commit_sha: str) -> Path:
        return self.base_storage_dir / org_id / repo_id / "extracted" / commit_sha

    async def get_or_create_snapshot(
        self,
        session: AsyncSession,
        org_id: str,
        repository: Repository,
        ref_or_commit: str = "HEAD",
        local_repo_path: str | Path | None = None,
    ) -> RepositorySnapshot:
        """Create an immutable commit-specific snapshot or retrieve existing one."""
        # 1. Determine the source repo path (local repo or fixture or cloned directory)
        repo_path = Path(local_repo_path or ".").resolve()

        # 2. Resolve to exact 40-character commit SHA
        commit_sha = await self.git_fetcher.resolve_commit_sha(repo_path, ref_or_commit)

        # 3. Check for existing snapshot in database (idempotent lookup)
        stmt = select(RepositorySnapshot).where(
            RepositorySnapshot.organization_id == org_id,
            RepositorySnapshot.repository_id == repository.id,
            RepositorySnapshot.commit_sha == commit_sha,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("Found existing immutable snapshot for %s at %s", repository.id, commit_sha)
            return existing

        # 4. Extract commit metadata using safe git log (no checkout)
        meta = await self.git_fetcher.get_commit_metadata(repo_path, commit_sha)

        # 5. List tree files using safe git ls-tree
        tree_files = await self.git_fetcher.list_tree_files(repo_path, commit_sha)
        total_files = len(tree_files)
        total_bytes = sum(f.get("size_bytes", 0) for f in tree_files)

        # Detect primary languages based on file extensions
        lang_counts: dict[str, int] = {}
        for f in tree_files:
            p = f.get("path", "")
            ext = Path(p).suffix.lower()
            if ext in {".py", ".pyw"}:
                lang_counts["Python"] = lang_counts.get("Python", 0) + 1
            elif ext in {".ts", ".tsx"}:
                lang_counts["TypeScript"] = lang_counts.get("TypeScript", 0) + 1
            elif ext in {".js", ".jsx", ".mjs", ".cjs"}:
                lang_counts["JavaScript"] = lang_counts.get("JavaScript", 0) + 1
            elif ext in {".json"}:
                lang_counts["JSON"] = lang_counts.get("JSON", 0) + 1

        stats_json = {
            "total_files": total_files,
            "total_bytes": total_bytes,
            "languages": lang_counts,
            "tree_sha": meta.tree_sha,
        }

        # 6. Create immutable tar.gz archive using safe git archive (no checkout or hooks)
        archive_path = self._get_snapshot_archive_path(org_id, repository.id, commit_sha)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        await self.git_fetcher.create_snapshot_archive(repo_path, commit_sha, archive_path)

        # 7. Persist snapshot record in DB
        snapshot = RepositorySnapshot(
            organization_id=org_id,
            repository_id=repository.id,
            commit_sha=commit_sha,
            tree_sha=meta.tree_sha,
            parent_shas=meta.parent_shas,
            branch_name=ref_or_commit
            if not meta.commit_sha.startswith(ref_or_commit)
            else repository.default_branch,
            ref=f"refs/heads/{ref_or_commit}"
            if not ref_or_commit.startswith("refs/")
            else ref_or_commit,
            summary=meta.summary[:512] if meta.summary else "Commit snapshot",
            author_name=meta.author_name[:255] if meta.author_name else None,
            author_email=meta.author_email[:255] if meta.author_email else None,
            committed_at=meta.committed_at,
            storage_path=str(archive_path),
            stats_json=stats_json,
        )
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        logger.info("Created immutable snapshot %s for commit %s", snapshot.id, commit_sha)
        return snapshot

    async def get_snapshot_reader(
        self,
        snapshot: RepositorySnapshot,
    ) -> SafeSnapshotReader:
        """Get a safe sandboxed reader for the snapshot, extracting archive safely if needed."""
        extract_dir = self._get_snapshot_extract_path(
            snapshot.organization_id, snapshot.repository_id, snapshot.commit_sha
        )
        if not extract_dir.exists():
            archive_path = Path(snapshot.storage_path or "")
            if not archive_path.exists():
                raise SnapshotError(f"Snapshot archive missing on disk: {archive_path}")

            extract_dir.mkdir(parents=True, exist_ok=True)
            # Safely extract archive verifying member paths
            with tarfile.open(archive_path, "r:gz") as tar:
                for member in tar.getmembers():
                    # Reject absolute paths or paths with '..'
                    member_path = member.name.replace("\\", "/")
                    if member_path.startswith("/") or ".." in member_path.split("/"):
                        raise SafePathTraversalError(f"Malicious archive member: {member.name}")

                    # Strip leading prefix if present (e.g. commit_sha/)
                    parts = member_path.split("/")
                    if len(parts) > 1 and parts[0] == snapshot.commit_sha:
                        member.name = "/".join(parts[1:])

                    dest = (extract_dir / member.name).resolve()
                    try:
                        dest.relative_to(extract_dir)
                    except ValueError as err:
                        raise SafePathTraversalError(
                            f"Member escapes extraction root: {member.name}"
                        ) from err

                    tar.extract(member, extract_dir)

        return SafeSnapshotReader(extract_dir)
