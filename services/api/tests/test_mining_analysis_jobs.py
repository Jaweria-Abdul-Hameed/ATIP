"""Comprehensive tests for analysis jobs, pipeline orchestrator, SSE progress, idempotency, and history (M3-05)."""

import subprocess
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.job import ExecutionJob, JobStatus, JobType
from atip_api.db.models.mining import AnalysisRun
from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
)
from atip_api.db.models.repository import Repository
from atip_api.modules.identity.session import create_session_token
from atip_api.modules.mining.orchestrator import AnalysisPipelineOrchestrator


@pytest.fixture
def repo_with_full_project():
    """Create a temporary git repository with commits, code, dependencies, and tests."""
    temp_dir = tempfile.mkdtemp(prefix="atip_orch_repo_")
    repo_path = Path(temp_dir)

    def _git(*args):
        subprocess.run(["git", *args], cwd=repo_path, check=True, capture_output=True)

    _git("init", "-b", "main")
    _git("config", "user.name", "Pipeline Tester")
    _git("config", "user.email", "pipeline@atip.test")

    # Initial commit
    (repo_path / "calc.py").write_text(
        "import math\n\ndef square(x):\n    if x >= 0:\n        return x * x\n    return 0\n",
        encoding="utf-8",
    )
    (repo_path / "test_calc.py").write_text(
        "import unittest\nfrom calc import square\n\nclass TestCalc(unittest.TestCase):\n    def test_square(self):\n        self.assertEqual(square(4), 16)\n",
        encoding="utf-8",
    )
    (repo_path / "widget.ts").write_text(
        "export function renderWidget(visible: boolean) {\n    if (visible) {\n        console.log('visible');\n    }\n}\n",
        encoding="utf-8",
    )
    _git("add", ".")
    _git("commit", "-m", "feat: initial commit with calc and widget")

    # Second commit
    (repo_path / "calc.py").write_text(
        "import math\n\ndef square(x):\n    if x >= 0:\n        return x * x\n    return 0\n\ndef cube(x):\n    return x * x * x\n",
        encoding="utf-8",
    )
    _git("add", ".")
    _git("commit", "-m", "feat: add cube function to calc")

    yield repo_path


@pytest.mark.asyncio
async def test_analysis_pipeline_orchestrator_direct(
    db_session: AsyncSession,
    repo_with_full_project: Path,
):
    """Verify AnalysisPipelineOrchestrator runs M3-01..M3-04 and updates job/analysis records."""
    repo_path = repo_with_full_project

    org = Organization(name="Orch Org", slug="orch-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=1234567,
        name="orch-repo",
        full_name="orch-org/orch-repo",
        default_branch="main",
        clone_url="https://github.com/orch-org/orch-repo.git",
    )
    db_session.add(repo)
    await db_session.flush()

    job = ExecutionJob(
        repository_id=repo.id,
        organization_id=org.id,
        job_type=JobType.REPO_MINING,
        status=JobStatus.QUEUED,
        progress_pct=0,
        current_step="Queued for test",
    )
    db_session.add(job)
    await db_session.flush()

    run = AnalysisRun(
        repository_id=repo.id,
        organization_id=org.id,
        commit_sha="HEAD",
        branch="main",
        job_id=job.id,
        status="queued",
    )
    db_session.add(run)
    await db_session.commit()

    orchestrator = AnalysisPipelineOrchestrator()
    completed_run = await orchestrator.run_pipeline(
        session=db_session,
        repository=repo,
        job=job,
        analysis_run=run,
        repo_path=str(repo_path),
        target_commit_or_ref="HEAD",
    )

    assert completed_run.status == "completed"
    assert completed_run.total_files >= 3
    assert completed_run.total_lines > 10
    assert completed_run.languages_json is not None
    assert "Python" in completed_run.languages_json
    assert "TypeScript" in completed_run.languages_json

    # Complexity & test inventory
    assert completed_run.complexity_summary is not None
    assert completed_run.complexity_summary["analyzed_files_count"] >= 3
    assert completed_run.test_inventory is not None
    assert len(completed_run.test_inventory) >= 1
    assert completed_run.test_inventory[0]["test_name"] == "test_square"

    # ExecutionJob status
    assert job.status == JobStatus.COMPLETED
    assert job.progress_pct == 100
    assert job.completed_at is not None


@pytest.mark.asyncio
async def test_analysis_api_trigger_and_idempotency(
    db_session: AsyncSession,
    client: AsyncClient,
    repo_with_full_project: Path,
):
    """Verify POST /analyses triggers execution synchronously with ?sync=true, and subsequent call is idempotent."""
    repo_path = repo_with_full_project

    org = Organization(name="Trigger Org", slug="trigger-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=2345678,
        name="trigger-repo",
        full_name="trigger-org/trigger-repo",
        default_branch="main",
        clone_url="https://github.com/trigger-org/trigger-repo.git",
    )
    db_session.add(repo)

    user = User(
        email="dev_trigger@atip.test",
        name="Trigger Dev",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.DEVELOPER,
    )
    db_session.add(membership)
    await db_session.commit()

    token, _ = create_session_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        org_ids=[org.id],
    )
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org.id}

    # 1. Trigger analysis synchronously
    trigger_payload = {
        "branch": "main",
        "repo_path": str(repo_path),
        "force_rerun": False,
    }
    res = await client.post(
        f"/api/v1/repositories/{repo.id}/analyses?sync=true",
        headers=headers,
        json=trigger_payload,
    )
    assert res.status_code == 202
    job_data = res.json()["data"]
    assert job_data["status"] == "completed"
    assert job_data["progress_pct"] == 100
    first_job_id = job_data["id"]

    # 2. Second trigger without force_rerun returns cached completed job/run (idempotency)
    res_cached = await client.post(
        f"/api/v1/repositories/{repo.id}/analyses?sync=true",
        headers=headers,
        json=trigger_payload,
    )
    assert res_cached.status_code == 202
    cached_data = res_cached.json()["data"]
    assert cached_data["status"] == "completed"
    assert cached_data["progress_pct"] == 100
    # Must match first job or analysis run ID
    assert cached_data["id"] in {first_job_id, job_data["id"]}

    # 3. Third trigger with force_rerun creates and runs a fresh analysis job
    res_forced = await client.post(
        f"/api/v1/repositories/{repo.id}/analyses?sync=true",
        headers=headers,
        json={"branch": "main", "repo_path": str(repo_path), "force_rerun": True},
    )
    assert res_forced.status_code == 202
    forced_data = res_forced.json()["data"]
    assert forced_data["status"] == "completed"
    assert forced_data["id"] != first_job_id


@pytest.mark.asyncio
async def test_analysis_query_and_history_endpoints(
    db_session: AsyncSession,
    client: AsyncClient,
    repo_with_full_project: Path,
):
    """Verify GET /analyses/{id} and GET /repositories/{id}/analyses historical list."""
    repo_path = repo_with_full_project

    org = Organization(name="Query Org", slug="query-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=3456789,
        name="query-repo",
        full_name="query-org/query-repo",
        default_branch="main",
        clone_url="https://github.com/query-org/query-repo.git",
    )
    db_session.add(repo)

    user = User(
        email="dev_query@atip.test",
        name="Query Dev",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.DEVELOPER,
    )
    db_session.add(membership)
    await db_session.commit()

    token, _ = create_session_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        org_ids=[org.id],
    )
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org.id}

    # Run one analysis
    trigger_res = await client.post(
        f"/api/v1/repositories/{repo.id}/analyses?sync=true",
        headers=headers,
        json={"branch": "main", "repo_path": str(repo_path)},
    )
    assert trigger_res.status_code == 202
    job_id = trigger_res.json()["data"]["id"]

    # 1. GET /analyses/{id}
    job_res = await client.get(f"/api/v1/analyses/{job_id}", headers=headers)
    assert job_res.status_code == 200
    j_data = job_res.json()["data"]
    assert j_data["id"] == job_id
    assert j_data["status"] == "completed"
    assert j_data["progress_pct"] == 100

    # 2. GET /analyses/invalid_id returns 404
    not_found = await client.get("/api/v1/analyses/job_nonexistent_999", headers=headers)
    assert not_found.status_code == 404

    # 3. GET /repositories/{id}/analyses lists historical runs
    history_res = await client.get(
        f"/api/v1/repositories/{repo.id}/analyses?page=1&page_size=10",
        headers=headers,
    )
    assert history_res.status_code == 200
    history_json = history_res.json()
    assert len(history_json["data"]) >= 1
    run_entry = history_json["data"][0]
    assert run_entry["repository_id"] == repo.id
    assert run_entry["status"] == "completed"
    assert run_entry["total_files"] >= 3
    assert history_json["pagination"]["total_items"] >= 1


@pytest.mark.asyncio
async def test_analysis_sse_event_stream(
    db_session: AsyncSession,
    client: AsyncClient,
    repo_with_full_project: Path,
):
    """Verify GET /analyses/{id}/events returns real SSE text/event-stream chunks."""
    org = Organization(name="SSE Org", slug="sse-org")
    db_session.add(org)
    await db_session.flush()

    job = ExecutionJob(
        repository_id="test_repo_sse",
        organization_id=org.id,
        job_type=JobType.REPO_MINING,
        status=JobStatus.COMPLETED,
        progress_pct=100,
        current_step="Analysis completed successfully",
    )
    db_session.add(job)
    await db_session.commit()

    sse_res = await client.get(f"/api/v1/analyses/{job.id}/events")
    assert sse_res.status_code == 200
    assert "text/event-stream" in sse_res.headers["content-type"]
    text = sse_res.text
    assert "event: analysis_progress" in text
    assert "progress_pct" in text
    assert "completed" in text
