"""Predictive ML modules for defect risk benchmarking and inference (M4-07..M4-14)."""

from atip_api.modules.risk.ml.benchmark import (
    BenchmarkReport,
    CandidateEvaluationResult,
    MultiModelBenchmarker,
)
from atip_api.modules.risk.ml.dataset_manifest import DatasetBuilder, DatasetManifest
from atip_api.modules.risk.ml.environment_gate import (
    EnvironmentCheckResult,
    TrainingEnvironmentGate,
)
from atip_api.modules.risk.ml.governance import (
    FEATURE_SCHEMA_COLUMNS,
    FeatureSchemaSpec,
    SupervisedTargetSpec,
    validate_tenant_consent_for_training,
)
from atip_api.modules.risk.ml.inference import DefectPredictionInferenceAdapter

__all__ = [
    "BenchmarkReport",
    "CandidateEvaluationResult",
    "DatasetBuilder",
    "DatasetManifest",
    "DefectPredictionInferenceAdapter",
    "EnvironmentCheckResult",
    "FEATURE_SCHEMA_COLUMNS",
    "FeatureSchemaSpec",
    "MultiModelBenchmarker",
    "SupervisedTargetSpec",
    "TrainingEnvironmentGate",
    "validate_tenant_consent_for_training",
]
