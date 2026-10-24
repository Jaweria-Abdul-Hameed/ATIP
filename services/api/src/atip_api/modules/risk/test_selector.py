"""Impacted regression test selector, test gap detection, and flakiness analysis."""

from typing import Any

from pydantic import BaseModel, Field

from atip_api.modules.risk.impact import ChangeImpactAnalyzer
from atip_api.modules.risk.schemas import ChangeImpactNode


class SelectedRegressionTest(BaseModel):
    """Test case or test file selected to run based on change-impact propagation."""

    test_file: str
    test_identifier: str = Field(..., example="tests/test_auth.py::test_session_expiry")
    priority: str = Field(..., example="high")  # critical, high, medium, low
    selection_reason: str = Field(..., example="Directly imports modified module 'src/auth/session.py'")
    target_file: str = Field(..., example="src/auth/session.py")
    depth: int = Field(default=1)
    is_flaky_candidate: bool = Field(default=False)
    flakiness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    flakiness_reasons: list[str] = Field(default_factory=list)


class TestGap(BaseModel):
    """File modified or impacted that lacks test coverage or associated test files."""

    file_path: str
    risk_score: int
    severity: str
    gap_type: str = Field(..., example="missing_test_suite")  # missing_test_suite, missing_coverage, untested_blast_radius
    impacted_dependents_count: int = Field(default=0)
    recommendation: str = Field(
        ...,
        example="Create dedicated unit tests covering boundary conditions and error handlers.",
    )


class TestSelectionResult(BaseModel):
    """Aggregated output of regression test selection and gap identification."""

    repository_id: str
    commit_sha: str
    total_existing_tests_count: int = Field(default=0)
    selected_tests_count: int = Field(default=0)
    selected_tests: list[SelectedRegressionTest] = Field(default_factory=list)
    test_gaps_count: int = Field(default=0)
    test_gaps: list[TestGap] = Field(default_factory=list)
    flaky_tests_count: int = Field(default=0)
    flaky_tests: list[SelectedRegressionTest] = Field(default_factory=list)
    selection_ratio_pct: float = Field(default=0.0, ge=0.0, le=100.0)


class ImpactedTestSelector:
    """Selects minimum sufficient regression tests covering impacted code and identifies gaps."""

    def __init__(self, impact_analyzer: ChangeImpactAnalyzer | None = None):
        self.impact_analyzer = impact_analyzer or ChangeImpactAnalyzer()

    def find_associated_test_files(
        self,
        source_file: str,
        all_test_files: list[str],
    ) -> list[str]:
        """Finds test files matching the source file via conventional naming patterns."""
        associated: list[str] = []
        base_name = source_file.split("/")[-1].split("\\")[-1]
        name_no_ext = base_name.rsplit(".", 1)[0] if "." in base_name else base_name

        patterns = [
            f"test_{name_no_ext}",
            f"{name_no_ext}_test",
            f"{name_no_ext}.test",
            f"{name_no_ext}.spec",
        ]

        for t in all_test_files:
            t_base = t.split("/")[-1].split("\\")[-1]
            if any(p in t_base for p in patterns):
                associated.append(t)

        return associated

    def detect_flakiness_signals(
        self,
        test_file: str,
        test_content_preview: str | None = None,
        past_flaky_history: bool = False,
    ) -> tuple[bool, float, list[str]]:
        """Evaluates whether a test is prone to non-deterministic flakiness."""
        reasons: list[str] = []
        score = 0.0

        if past_flaky_history:
            score += 0.50
            reasons.append("Historical run records show intermittent passes/failures on same commit.")

        if test_content_preview:
            lower = test_content_preview.lower()
            if "sleep(" in lower or "settimeout" in lower or "time.sleep" in lower:
                score += 0.35
                reasons.append("Contains explicit timing delays (sleep/timeout) susceptible to host load.")
            if "asyncio.gather" in lower or "race(" in lower:
                score += 0.20
                reasons.append("Contains concurrent async orchestration susceptible to race conditions.")
            if "random" in lower or "uuid" in lower:
                score += 0.15
                reasons.append("Uses dynamic random/entropy generation without deterministic seed.")

        score = min(1.0, score)
        is_candidate = score >= 0.30
        return is_candidate, round(score, 2), reasons

    def select_tests(
        self,
        repository_id: str,
        commit_sha: str,
        changed_files: list[str],
        dependency_edges: list[dict[str, Any]],
        all_discovered_tests: list[dict[str, Any]],
        file_risks: dict[str, int] | None = None,
    ) -> TestSelectionResult:
        """
        Computes impact graph, selects regression tests for modified and impacted files,
        flags unmonitored test gaps, and highlights flakiness risks.
        """
        file_risks = file_risks or {}
        impacted_nodes: list[ChangeImpactNode] = self.impact_analyzer.compute_impact(
            changed_files, dependency_edges
        )

        all_test_paths = [t.get("file_path", "") for t in all_discovered_tests if t.get("file_path")]

        # Map tests that import or target changed/impacted files
        reverse_deps = self.impact_analyzer.build_reverse_dependency_map(dependency_edges)

        selected_tests: list[SelectedRegressionTest] = []
        selected_set: set[str] = set()
        covered_files: set[str] = set()

        for node in impacted_nodes:
            file_path = node.file_path
            # Check 1: direct naming association
            associated = self.find_associated_test_files(file_path, all_test_paths)
            for t_path in associated:
                if t_path not in selected_set:
                    selected_set.add(t_path)
                    covered_files.add(file_path)
                    prio = "critical" if node.is_direct else ("high" if node.depth == 1 else "medium")
                    selected_tests.append(
                        SelectedRegressionTest(
                            test_file=t_path,
                            test_identifier=f"{t_path}::suite",
                            priority=prio,
                            selection_reason=f"Dedicated test file associated with {file_path}",
                            target_file=file_path,
                            depth=node.depth,
                        )
                    )

            # Check 2: tests that import this file in the dependency graph
            importers = reverse_deps.get(file_path, [])
            for imp in importers:
                # Is importer a test file?
                if any(imp.endswith(ext) for ext in ["_test.py", "test_.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js"]) or "test" in imp:
                    if imp not in selected_set:
                        selected_set.add(imp)
                        covered_files.add(file_path)
                        prio = "critical" if node.is_direct else "high"
                        selected_tests.append(
                            SelectedRegressionTest(
                                test_file=imp,
                                test_identifier=f"{imp}::suite",
                                priority=prio,
                                selection_reason=f"Test imports changed module '{file_path}' (depth {node.depth})",
                                target_file=file_path,
                                depth=node.depth,
                            )
                        )

        # Annotate flakiness
        flaky_tests: list[SelectedRegressionTest] = []
        for test in selected_tests:
            is_flaky, flk_score, flk_reasons = self.detect_flakiness_signals(test.test_file)
            test.is_flaky_candidate = is_flaky
            test.flakiness_score = flk_score
            test.flakiness_reasons = flk_reasons
            if is_flaky:
                flaky_tests.append(test)

        # Identify Test Gaps
        test_gaps: list[TestGap] = []
        for node in impacted_nodes:
            file_path = node.file_path
            if file_path not in covered_files and not any(file_path.endswith(t) for t in ["_test.py", ".test.ts", ".spec.ts"]):
                r_score = file_risks.get(file_path, int(node.impact_score))
                severity = "critical" if r_score >= 85 else ("high" if r_score >= 65 else "medium")

                gap_type = "missing_test_suite" if node.is_direct else "untested_blast_radius"
                rec = (
                    f"Create dedicated unit and boundary tests for directly modified '{file_path}'."
                    if node.is_direct
                    else f"Ensure downstream regression coverage for '{file_path}' impacted transitively via {', '.join(node.imported_by[:2])}."
                )

                test_gaps.append(
                    TestGap(
                        file_path=file_path,
                        risk_score=r_score,
                        severity=severity,
                        gap_type=gap_type,
                        impacted_dependents_count=len(reverse_deps.get(file_path, [])),
                        recommendation=rec,
                    )
                )

        # Sort gaps by risk descending
        test_gaps.sort(key=lambda g: g.risk_score, reverse=True)

        total_discovered = len(all_discovered_tests)
        sel_count = len(selected_tests)
        ratio = round((sel_count / max(1, total_discovered)) * 100.0, 1) if total_discovered else 100.0

        return TestSelectionResult(
            repository_id=repository_id,
            commit_sha=commit_sha,
            total_existing_tests_count=total_discovered,
            selected_tests_count=sel_count,
            selected_tests=selected_tests,
            test_gaps_count=len(test_gaps),
            test_gaps=test_gaps,
            flaky_tests_count=len(flaky_tests),
            flaky_tests=flaky_tests,
            selection_ratio_pct=ratio,
        )
