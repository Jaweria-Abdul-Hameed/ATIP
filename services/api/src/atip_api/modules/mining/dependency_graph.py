"""Python and JavaScript/TypeScript import and dependency graph analyzer with parser fallback."""

import ast
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.mining import DependencyEdgeRecord
from atip_api.modules.mining.git_fetcher import SHA_RE, SafeGitFetcher

logger = logging.getLogger(__name__)

# Fallback regexes for Python imports (single-line horizontal whitespace only)
PY_IMPORT_RE = re.compile(r"^[ \t]*import[ \t]+([a-zA-Z0-9_\., \t]+)", re.MULTILINE)
PY_FROM_RE = re.compile(
    r"^[ \t]*from[ \t]+([a-zA-Z0-9_\.]+)[ \t]+import[ \t]+([a-zA-Z0-9_\.,\*\(\) \t]+)",
    re.MULTILINE,
)

# Robust regexes for JavaScript/TypeScript imports
JS_STATIC_IMPORT_RE = re.compile(
    r"""import\s+(?:(?:(?:type\s+)?[\w*\s{},$]+)\s+from\s+)?['"]([^'"]+)['"]""",
    re.MULTILINE,
)
JS_EXPORT_FROM_RE = re.compile(
    r"""export\s+(?:(?:type\s+)?[\w*\s{},$]+)\s+from\s+['"]([^'"]+)['"]""",
    re.MULTILINE,
)
JS_REQUIRE_RE = re.compile(
    r"""(?:const|let|var)\s+[\w{},$\s]+\s*=\s*require\(\s*['"]([^'"]+)['"]\s*\)""",
    re.MULTILINE,
)
JS_DYNAMIC_IMPORT_RE = re.compile(
    r"""import\(\s*['"]([^'"]+)['"]\s*\)""",
    re.MULTILINE,
)


@dataclass
class ExtractedImport:
    target_module: str
    import_type: str
    imported_names: list[str] = field(default_factory=list)
    line_number: int = 1
    is_relative: bool = False
    relative_level: int = 0
    parser: str = "ast"  # "ast" or "regex_fallback"


class PythonImportExtractor:
    """Extracts imports from Python source using AST with regex fallback."""

    @staticmethod
    def extract(source_text: str, file_path: str = "") -> list[ExtractedImport]:
        imports: list[ExtractedImport] = []
        parsed_ast = False

        try:
            tree = ast.parse(source_text, filename=file_path)
            parsed_ast = True
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(
                            ExtractedImport(
                                target_module=alias.name,
                                import_type="python_import",
                                imported_names=[alias.asname or alias.name],
                                line_number=node.lineno,
                                is_relative=False,
                                relative_level=0,
                                parser="ast",
                            )
                        )
                elif isinstance(node, ast.ImportFrom):
                    level = node.level or 0
                    if level > 0:
                        module = ("." * level) + (node.module or "")
                    else:
                        module = node.module or ""
                    names = [alias.asname or alias.name for alias in node.names]
                    imports.append(
                        ExtractedImport(
                            target_module=module,
                            import_type="python_from_import",
                            imported_names=names,
                            line_number=node.lineno,
                            is_relative=level > 0,
                            relative_level=level,
                            parser="ast",
                        )
                    )
        except Exception as e:
            logger.debug(
                "Python AST parse error for %s (%s); engaging regex fallback", file_path, e
            )

        if not parsed_ast:
            # Regex Fallback
            for match in PY_FROM_RE.finditer(source_text):
                mod, names_str = match.groups()
                names = [
                    n.strip()
                    for n in names_str.replace("(", "").replace(")", "").split(",")
                    if n.strip()
                ]
                line = source_text[: match.start()].count("\n") + 1
                imports.append(
                    ExtractedImport(
                        target_module=mod,
                        import_type="python_from_import",
                        imported_names=names,
                        line_number=line,
                        is_relative=mod.startswith("."),
                        relative_level=mod.count(".") if mod.startswith(".") else 0,
                        parser="regex_fallback",
                    )
                )

            for match in PY_IMPORT_RE.finditer(source_text):
                mods = [
                    m.strip().split(" as ")[0].strip()
                    for m in match.group(1).split(",")
                    if m.strip()
                ]
                line = source_text[: match.start()].count("\n") + 1
                for mod in mods:
                    imports.append(
                        ExtractedImport(
                            target_module=mod,
                            import_type="python_import",
                            imported_names=[mod],
                            line_number=line,
                            is_relative=False,
                            relative_level=0,
                            parser="regex_fallback",
                        )
                    )

        return imports


class JsTsImportExtractor:
    """Extracts ES6 static, dynamic, require, and export-from imports from JS/TS code."""

    @staticmethod
    def extract(source_text: str, file_path: str = "") -> list[ExtractedImport]:
        imports: list[ExtractedImport] = []

        # 1. ES6 static imports
        for match in JS_STATIC_IMPORT_RE.finditer(source_text):
            target = match.group(1).strip()
            line = source_text[: match.start()].count("\n") + 1
            imports.append(
                ExtractedImport(
                    target_module=target,
                    import_type="es6_import",
                    line_number=line,
                    is_relative=target.startswith("."),
                    parser="regex_static",
                )
            )

        # 2. ES6 re-exports
        for match in JS_EXPORT_FROM_RE.finditer(source_text):
            target = match.group(1).strip()
            line = source_text[: match.start()].count("\n") + 1
            imports.append(
                ExtractedImport(
                    target_module=target,
                    import_type="es6_export_from",
                    line_number=line,
                    is_relative=target.startswith("."),
                    parser="regex_export",
                )
            )

        # 3. CommonJS require()
        for match in JS_REQUIRE_RE.finditer(source_text):
            target = match.group(1).strip()
            line = source_text[: match.start()].count("\n") + 1
            imports.append(
                ExtractedImport(
                    target_module=target,
                    import_type="commonjs_require",
                    line_number=line,
                    is_relative=target.startswith("."),
                    parser="regex_require",
                )
            )

        # 4. Dynamic import()
        for match in JS_DYNAMIC_IMPORT_RE.finditer(source_text):
            target = match.group(1).strip()
            line = source_text[: match.start()].count("\n") + 1
            imports.append(
                ExtractedImport(
                    target_module=target,
                    import_type="dynamic_import",
                    line_number=line,
                    is_relative=target.startswith("."),
                    parser="regex_dynamic",
                )
            )

        return imports


class DependencyResolver:
    """Resolves imported module specifiers against known repository tree files."""

    def __init__(self, all_repo_files: list[str]):
        self.files_set = set(all_repo_files)

    def resolve(
        self,
        importer_path: str,
        target_module: str,
        is_relative: bool,
        relative_level: int = 0,
    ) -> tuple[str | None, bool]:
        """Returns (resolved_file_path_or_none, is_external)."""
        clean_importer = importer_path.replace("\\", "/")
        parent_dir = str(Path(clean_importer).parent).replace("\\", "/")
        if parent_dir == ".":
            parent_dir = ""

        # Relative import resolution
        if is_relative or target_module.startswith("."):
            base = Path(parent_dir)
            if relative_level > 1:
                for _ in range(relative_level - 1):
                    base = base.parent

            clean_target = target_module.lstrip(".").lstrip("/")
            # Support dotted package paths in Python (e.g. core.errors -> core/errors)
            clean_target_path = clean_target.replace(".", "/")
            candidate_base = (base / clean_target_path).as_posix().lstrip("./")

            # Try direct file with standard extensions
            candidates = [
                candidate_base,
                f"{candidate_base}.ts",
                f"{candidate_base}.tsx",
                f"{candidate_base}.js",
                f"{candidate_base}.jsx",
                f"{candidate_base}/index.ts",
                f"{candidate_base}/index.tsx",
                f"{candidate_base}/index.js",
                f"{candidate_base}/index.jsx",
                f"{candidate_base}.py",
                f"{candidate_base}/__init__.py",
            ]
            for c in candidates:
                if c in self.files_set:
                    return c, False

            return None, False  # Internal relative import, but file not in tree

        # Non-relative import: check if matching top-level project folders
        py_candidate = f"{target_module.replace('.', '/')}.py"
        py_init = f"{target_module.replace('.', '/')}/__init__.py"
        if py_candidate in self.files_set:
            return py_candidate, False
        if py_init in self.files_set:
            return py_init, False

        # Try prefix matching with project subdirs (e.g. src/..., lib/...)
        for prefix in ["src", "lib", "app", "packages"]:
            prefixed = f"{prefix}/{target_module.replace('.', '/')}.py"
            if prefixed in self.files_set:
                return prefixed, False
            prefixed_ts = f"{prefix}/{target_module}.ts"
            if prefixed_ts in self.files_set:
                return prefixed_ts, False

        # Otherwise it is an external 3rd-party library (e.g., fastapi, react, lodash)
        return None, True


class DependencyGraphBuilder:
    """Constructs, analyzes, and persists the dependency graph for a commit snapshot."""

    def __init__(self, git_fetcher: SafeGitFetcher | None = None):
        self.git_fetcher = git_fetcher or SafeGitFetcher()

    async def build_and_persist_graph(
        self,
        session: AsyncSession,
        org_id: str,
        repository_id: str,
        commit_sha: str,
        repo_path: str | Path = ".",
    ) -> dict[str, Any]:
        """Build dependency edges for all files in tree at commit_sha without checkout."""
        # 1. Resolve commit SHA if passed ref/HEAD
        if not SHA_RE.match(commit_sha):
            commit_sha = await self.git_fetcher.resolve_commit_sha(repo_path, commit_sha)

        # 2. List all files in tree
        tree_files = await self.git_fetcher.list_tree_files(repo_path, commit_sha)
        all_paths = [f["path"] for f in tree_files]
        resolver = DependencyResolver(all_paths)

        # 3. Clear old dependency edges for this commit
        del_stmt = delete(DependencyEdgeRecord).where(
            DependencyEdgeRecord.organization_id == org_id,
            DependencyEdgeRecord.repository_id == repository_id,
            DependencyEdgeRecord.commit_sha == commit_sha,
        )
        await session.execute(del_stmt)

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        file_to_deps: dict[str, list[str]] = defaultdict(list)
        file_to_dependents: dict[str, list[str]] = defaultdict(list)

        for f_info in tree_files:
            file_path = f_info["path"]
            ext = Path(file_path).suffix.lower()

            # Skip non-code files
            if ext not in {".py", ".pyw", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
                continue

            # Read file blob safely
            try:
                content_bytes = await self.git_fetcher.read_file_at_commit(
                    repo_path=repo_path,
                    commit_sha=commit_sha,
                    file_path=file_path,
                )
                source_text = content_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning("Failed to read file %s at %s: %s", file_path, commit_sha, e)
                continue

            # Extract imports based on language
            if ext in {".py", ".pyw"}:
                raw_imports = PythonImportExtractor.extract(source_text, file_path)
            else:
                raw_imports = JsTsImportExtractor.extract(source_text, file_path)

            for imp in raw_imports:
                resolved_file, is_external = resolver.resolve(
                    importer_path=file_path,
                    target_module=imp.target_module,
                    is_relative=imp.is_relative,
                    relative_level=imp.relative_level,
                )

                edge_rec = DependencyEdgeRecord(
                    organization_id=org_id,
                    repository_id=repository_id,
                    commit_sha=commit_sha,
                    source_file=file_path,
                    target_module=imp.target_module,
                    target_file=resolved_file,
                    import_type=imp.import_type,
                    is_external=is_external,
                    edge_metadata={
                        "line_number": imp.line_number,
                        "imported_names": imp.imported_names,
                        "parser": imp.parser,
                    },
                )
                session.add(edge_rec)

                edge_data = {
                    "source": file_path,
                    "target": resolved_file or imp.target_module,
                    "target_module": imp.target_module,
                    "target_file": resolved_file,
                    "is_external": is_external,
                    "import_type": imp.import_type,
                    "line": imp.line_number,
                }
                edges.append(edge_data)

                if resolved_file:
                    file_to_deps[file_path].append(resolved_file)
                    file_to_dependents[resolved_file].append(file_path)

        await session.commit()

        # Build node metadata with fan-in and fan-out
        all_code_files = set(file_to_deps.keys()).union(file_to_dependents.keys())
        for f in all_code_files:
            nodes.append(
                {
                    "id": f,
                    "file_path": f,
                    "fan_out": len(file_to_deps[f]),
                    "fan_in": len(file_to_dependents[f]),
                    "dependencies": file_to_deps[f],
                    "dependents": file_to_dependents[f],
                }
            )

        # Detect circular dependency cycles
        cycles = self._find_cycles(file_to_deps)

        logger.info(
            "Built dependency graph for %s (%d nodes, %d edges, %d cycles)",
            commit_sha[:8],
            len(nodes),
            len(edges),
            len(cycles),
        )

        return {
            "commit_sha": commit_sha,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "internal_edges_count": sum(1 for e in edges if not e["is_external"]),
            "external_edges_count": sum(1 for e in edges if e["is_external"]),
            "circular_cycles": cycles,
            "nodes": nodes,
            "edges": edges,
        }

    @staticmethod
    def _find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
        """Find simple cycles in internal dependency graph using DFS."""
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: list[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle detected
                    idx = rec_stack.index(neighbor)
                    cycle = [*rec_stack[idx:], neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)

            rec_stack.pop()

        for n in list(graph.keys()):
            if n not in visited:
                dfs(n)

        return cycles[:20]  # Cap maximum detected cycles
