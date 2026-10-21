"""Repository commit history mining, diff extraction, and change-frequency engine."""

import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.mining import CommitRecord, FileChangeRecord
from atip_api.db.models.repository import Repository
from atip_api.modules.mining.git_fetcher import SafeGitFetcher

logger = logging.getLogger(__name__)


class HistoryMiner:
    """Mines commit history, file changes, diffs, ownership, and change frequency."""

    def __init__(self, git_fetcher: SafeGitFetcher | None = None):
        self.git_fetcher = git_fetcher or SafeGitFetcher()

    async def mine_repository_history(
        self,
        session: AsyncSession,
        org_id: str,
        repository: Repository,
        branch: str = "HEAD",
        max_commits: int = 50,
        local_repo_path: str | Path | None = None,
        include_patch: bool = False,
    ) -> list[CommitRecord]:
        """Mine commit history and file diffs for a repository branch without checkout."""
        repo_path = Path(local_repo_path or ".").resolve()

        # 1. List commits using safe git log
        commits_meta = await self.git_fetcher.list_commits(
            repo_path=repo_path,
            max_count=max_commits,
            branch=branch,
        )

        mined_records: list[CommitRecord] = []

        for meta in commits_meta:
            # Check if commit already recorded (idempotent lookup)
            stmt = select(CommitRecord).where(
                CommitRecord.organization_id == org_id,
                CommitRecord.repository_id == repository.id,
                CommitRecord.commit_sha == meta.commit_sha,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                mined_records.append(existing)
                continue

            # Extract file changes using diff-tree
            file_changes_raw = await self.git_fetcher.get_commit_file_changes(
                repo_path=repo_path,
                commit_sha=meta.commit_sha,
                include_patch=include_patch,
            )

            total_ins = sum(fc["insertions"] for fc in file_changes_raw)
            total_del = sum(fc["deletions"] for fc in file_changes_raw)
            files_changed_count = len(file_changes_raw)

            stats_json = {
                "insertions": total_ins,
                "deletions": total_del,
                "files_changed_count": files_changed_count,
            }

            commit_rec = CommitRecord(
                organization_id=org_id,
                repository_id=repository.id,
                commit_sha=meta.commit_sha,
                tree_sha=meta.tree_sha,
                parent_shas=meta.parent_shas,
                author_name=meta.author_name[:255] if meta.author_name else None,
                author_email=meta.author_email[:255] if meta.author_email else None,
                committer_name=meta.committer_name[:255] if meta.committer_name else None,
                committer_email=meta.committer_email[:255] if meta.committer_email else None,
                committed_at=meta.committed_at,
                message=meta.message,
                summary=meta.summary[:512] if meta.summary else "",
                insertions=total_ins,
                deletions=total_del,
                files_changed_count=files_changed_count,
                stats_json=stats_json,
            )
            session.add(commit_rec)
            await session.flush()  # allocate ID

            for fc in file_changes_raw:
                f_record = FileChangeRecord(
                    organization_id=org_id,
                    repository_id=repository.id,
                    commit_id=commit_rec.id,
                    commit_sha=meta.commit_sha,
                    file_path=fc["file_path"],
                    previous_path=fc.get("previous_path"),
                    change_type=fc["change_type"],
                    insertions=fc["insertions"],
                    deletions=fc["deletions"],
                    patch=fc.get("patch"),
                    is_test=fc["is_test"],
                    language=fc.get("language"),
                )
                session.add(f_record)

            mined_records.append(commit_rec)

        await session.commit()
        logger.info(
            "Mined %d commits for repo %s (%s)",
            len(mined_records),
            repository.id,
            branch,
        )
        return mined_records

    async def compute_hotspots_and_ownership(
        self,
        session: AsyncSession,
        org_id: str,
        repository_id: str,
        min_changes: int = 1,
    ) -> list[dict[str, Any]]:
        """Compute file churn, authorship ownership, and hotspot risk ranking."""
        # Query all file changes joined with their commits
        stmt = (
            select(
                FileChangeRecord.file_path,
                FileChangeRecord.change_type,
                FileChangeRecord.insertions,
                FileChangeRecord.deletions,
                FileChangeRecord.is_test,
                FileChangeRecord.language,
                CommitRecord.author_name,
                CommitRecord.committed_at,
            )
            .join(CommitRecord, FileChangeRecord.commit_id == CommitRecord.id)
            .where(
                FileChangeRecord.organization_id == org_id,
                FileChangeRecord.repository_id == repository_id,
            )
        )
        rows = (await session.execute(stmt)).all()

        file_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "change_count": 0,
                "total_insertions": 0,
                "total_deletions": 0,
                "authors": defaultdict(int),
                "is_test": False,
                "language": None,
                "last_modified": None,
            }
        )

        for row in rows:
            path, _, ins, dels, is_test, lang, author, committed_at = row
            stats = file_stats[path]
            stats["change_count"] += 1
            stats["total_insertions"] += ins
            stats["total_deletions"] += dels
            stats["is_test"] = stats["is_test"] or is_test
            if lang and not stats["language"]:
                stats["language"] = lang
            if author:
                stats["authors"][author] += 1
            if committed_at:
                if not stats["last_modified"] or committed_at > stats["last_modified"]:
                    stats["last_modified"] = committed_at

        hotspots: list[dict[str, Any]] = []
        for path, stats in file_stats.items():
            if stats["change_count"] < min_changes:
                continue

            authors_dict = dict(stats["authors"])
            distinct_authors = len(authors_dict)
            total_churn = stats["total_insertions"] + stats["total_deletions"]

            if authors_dict:
                primary_owner = max(authors_dict.items(), key=lambda kv: kv[1])[0]
                owner_commits = authors_dict[primary_owner]
                ownership_pct = round((owner_commits / stats["change_count"]) * 100, 1)
            else:
                primary_owner = "Unknown"
                ownership_pct = 0.0

            # Hotspot score: log2(churn + 1) * change_count * (distinct_authors ^ 0.5)
            hotspot_score = round(
                math.log2(total_churn + 1)
                * stats["change_count"]
                * (math.sqrt(distinct_authors) if distinct_authors > 0 else 1.0),
                2,
            )

            hotspots.append(
                {
                    "file_path": path,
                    "change_count": stats["change_count"],
                    "total_insertions": stats["total_insertions"],
                    "total_deletions": stats["total_deletions"],
                    "total_churn": total_churn,
                    "distinct_authors_count": distinct_authors,
                    "primary_owner": primary_owner,
                    "ownership_pct": ownership_pct,
                    "authors": authors_dict,
                    "is_test": stats["is_test"],
                    "language": stats["language"],
                    "hotspot_score": hotspot_score,
                    "last_modified": stats["last_modified"].isoformat()
                    if stats["last_modified"]
                    else None,
                }
            )

        # Sort descending by hotspot score
        hotspots.sort(key=lambda h: h["hotspot_score"], reverse=True)
        return hotspots
