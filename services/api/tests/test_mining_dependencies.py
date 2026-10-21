"""Comprehensive tests for Python + JS/TS import extraction, dependency graph, and cycle detection (M3-03)."""

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
from atip_api.modules.mining.dependency_graph import (
    DependencyGraphBuilder,
    DependencyResolver,
    JsTsImportExtractor,
    PythonImportExtractor,
)


def test_python_import_extractor_ast_and_fallback():
    """Verify AST extraction and regex fallback for syntactically invalid Python code."""
    # 1. Valid Python code
    valid_py = """
import os
import sys as system
from collections.abc import AsyncGenerator
from .relative_mod import helper, util
from ..parent_mod import parent_func
"""
    imports = PythonImportExtractor.extract(valid_py, "test.py")
    assert len(imports) == 5
    modules = {imp.target_module for imp in imports}
    assert "os" in modules
    assert "sys" in modules
    assert "collections.abc" in modules
    assert ".relative_mod" in modules
    assert any(imp.is_relative for imp in imports)
    assert all(imp.parser == "ast" for imp in imports)

    # 2. Syntactically invalid Python code (trigger fallback)
    invalid_py = """
import math
from datetime import datetime, date (syntax error unclosed
def broken_func(:
    pass
import json
"""
    fallback_imports = PythonImportExtractor.extract(invalid_py, "broken.py")
    fallback_mods = {imp.target_module for imp in fallback_imports}
    assert "math" in fallback_mods
    assert "json" in fallback_mods
    assert "datetime" in fallback_mods
    assert any(imp.parser == "regex_fallback" for imp in fallback_imports)


def test_jsts_import_extractor():
    """Verify ES6 static, dynamic, require, and export-from imports for JS/TS."""
    ts_source = """
import React, { useState, useEffect } from 'react';
import type { Metadata } from 'next';
import { Button } from './components/button';
import './globals.css';
export * from './types';
export { Header } from './layout/header';
const config = require('./config.json');
const path = require('path');

async function loadModule() {
    const mod = await import('./dynamic-widget');
}
"""
    imports = JsTsImportExtractor.extract(ts_source, "page.tsx")
    assert len(imports) >= 7
    targets = {imp.target_module for imp in imports}
    assert "react" in targets
    assert "next" in targets
    assert "./components/button" in targets
    assert "./globals.css" in targets
    assert "./types" in targets
    assert "./config.json" in targets
    assert "path" in targets
    assert "./dynamic-widget" in targets


def test_dependency_resolver():
    """Verify relative internal vs 3rd-party external dependency classification."""
    all_files = [
        "src/index.ts",
        "src/components/button.tsx",
        "src/utils/math.ts",
        "atip_api/main.py",
        "atip_api/core/errors.py",
    ]
    resolver = DependencyResolver(all_files)

    # Relative internal
    res, is_ext = resolver.resolve("src/index.ts", "./components/button", is_relative=True)
    assert res == "src/components/button.tsx"
    assert is_ext is False

    # External library
    res_ext, is_ext2 = resolver.resolve("src/index.ts", "react", is_relative=False)
    assert res_ext is None
    assert is_ext2 is True

    # Python relative
    res_py, is_ext_py = resolver.resolve(
        "atip_api/main.py", ".core.errors", is_relative=True, relative_level=1
    )
    assert res_py == "atip_api/core/errors.py"
    assert is_ext_py is False


@pytest.fixture
def repo_with_cycles():
    """Create a git repo with intentional circular dependencies: A -> B -> C -> A."""
    temp_dir = tempfile.mkdtemp(prefix="atip_dep_repo_")
    repo_path = Path(temp_dir)

    def _git(*args):
        subprocess.run(["git", *args], cwd=repo_path, check=True, capture_output=True)

    _git("init", "-b", "main")
    _git("config", "user.name", "Graph Tester")
    _git("config", "user.email", "graph@atip.test")

    # Cycle: a.py -> b.py -> c.py -> a.py
    (repo_path / "a.py").write_text("import b\ndef fn_a(): return b.fn_b()\n", encoding="utf-8")
    (repo_path / "b.py").write_text("import c\ndef fn_b(): return c.fn_c()\n", encoding="utf-8")
    (repo_path / "c.py").write_text("import a\ndef fn_c(): return a.fn_a()\n", encoding="utf-8")

    # Independent file d.py that depends on c.py and external os
    (repo_path / "d.py").write_text("import os\nimport c\n", encoding="utf-8")

    _git("add", ".")
    _git("commit", "-m", "feat: create cyclic graph fixture")

    yield repo_path


@pytest.mark.asyncio
async def test_dependency_graph_builder_and_cycle_detection(
    db_session: AsyncSession, repo_with_cycles
):
    """Verify dependency graph building, fan-in/fan-out, and circular cycle detection."""
    repo_path = repo_with_cycles

    org = Organization(name="Dep Org", slug="dep-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=33445566,
        name="dep-repo",
        full_name="dep-org/dep-repo",
        default_branch="main",
        clone_url="https://github.com/dep-org/dep-repo.git",
    )
    db_session.add(repo)
    await db_session.flush()

    builder = DependencyGraphBuilder()
    graph_data = await builder.build_and_persist_graph(
        session=db_session,
        org_id=org.id,
        repository_id=repo.id,
        commit_sha="HEAD",
        repo_path=repo_path,
    )

    assert graph_data["total_nodes"] >= 4
    assert graph_data["total_edges"] >= 4
    assert graph_data["external_edges_count"] >= 1  # os

    # Cycle detection
    cycles = graph_data["circular_cycles"]
    assert len(cycles) > 0
    cycle_files = set(cycles[0])
    assert {"a.py", "b.py", "c.py"}.issubset(cycle_files)

    # Fan-in check: c.py is imported by b.py and d.py -> fan_in >= 2
    c_node = next(n for n in graph_data["nodes"] if n["file_path"] == "c.py")
    assert c_node["fan_in"] >= 2


@pytest.mark.asyncio
async def test_dependency_graph_api_endpoints(
    client: AsyncClient, db_session: AsyncSession, repo_with_cycles
):
    """Verify REST API endpoints for repository dependencies and blast radius."""
    repo_path = repo_with_cycles

    org = Organization(name="API Dep Org", slug="api-dep-org")
    db_session.add(org)
    await db_session.flush()

    user = User(email="depuser@atip.test", name="Dep User", is_active=True)
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
        github_repo_id=44556677,
        name="api-dep-repo",
        full_name="api-dep-org/api-dep-repo",
        default_branch="main",
        clone_url="https://github.com/api-dep-org/api-dep-repo.git",
    )
    db_session.add(repo)
    await db_session.flush()

    # Pre-build graph
    builder = DependencyGraphBuilder()
    await builder.build_and_persist_graph(
        session=db_session,
        org_id=org.id,
        repository_id=repo.id,
        commit_sha="HEAD",
        repo_path=repo_path,
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

    # 1. GET repository dependencies
    res_deps = await client.get(
        f"/api/v1/repositories/{repo.id}/dependencies?repo_path={repo_path}",
        headers=auth_headers,
    )
    assert res_deps.status_code == 200
    data = res_deps.json()["data"]
    assert data["total_nodes"] >= 4
    assert len(data["circular_cycles"]) > 0

    # 2. GET file dependencies (blast radius) for c.py
    res_file = await client.get(
        f"/api/v1/repositories/{repo.id}/dependencies/file?path=c.py&repo_path={repo_path}",
        headers=auth_headers,
    )
    assert res_file.status_code == 200
    file_data = res_file.json()["data"]
    assert file_data["file_path"] == "c.py"
    assert file_data["blast_radius_count"] >= 2  # imported by b.py and d.py
