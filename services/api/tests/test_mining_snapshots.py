"""Comprehensive tests for immutable repository snapshots and safe git fetching (M3-01)."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient

from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
)
from atip_api.db.models.repository import Repository, RepositorySnapshot
from atip_api.modules.identity.session import create_session_token
from atip_api.modules.mining.git_fetcher import (
    GitSecurityError,
    SafeGitFetcher,
)
from atip_api.modules.mining.snapshot import (
    SafePathTraversalError,
    SafeSnapshotReader,
    SnapshotManager,
)


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository with initial commits, hooks, and test files."""
    temp_dir = tempfile.mkdtemp(prefix="atip_test_repo_")
    repo_path = Path(temp_dir)

    # Init repo with specific user
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test Committer"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "committer@atip.test"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # 1. Add normal files
    (repo_path / "README.md").write_text("# Test Repo\nHello world\n", encoding="utf-8")
    (repo_path / "main.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (repo_path / "index.ts").write_text("export const PI = 3.14159;\n", encoding="utf-8")

    pkg_dir = repo_path / "src" / "pkg"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "util.py").write_text("def greet():\n    return 'hello'\n", encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: initial commit with Python and TypeScript"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # 2. Plant a malicious Git hook that creates a flag file if executed
    hooks_dir = repo_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    flag_file = repo_path / "HOOK_EXECUTED.txt"

    post_checkout_hook = hooks_dir / ("post-checkout.bat" if os.name == "nt" else "post-checkout")
    if os.name == "nt":
        post_checkout_hook.write_text(f'echo EXECUTED > "{flag_file}"\n', encoding="utf-8")
    else:
        post_checkout_hook.write_text(
            f'#!/bin/sh\necho EXECUTED > "{flag_file}"\n', encoding="utf-8"
        )
        post_checkout_hook.chmod(0o755)

    pre_commit_hook = hooks_dir / ("pre-commit.bat" if os.name == "nt" else "pre-commit")
    if os.name == "nt":
        pre_commit_hook.write_text(f'echo EXECUTED > "{flag_file}"\n', encoding="utf-8")
    else:
        pre_commit_hook.write_text(f'#!/bin/sh\necho EXECUTED > "{flag_file}"\n', encoding="utf-8")
        pre_commit_hook.chmod(0o755)

    yield repo_path, flag_file


@pytest.mark.asyncio
async def test_safe_git_fetcher_never_executes_hooks(temp_git_repo):
    """Verify that SafeGitFetcher neutralizes and never triggers repository hooks."""
    repo_path, flag_file = temp_git_repo
    fetcher = SafeGitFetcher()

    # Resolve commit SHA
    commit_sha = await fetcher.resolve_commit_sha(repo_path, "main")
    assert len(commit_sha) == 40

    # Get metadata
    meta = await fetcher.get_commit_metadata(repo_path, commit_sha)
    assert meta.commit_sha == commit_sha
    assert meta.author_name == "Test Committer"
    assert "initial commit" in meta.summary
    assert meta.tree_sha

    # Create archive
    tar_out = repo_path / "archive.tar.gz"
    archive_path = await fetcher.create_snapshot_archive(repo_path, commit_sha, tar_out)
    assert archive_path.exists()
    assert archive_path.stat().st_size > 0

    # Read blob
    content = await fetcher.read_file_at_commit(repo_path, commit_sha, "main.py")
    assert b"def add(a, b):" in content

    # Crucial security assertion: hook flag file must NOT exist!
    assert not flag_file.exists(), "SECURITY VIOLATION: Malicious Git hook was executed!"


@pytest.mark.asyncio
async def test_safe_git_fetcher_rejects_unsafe_refs(temp_git_repo):
    """Verify that malicious ref names and path traversals are rejected."""
    repo_path, _ = temp_git_repo
    fetcher = SafeGitFetcher()

    # Reject flag injection
    with pytest.raises(GitSecurityError):
        await fetcher.resolve_commit_sha(repo_path, "--upload-pack=evil")

    # Reject space / shell metacharacters
    with pytest.raises(GitSecurityError):
        await fetcher.resolve_commit_sha(repo_path, "main; rm -rf /")

    # Reject reading file with path traversal
    commit_sha = await fetcher.resolve_commit_sha(repo_path, "main")
    with pytest.raises(GitSecurityError):
        await fetcher.read_file_at_commit(repo_path, commit_sha, "../../etc/passwd")

    with pytest.raises(GitSecurityError):
        await fetcher.read_file_at_commit(repo_path, commit_sha, "/etc/shadow")


@pytest.mark.asyncio
async def test_safe_snapshot_reader_path_traversal_defense(tmp_path):
    """Verify SafeSnapshotReader enforces strict sandboxing within snapshot root."""
    snapshot_dir = tmp_path / "snapshot"
    snapshot_dir.mkdir()
    (snapshot_dir / "safe.txt").write_text("safe content", encoding="utf-8")

    # Nested folder
    sub = snapshot_dir / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested content", encoding="utf-8")

    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("classified data", encoding="utf-8")

    reader = SafeSnapshotReader(snapshot_dir)

    # Valid reads
    assert reader.read_text("safe.txt") == "safe content"
    assert reader.read_text("sub/nested.txt") == "nested content"

    # Traversal attempts must raise SafePathTraversalError
    with pytest.raises(SafePathTraversalError):
        reader.read_text("../secret.txt")

    with pytest.raises(SafePathTraversalError):
        reader.read_text("../../secret.txt")

    with pytest.raises(SafePathTraversalError):
        reader.read_text("/etc/passwd")


@pytest.mark.asyncio
async def test_snapshot_manager_idempotency(db_session, temp_git_repo, tmp_path):
    """Verify SnapshotManager creates immutable snapshot and returns same record on repeat."""
    repo_path, _ = temp_git_repo

    # Set up organization and repository in DB
    org = Organization(name="Test Mining Org", slug="test-mining-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=98765432,
        name="test-mining-repo",
        full_name="test-org/test-mining-repo",
        default_branch="main",
        clone_url="https://github.com/test-org/test-mining-repo.git",
    )
    db_session.add(repo)
    await db_session.flush()

    manager = SnapshotManager(base_storage_dir=tmp_path / "storage")

    # 1. First snapshot creation
    snapshot1 = await manager.get_or_create_snapshot(
        session=db_session,
        org_id=org.id,
        repository=repo,
        ref_or_commit="main",
        local_repo_path=repo_path,
    )
    assert snapshot1.id.startswith("snap_")
    assert len(snapshot1.commit_sha) == 40
    assert snapshot1.tree_sha
    assert snapshot1.stats_json["total_files"] >= 3
    assert "Python" in snapshot1.stats_json["languages"]
    assert "TypeScript" in snapshot1.stats_json["languages"]
    assert Path(snapshot1.storage_path).exists()

    # 2. Second snapshot creation with same commit must return existing record
    snapshot2 = await manager.get_or_create_snapshot(
        session=db_session,
        org_id=org.id,
        repository=repo,
        ref_or_commit=snapshot1.commit_sha,
        local_repo_path=repo_path,
    )
    assert snapshot2.id == snapshot1.id
    assert snapshot2.commit_sha == snapshot1.commit_sha

    # 3. Verify safe extraction and reader
    reader = await manager.get_snapshot_reader(snapshot1)
    files = reader.list_files()
    file_paths = [f.path for f in files]
    assert "main.py" in file_paths
    assert "index.ts" in file_paths
    assert reader.read_text("main.py").startswith("def add(a, b):")


@pytest.mark.asyncio
async def test_snapshot_api_endpoints(client: AsyncClient, db_session):
    """Verify HTTP API endpoints for repository snapshots."""
    # 1. Create org and user
    org = Organization(name="Snap Org", slug="snap-org")
    db_session.add(org)
    await db_session.flush()

    user = User(email="miner@atip.test", name="Miner User", is_active=True)
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.MAINTAINER,
    )
    db_session.add(membership)

    repo = Repository(
        organization_id=org.id,
        github_repo_id=11223344,
        name="api-test-repo",
        full_name="snap-org/api-test-repo",
        default_branch="main",
        clone_url="https://github.com/snap-org/api-test-repo.git",
    )
    db_session.add(repo)
    await db_session.flush()

    # Seed an immutable snapshot
    snapshot = RepositorySnapshot(
        organization_id=org.id,
        repository_id=repo.id,
        commit_sha="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        tree_sha="tree11223344556677889900aabbccddeeff1122",
        parent_shas=["parent00112233445566778899aabbccddeeff"],
        branch_name="main",
        ref="refs/heads/main",
        summary="feat: core snapshot feature",
        author_name="Miner User",
        author_email="miner@atip.test",
        stats_json={"total_files": 12, "languages": {"Python": 8, "TypeScript": 4}},
    )
    db_session.add(snapshot)
    await db_session.commit()

    token, _ = create_session_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        org_ids=[org.id],
    )

    auth_headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org.id,
    }

    # GET list snapshots
    res = await client.get(f"/api/v1/repositories/{repo.id}/snapshots", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["commit_sha"] == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    assert data[0]["stats_json"]["total_files"] == 12

    # GET single snapshot by SHA
    res_single = await client.get(
        f"/api/v1/repositories/{repo.id}/snapshots/{snapshot.commit_sha}",
        headers=auth_headers,
    )
    assert res_single.status_code == 200
    assert res_single.json()["data"]["id"] == snapshot.id

    # Tenant isolation check: request with different org ID
    foreign_org = Organization(name="Foreign Org", slug="foreign-org")
    db_session.add(foreign_org)
    await db_session.commit()

    res_foreign = await client.get(
        f"/api/v1/repositories/{repo.id}/snapshots",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": foreign_org.id},
    )
    assert res_foreign.status_code == 403
