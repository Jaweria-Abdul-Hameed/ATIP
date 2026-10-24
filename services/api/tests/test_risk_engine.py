"""Tests for deterministic risk model, change-impact propagation, and test selection (M4-01..M4-04)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
)
from atip_api.modules.identity.session import create_session_token
from atip_api.modules.risk.engine import (
    DeterministicRiskEngine,
    DeterministicRiskModelConfig,
)
from atip_api.modules.risk.impact import ChangeImpactAnalyzer
from atip_api.modules.risk.test_selector import ImpactedTestSelector


async def _create_test_env(
    db: AsyncSession,
    email: str,
    name: str,
    org_slug: str,
    role: MembershipRole = MembershipRole.ADMIN,
) -> tuple[User, Organization, str]:
    user = User(email=email, name=name, is_active=True)
    db.add(user)
    await db.flush()

    org = Organization(name=f"{name}'s Org", slug=org_slug, is_active=True)
    db.add(org)
    await db.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=role,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(user)
    await db.refresh(org)

    token, _ = create_session_token(
        user_id=user.id, email=user.email, name=user.name, org_ids=[org.id]
    )
    return user, org, token


def test_deterministic_risk_config_weights_sum_to_one():
    """Verify explainable weights strictly sum to 1.0."""
    config = DeterministicRiskModelConfig()
    total_weights = (
        config.weight_complexity
        + config.weight_churn
        + config.weight_blast_radius
        + config.weight_coverage_gap
        + config.weight_defect_history
    )
    assert pytest.approx(total_weights, rel=1e-5) == 1.0


def test_complexity_factor_evaluation_and_missing_data():
    """Test complexity scoring with both precise metrics and missing data fallbacks."""
    engine = DeterministicRiskEngine()

    # 1. Low complexity
    f_low = engine.evaluate_complexity_factor(cyclomatic=3, maintainability_index=85.0, loc=45)
    assert f_low.normalized_score == 10.0
    assert f_low.impact == "low"
    assert f_low.confidence == 0.95
    assert not f_low.is_missing

    # 2. High complexity with maintainability penalty
    f_high = engine.evaluate_complexity_factor(cyclomatic=25, maintainability_index=42.0, loc=520)
    assert f_high.normalized_score == 90.0  # 75 base + 15 penalty
    assert f_high.impact == "critical"
    assert not f_high.is_missing

    # 3. Missing complexity with LOC proxy
    f_missing_loc = engine.evaluate_complexity_factor(cyclomatic=None, maintainability_index=None, loc=100)
    assert f_missing_loc.is_missing
    assert f_missing_loc.confidence == 0.45
    assert "LOC" in f_missing_loc.description
    assert f_missing_loc.missing_reason is not None

    # 4. Completely missing complexity
    f_none = engine.evaluate_complexity_factor(cyclomatic=None, maintainability_index=None, loc=None)
    assert f_none.is_missing
    assert f_none.confidence == 0.30
    assert f_none.normalized_score == 30.0


def test_churn_factor_evaluation_and_shallow_history():
    """Test commit churn evaluation and shallow repository history handling."""
    engine = DeterministicRiskEngine()

    # Normal churn
    f_norm = engine.evaluate_churn_factor(churn_count=6, lines_changed=300, total_repo_commits=25)
    assert f_norm.normalized_score == 85.0  # 70 base + 15 line bonus
    assert f_norm.impact == "critical"
    assert not f_norm.is_missing

    # Shallow history (< 3 commits)
    f_shallow = engine.evaluate_churn_factor(churn_count=2, lines_changed=20, total_repo_commits=2)
    assert f_shallow.is_missing
    assert f_shallow.confidence == 0.55
    assert "Shallow" in f_shallow.description

    # Completely missing churn
    f_none = engine.evaluate_churn_factor(churn_count=None, lines_changed=None)
    assert f_none.is_missing
    assert f_none.confidence == 0.40


def test_blast_radius_and_coverage_gap_factors():
    """Test blast radius and test coverage gap evaluation."""
    engine = DeterministicRiskEngine()

    # Blast radius: isolated vs architectural core
    f_iso = engine.evaluate_blast_radius_factor(direct_dependents=0, transitive_dependents=0)
    assert f_iso.normalized_score == 10.0

    f_core = engine.evaluate_blast_radius_factor(direct_dependents=12, transitive_dependents=35)
    assert f_core.normalized_score == 95.0
    assert f_core.impact == "critical"

    # Missing graph
    f_graph_missing = engine.evaluate_blast_radius_factor(direct_dependents=None, transitive_dependents=None, graph_available=False)
    assert f_graph_missing.is_missing
    assert f_graph_missing.confidence == 0.45

    # Coverage gap: high coverage vs no test
    f_cov_good = engine.evaluate_coverage_gap_factor(coverage_pct=92.5, has_test_file=True)
    assert f_cov_good.normalized_score == 10.0
    assert f_cov_good.impact == "low"

    f_cov_gap = engine.evaluate_coverage_gap_factor(coverage_pct=None, has_test_file=False)
    assert f_cov_gap.normalized_score == 85.0
    assert f_cov_gap.impact == "critical"


def test_file_and_repository_risk_aggregation():
    """Test composite file risk calculation and repository hotspot aggregation."""
    engine = DeterministicRiskEngine()

    # Low risk file
    file_low = engine.evaluate_file(
        file_path="src/utils/helpers.ts",
        cyclomatic=2,
        maintainability_index=90.0,
        loc=30,
        churn_count=1,
        lines_changed=10,
        direct_dependents=1,
        transitive_dependents=1,
        coverage_pct=88.0,
        has_test_file=True,
        defect_commit_count=0,
    )
    assert file_low.risk_score < 35
    assert file_low.risk_tier == "low"
    assert not file_low.has_missing_data

    # High risk core file
    file_core = engine.evaluate_file(
        file_path="src/auth/session.ts",
        cyclomatic=28,
        maintainability_index=45.0,
        loc=420,
        churn_count=9,
        lines_changed=450,
        direct_dependents=15,
        transitive_dependents=32,
        coverage_pct=34.0,
        has_test_file=True,
        defect_commit_count=3,
    )
    assert file_core.risk_score >= 80
    assert file_core.risk_tier in ("high", "critical")

    # Repository aggregation
    summary = engine.evaluate_repository(
        assessment_id="rsk_test1",
        repository_id="repo_1",
        commit_sha="c1a2f3",
        branch="main",
        file_assessments=[file_low, file_core],
    )
    assert summary.overall_score > file_low.risk_score
    assert summary.summary_stats["files_analyzed"] == 2
    assert summary.model_version == "deterministic-v1.0.0"


def test_change_impact_analyzer_bounded_traversal_and_cycles():
    """Verify bounded BFS dependency propagation, decay attenuation, and circular import defense."""
    analyzer = ChangeImpactAnalyzer(max_depth=3, decay_factor=0.5)

    # Dependency graph:
    # A is imported by B (B -> imports -> A)
    # B is imported by C (C -> imports -> B)
    # C is imported by D (D -> imports -> C)
    # Circular edge: B is imported by A (A -> imports -> B)
    edges = [
        {"source_file": "B.ts", "target_file": "A.ts"},
        {"source_file": "C.ts", "target_file": "B.ts"},
        {"source_file": "D.ts", "target_file": "C.ts"},
        {"source_file": "A.ts", "target_file": "B.ts"},  # cycle
    ]

    impacted = analyzer.compute_impact(changed_files=["A.ts"], dependency_edges=edges)

    # Directly changed file A.ts must be depth 0 with 100.0 impact
    a_node = next(n for n in impacted if n.file_path == "A.ts")
    assert a_node.depth == 0
    assert a_node.impact_score == 100.0
    assert a_node.is_direct

    # B.ts directly imports A.ts -> depth 1, impact 100 * 0.5^1 = 50.0
    b_node = next(n for n in impacted if n.file_path == "B.ts")
    assert b_node.depth == 1
    assert b_node.impact_score == 50.0
    assert not b_node.is_direct

    # C.ts imports B.ts -> depth 2, impact 100 * 0.5^2 = 25.0
    c_node = next(n for n in impacted if n.file_path == "C.ts")
    assert c_node.depth == 2
    assert c_node.impact_score == 25.0

    # Max depth is 3: D.ts reached at depth 3
    d_node = next(n for n in impacted if n.file_path == "D.ts")
    assert d_node.depth == 3

    # Blast radius counts
    direct, transitive = analyzer.compute_blast_radius_counts("A.ts", edges)
    assert direct == 1  # B.ts imports A.ts
    assert transitive >= 3  # B, C, D


def test_impacted_regression_test_selector_and_gaps():
    """Verify regression test selection, test gap identification, and flakiness flagging."""
    selector = ImpactedTestSelector()

    edges = [
        {"source_file": "tests/test_auth.py", "target_file": "src/auth/session.py"},
        {"source_file": "tests/test_flaky.py", "target_file": "src/auth/session.py"},
        {"source_file": "src/api/router.py", "target_file": "src/auth/session.py"},
    ]

    all_tests = [
        {"file_path": "tests/test_auth.py", "test_name": "test_login"},
        {"file_path": "tests/test_flaky.py", "test_name": "test_async_sleep"},
        {"file_path": "tests/test_unrelated.py", "test_name": "test_other"},
    ]

    file_risks = {
        "src/auth/session.py": 85,
        "src/api/router.py": 72,
    }

    result = selector.select_tests(
        repository_id="repo_1",
        commit_sha="c1a2f3",
        changed_files=["src/auth/session.py"],
        dependency_edges=edges,
        all_discovered_tests=all_tests,
        file_risks=file_risks,
    )

    # 1. Selected tests: test_auth.py and test_flaky.py must be selected because they import auth/session.py
    sel_files = [t.test_file for t in result.selected_tests]
    assert "tests/test_auth.py" in sel_files
    assert "tests/test_flaky.py" in sel_files
    assert "tests/test_unrelated.py" not in sel_files

    # 2. Test gaps: src/api/router.py is impacted by auth/session.py but has no dedicated test file!
    gap_files = [g.file_path for g in result.test_gaps]
    assert "src/api/router.py" in gap_files

    # 3. Flakiness check: test_flaky.py with timing delay heuristic
    is_flaky, score, reasons = selector.detect_flakiness_signals(
        "tests/test_flaky.py", test_content_preview="async def test(): time.sleep(0.5)"
    )
    assert is_flaky
    assert score >= 0.35
    assert len(reasons) > 0


@pytest.mark.asyncio
async def test_risk_api_endpoints_and_tenant_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verify GET/POST risk endpoints, evidence breakdown, test selection, and tenant boundary enforcement."""
    user1, org1, token1 = await _create_test_env(
        db_session, "user1@atip.dev", "User One", "tenant-one", MembershipRole.ADMIN
    )
    headers = {"Authorization": f"Bearer {token1}"}

    # 1. Create Repository in Tenant 1 directly in db
    from atip_api.db.models.repository import Repository
    repo = Repository(
        organization_id=org1.id,
        github_repo_id=98765432,
        name="risk-repo",
        full_name="tenant-one/risk-repo",
        default_branch="main",
        clone_url="https://github.com/tenant-one/risk-repo.git",
        is_private=False,
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)
    repo_id = repo.id

    # 2. Query risks: should return explainable risk summary with honest missing data flags
    risk_resp = await client.get(
        f"/api/v1/repositories/{repo_id}/risks",
        headers={**headers, "X-Organization-ID": org1.id},
    )
    assert risk_resp.status_code == 200
    risk_data = risk_resp.json()["data"]
    assert risk_data["repository_id"] == repo_id
    assert risk_data["model_version"] == "deterministic-v1.0.0"
    assert "complexity" in risk_data["feature_weights"]
    assert "churn" in risk_data["feature_weights"]
    assert "blast_radius" in risk_data["feature_weights"]

    # 3. Trigger on-demand evaluation
    eval_resp = await client.post(
        f"/api/v1/repositories/{repo_id}/risks/evaluate",
        json={"branch": "main", "force_recompute": True},
        headers={**headers, "X-Organization-ID": org1.id},
    )
    assert eval_resp.status_code == 200
    assert eval_resp.json()["data"]["model_type"] == "deterministic"

    # 4. Impact propagation endpoint
    impact_resp = await client.get(
        f"/api/v1/repositories/{repo_id}/risks/impact",
        headers={**headers, "X-Organization-ID": org1.id},
    )
    assert impact_resp.status_code == 200
    assert isinstance(impact_resp.json()["data"], list)

    # 5. Impacted test selection endpoint
    sel_resp = await client.get(
        f"/api/v1/repositories/{repo_id}/risks/test-selection",
        headers={**headers, "X-Organization-ID": org1.id},
    )
    assert sel_resp.status_code == 200
    sel_data = sel_resp.json()["data"]
    assert "selected_tests" in sel_data
    assert "test_gaps" in sel_data

    # 6. Strict Tenant Isolation Check: Different user/org cannot access this repository's risk data
    user2, org2, token2 = await _create_test_env(
        db_session, "user2@atip.dev", "User Two", "tenant-two", MembershipRole.ADMIN
    )
    unauth_resp = await client.get(
        f"/api/v1/repositories/{repo_id}/risks",
        headers={"Authorization": f"Bearer {token2}", "X-Organization-ID": org2.id},
    )
    assert unauth_resp.status_code in (403, 404)
