"""Comprehensive tests for static complexity, test discovery, and coverage ingestion (M3-04)."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
)
from atip_api.db.models.repository import Repository
from atip_api.modules.identity.session import create_session_token
from atip_api.modules.mining.static_analyzer import (
    CodeComplexityAnalyzer,
    CoverageIngester,
    TestDiscoverer,
)


def test_code_complexity_python():
    """Verify LOC breakdown, cyclomatic complexity, function inventory, and maintainability index for Python."""
    py_code = '''"""Module docstring."""
# A simple comment

def simple_function(a, b):
    # comment
    return a + b

def complex_function(x, y, z):
    if x > 0 and y > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
    elif z:
        while z > 0:
            z -= 1
    else:
        try:
            val = x / y
        except ZeroDivisionError:
            val = 0
    return val
'''
    metrics = CodeComplexityAnalyzer.analyze_source(py_code, "calculator.py")
    assert metrics.language == "Python"
    assert metrics.lines_total > 20
    assert metrics.lines_comments >= 3
    assert metrics.lines_blank >= 2
    assert metrics.lines_code > 10
    assert metrics.cyclomatic_complexity > 5
    assert len(metrics.functions) == 2

    # Verify functions
    func_names = {f.name for f in metrics.functions}
    assert "simple_function" in func_names
    assert "complex_function" in func_names

    simple_fn = next(f for f in metrics.functions if f.name == "simple_function")
    assert simple_fn.arg_count == 2
    assert simple_fn.complexity == 1

    complex_fn = next(f for f in metrics.functions if f.name == "complex_function")
    assert complex_fn.arg_count == 3
    assert complex_fn.complexity >= 6

    assert 0.0 <= metrics.maintainability_index <= 100.0


def test_code_complexity_python_syntax_fallback():
    """Verify fallback regex complexity for invalid Python syntax."""
    broken_py = """
def broken_fn(
    if x > 10 and y < 5:
        return True
    elif z:
        return False
"""
    metrics = CodeComplexityAnalyzer.analyze_source(broken_py, "broken.py")
    assert metrics.cyclomatic_complexity >= 3
    assert metrics.language == "Python"


def test_code_complexity_jsts():
    """Verify LOC, cyclomatic complexity, and function detection for TypeScript/JavaScript."""
    ts_code = """// Header comment
import { useState } from 'react';

/* Multi-line
   comment */
function processData(items: string[]): boolean {
    if (!items || items.length === 0) {
        return false;
    }
    for (const item of items) {
        if (item.includes('test') && item.length > 5) {
            console.log(item);
        }
    }
    return true;
}

const formatTitle = (title: string) => {
    return title ?? 'Default';
};
"""
    metrics = CodeComplexityAnalyzer.analyze_source(ts_code, "utils.ts")
    assert metrics.language == "TypeScript"
    assert metrics.lines_comments >= 3
    assert metrics.cyclomatic_complexity >= 4
    assert len(metrics.functions) >= 2
    assert 0.0 <= metrics.maintainability_index <= 100.0


def test_test_discovery_python():
    """Verify test discovery for pytest functions and unittest/pytest classes."""
    test_py = '''"""Test suite."""
import unittest

def test_standalone_one():
    assert 1 + 1 == 2

def test_standalone_two():
    assert True

class TestMathOperations(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(2 + 2, 4)

    def test_subtraction(self):
        self.assertEqual(5 - 2, 3)

    def helper_method(self):
        pass
'''
    discovered = TestDiscoverer.discover_in_file(test_py, "test_math.py")
    assert len(discovered) == 4
    names = {d.test_name for d in discovered}
    assert "test_standalone_one" in names
    assert "test_standalone_two" in names
    assert "test_addition" in names
    assert "test_subtraction" in names
    assert "helper_method" not in names

    suites = {d.suite_name for d in discovered}
    assert "TestMathOperations" in suites
    assert "test_math" in suites
    assert all(d.language == "Python" for d in discovered)


def test_test_discovery_jsts():
    """Verify test discovery for jest / vitest suites and assertions."""
    test_ts = """describe('AuthService', () => {
    it('should authenticate user with valid credentials', async () => {
        expect(true).toBe(true);
    });

    test('should reject invalid password', () => {
        expect(false).toBe(false);
    });
});

describe('TokenManager', () => {
    it('should refresh token before expiry', () => {
        expect(1).toBe(1);
    });
});
"""
    discovered = TestDiscoverer.discover_in_file(test_ts, "auth.test.ts")
    assert len(discovered) == 3
    names = {d.test_name for d in discovered}
    assert "should authenticate user with valid credentials" in names
    assert "should reject invalid password" in names
    assert "should refresh token before expiry" in names

    suites = {d.suite_name for d in discovered}
    assert "AuthService" in suites
    assert "TokenManager" in suites
    assert all(d.framework == "jest/vitest" for d in discovered)
    assert all(d.language == "TypeScript" for d in discovered)


def test_coverage_ingestion_coverage_json():
    """Verify ingestion of Coverage.py JSON format."""
    cov_json = {
        "meta": {"version": "7.4.0"},
        "totals": {
            "covered_lines": 42,
            "num_statements": 50,
            "percent_covered": 84.0,
            "covered_branches": 8,
            "num_branches": 10,
            "percent_covered_branches": 80.0,
        },
        "files": {
            "atip_api/main.py": {
                "executed_lines": [1, 2, 3, 4, 5, 8, 9, 10],
                "missing_lines": [6, 7],
                "summary": {
                    "covered_lines": 8,
                    "num_statements": 10,
                    "percent_covered": 80.0,
                },
            },
            "atip_api/core/errors.py": {
                "executed_lines": [1, 2, 3, 4, 5],
                "missing_lines": [],
                "summary": {
                    "covered_lines": 5,
                    "num_statements": 5,
                    "percent_covered": 100.0,
                },
            },
        },
    }
    report = CoverageIngester.parse_coverage_json(json.dumps(cov_json))
    assert report.format_type == "coverage.json"
    assert report.statements_total == 50
    assert report.statements_covered == 42
    assert report.statement_coverage_pct == 84.0
    assert report.branches_total == 10
    assert report.branches_covered == 8
    assert report.branch_coverage_pct == 80.0
    assert len(report.files) == 2
    assert "atip_api/main.py" in report.files
    assert report.files["atip_api/main.py"].uncovered_lines == [6, 7]


def test_coverage_ingestion_lcov():
    """Verify ingestion of LCOV info format."""
    lcov_content = """TN:
SF:src/components/button.tsx
DA:1,1
DA:2,1
DA:3,0
DA:4,1
LF:4
LH:3
BRF:2
BRH:1
end_of_record
SF:src/lib/utils.ts
DA:1,1
DA:2,1
LF:2
LH:2
BRF:0
BRH:0
end_of_record
"""
    report = CoverageIngester.parse_lcov(lcov_content)
    assert report.format_type == "lcov"
    assert report.statements_total == 6
    assert report.statements_covered == 5
    assert report.statement_coverage_pct == 83.3
    assert report.branches_total == 2
    assert report.branches_covered == 1
    assert report.branch_coverage_pct == 50.0
    assert len(report.files) == 2
    assert report.files["src/components/button.tsx"].uncovered_lines == [3]


def test_coverage_ingestion_cobertura_xml():
    """Verify ingestion of Cobertura XML format."""
    xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.75" branch-rate="0.5" version="2.0">
    <packages>
        <package name="core">
            <classes>
                <class name="errors" filename="src/errors.py">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="1"/>
                        <line number="3" hits="1"/>
                        <line number="4" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""
    report = CoverageIngester.parse_cobertura_xml(xml_content)
    assert report.format_type == "cobertura_xml"
    assert report.statements_total == 4
    assert report.statements_covered == 3
    assert report.statement_coverage_pct == 75.0
    assert len(report.files) == 1
    assert "src/errors.py" in report.files
    assert report.files["src/errors.py"].uncovered_lines == [4]


@pytest.fixture
def repo_with_code_and_tests():
    """Create a temporary git repository with Python code, TS code, and tests."""
    temp_dir = tempfile.mkdtemp(prefix="atip_static_repo_")
    repo_path = Path(temp_dir)

    def _git(*args):
        subprocess.run(["git", *args], cwd=repo_path, check=True, capture_output=True)

    _git("init", "-b", "main")
    _git("config", "user.name", "Static Tester")
    _git("config", "user.email", "static@atip.test")

    # Source files
    (repo_path / "math_ops.py").write_text(
        "def add(a, b):\n    if a > 0:\n        return a + b\n    return b\n",
        encoding="utf-8",
    )
    (repo_path / "test_math_ops.py").write_text(
        "def test_add_positive():\n    assert True\n\ndef test_add_negative():\n    assert True\n",
        encoding="utf-8",
    )
    (repo_path / "app.ts").write_text(
        "export function run(flag: boolean) {\n    if (flag) {\n        console.log('ok');\n    }\n}\n",
        encoding="utf-8",
    )

    _git("add", ".")
    _git("commit", "-m", "feat: initial code and tests")

    yield repo_path


@pytest.mark.asyncio
async def test_api_endpoints_complexity_and_tests(
    db_session: AsyncSession,
    client: AsyncClient,
    repo_with_code_and_tests: Path,
):
    """Verify GET /complexity and GET /tests REST endpoints."""
    repo_path = repo_with_code_and_tests

    org = Organization(name="Static Org", slug="static-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=9876543,
        name="test-static-repo",
        full_name="static-org/test-static-repo",
        default_branch="main",
        clone_url="https://github.com/static-org/test-static-repo.git",
    )
    db_session.add(repo)

    user = User(
        email="dev_static@atip.test",
        name="Static Dev",
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

    # 1. GET /complexity (all files)
    comp_res = await client.get(
        f"/api/v1/repositories/{repo.id}/complexity?repo_path={repo_path}",
        headers=headers,
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()["data"]
    assert len(comp_data) >= 3
    file_paths = {item["file_path"] for item in comp_data}
    assert "math_ops.py" in file_paths
    assert "app.ts" in file_paths

    # 2. GET /complexity (single file)
    single_res = await client.get(
        f"/api/v1/repositories/{repo.id}/complexity?repo_path={repo_path}&file_path=math_ops.py",
        headers=headers,
    )
    assert single_res.status_code == 200
    single_data = single_res.json()["data"]
    assert len(single_data) == 1
    assert single_data[0]["file_path"] == "math_ops.py"
    assert single_data[0]["cyclomatic_complexity"] >= 2
    assert len(single_data[0]["functions"]) == 1
    assert single_data[0]["functions"][0]["name"] == "add"

    # 3. GET /tests
    tests_res = await client.get(
        f"/api/v1/repositories/{repo.id}/tests?repo_path={repo_path}",
        headers=headers,
    )
    assert tests_res.status_code == 200
    tests_data = tests_res.json()["data"]
    assert len(tests_data) == 2
    test_names = {t["test_name"] for t in tests_data}
    assert "test_add_positive" in test_names
    assert "test_add_negative" in test_names


@pytest.mark.asyncio
async def test_api_coverage_ingest_and_get(
    db_session: AsyncSession,
    client: AsyncClient,
):
    """Verify POST /coverage/ingest and GET /coverage endpoints."""
    org = Organization(name="Coverage Org", slug="cov-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=55443322,
        name="test-cov-repo",
        full_name="cov-org/test-cov-repo",
        default_branch="main",
        clone_url="https://github.com/cov-org/test-cov-repo.git",
    )
    db_session.add(repo)

    user = User(
        email="dev_cov@atip.test",
        name="Cov Dev",
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

    # 1. GET /coverage before ingestion returns null (honest empty state)
    empty_res = await client.get(
        f"/api/v1/repositories/{repo.id}/coverage",
        headers=headers,
    )
    assert empty_res.status_code == 200
    assert empty_res.json()["data"] is None

    # 2. Ingest coverage.json
    cov_payload = {
        "format_type": "coverage.json",
        "content": json.dumps(
            {
                "totals": {
                    "covered_lines": 18,
                    "num_statements": 20,
                    "percent_covered": 90.0,
                    "covered_branches": 2,
                    "num_branches": 2,
                    "percent_covered_branches": 100.0,
                },
                "files": {
                    "math_ops.py": {
                        "executed_lines": [1, 2, 3],
                        "missing_lines": [],
                        "summary": {
                            "covered_lines": 3,
                            "num_statements": 3,
                            "percent_covered": 100.0,
                        },
                    }
                },
            }
        ),
    }
    ingest_res = await client.post(
        f"/api/v1/repositories/{repo.id}/coverage/ingest?commit_sha=test_sha_123",
        headers=headers,
        json=cov_payload,
    )
    assert ingest_res.status_code == 201
    ingest_data = ingest_res.json()["data"]
    assert ingest_data["format_type"] == "coverage.json"
    assert ingest_data["statements_covered"] == 18
    assert ingest_data["statements_total"] == 20
    assert ingest_data["statement_coverage_pct"] == 90.0
    assert "math_ops.py" in ingest_data["files"]

    # 3. GET /coverage after ingestion returns persisted report
    get_res = await client.get(
        f"/api/v1/repositories/{repo.id}/coverage?commit_sha=test_sha_123",
        headers=headers,
    )
    assert get_res.status_code == 200
    retrieved = get_res.json()["data"]
    assert retrieved is not None
    assert retrieved["statements_covered"] == 18
    assert retrieved["statements_total"] == 20
    assert retrieved["statement_coverage_pct"] == 90.0
    assert retrieved["files"]["math_ops.py"]["coverage_pct"] == 100.0

    # 4. Ingest invalid format returns 400 Bad Request
    invalid_res = await client.post(
        f"/api/v1/repositories/{repo.id}/coverage/ingest",
        headers=headers,
        json={"format_type": "unsupported_fmt", "content": "not-supported"},
    )
    assert invalid_res.status_code == 400
