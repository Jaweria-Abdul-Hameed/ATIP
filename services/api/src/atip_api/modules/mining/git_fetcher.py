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

    async def clone_or_fetch_remote(
        self,
        clone_url: str,
        target_dir: str | Path,
        token: str | None = None,
        branch: str | None = None,
    ) -> Path:
        """Safely clone or fetch a remote repository into target directory with token authentication."""
        target = Path(target_dir).resolve()
        auth_url = clone_url
        if token and "github.com" in clone_url:
            clean = clone_url.removeprefix("https://").removeprefix("http://")
            if "@" in clean:
                clean = clean.split("@", 1)[1]
            auth_url = f"https://x-access-token:{token}@{clean}"

        if not (target / ".git").exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            args = ["clone", "--depth", "50"]
            if branch:
                args.extend(["--branch", branch])
            args.extend([auth_url, str(target)])
            code, stdout, stderr = await self.run_git(args, timeout=120)
            if code != 0:
                raise GitExecutionError(f"Failed to clone repository: {stderr.strip()}")
        else:
            code, stdout, stderr = await self.run_git(
                ["fetch", "--depth", "50", "origin"], cwd=target, timeout=60
            )
            if code != 0:
                logger.warning("Fetch failed on existing clone: %s", stderr)
        return target


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

    async def list_commits(
        self,
        repo_path: str | Path,
        max_count: int = 100,
        branch: str = "HEAD",
    ) -> list[CommitMetadata]:
        """List historical commits from branch/ref without checking out files."""
        clean_branch = branch.strip()
        if not REF_RE.match(clean_branch) or clean_branch.startswith("-"):
            raise GitSecurityError(f"Invalid branch/ref: {branch}")

        fmt = "%H%x00%T%x00%P%x00%an%x00%ae%x00%cn%x00%ce%x00%cI%x00%s%x00%B%x01"
        code, stdout, stderr = await self.run_git(
            ["log", f"-n{max_count}", f"--format={fmt}", clean_branch],
            cwd=repo_path,
        )
        if code != 0:
            raise GitExecutionError(f"Failed to list commits for {branch}: {stderr.strip()}")

        commits: list[CommitMetadata] = []
        raw_commits = stdout.split("\x01")
        for raw in raw_commits:
            raw = raw.strip()
            if not raw:
                continue
            parts = raw.split("\x00")
            if len(parts) < 10:
                continue
            sha = parts[0].strip()
            if not SHA_RE.match(sha):
                continue
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

            commits.append(
                CommitMetadata(
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
            )

        return commits

    async def get_commit_file_changes(
        self,
        repo_path: str | Path,
        commit_sha: str,
        include_patch: bool = False,
        max_patch_bytes: int = 50000,
    ) -> list[dict[str, Any]]:
        """Extract file changes (added/modified/deleted/renamed, insertions, deletions) for commit."""
        if not SHA_RE.match(commit_sha):
            raise GitSecurityError(f"Invalid commit SHA: {commit_sha}")

        # 1. Get name-status to distinguish Added, Modified, Deleted, Renamed
        code, status_out, stderr = await self.run_git(
            ["diff-tree", "--no-commit-id", "-r", "--name-status", "--root", "-M", commit_sha],
            cwd=repo_path,
        )
        if code != 0:
            raise GitExecutionError(f"Failed to get name-status for {commit_sha}: {stderr.strip()}")

        status_map: dict[str, tuple[str, str | None]] = {}
        for line in status_out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            code_letter = parts[0][0] if parts[0] else "M"
            if code_letter == "A":
                status_map[parts[1]] = ("added", None)
            elif code_letter == "D":
                status_map[parts[1]] = ("deleted", None)
            elif code_letter == "R":
                old_path = parts[1]
                new_path = parts[2] if len(parts) > 2 else parts[1]
                status_map[new_path] = ("renamed", old_path)
            else:
                status_map[parts[1]] = ("modified", None)

        # 2. Get numstat for insertions and deletions
        code, numstat_out, stderr = await self.run_git(
            ["diff-tree", "--no-commit-id", "-r", "--numstat", "--root", "-M", commit_sha],
            cwd=repo_path,
        )
        if code != 0:
            raise GitExecutionError(f"Failed to get numstat for {commit_sha}: {stderr.strip()}")

        changes: list[dict[str, Any]] = []
        for line in numstat_out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            ins_str, del_str, file_col = parts[0], parts[1], parts[2]
            try:
                insertions = int(ins_str) if ins_str != "-" else 0
                deletions = int(del_str) if del_str != "-" else 0
            except ValueError:
                insertions, deletions = 0, 0

            file_path = file_col
            old_path = None
            change_type = "modified"

            if file_col in status_map:
                change_type, old_path = status_map[file_col]
                file_path = file_col
            elif " => " in file_col:
                # Git rename notation: '{old => new}' or 'old => new' or 'path/{old => new}'
                for mapped_path, (ct, prev) in status_map.items():
                    if ct == "renamed" and (
                        file_col.endswith(mapped_path) or mapped_path in file_col
                    ):
                        change_type = ct
                        old_path = prev
                        file_path = mapped_path
                        break
            else:
                for mapped_path, (ct, prev) in status_map.items():
                    if mapped_path == file_path or file_path.endswith("/" + mapped_path):
                        change_type = ct
                        old_path = prev
                        file_path = mapped_path
                        break

            is_test = is_test_file(file_path)
            lang = detect_language(file_path)

            changes.append(
                {
                    "file_path": file_path,
                    "previous_path": old_path,
                    "change_type": change_type,
                    "insertions": insertions,
                    "deletions": deletions,
                    "is_test": is_test,
                    "language": lang,
                    "patch": None,
                }
            )

        # 3. Optional patch extraction
        if include_patch and changes:
            code, patch_out, _ = await self.run_git(
                ["diff-tree", "--no-commit-id", "-r", "-p", "--root", "-M", commit_sha],
                cwd=repo_path,
            )
            if code == 0 and patch_out:
                if len(patch_out.encode("utf-8")) > max_patch_bytes:
                    patch_out = patch_out[:max_patch_bytes] + "\n... [diff truncated]"
                changes[0]["patch"] = patch_out

        return changes


def is_test_file(path: str) -> bool:
    """Classify whether a file path corresponds to a test file."""
    norm = path.replace("\\", "/").lower()
    filename = norm.split("/")[-1]
    parts = norm.split("/")
    if any(p in {"tests", "test", "__tests__", "spec", "specs"} for p in parts[:-1]):
        return True
    if filename.startswith("test_") or filename.endswith("_test.py") or filename == "conftest.py":
        return True
    return any(
        filename.endswith(ext)
        for ext in [
            ".test.ts",
            ".spec.ts",
            ".test.tsx",
            ".spec.tsx",
            ".test.js",
            ".spec.js",
            ".test.jsx",
            ".spec.jsx",
        ]
    )


def detect_language(path: str) -> str | None:
    """Detect programming or markup language from file path."""
    ext = Path(path).suffix.lower()
    mapping = {
        ".py": "Python",
        ".pyw": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".mjs": "JavaScript",
        ".cjs": "JavaScript",
        ".json": "JSON",
        ".md": "Markdown",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "CSS",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bash": "Shell",
    }
    return mapping.get(ext)
