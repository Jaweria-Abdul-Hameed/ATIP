"""Tests for ML data governance, environment gates, multi-model benchmarking, and inference (M4-07..M4-14)."""

import os
import shutil
import tempfile

from atip_api.modules.risk.ml.benchmark import MultiModelBenchmarker
from atip_api.modules.risk.ml.dataset_manifest import DatasetBuilder
from atip_api.modules.risk.ml.environment_gate import TrainingEnvironmentGate
from atip_api.modules.risk.ml.governance import (
    FEATURE_SCHEMA_COLUMNS,
    FeatureSchemaSpec,
    SupervisedTargetSpec,
    validate_tenant_consent_for_training,
)
from atip_api.modules.risk.ml.inference import DefectPredictionInferenceAdapter


def test_ml_data_governance_and_leakage_safeguards():
    """Verify prediction target specification, feature schema, and strict tenant consent (M4-07)."""
    target = SupervisedTargetSpec()
    assert target.target_name == "defect_introduced"
    assert target.observation_window_days == 90
    assert "SZZ" in target.positive_label_definition

    schema = FeatureSchemaSpec()
    assert len(schema.columns) == len(FEATURE_SCHEMA_COLUMNS)
    assert "cyclomatic_complexity" in schema.columns
    assert "prior_churn_count" in schema.columns
    assert "future_commit_leakage" in schema.leakage_threats_and_safeguards

    # Tenant consent check: private tenant without explicit opt-in must be rejected
    consent_registry = {"consented_org_123": True}
    assert not validate_tenant_consent_for_training("private_tenant_999", consent_registry)
    assert validate_tenant_consent_for_training("consented_org_123", consent_registry)


def test_training_environment_gate():
    """Verify local host computational resources check before training (M4-11, M4-12)."""
    gate = TrainingEnvironmentGate(min_free_disk_gb=0.1, min_memory_gb=0.1)
    env_report = gate.evaluate_environment()

    assert env_report.cpu_count >= 1
    assert env_report.free_disk_space_gb > 0.0
    assert env_report.is_cpu_suitable
    assert not env_report.requires_cloud_gpu


def test_dataset_extraction_and_immutable_manifest():
    """Verify reproducible dataset generation, class imbalance, and time-based splits (M4-07, M4-08)."""
    X, y, metadata = DatasetBuilder.generate_curated_benchmark_dataset(sample_count=200, random_seed=42)
    assert len(X) == 200
    assert len(y) == 200
    assert X.shape[1] == len(FEATURE_SCHEMA_COLUMNS)

    # Class imbalance should be ~20%
    defect_rate = sum(y) / len(y)
    assert 0.15 <= defect_rate <= 0.25

    (X_train, y_train), (X_val, y_val), (X_test, y_test), manifest = (
        DatasetBuilder.create_leakage_free_splits(X, y, metadata)
    )

    assert len(X_train) == 140  # 70%
    assert len(X_val) == 30    # 15%
    assert len(X_test) == 30   # 15%
    assert len(manifest.sha256_checksum) == 64
    assert manifest.total_samples == 200
    assert len(manifest.sources) == 3


def test_multi_model_benchmarking_and_champion_selection():
    """
    Execute mandatory multi-model benchmark across Logistic Regression,
    Random Forest, LightGBM, and XGBoost vs Deterministic Baseline (M4-09).
    """
    tmp_dir = tempfile.mkdtemp(prefix="atip_ml_bench_")
    try:
        X, y, metadata = DatasetBuilder.generate_curated_benchmark_dataset(sample_count=250, random_seed=123)
        (X_train, y_train), (X_val, y_val), (X_test, y_test), manifest = (
            DatasetBuilder.create_leakage_free_splits(X, y, metadata)
        )

        benchmarker = MultiModelBenchmarker(random_seed=123)
        report = benchmarker.run_benchmark(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            manifest_id=manifest.manifest_id,
            artifacts_dir=tmp_dir,
        )

        # 5 candidates must be present: Baseline + 4 ML models
        candidate_names = [c.model_name for c in report.candidates]
        assert "Deterministic Baseline (Heuristic Engine)" in candidate_names
        assert "Logistic Regression (L2)" in candidate_names
        assert "Random Forest" in candidate_names
        assert "LightGBM" in candidate_names
        assert "XGBoost" in candidate_names

        # Verify PR-AUC and calibration evaluated for all
        for cand in report.candidates:
            assert 0.0 <= cand.pr_auc <= 1.0
            assert 0.0 <= cand.brier_score <= 1.0
            assert cand.latency_ms_per_sample >= 0.0
            assert 0.0 <= cand.recall_at_top_20_pct <= 1.0

        # Champion model must be selected and saved
        assert report.selected_champion_model != ""
        model_file = os.path.join(tmp_dir, "champion_defect_model.joblib")
        assert os.path.exists(model_file)

        report_file = os.path.join(tmp_dir, "benchmark_report.json")
        assert os.path.exists(report_file)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_inference_adapter_and_safe_fallback():
    """Verify model inference with latency measurement and deterministic fallback (M4-10)."""
    tmp_dir = tempfile.mkdtemp(prefix="atip_ml_inf_")
    try:
        # 1. Train a model in tmp_dir
        X, y, metadata = DatasetBuilder.generate_curated_benchmark_dataset(sample_count=200, random_seed=99)
        (X_train, y_train), (X_val, y_val), (X_test, y_test), manifest = (
            DatasetBuilder.create_leakage_free_splits(X, y, metadata)
        )
        benchmarker = MultiModelBenchmarker(random_seed=99)
        benchmarker.run_benchmark(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            manifest_id=manifest.manifest_id,
            artifacts_dir=tmp_dir,
        )

        model_path = os.path.join(tmp_dir, "champion_defect_model.joblib")
        adapter = DefectPredictionInferenceAdapter(
            model_artifact_path=model_path,
            is_approved_for_production=True,
        )
        assert adapter.is_ml_active
        assert "ml-" in adapter.active_model_version

        # Predict with ML
        prob, version, lat = adapter.predict_file_defect_risk(
            cyclomatic=25, maintainability_index=45.0, loc=500, lines_changed=200, churn_count=8, direct_dependents=10
        )
        assert 0.0 <= prob <= 1.0
        assert lat >= 0.0
        assert version == adapter.active_model_version

        # 2. Test Safe Fallback when ML is unapproved / disabled
        adapter_unapproved = DefectPredictionInferenceAdapter(
            model_artifact_path=model_path,
            is_approved_for_production=False,  # Unapproved by human gate
        )
        assert not adapter_unapproved.is_ml_active
        assert adapter_unapproved.active_model_version == "deterministic-v1.0.0"

        prob_fallback, ver_fallback, _ = adapter_unapproved.predict_file_defect_risk(cyclomatic=25)
        assert ver_fallback == "deterministic-v1.0.0"
        assert 0.0 <= prob_fallback <= 1.0

        # 3. Test Safe Fallback when model file does not exist
        adapter_missing = DefectPredictionInferenceAdapter(
            model_artifact_path="/nonexistent/model.joblib",
        )
        assert not adapter_missing.is_ml_active
        prob_miss, ver_miss, _ = adapter_missing.predict_file_defect_risk(cyclomatic=5)
        assert ver_miss == "deterministic-v1.0.0"

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
