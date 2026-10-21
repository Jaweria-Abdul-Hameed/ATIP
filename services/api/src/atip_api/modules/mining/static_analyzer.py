"""Static analysis, code complexity, test discovery, and coverage report ingestion."""

import ast
import json
import logging
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# JS/TS decision point regexes for Cyclomatic Complexity
JS_DECISION_RE = re.compile(
    r"""(?:\bif\b|\belse\s+if\b|\bfor\b|\bwhile\b|\bcase\b|\bcatch\b|&&|\|\||\?\?|\?[^:]*:)"""
)
JS_FUNCTION_RE = re.compile(
    r"""(?:function\s+([a-zA-Z0-9_$]+)|(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(?:async\s+)?(?!(?:if|for|while|switch|catch)\b)([a-zA-Z0-9_$]+)\s*\([^)]*\)\s*\{)"""
)

# Test discovery regexes for JS/TS
JS_TEST_RE = re.compile(r"""(?:it|test)\s*\(\s*['"`]([^'"`]+)['"`]""")
JS_SUITE_RE = re.compile(r"""describe\s*\(\s*['"`]([^'"`]+)['"`]""")


@dataclass
class FunctionComplexity:
    name: str
    line_start: int
    line_end: int
    complexity: int
    arg_count: int


@dataclass
class FileComplexityMetrics:
    file_path: str
    language: str
    lines_total: int
    lines_code: int
    lines_comments: int
    lines_blank: int
    cyclomatic_complexity: int
    average_function_complexity: float
    max_function_complexity: int
    maintainability_index: float
    functions: list[FunctionComplexity] = field(default_factory=list)


@dataclass
class DiscoveredTestCase:
    file_path: str
    suite_name: str
    test_name: str
    line_number: int
    framework: str
    language: str


@dataclass
class FileCoverageDetail:
    file_path: str
    statements_total: int
    statements_covered: int
    coverage_pct: float
    covered_lines: list[int] = field(default_factory=list)
    uncovered_lines: list[int] = field(default_factory=list)


@dataclass
class CoverageReport:
    format_type: str
    statements_total: int
    statements_covered: int
    statement_coverage_pct: float
    branches_total: int
    branches_covered: int
    branch_coverage_pct: float
    files: dict[str, FileCoverageDetail] = field(default_factory=dict)


class CodeComplexityAnalyzer:
    """Computes LOC, cyclomatic complexity, function inventory, and maintainability."""

    @staticmethod
    def analyze_source(
        source_text: str, file_path: str, language: str | None = None
    ) -> FileComplexityMetrics:
        lines = source_text.splitlines()
        lines_total = len(lines)
        lines_blank = sum(1 for line in lines if not line.strip())

        in_multiline_py = False
        in_multiline_c = False
        lines_comments = 0
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if in_multiline_py:
                lines_comments += 1
                if '"""' in s or "'''" in s:
                    in_multiline_py = False
                continue
            if in_multiline_c:
                lines_comments += 1
                if "*/" in s:
                    in_multiline_c = False
                continue
            if s.startswith(('"""', "'''")):
                lines_comments += 1
                if not (s.endswith(('"""', "'''")) and len(s) > 3):
                    in_multiline_py = True
                continue
            if s.startswith("/*"):
                lines_comments += 1
                if "*/" not in s:
                    in_multiline_c = True
                continue
            if s.startswith(("#", "//", "*")):
                lines_comments += 1

        lines_code = max(0, lines_total - lines_blank - lines_comments)

        detected_lang = language or (
            "Python" if file_path.endswith((".py", ".pyw")) else "TypeScript"
        )

        if detected_lang == "Python":
            complexity, functions = CodeComplexityAnalyzer._analyze_python(source_text, file_path)
        else:
            complexity, functions = CodeComplexityAnalyzer._analyze_jsts(source_text, lines)

        max_func_complexity = max((f.complexity for f in functions), default=1)
        avg_func_complexity = (
            round(sum(f.complexity for f in functions) / len(functions), 1)
            if functions
            else float(complexity)
        )

        # Maintainability Index: 171 - 5.2 * ln(Halstead/LOC) - 0.23 * Complexity - 16.2 * ln(LOC)
        # Scaled between 0 and 100
        loc_term = math.log(max(1, lines_code))
        raw_mi = 171.0 - 0.23 * complexity - 16.2 * loc_term
        maintainability_index = max(0.0, min(100.0, round((raw_mi * 100.0) / 171.0, 1)))

        return FileComplexityMetrics(
            file_path=file_path,
            language=detected_lang,
            lines_total=lines_total,
            lines_code=lines_code,
            lines_comments=lines_comments,
            lines_blank=lines_blank,
            cyclomatic_complexity=complexity,
            average_function_complexity=avg_func_complexity,
            max_function_complexity=max_func_complexity,
            maintainability_index=maintainability_index,
            functions=functions,
        )

    @staticmethod
    def _analyze_python(source_text: str, file_path: str) -> tuple[int, list[FunctionComplexity]]:
        file_complexity = 1
        functions: list[FunctionComplexity] = []

        try:
            tree = ast.parse(source_text, filename=file_path)
            for node in ast.walk(tree):
                # Count branch decision points for file
                if isinstance(
                    node,
                    (
                        ast.If,
                        ast.While,
                        ast.For,
                        ast.AsyncFor,
                        ast.ExceptHandler,
                        ast.With,
                        ast.AsyncWith,
                        ast.Assert,
                    ),
                ):
                    file_complexity += 1
                elif isinstance(node, ast.BoolOp):
                    # Each extra condition in an and/or adds 1
                    file_complexity += len(node.values) - 1

                # Function level complexity
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn_complexity = 1
                    for child in ast.walk(node):
                        if isinstance(
                            child,
                            (
                                ast.If,
                                ast.While,
                                ast.For,
                                ast.AsyncFor,
                                ast.ExceptHandler,
                                ast.Assert,
                            ),
                        ):
                            fn_complexity += 1
                        elif isinstance(child, ast.BoolOp):
                            fn_complexity += len(child.values) - 1

                    line_end = getattr(node, "end_lineno", node.lineno)
                    arg_count = len(node.args.args)
                    functions.append(
                        FunctionComplexity(
                            name=node.name,
                            line_start=node.lineno,
                            line_end=line_end,
                            complexity=fn_complexity,
                            arg_count=arg_count,
                        )
                    )
        except Exception:
            # Fallback regex counting for syntax errors
            file_complexity = max(
                1, len(re.findall(r"\b(if|elif|while|for|except|assert|and|or)\b", source_text))
            )

        return file_complexity, functions

    @staticmethod
    def _analyze_jsts(source_text: str, lines: list[str]) -> tuple[int, list[FunctionComplexity]]:
        matches = JS_DECISION_RE.findall(source_text)
        file_complexity = 1 + len(matches)

        functions: list[FunctionComplexity] = []
        for line_idx, line in enumerate(lines, 1):
            fn_match = JS_FUNCTION_RE.search(line)
            if fn_match:
                name = next((g for g in fn_match.groups() if g), "anonymous")
                functions.append(
                    FunctionComplexity(
                        name=name,
                        line_start=line_idx,
                        line_end=line_idx + 10,  # approximate
                        complexity=1,
                        arg_count=1,
                    )
                )

        return file_complexity, functions


class TestDiscoverer:
    """Discovers test suites, test cases, and framework types across Python and JS/TS."""

    @staticmethod
    def discover_in_file(source_text: str, file_path: str) -> list[DiscoveredTestCase]:
        tests: list[DiscoveredTestCase] = []
        ext = Path(file_path).suffix.lower()

        if ext in {".py", ".pyw"}:
            tests.extend(TestDiscoverer._discover_python(source_text, file_path))
        elif ext in {".ts", ".tsx", ".js", ".jsx"}:
            tests.extend(TestDiscoverer._discover_jsts(source_text, file_path))

        return tests

    @staticmethod
    def _discover_python(source_text: str, file_path: str) -> list[DiscoveredTestCase]:
        tests: list[DiscoveredTestCase] = []
        try:
            tree = ast.parse(source_text, filename=file_path)
            visited_functions: set[ast.AST] = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and (
                    node.name.startswith("Test") or node.name.endswith("Test")
                ):
                    suite_name = node.name
                    for item in node.body:
                        if isinstance(
                            item, (ast.FunctionDef, ast.AsyncFunctionDef)
                        ) and item.name.startswith("test_"):
                            visited_functions.add(item)
                            tests.append(
                                DiscoveredTestCase(
                                    file_path=file_path,
                                    suite_name=suite_name,
                                    test_name=item.name,
                                    line_number=item.lineno,
                                    framework="pytest/unittest",
                                    language="Python",
                                )
                            )

            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name.startswith("test_")
                    and node not in visited_functions
                ):
                    # Standalone test function
                    tests.append(
                        DiscoveredTestCase(
                            file_path=file_path,
                            suite_name=Path(file_path).stem,
                            test_name=node.name,
                            line_number=node.lineno,
                            framework="pytest",
                            language="Python",
                        )
                    )
        except Exception:
            # Fallback regex discovery
            for match in re.finditer(r"def\s+(test_[a-zA-Z0-9_]+)\s*\(", source_text):
                test_name = match.group(1)
                line = source_text[: match.start()].count("\n") + 1
                tests.append(
                    DiscoveredTestCase(
                        file_path=file_path,
                        suite_name=Path(file_path).stem,
                        test_name=test_name,
                        line_number=line,
                        framework="pytest",
                        language="Python",
                    )
                )

        return tests

    @staticmethod
    def _discover_jsts(source_text: str, file_path: str) -> list[DiscoveredTestCase]:
        tests: list[DiscoveredTestCase] = []
        current_suite = Path(file_path).stem

        lines = source_text.splitlines()
        for line_num, line in enumerate(lines, 1):
            suite_match = JS_SUITE_RE.search(line)
            if suite_match:
                current_suite = suite_match.group(1)

            test_match = JS_TEST_RE.search(line)
            if test_match:
                test_name = test_match.group(1)
                tests.append(
                    DiscoveredTestCase(
                        file_path=file_path,
                        suite_name=current_suite,
                        test_name=test_name,
                        line_number=line_num,
                        framework="jest/vitest",
                        language="TypeScript"
                        if file_path.endswith((".ts", ".tsx"))
                        else "JavaScript",
                    )
                )

        return tests


class CoverageIngester:
    """Parses coverage reports in Coverage.py JSON, LCOV, and Cobertura XML formats."""

    @staticmethod
    def parse_coverage_json(json_content: str) -> CoverageReport:
        """Parse Python coverage.json format."""
        data = json.loads(json_content)
        totals = data.get("totals", {})

        total_stmts = totals.get("num_statements", 0)
        covered_stmts = totals.get("covered_lines", 0)
        stmt_pct = totals.get("percent_covered", 0.0)

        total_branches = totals.get("num_branches", 0)
        covered_branches = totals.get("covered_branches", 0)
        branch_pct = totals.get("percent_covered_branches", 0.0)

        files_map: dict[str, FileCoverageDetail] = {}
        for f_path, f_data in data.get("files", {}).items():
            summary = f_data.get("summary", {})
            executed = f_data.get("executed_lines", [])
            missing = f_data.get("missing_lines", [])
            f_total = summary.get("num_statements", len(executed) + len(missing))
            f_covered = summary.get("covered_lines", len(executed))
            f_pct = summary.get(
                "percent_covered", round((f_covered / f_total * 100), 1) if f_total else 0.0
            )

            clean_path = f_path.replace("\\", "/").lstrip("/")
            files_map[clean_path] = FileCoverageDetail(
                file_path=clean_path,
                statements_total=f_total,
                statements_covered=f_covered,
                coverage_pct=f_pct,
                covered_lines=executed,
                uncovered_lines=missing,
            )

        return CoverageReport(
            format_type="coverage.json",
            statements_total=total_stmts,
            statements_covered=covered_stmts,
            statement_coverage_pct=round(stmt_pct, 1),
            branches_total=total_branches,
            branches_covered=covered_branches,
            branch_coverage_pct=round(branch_pct, 1),
            files=files_map,
        )

    @staticmethod
    def parse_lcov(lcov_text: str) -> CoverageReport:
        """Parse LCOV (.info) coverage format for JS/TS."""
        files_map: dict[str, FileCoverageDetail] = {}
        current_file: str | None = None
        current_covered: list[int] = []
        current_uncovered: list[int] = []
        lf = 0
        lh = 0
        brf = 0
        brh = 0

        total_lf = 0
        total_lh = 0
        total_brf = 0
        total_brh = 0

        for line in lcov_text.splitlines():
            line = line.strip()
            if line.startswith("SF:"):
                current_file = line[3:].replace("\\", "/").strip()
                current_covered = []
                current_uncovered = []
                lf, lh, brf, brh = 0, 0, 0, 0
            elif line.startswith("DA:"):
                parts = line[3:].split(",")
                if len(parts) >= 2:
                    lineno = int(parts[0])
                    hits = int(parts[1])
                    if hits > 0:
                        current_covered.append(lineno)
                    else:
                        current_uncovered.append(lineno)
            elif line.startswith("LF:"):
                lf = int(line[3:])
                total_lf += lf
            elif line.startswith("LH:"):
                lh = int(line[3:])
                total_lh += lh
            elif line.startswith("BRF:"):
                brf = int(line[4:])
                total_brf += brf
            elif line.startswith("BRH:"):
                brh = int(line[4:])
                total_brh += brh
            elif line == "end_of_record" and current_file:
                stmts_tot = lf or (len(current_covered) + len(current_uncovered))
                stmts_cov = lh or len(current_covered)
                cov_pct = round((stmts_cov / stmts_tot * 100), 1) if stmts_tot else 0.0
                files_map[current_file] = FileCoverageDetail(
                    file_path=current_file,
                    statements_total=stmts_tot,
                    statements_covered=stmts_cov,
                    coverage_pct=cov_pct,
                    covered_lines=current_covered,
                    uncovered_lines=current_uncovered,
                )

        total_stmts = total_lf or sum(f.statements_total for f in files_map.values())
        total_cov = total_lh or sum(f.statements_covered for f in files_map.values())
        stmt_pct = round((total_cov / total_stmts * 100), 1) if total_stmts else 0.0
        branch_pct = round((total_brh / total_brf * 100), 1) if total_brf else 0.0

        return CoverageReport(
            format_type="lcov",
            statements_total=total_stmts,
            statements_covered=total_cov,
            statement_coverage_pct=stmt_pct,
            branches_total=total_brf,
            branches_covered=total_brh,
            branch_coverage_pct=branch_pct,
            files=files_map,
        )

    @staticmethod
    def parse_cobertura_xml(xml_content: str) -> CoverageReport:
        """Parse Cobertura XML coverage format."""
        root = ET.fromstring(xml_content)
        line_rate = float(root.attrib.get("line-rate", 0.0))
        branch_rate = float(root.attrib.get("branch-rate", 0.0))

        files_map: dict[str, FileCoverageDetail] = {}
        total_lines = 0
        covered_lines_total = 0

        for cls_elem in root.iter("class"):
            filename = cls_elem.attrib.get("filename", "").replace("\\", "/")
            if not filename:
                continue

            covered_lines: list[int] = []
            uncovered_lines: list[int] = []

            for line_elem in cls_elem.iter("line"):
                num = int(line_elem.attrib.get("number", 0))
                hits = int(line_elem.attrib.get("hits", 0))
                if hits > 0:
                    covered_lines.append(num)
                else:
                    uncovered_lines.append(num)

            f_total = len(covered_lines) + len(uncovered_lines)
            f_cov = len(covered_lines)
            total_lines += f_total
            covered_lines_total += f_cov
            pct = round((f_cov / f_total * 100), 1) if f_total else 0.0

            files_map[filename] = FileCoverageDetail(
                file_path=filename,
                statements_total=f_total,
                statements_covered=f_cov,
                coverage_pct=pct,
                covered_lines=covered_lines,
                uncovered_lines=uncovered_lines,
            )

        stmt_pct = (
            round(line_rate * 100, 1)
            if line_rate
            else (round((covered_lines_total / total_lines * 100), 1) if total_lines else 0.0)
        )
        branch_pct = round(branch_rate * 100, 1)

        return CoverageReport(
            format_type="cobertura_xml",
            statements_total=total_lines,
            statements_covered=covered_lines_total,
            statement_coverage_pct=stmt_pct,
            branches_total=0,
            branches_covered=0,
            branch_coverage_pct=branch_pct,
            files=files_map,
        )
