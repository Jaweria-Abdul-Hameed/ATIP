"""Comprehensive tests for commit history, diffs, ownership, and churn hotspot mining (M3-02)."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.mining import FileChangeRecord
from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
)
from atip_api.db.models.repository import Repository
from atip_api.modules.identity.session import create_session_token
from atip_api.modules.mining.git_fetcher import is_test_file
from atip_api.modules.mining.history_miner import HistoryMiner


@pytest.fixture
def multi_commit_git_repo():
    """Create a temporary git repository with 4 distinct commits across multiple authors."""
    temp_dir = tempfile.mkdtemp(prefix="atip_history_repo_")
    repo_path = Path(temp_dir)

    def _git(*args, author=None, email=None):
        env = dict(os.environ)
        if author:
            env["GIT_AUTHOR_NAME"] = author
            env["GIT_COMMITTER_NAME"] = author
        if email:
            env["GIT_AUTHOR_EMAIL"] = email
            env["GIT_COMMITTER_EMAIL"] = email
        subprocess.run(["git", *args], cwd=repo_path, check=True, capture_output=True, env=env)

    _git("init", "-b", "main")
    _git("config", "user.name", "Initial Author")
    _git("config", "user.email", "author1@atip.test")

    # Commit 1 by Author 1
    (repo_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (repo_path / "test_main.py").write_text("def test_hello(): assert True", encoding="utf-8")
    (repo_path / "README.md").write_text("# Documentation", encoding="utf-8")
    _git("add", ".")
    _git("commit", "-m", "feat: initial commit", author="Alice Developer", email="alice@atip.test")

    # Commit 2 by Author 2: add utils, modify main
    (repo_path / "main.py").write_text("import utils\nprint(utils.greet())", encoding="utf-8")
    (repo_path / "utils.py").write_text("def greet(): return 'hi'", encoding="utf-8")
    _git("add", ".")
    _git("commit", "-m", "feat: add utils module", author="Bob Architect", email="bob@atip.test")

    # Commit 3 by Author 1: rename utils to helpers, modify main again
    (repo_path / "main.py").write_text("import helpers\nprint(helpers.greet())", encoding="utf-8")
    _git("mv", "utils.py", "helpers.py")
    _git("add", ".")
    _git(
        "commit",
        "-m",
        "refactor: rename utils to helpers",
        author="Alice Developer",
        email="alice@atip.test",
    )

    # Commit 4 by Author 2: delete README
    _git("rm", "README.md")
    _git("commit", "-m", "chore: delete readme", author="Bob Architect", email="bob@atip.test")

    yield repo_path


def test_is_test_file_classification():
    """Verify test file heuristic classification for Python and JS/TS."""
    assert is_test_file("tests/test_api.py") is True
    assert is_test_file("test_something.py") is True
    assert is_test_file("services/api/conftest.py") is True
    assert is_test_file("src/__tests__/app.test.tsx") is True
    assert is_test_file("components/button.spec.ts") is True
    assert is_test_file("main.py") is False
    assert is_test_file("src/lib/api-client.ts") is False
    assert is_test_file("README.md") is False


@pytest.mark.asyncio
async def test_history_miner_commits_and_diffs(db_session: AsyncSession, multi_commit_git_repo):
    """Verify mining commit history, file changes, renames, and diffs."""
    repo_path = multi_commit_git_repo

    org = Organization(name="Mining Org", slug="mining-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=55667788,
        name="multi-commit-repo",
        full_name="mining-org/multi-commit-repo",
        default_branch="main",
        clone_url="https://github.com/mining-org/multi-commit-repo.git",
    )
    db_session.add(repo)
    await db_session.flush()

    miner = HistoryMiner()
    mined_commits = await miner.mine_repository_history(
        session=db_session,
        org_id=org.id,
        repository=repo,
        branch="main",
        max_commits=10,
        local_repo_path=repo_path,
        include_patch=True,
    )

    # 4 commits should be mined
    assert len(mined_commits) == 4
    authors = {c.author_name for c in mined_commits}
    assert "Alice Developer" in authors
    assert "Bob Architect" in authors

    # Inspect file changes for each commit
    head_commit = mined_commits[0]
    head_fcs = (
        (
            await db_session.execute(
                select(FileChangeRecord).where(FileChangeRecord.commit_id == head_commit.id)
            )
        )
        .scalars()
        .all()
    )
    # Commit 4 deleted README.md
    assert any(fc.file_path == "README.md" and fc.change_type == "deleted" for fc in head_fcs)

    # Commit 3 renamed utils.py to helpers.py
    rename_commit = mined_commits[1]
    rename_fcs = (
        (
            await db_session.execute(
                select(FileChangeRecord).where(FileChangeRecord.commit_id == rename_commit.id)
            )
        )
        .scalars()
        .all()
    )
    helpers_fc = next((fc for fc in rename_fcs if fc.file_path == "helpers.py"), None)
    assert helpers_fc is not None
    assert helpers_fc.change_type == "renamed"
    assert helpers_fc.previous_path == "utils.py"

    # Commit 1 had test file
    init_commit = mined_commits[3]
    init_fcs = (
        (
            await db_session.execute(
                select(FileChangeRecord).where(FileChangeRecord.commit_id == init_commit.id)
            )
        )
        .scalars()
        .all()
    )
    test_fc = next((fc for fc in init_fcs if fc.file_path == "test_main.py"), None)
    assert test_fc is not None
    assert test_fc.is_test is True
    assert test_fc.language == "Python"


@pytest.mark.asyncio
async def test_compute_hotspots_and_ownership(db_session: AsyncSession, multi_commit_git_repo):
    """Verify hotspot churn calculation and multi-author ownership attribution."""
    repo_path = multi_commit_git_repo

    org = Organization(name="Hotspot Org", slug="hotspot-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=99001122,
        name="hotspot-repo",
        full_name="hotspot-org/hotspot-repo",
        default_branch="main",
        clone_url="https://github.com/hotspot-org/hotspot-repo.git",
    )
    db_session.add(repo)
    await db_session.flush()

    miner = HistoryMiner()
    await miner.mine_repository_history(
        session=db_session,
        org_id=org.id,
        repository=repo,
        branch="main",
        local_repo_path=repo_path,
    )

    hotspots = await miner.compute_hotspots_and_ownership(
        session=db_session,
        org_id=org.id,
        repository_id=repo.id,
    )

    assert len(hotspots) > 0
    # main.py should be the top hotspot since it was touched in Commits 1, 2, and 3
    top_file = hotspots[0]
    assert top_file["file_path"] == "main.py"
    assert top_file["change_count"] == 3
    assert top_file["distinct_authors_count"] == 2  # Alice and Bob
    assert "Alice Developer" in top_file["authors"]
    assert "Bob Architect" in top_file["authors"]
    assert top_file["hotspot_score"] > 0


@pytest.mark.asyncio
async def test_mining_history_api_endpoints(
    client: AsyncClient, db_session: AsyncSession, multi_commit_git_repo
):
    """Verify REST API endpoints for repository commits, diffs, and hotspots."""
    repo_path = multi_commit_git_repo

    org = Organization(name="API Mining Org", slug="api-mining-org")
    db_session.add(org)
    await db_session.flush()

    user = User(email="miner2@atip.test", name="Miner Two", is_active=True)
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.DEVELOPER,
    )
    db_session.add(membership)

    repo = Repository(
        organization_id=org.id,
        github_repo_id=77889900,
        name="api-mining-repo",
        full_name="api-mining-org/api-mining-repo",
        default_branch="main",
        clone_url="https://github.com/api-mining-org/api-mining-repo.git",
    )
    db_session.add(repo)
    await db_session.flush()

    # Pre-mine using local repo
    miner = HistoryMiner()
    await miner.mine_repository_history(
        session=db_session,
        org_id=org.id,
        repository=repo,
        branch="main",
        local_repo_path=repo_path,
        include_patch=True,
    )

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

    # 1. GET commits list
    res_commits = await client.get(f"/api/v1/repositories/{repo.id}/commits", headers=auth_headers)
    assert res_commits.status_code == 200
    data_commits = res_commits.json()["data"]
    assert len(data_commits) == 4
    first_commit_sha = data_commits[0]["commit_sha"]

    # 2. GET commit detail
    res_detail = await client.get(
        f"/api/v1/repositories/{repo.id}/commits/{first_commit_sha}",
        headers=auth_headers,
    )
    assert res_detail.status_code == 200
    commit_detail = res_detail.json()["data"]
    assert commit_detail["commit"]["commit_sha"] == first_commit_sha
    assert len(commit_detail["file_changes"]) > 0

    # 3. GET hotspots ranking
    res_hotspots = await client.get(
        f"/api/v1/repositories/{repo.id}/hotspots", headers=auth_headers
    )
    assert res_hotspots.status_code == 200
    hotspots_data = res_hotspots.json()["data"]
    assert len(hotspots_data) >= 3
    assert hotspots_data[0]["file_path"] == "main.py"
    assert hotspots_data[0]["distinct_authors_count"] == 2

    # 4. Cross-tenant isolation
    other_org = Organization(name="Other Org", slug="other-org")
    db_session.add(other_org)
    await db_session.commit()

    res_forbidden = await client.get(
        f"/api/v1/repositories/{repo.id}/commits",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": other_org.id},
    )
    assert res_forbidden.status_code == 403
