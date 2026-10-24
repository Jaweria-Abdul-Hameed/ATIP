"""Change-impact analysis and dependency propagation with bounded graph traversal."""

from collections import defaultdict, deque
from typing import Any

from atip_api.modules.risk.schemas import ChangeImpactNode


class ChangeImpactAnalyzer:
    """Computes bounded change-impact propagation across code dependency graphs."""

    def __init__(
        self,
        max_depth: int = 5,
        max_impacted_nodes: int = 500,
        decay_factor: float = 0.65,
    ):
        self.max_depth = max_depth
        self.max_impacted_nodes = max_impacted_nodes
        self.decay_factor = decay_factor

    def build_reverse_dependency_map(
        self,
        dependency_edges: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        """Builds a mapping from imported file (target) -> importing files (dependents).

        If file A imports file B, when B changes, A is impacted.
        Reverse map: B -> [A]
        """
        reverse_map: dict[str, list[str]] = defaultdict(list)
        for edge in dependency_edges:
            target = edge.get("target_file")
            source = edge.get("source_file")
            if target and source and target != source:
                if source not in reverse_map[target]:
                    reverse_map[target].append(source)
        return reverse_map

    def compute_impact(
        self,
        changed_files: list[str],
        dependency_edges: list[dict[str, Any]],
    ) -> list[ChangeImpactNode]:
        """Performs bounded BFS propagation from changed files through the reverse dependency graph.

        Returns ordered list of ChangeImpactNode with propagation reasons and decay.
        """
        if not changed_files:
            return []

        reverse_map = self.build_reverse_dependency_map(dependency_edges)

        impacted_map: dict[str, ChangeImpactNode] = {}
        # Queue item: (current_file, depth, path)
        queue: deque[tuple[str, int, list[str]]] = deque()

        # Seed queue with directly modified files
        for f in changed_files:
            impacted_map[f] = ChangeImpactNode(
                file_path=f,
                depth=0,
                impact_score=100.0,
                is_direct=True,
                imported_by=[],
                propagation_reason="Directly modified in commit / pull request.",
            )
            queue.append((f, 0, [f]))

        cycles_detected = 0

        while queue and len(impacted_map) < self.max_impacted_nodes:
            curr_file, depth, path = queue.popleft()

            if depth >= self.max_depth:
                continue

            dependents = reverse_map.get(curr_file, [])
            for dep in dependents:
                # Cycle check
                if dep in path:
                    cycles_detected += 1
                    continue

                next_depth = depth + 1
                attenuated_score = round(100.0 * (self.decay_factor ** next_depth), 1)

                if dep in impacted_map:
                    # Already reached: update if this path had higher impact / lower depth
                    existing = impacted_map[dep]
                    if next_depth < existing.depth:
                        existing.depth = next_depth
                        existing.impact_score = max(existing.impact_score, attenuated_score)
                    if curr_file not in existing.imported_by:
                        existing.imported_by.append(curr_file)
                else:
                    reason = (
                        f"Directly imports modified file '{curr_file}'."
                        if next_depth == 1
                        else f"Transitively dependent (depth {next_depth}) via '{curr_file}'."
                    )
                    impacted_map[dep] = ChangeImpactNode(
                        file_path=dep,
                        depth=next_depth,
                        impact_score=attenuated_score,
                        is_direct=False,
                        imported_by=[curr_file],
                        propagation_reason=reason,
                    )

                new_path = path + [dep]
                queue.append((dep, next_depth, new_path))

        # Sort: directly changed first, then descending by impact score and ascending by depth
        sorted_nodes = sorted(
            impacted_map.values(),
            key=lambda n: (not n.is_direct, -n.impact_score, n.depth, n.file_path),
        )
        return sorted_nodes

    def compute_blast_radius_counts(
        self,
        file_path: str,
        dependency_edges: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """
        Computes (direct_dependents_count, transitive_dependents_count) for a specific file.
        """
        reverse_map = self.build_reverse_dependency_map(dependency_edges)
        direct = len(reverse_map.get(file_path, []))

        transitive_visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(file_path, 0)])

        while queue and len(transitive_visited) < self.max_impacted_nodes:
            curr, depth = queue.popleft()
            if depth >= self.max_depth:
                continue

            for dep in reverse_map.get(curr, []):
                if dep != file_path and dep not in transitive_visited:
                    transitive_visited.add(dep)
                    queue.append((dep, depth + 1))

        return direct, len(transitive_visited)
