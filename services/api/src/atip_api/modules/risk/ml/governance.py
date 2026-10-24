"""ML data governance, prediction target definition, feature schema, and leakage defense (M4-07)."""

from dataclasses import dataclass, field

FEATURE_SCHEMA_COLUMNS = [
    "cyclomatic_complexity",
    "maintainability_index",
    "lines_code",
    "lines_changed",
    "prior_churn_count",
    "direct_dependents",
    "transitive_dependents",
    "has_test_file",
    "prior_defect_count",
]


@dataclass(frozen=True)
class SupervisedTargetSpec:
    """Specification of the supervised prediction target and labeling policy."""

    target_name: str = "defect_introduced"
    target_type: str = "binary_classification"
    positive_label_definition: str = (
        "Commit introduced code that was subsequently identified, patched, or referenced in a "
        "verified defect-fix commit (SZZ heuristic algorithm)."
    )
    negative_label_definition: str = (
        "Commit introduced code with clean operational history across observation window "
        "without triggering subsequent defect-fix commits."
    )
    observation_window_days: int = 90
    uncertain_label_policy: str = (
        "Commits with ambiguous commit messages or within active 90-day observation window "
        "without fix commits are excluded from test sets to prevent false negative leakage."
    )


@dataclass(frozen=True)
class FeatureSchemaSpec:
    """Prediction-time feature schema guaranteeing zero future-data leakage."""

    columns: list[str] = field(default_factory=lambda: list(FEATURE_SCHEMA_COLUMNS))
    leakage_threats_and_safeguards: dict[str, str] = field(
        default_factory=lambda: {
            "future_commit_leakage": "Features are strictly computed looking backward up to commit timestamp.",
            "test_run_outcome_leakage": "No post-commit CI test results or run logs are used as input features.",
            "temporal_split_leakage": "Chronological splitting ensures training commits precede test commits.",
            "repository_held_out_leakage": "Whole-repository splits test generalization to unseen architectures.",
            "scaler_data_leakage": "Feature scaling and imputation transformers are fit exclusively on train set.",
            "cross_tenant_leakage": "Private tenant source code is default-deny and excluded from shared training.",
        }
    )


def validate_tenant_consent_for_training(org_id: str, consent_registry: dict[str, bool]) -> bool:
    """
    Verifies explicit tenant consent before including repository data in ML training sets.
    Returns False by default for private tenants (SECURITY.md compliance).
    """
    return consent_registry.get(org_id, False)
