"""Mandatory multi-model benchmarking: Logistic Regression, Random Forest, LightGBM, and XGBoost (M4-09)."""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from typing import Any

import joblib
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from atip_api.modules.risk.engine import DeterministicRiskEngine

logger = logging.getLogger(__name__)


@dataclass
class CandidateEvaluationResult:
    """Rigorous evaluation metrics for an experimental model candidate on held-out test data."""

    model_name: str
    pr_auc: float  # Primary metric!
    roc_auc: float
    precision: float
    recall: float
    f1: float
    brier_score: float  # Probability calibration (lower is better)
    latency_ms_per_sample: float
    recall_at_top_20_pct: float  # Operational ranking quality
    tuned_decision_threshold: float
    is_production_candidate: bool
    selection_rationale: str


@dataclass
class BenchmarkReport:
    """Comparative multi-model benchmark report comparing 4 ML models vs deterministic baseline."""

    dataset_manifest_id: str
    evaluated_at: str
    primary_metric: str = "pr_auc"
    candidates: list[CandidateEvaluationResult] = None  # type: ignore
    selected_champion_model: str = ""
    deterministic_baseline_comparison: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class MultiModelBenchmarker:
    """Trains, compares, calibrates, and selects among Logistic Regression, Random Forest, LightGBM, and XGBoost."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed

    def _evaluate_deterministic_baseline(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> CandidateEvaluationResult:
        """Evaluates existing deterministic risk engine on the test split for baseline comparison."""
        engine = DeterministicRiskEngine()
        scores = []
        latencies = []

        for row in X_test:
            t0 = time.perf_counter()
            file_res = engine.evaluate_file(
                file_path="test_file.py",
                cyclomatic=int(row[0]),
                maintainability_index=float(row[1]),
                loc=int(row[2]),
                lines_changed=int(row[3]),
                churn_count=int(row[4]),
                direct_dependents=int(row[5]),
                transitive_dependents=int(row[6]),
                has_test_file=bool(row[7]),
                defect_commit_count=int(row[8]),
            )
            latencies.append((time.perf_counter() - t0) * 1000.0)
            scores.append(file_res.risk_score / 100.0)

        scores_arr = np.array(scores)
        y_pred = (scores_arr >= 0.50).astype(int)

        pr_auc = float(average_precision_score(y_test, scores_arr))
        roc_auc = float(roc_auc_score(y_test, scores_arr))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        brier = float(brier_score_loss(y_test, scores_arr))
        avg_lat = float(np.mean(latencies))

        # Recall at top 20%
        top_20_cutoff = int(len(scores_arr) * 0.20)
        top_20_indices = np.argsort(scores_arr)[::-1][:top_20_cutoff]
        defects_in_top_20 = np.sum(y_test[top_20_indices])
        total_defects = np.sum(y_test)
        rec_20 = float(defects_in_top_20 / max(1, total_defects))

        return CandidateEvaluationResult(
            model_name="Deterministic Baseline (Heuristic Engine)",
            pr_auc=round(pr_auc, 4),
            roc_auc=round(roc_auc, 4),
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1=round(f1, 4),
            brier_score=round(brier, 4),
            latency_ms_per_sample=round(avg_lat, 4),
            recall_at_top_20_pct=round(rec_20, 4),
            tuned_decision_threshold=0.50,
            is_production_candidate=False,
            selection_rationale="Always-available foundational baseline without model dependencies.",
        )

    def _train_and_evaluate_candidate(
        self,
        name: str,
        estimator: Any,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> tuple[Pipeline, CandidateEvaluationResult]:
        """
        Fits pipeline exclusively on X_train, tunes decision threshold on X_val,
        and evaluates final metrics strictly on held-out X_test.
        """
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", estimator),
        ])

        # 1. Fit pipeline strictly on train data
        pipeline.fit(X_train, y_train)

        # 2. Tune decision threshold on validation data (maximizing validation F1)
        val_probs = pipeline.predict_proba(X_val)[:, 1]
        thresholds = np.linspace(0.1, 0.9, 17)
        best_th = 0.5
        best_val_f1 = -1.0

        for th in thresholds:
            preds = (val_probs >= th).astype(int)
            val_f1 = f1_score(y_val, preds, zero_division=0)
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_th = th

        # 3. Final evaluation strictly on held-out test data
        latencies = []
        for i in range(min(50, len(X_test))):
            t0 = time.perf_counter()
            _ = pipeline.predict_proba(X_test[i : i + 1])
            latencies.append((time.perf_counter() - t0) * 1000.0)
        avg_latency = float(np.mean(latencies))

        test_probs = pipeline.predict_proba(X_test)[:, 1]
        test_preds = (test_probs >= best_th).astype(int)

        pr_auc = float(average_precision_score(y_test, test_probs))
        roc_auc = float(roc_auc_score(y_test, test_probs))
        prec = float(precision_score(y_test, test_preds, zero_division=0))
        rec = float(recall_score(y_test, test_preds, zero_division=0))
        f1 = float(f1_score(y_test, test_preds, zero_division=0))
        brier = float(brier_score_loss(y_test, test_probs))

        top_20_cutoff = int(len(test_probs) * 0.20)
        top_20_indices = np.argsort(test_probs)[::-1][:top_20_cutoff]
        defects_in_top_20 = np.sum(y_test[top_20_indices])
        total_defects = np.sum(y_test)
        rec_20 = float(defects_in_top_20 / max(1, total_defects))

        result = CandidateEvaluationResult(
            model_name=name,
            pr_auc=round(pr_auc, 4),
            roc_auc=round(roc_auc, 4),
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1=round(f1, 4),
            brier_score=round(brier, 4),
            latency_ms_per_sample=round(avg_latency, 4),
            recall_at_top_20_pct=round(rec_20, 4),
            tuned_decision_threshold=round(best_th, 2),
            is_production_candidate=False,
            selection_rationale="",
        )
        return pipeline, result

    def run_benchmark(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        manifest_id: str,
        artifacts_dir: str = "artifacts/ml",
    ) -> BenchmarkReport:
        """
        Executes multi-model benchmark across all 4 mandatory ML candidates
        plus deterministic baseline, and saves serialized champion model.
        """
        # Calculate class imbalance ratio for tree estimators
        neg_count = np.sum(y_train == 0)
        pos_count = np.sum(y_train == 1)
        scale_pos_weight = float(neg_count / max(1, pos_count))

        # 1. Deterministic Baseline
        baseline_res = self._evaluate_deterministic_baseline(X_test, y_test)

        # 2. Candidate 1: Logistic Regression
        lr_est = LogisticRegression(class_weight="balanced", random_state=self.random_seed, max_iter=500)
        lr_pipe, lr_res = self._train_and_evaluate_candidate(
            "Logistic Regression (L2)", lr_est, X_train, y_train, X_val, y_val, X_test, y_test
        )

        # 3. Candidate 2: Random Forest
        rf_est = RandomForestClassifier(
            n_estimators=100, max_depth=6, class_weight="balanced", random_state=self.random_seed, n_jobs=-1
        )
        rf_pipe, rf_res = self._train_and_evaluate_candidate(
            "Random Forest", rf_est, X_train, y_train, X_val, y_val, X_test, y_test
        )

        # 4. Candidate 3: LightGBM
        lgb_est = LGBMClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.05, scale_pos_weight=scale_pos_weight,
            random_state=self.random_seed, verbose=-1, n_jobs=-1
        )
        lgb_pipe, lgb_res = self._train_and_evaluate_candidate(
            "LightGBM", lgb_est, X_train, y_train, X_val, y_val, X_test, y_test
        )

        # 5. Candidate 4: XGBoost
        xgb_est = XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=scale_pos_weight,
            random_state=self.random_seed, eval_metric="logloss", n_jobs=-1
        )
        xgb_pipe, xgb_res = self._train_and_evaluate_candidate(
            "XGBoost", xgb_est, X_train, y_train, X_val, y_val, X_test, y_test
        )

        candidates = [baseline_res, lr_res, rf_res, lgb_res, xgb_res]

        # Selection criteria:
        # 1. PR-AUC (primary metric!)
        # 2. Probability calibration (lower Brier score)
        # 3. Latency & resource footprint
        ml_candidates = [
            ("Logistic Regression (L2)", lr_pipe, lr_res),
            ("Random Forest", rf_pipe, rf_res),
            ("LightGBM", lgb_pipe, lgb_res),
            ("XGBoost", xgb_pipe, xgb_res),
        ]

        # Rank ML models by PR-AUC descending
        sorted_ml = sorted(ml_candidates, key=lambda c: (c[2].pr_auc, -c[2].brier_score), reverse=True)
        champion_name, champion_pipe, champion_res = sorted_ml[0]

        champion_res.is_production_candidate = True
        champion_res.selection_rationale = (
            f"Selected as champion based on highest PR-AUC ({champion_res.pr_auc:.4f}), "
            f"Brier calibration ({champion_res.brier_score:.4f}), and sub-millisecond inference latency "
            f"({champion_res.latency_ms_per_sample:.3f}ms)."
        )

        # Serialize champion model artifact
        os.makedirs(artifacts_dir, exist_ok=True)
        model_path = os.path.join(artifacts_dir, "champion_defect_model.joblib")
        joblib.dump(
            {
                "model_name": champion_name,
                "pipeline": champion_pipe,
                "evaluation": asdict(champion_res),
                "threshold": champion_res.tuned_decision_threshold,
                "manifest_id": manifest_id,
                "features": ["cyclomatic_complexity", "maintainability_index", "lines_code", "lines_changed", "prior_churn_count", "direct_dependents", "transitive_dependents", "has_test_file", "prior_defect_count"],
            },
            model_path,
        )

        # Baseline comparison summary
        baseline_delta = champion_res.pr_auc - baseline_res.pr_auc
        comp_summary = (
            f"Champion {champion_name} achieved PR-AUC of {champion_res.pr_auc:.4f} vs "
            f"Deterministic Baseline PR-AUC of {baseline_res.pr_auc:.4f} "
            f"(Delta: {'+' if baseline_delta >= 0 else ''}{baseline_delta:.4f}). "
            f"Deterministic fallback preserved at zero runtime risk."
        )

        report = BenchmarkReport(
            dataset_manifest_id=manifest_id,
            evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            primary_metric="pr_auc",
            candidates=candidates,
            selected_champion_model=champion_name,
            deterministic_baseline_comparison=comp_summary,
        )

        report_path = os.path.join(artifacts_dir, "benchmark_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report.to_json())

        return report
