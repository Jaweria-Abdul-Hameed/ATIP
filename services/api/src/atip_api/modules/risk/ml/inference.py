"""Model inference adapter with safe deterministic fallback and latency monitoring (M4-10)."""

import logging
import os
import time
from typing import Any

import joblib
import numpy as np

from atip_api.modules.risk.engine import DeterministicRiskEngine

logger = logging.getLogger(__name__)


class DefectPredictionInferenceAdapter:
    """Inference adapter serving trained ML models with zero-dependency deterministic fallback."""

    def __init__(
        self,
        model_artifact_path: str = "artifacts/ml/champion_defect_model.joblib",
        deterministic_engine: DeterministicRiskEngine | None = None,
        is_approved_for_production: bool = True,
    ):
        self.model_artifact_path = model_artifact_path
        self.deterministic_engine = deterministic_engine or DeterministicRiskEngine()
        self.is_approved_for_production = is_approved_for_production
        self._loaded_model_data: dict[str, Any] | None = None
        self._load_artifact()

    def _load_artifact(self) -> None:
        """Loads serialized model artifact safely."""
        if not os.path.exists(self.model_artifact_path):
            logger.info("No trained ML artifact found at '%s'. Using deterministic fallback.", self.model_artifact_path)
            return

        try:
            self._loaded_model_data = joblib.load(self.model_artifact_path)
            logger.info("Successfully loaded champion defect model '%s'", self._loaded_model_data.get("model_name"))
        except Exception as exc:
            logger.warning("Failed to load model artifact '%s': %s. Safe deterministic fallback active.", self.model_artifact_path, exc)
            self._loaded_model_data = None

    @property
    def is_ml_active(self) -> bool:
        return self._loaded_model_data is not None and self.is_approved_for_production

    @property
    def active_model_version(self) -> str:
        if self.is_ml_active and self._loaded_model_data:
            name = self._loaded_model_data.get("model_name", "ml-model").lower().replace(" ", "-")
            return f"ml-{name}-v1.0.0"
        return self.deterministic_engine.config.version

    def predict_file_defect_risk(
        self,
        cyclomatic: int | None = None,
        maintainability_index: float | None = None,
        loc: int | None = None,
        lines_changed: int | None = None,
        churn_count: int | None = None,
        direct_dependents: int | None = None,
        transitive_dependents: int | None = None,
        has_test_file: bool = False,
        defect_commit_count: int | None = None,
    ) -> tuple[float, str, float]:
        """
        Predicts defect probability using the champion ML model when available and approved.
        Falls back smoothly to deterministic risk engine score if ML is unavailable or missing data is severe.

        Returns (probability_0_to_1, model_version_provenance, latency_ms).
        """
        t0 = time.perf_counter()

        if not self.is_ml_active:
            # Safe deterministic fallback
            det_res = self.deterministic_engine.evaluate_file(
                file_path="inference_file.py",
                cyclomatic=cyclomatic,
                maintainability_index=maintainability_index,
                loc=loc,
                churn_count=churn_count,
                lines_changed=lines_changed,
                direct_dependents=direct_dependents,
                transitive_dependents=transitive_dependents,
                has_test_file=has_test_file,
                defect_commit_count=defect_commit_count,
            )
            lat = (time.perf_counter() - t0) * 1000.0
            return (det_res.risk_score / 100.0, self.active_model_version, round(lat, 3))

        # ML Prediction pipeline
        try:
            pipeline = self._loaded_model_data["pipeline"]  # type: ignore
            raw_features = np.array([[
                float(cyclomatic) if cyclomatic is not None else np.nan,
                float(maintainability_index) if maintainability_index is not None else np.nan,
                float(loc) if loc is not None else np.nan,
                float(lines_changed) if lines_changed is not None else 0.0,
                float(churn_count) if churn_count is not None else 0.0,
                float(direct_dependents) if direct_dependents is not None else 0.0,
                float(transitive_dependents) if transitive_dependents is not None else 0.0,
                1.0 if has_test_file else 0.0,
                float(defect_commit_count) if defect_commit_count is not None else 0.0,
            ]])

            prob = float(pipeline.predict_proba(raw_features)[0, 1])
            lat = (time.perf_counter() - t0) * 1000.0
            return (round(prob, 4), self.active_model_version, round(lat, 3))

        except Exception as exc:
            logger.warning("ML inference exception: %s. Falling back to deterministic score.", exc)
            det_res = self.deterministic_engine.evaluate_file(
                file_path="inference_file.py",
                cyclomatic=cyclomatic,
                maintainability_index=maintainability_index,
                loc=loc,
                churn_count=churn_count,
                lines_changed=lines_changed,
                direct_dependents=direct_dependents,
                transitive_dependents=transitive_dependents,
                has_test_file=has_test_file,
                defect_commit_count=defect_commit_count,
            )
            lat = (time.perf_counter() - t0) * 1000.0
            return (det_res.risk_score / 100.0, self.deterministic_engine.config.version, round(lat, 3))
