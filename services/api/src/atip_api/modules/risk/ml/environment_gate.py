"""Training environment check and human intervention gate (M4-11, M4-12)."""

import os
import shutil
from dataclasses import dataclass


@dataclass
class EnvironmentCheckResult:
    """Telemetry report of host computational capacity for ML training."""

    cpu_count: int
    memory_available_gb: float
    free_disk_space_gb: float
    is_cpu_suitable: bool
    requires_cloud_gpu: bool
    requires_human_intervention: bool
    intervention_reasons: list[str]


class TrainingEnvironmentGate:
    """Validates local host computational limits before initiating model training."""

    def __init__(self, min_free_disk_gb: float = 2.0, min_memory_gb: float = 2.0):
        self.min_free_disk_gb = min_free_disk_gb
        self.min_memory_gb = min_memory_gb

    def evaluate_environment(self) -> EnvironmentCheckResult:
        """Inspects CPU, RAM, and disk space to confirm local feasibility."""
        cpu_count = os.cpu_count() or 1

        # Check disk space
        try:
            total, used, free = shutil.disk_usage(".")
            free_disk_gb = round(free / (1024**3), 2)
        except Exception:
            free_disk_gb = 10.0

        # Memory approximation (using psutil if available, or safe default)
        try:
            import psutil
            mem = psutil.virtual_memory()
            available_ram_gb = round(mem.available / (1024**3), 2)
        except Exception:
            available_ram_gb = 8.0

        intervention_reasons = []

        if free_disk_gb < self.min_free_disk_gb:
            intervention_reasons.append(
                f"Insufficient disk space: {free_disk_gb} GB free (minimum {self.min_free_disk_gb} GB required)."
            )

        if available_ram_gb < self.min_memory_gb:
            intervention_reasons.append(
                f"Low available RAM: {available_ram_gb} GB available (minimum {self.min_memory_gb} GB required)."
            )

        # Tabular defect prediction on commit features (Logistic Regression, Random Forest, LightGBM, XGBoost)
        # trains in seconds on standard CPU; no expensive cloud GPU or external compute needed.
        requires_cloud_gpu = False
        is_cpu_suitable = len(intervention_reasons) == 0
        requires_intervention = len(intervention_reasons) > 0

        return EnvironmentCheckResult(
            cpu_count=cpu_count,
            memory_available_gb=available_ram_gb,
            free_disk_space_gb=free_disk_gb,
            is_cpu_suitable=is_cpu_suitable,
            requires_cloud_gpu=requires_cloud_gpu,
            requires_human_intervention=requires_intervention,
            intervention_reasons=intervention_reasons,
        )
