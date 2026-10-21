"""Safe Git fetching and repository isolation without script execution."""

import asyncio
import logging
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Strict hex SHA validation (40 characters)
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
# Safe ref name validation (alphanumeric, slash, dash, dot, underscore)
REF_RE = re.compile(r"^[a-zA-Z0-9_\-\./]+$")


class GitSecurityError(Exception):
    """Raised when an unsafe Git operation or malicious repository input is detected."""

    pass


class GitExecutionError(Exception):
    """Raised when a Git command fails."""

    pass


@dataclass(frozen=True)
class CommitMetadata:
    commit_sha: str
    tree_sha: str
    parent_shas: list[str]
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    committed_at: datetime
    message: str
    summary: str


class SafeGitFetcher:
    """Safe Git fetcher ensuring untrusted repository code never executes."""

    def __init__(self, timeout_seconds: int = 45):
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _safe_git_env() -> dict[str, str]:
        """Produce an isolated environment for Git commands disabling hooks and extensions."""
        env = dict(os.environ)
        # Disable all git hooks completely
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_TERMINAL_PROMPT"] = "0"
        # Disable external protocol extensions
        env["GIT_ALLOW_PROTOCOL"] = "file:https:http"
        return env

    @staticmethod
    def _safe_git_args() -> list[str]:
        """Core safety arguments appended to every git command."""
        # On Windows 'NUL' or empty string, on Unix '/dev/null' or empty string.
        # Setting core.hooksPath to empty string completely disables hooks in git >= 2.9
        hooks_null = "NUL" if os.name == "nt" else "/dev/null"
        return [
            "-c",
            f"core.hooksPath={hooks_null}",
            "-c",
            "protocol.ext.allow=never",
            "-c",
            "filter.lfs.smudge=",
            "-c",
            "filter.lfs.clean=",
            "-c",
            "core.protectNTFS=true",
            "-c",
            "core.protectHFS=true",
        ]

    async def run_git(
        self,
        args: list[str],
        cwd: str | Path | None = None,
        timeout: int | None = None,
    ) -> tuple[int, str, str]:
        """Execute git command safely with process isolation and timeout."""
        cmd = ["git", *self._safe_git_args(), *args]
        effective_timeout = timeout or self.timeout_seconds
        env = self._safe_git_env()

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(cwd) if cwd else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=effective_timeout,
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            return proc.returncode or 0, stdout, stderr
        except TimeoutError as err:
            try:
                proc.kill()
            except Exception:
                pass
            raise GitExecutionError(
                f"Git command timed out after {effective_timeout}s: {' '.join(args[:4])}"
            ) from err
        except FileNotFoundError as err:
            raise GitExecutionError("Git executable not found in PATH") from err

    async def resolve_commit_sha(self, repo_path: str | Path, ref: str) -> str:
        """Resolve a branch, tag, or ref to an exact 40-character commit SHA."""
        clean_ref = ref.strip()
        if not REF_RE.match(clean_ref) or clean_ref.startswith("-"):
            raise GitSecurityError(f"Invalid or unsafe ref name: {ref}")

        code, stdout, stderr = await self.run_git(
            ["rev-parse", f"{clean_ref}^{{commit}}"],
            cwd=repo_path,
        )
        if code != 0:
            # Fallback to direct rev-parse if not a direct commit
            code, stdout, stderr = await self.run_git(
                ["rev-parse", clean_ref],
                cwd=repo_path,
            )
            if code != 0:
                raise GitExecutionError(f"Failed to resolve ref '{ref}': {stderr.strip()}")

        sha = stdout.strip()
        if not SHA_RE.match(sha):
            raise GitExecutionError(
                f"Resolved ref '{ref}' did not yield a valid 40-char SHA: {sha}"
            )
        return sha

    async def get_commit_metadata(self, repo_path: str | Path, commit_sha: str) -> CommitMetadata:
        """Extract structured metadata for a specific commit without checking out code."""
        if not SHA_RE.match(commit_sha):
            raise GitSecurityError(f"Invalid commit SHA: {commit_sha}")

        # Extract commit hash, tree hash, parent hashes, author, committer, timestamp
        # Format: %H%x00%T%x00%P%x00%an%x00%ae%x00%cn%x00%ce%x00%cI%x00%s%x00%B
        fmt = "%H%x00%T%x00%P%x00%an%x00%ae%x00%cn%x00%ce%x00%cI%x00%s%x00%B"
        code, stdout, stderr = await self.run_git(
            ["log", "-1", f"--format={fmt}", commit_sha],
            cwd=repo_path,
        )
        if code != 0:
            raise GitExecutionError(f"Failed to get commit info for {commit_sha}: {stderr.strip()}")

        parts = stdout.split("\x00")
        if len(parts) < 10:
            raise GitExecutionError(f"Malformed commit format returned for {commit_sha}")

        sha = parts[0].strip()
        tree_sha = parts[1].strip()
        parents_raw = parts[2].strip()
        parent_shas = [p for p in parents_raw.split() if p] if parents_raw else []
        author_name = parts[3].strip()
        author_email = parts[4].strip()
        committer_name = parts[5].strip()
        committer_email = parts[6].strip()
        committed_at_str = parts[7].strip()
        summary = parts[8].strip()
        message = parts[9].strip() if len(parts) > 9 else summary

        try:
            committed_at = datetime.fromisoformat(committed_at_str)
        except Exception:
            committed_at = datetime.now(UTC)

        return CommitMetadata(
            commit_sha=sha,
            tree_sha=tree_sha,
            parent_shas=parent_shas,
            author_name=author_name,
            author_email=author_email,
            committer_name=committer_name,
            committer_email=committer_email,
            committed_at=committed_at,
            message=message,
            summary=summary,
        )

    async def create_snapshot_archive(
        self,
        repo_path: str | Path,
        commit_sha: str,
        output_tar_gz: str | Path,
    ) -> Path:
        """Create an immutable commit-specific tar.gz archive using git-archive.

        git archive operates directly on Git tree objects without checkout or hook execution.
        """
        if not SHA_RE.match(commit_sha):
            raise GitSecurityError(f"Invalid commit SHA: {commit_sha}")

        output_path = Path(output_tar_gz).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        code, _, stderr = await self.run_git(
            [
                "archive",
                "--format=tar.gz",
                f"--prefix={commit_sha}/",
                "-o",
                str(output_path),
                commit_sha,
            ],
            cwd=repo_path,
        )
        if code != 0 or not output_path.exists():
            raise GitExecutionError(
                f"Failed to create git archive for {commit_sha}: {stderr.strip()}"
            )

        return output_path

    async def list_tree_files(
        self,
        repo_path: str | Path,
        commit_sha: str,
    ) -> list[dict[str, Any]]:
        """List all files in the tree at commit_sha using git ls-tree without checkout."""
        if not SHA_RE.match(commit_sha):
            raise GitSecurityError(f"Invalid commit SHA: {commit_sha}")

        code, stdout, stderr = await self.run_git(
            ["ls-tree", "-r", "-l", commit_sha],
            cwd=repo_path,
        )
        if code != 0:
            raise GitExecutionError(f"Failed to list tree for {commit_sha}: {stderr.strip()}")

        files: list[dict[str, Any]] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # Format: <mode> <type> <object> <size>\t<file>
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            meta, path = parts
            meta_parts = meta.split()
            if len(meta_parts) >= 4:
                obj_mode = meta_parts[0]
                obj_type = meta_parts[1]
                obj_sha = meta_parts[2]
                try:
                    obj_size = int(meta_parts[3])
                except ValueError:
                    obj_size = 0
            else:
                obj_mode, obj_type, obj_sha, obj_size = "100644", "blob", "", 0

            files.append(
                {
                    "path": path,
                    "type": obj_type,
                    "mode": obj_mode,
                    "sha": obj_sha,
                    "size_bytes": obj_size,
                }
            )

        return files

    async def read_file_at_commit(
        self,
        repo_path: str | Path,
        commit_sha: str,
        file_path: str,
        max_bytes: int = 10 * 1024 * 1024,
    ) -> bytes:
        """Safely read blob content at commit_sha using git cat-file without checkout."""
        if not SHA_RE.match(commit_sha):
            raise GitSecurityError(f"Invalid commit SHA: {commit_sha}")

        # Sanitize file_path against path traversal or flag injection
        clean_path = file_path.replace("\\", "/").strip()
        if (
            clean_path.startswith("/")
            or clean_path.startswith("-")
            or ".." in clean_path.split("/")
        ):
            raise GitSecurityError(f"Unsafe path requested: {file_path}")

        code, stdout, stderr = await self.run_git(
            ["cat-file", "-s", f"{commit_sha}:{clean_path}"],
            cwd=repo_path,
        )
        if code != 0:
            raise GitExecutionError(f"File '{file_path}' not found at commit {commit_sha}")

        try:
            size = int(stdout.strip())
            if size > max_bytes:
                raise GitSecurityError(
                    f"File size {size} exceeds maximum safe limit of {max_bytes} bytes"
                )
        except ValueError:
            pass

        # Read binary blob
        cmd = ["git", *self._safe_git_args(), "cat-file", "-p", f"{commit_sha}:{clean_path}"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._safe_git_env(),
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=self.timeout_seconds,
        )
        if proc.returncode != 0:
            raise GitExecutionError(
                f"Failed to read file content: {stderr_bytes.decode('utf-8', errors='replace')}"
            )

        return stdout_bytes
