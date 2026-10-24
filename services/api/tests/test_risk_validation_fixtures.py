"""Validation on known fixture commits, measurement of limitations, and anti-fabrication assertions (M4-06)."""


from atip_api.modules.risk.engine import (
    DeterministicRiskEngine,
)
from atip_api.modules.risk.test_selector import ImpactedTestSelector


def test_fixture_commit_hotspot_vs_benign_discrimination():
    """
    Validate that a known high-risk defect hotspot commit is ranked strictly higher
    than a benign documentation or cosmetic formatting commit.
    """
    engine = DeterministicRiskEngine()

    # Fixture A: Critical defect hotspot
    # High cyclomatic complexity (32), low maintainability (38), modified in 12 commits including 4 bug fixes,
    # imported by 18 files, test coverage deficient (28%).
    hotspot_file = engine.evaluate_file(
        file_path="src/payments/processor.py",
        cyclomatic=32,
        maintainability_index=38.5,
        loc=650,
        churn_count=12,
        lines_changed=580,
        direct_dependents=8,
        transitive_dependents=18,
        coverage_pct=28.0,
        has_test_file=True,
        defect_commit_count=4,
    )

    # Fixture B: Benign utility change
    # Clean cyclomatic complexity (3), high maintainability (92), 1 past commit, 0 bug fixes,
    # 1 dependent, well covered (95%).
    benign_file = engine.evaluate_file(
        file_path="src/utils/string_format.py",
        cyclomatic=3,
        maintainability_index=92.0,
        loc=40,
        churn_count=1,
        lines_changed=8,
        direct_dependents=1,
        transitive_dependents=1,
        coverage_pct=95.0,
        has_test_file=True,
        defect_commit_count=0,
    )

    # Fixture C: New file with missing data (unparsed syntax / no git history)
    missing_data_file = engine.evaluate_file(
        file_path="src/experimental/new_feature.ts",
        cyclomatic=None,
        maintainability_index=None,
        loc=80,
        churn_count=None,
        lines_changed=None,
        direct_dependents=None,
        transitive_dependents=None,
        coverage_pct=None,
        has_test_file=False,
        defect_commit_count=None,
        total_repo_commits=1,
        graph_available=False,
        tests_discovered=False,
    )

    # Verification of risk discrimination
    assert hotspot_file.risk_score >= 85, f"Expected critical risk, got {hotspot_file.risk_score}"
    assert hotspot_file.risk_tier == "critical"
    assert hotspot_file.confidence >= 0.90
    assert not hotspot_file.has_missing_data

    assert benign_file.risk_score <= 25, f"Expected low risk, got {benign_file.risk_score}"
    assert benign_file.risk_tier == "low"
    assert benign_file.confidence >= 0.90
    assert not benign_file.has_missing_data

    # Discrimination margin must exceed 50 points
    risk_delta = hotspot_file.risk_score - benign_file.risk_score
    assert risk_delta >= 60, f"Expected robust discrimination delta >= 60, got {risk_delta}"

    # Missing data file verification: must not fabricate 0 or 100, must reduce confidence
    assert 25 <= missing_data_file.risk_score <= 65
    assert missing_data_file.has_missing_data
    assert missing_data_file.confidence <= 0.60
    assert len(missing_data_file.missing_reasons) >= 3


def test_validation_known_limitations_and_unsupported_states():
    """
    Validate that the engine explicitly documents known technical limitations
    rather than fabricating absolute predictive accuracy.
    """
    engine = DeterministicRiskEngine()

    # Evaluation with unparsed complexity
    file_unparsed = engine.evaluate_file(
        file_path="src/legacy/opaque_script.sh",
        cyclomatic=None,
        loc=150,
    )
    assert file_unparsed.has_missing_data
    assert any("AST parser did not produce cyclomatic metrics" in r for r in file_unparsed.missing_reasons)

    # Evaluation with shallow repository history
    file_shallow = engine.evaluate_file(
        file_path="src/init.py",
        churn_count=1,
        total_repo_commits=1,
    )
    assert file_shallow.has_missing_data
    assert any("fewer than 3 commits" in r for r in file_shallow.missing_reasons)


def test_test_gap_and_regression_coverage_limits():
    """Verify that test gaps are discovered when code changes lack regression tests."""
    selector = ImpactedTestSelector()

    edges = [
        {"source_file": "src/api/auth.py", "target_file": "src/core/crypto.py"},
    ]
    # No test file imports src/core/crypto.py or src/api/auth.py
    discovered_tests: list[dict] = []

    res = selector.select_tests(
        repository_id="repo_val",
        commit_sha="abc1234",
        changed_files=["src/core/crypto.py"],
        dependency_edges=edges,
        all_discovered_tests=discovered_tests,
        file_risks={"src/core/crypto.py": 90, "src/api/auth.py": 75},
    )

    assert res.selected_tests_count == 0
    assert res.test_gaps_count >= 2
    assert any(g.file_path == "src/core/crypto.py" and g.gap_type == "missing_test_suite" for g in res.test_gaps)
    assert any(g.file_path == "src/api/auth.py" and g.gap_type == "untested_blast_radius" for g in res.test_gaps)
