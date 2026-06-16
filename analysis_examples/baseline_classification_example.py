"""
Baseline classification example for EEG-based workload decoding.

This script provides a sanitized and self-contained example of the
classification logic used in the EEG workload project.

Main goals:
- demonstrate a leakage-aware machine-learning pipeline;
- keep scaling inside the training pipeline;
- compare Logistic Regression and shrinkage LDA;
- optionally evaluate leave-one-subject-out generalization.

No participant data are included. If no input CSV is provided, the script
generates synthetic feature data for demonstration purposes.

Expected input CSV format, if using real features:
- one row per EEG window;
- numeric feature columns;
- one label column, for example: label, workload_label, condition;
- optional subject column, for example: subject_id.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import LeaveOneGroupOut, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


RANDOM_STATE = 42

ELECTRODES = ["Fz", "C3", "Cz", "C4", "Pz", "PO7", "POz", "PO8"]
BANDS = ["delta", "theta", "alpha", "beta"]


def generate_synthetic_feature_table(
    n_subjects: int = 15,
    windows_per_condition: int = 12,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Generate a synthetic EEG-feature table for demonstration purposes.

    The generated data mimic a binary workload problem:
    - low workload;
    - high workload.

    The synthetic high-workload condition has slightly increased theta/beta
    and reduced alpha activity, with subject-specific variability.
    """
    rng = np.random.default_rng(random_state)

    rows = []

    for subject_idx in range(1, n_subjects + 1):
        subject_id = f"S{subject_idx:02d}"
        subject_offset = rng.normal(loc=0.0, scale=0.25)

        for label in ["low", "high"]:
            for window_idx in range(windows_per_condition):
                row = {
                    "subject_id": subject_id,
                    "window_id": window_idx,
                    "label": label,
                }

                for electrode in ELECTRODES:
                    for band in BANDS:
                        value = rng.normal(loc=0.0, scale=0.35)
                        value += subject_offset

                        if label == "high":
                            if band == "theta":
                                value += 0.45
                            elif band == "alpha":
                                value -= 0.35
                            elif band == "beta":
                                value += 0.25

                        row[f"{electrode}_{band}_logpower"] = value

                    theta = row[f"{electrode}_theta_logpower"]
                    alpha = row[f"{electrode}_alpha_logpower"]
                    beta = row[f"{electrode}_beta_logpower"]

                    theta_power = np.exp(theta)
                    alpha_power = np.exp(alpha)
                    beta_power = np.exp(beta)

                    row[f"{electrode}_theta_alpha_ratio"] = theta_power / (
                        alpha_power + 1e-12
                    )
                    row[f"{electrode}_alpha_theta_ratio"] = alpha_power / (
                        theta_power + 1e-12
                    )
                    row[f"{electrode}_engagement_index"] = beta_power / (
                        alpha_power + theta_power + 1e-12
                    )

                rows.append(row)

    return pd.DataFrame(rows)


def get_feature_columns(
    df: pd.DataFrame,
    label_col: str,
    group_col: str | None = None,
) -> list[str]:
    """
    Select numeric feature columns while excluding labels and identifiers.
    """
    excluded_columns = {label_col}

    if group_col is not None:
        excluded_columns.add(group_col)

    excluded_columns.update(
        {
            "window_id",
            "window_start_sample",
            "window_end_sample",
            "window_start_seconds",
            "window_end_seconds",
        }
    )

    feature_columns = []

    for column in df.columns:
        if column in excluded_columns:
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            feature_columns.append(column)

    if not feature_columns:
        raise ValueError("No numeric feature columns found.")

    return feature_columns


def build_models() -> dict[str, Pipeline]:
    """
    Build classification models using leakage-aware sklearn pipelines.

    StandardScaler is fitted only on training data inside each pipeline.
    """
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "shrinkage_lda": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LinearDiscriminantAnalysis(
                        solver="lsqr",
                        shrinkage="auto",
                    ),
                ),
            ]
        ),
    }


def print_metrics(
    title: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> None:
    """
    Print standard classification metrics.
    """
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    print(f"Accuracy:          {accuracy_score(y_true, y_pred):.3f}")
    print(f"Balanced accuracy: {balanced_accuracy_score(y_true, y_pred):.3f}")
    print(f"Macro F1-score:    {f1_score(y_true, y_pred, average='macro'):.3f}")

    print("\nConfusion matrix:")
    print(confusion_matrix(y_true, y_pred))

    print("\nClassification report:")
    print(classification_report(y_true, y_pred))


def evaluate_holdout_split(
    df: pd.DataFrame,
    feature_columns: list[str],
    label_col: str,
    test_size: float = 0.30,
) -> None:
    """
    Evaluate models using a stratified train/test split.

    This is a simple baseline evaluation. Scaling is fitted only on the
    training split through the sklearn Pipeline.
    """
    X = df[feature_columns].to_numpy(dtype=float)
    y = df[label_col].to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    models = build_models()

    for model_name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        print_metrics(
            title=f"Holdout evaluation - {model_name}",
            y_true=y_test,
            y_pred=y_pred,
        )


def evaluate_leave_one_subject_out(
    df: pd.DataFrame,
    feature_columns: list[str],
    label_col: str,
    group_col: str,
) -> None:
    """
    Evaluate models with leave-one-subject-out validation.

    In each fold, all windows from one subject are kept for testing and all
    other subjects are used for training.
    """
    X = df[feature_columns].to_numpy(dtype=float)
    y = df[label_col].to_numpy()
    groups = df[group_col].to_numpy()

    unique_groups = np.unique(groups)

    if len(unique_groups) < 2:
        print("\nSkipping LOSO evaluation: at least two subjects are required.")
        return

    logo = LeaveOneGroupOut()
    models = build_models()

    for model_name, model in models.items():
        all_true = []
        all_pred = []

        print("\n" + "-" * 80)
        print(f"Running LOSO evaluation - {model_name}")
        print("-" * 80)

        for train_idx, test_idx in logo.split(X, y, groups):
            test_subject = np.unique(groups[test_idx])[0]

            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            fold_acc = accuracy_score(y_test, y_pred)
            print(f"Left-out subject {test_subject}: accuracy = {fold_acc:.3f}")

            all_true.extend(y_test)
            all_pred.extend(y_pred)

        print_metrics(
            title=f"Leave-one-subject-out evaluation - {model_name}",
            y_true=np.asarray(all_true),
            y_pred=np.asarray(all_pred),
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baseline classification example for EEG workload features."
    )

    parser.add_argument(
        "--input_csv",
        type=str,
        default=None,
        help="Optional path to a CSV feature table.",
    )

    parser.add_argument(
        "--label_col",
        type=str,
        default="label",
        help="Name of the label column.",
    )

    parser.add_argument(
        "--group_col",
        type=str,
        default="subject_id",
        help="Name of the subject/group column for LOSO evaluation.",
    )

    parser.add_argument(
        "--skip_loso",
        action="store_true",
        help="Skip leave-one-subject-out evaluation.",
    )

    args = parser.parse_args()

    if args.input_csv is None:
        print("No input CSV provided. Generating synthetic feature data.")
        df = generate_synthetic_feature_table()
    else:
        input_path = Path(args.input_csv)

        if not input_path.exists():
            raise FileNotFoundError(f"Input CSV not found: {input_path}")

        df = pd.read_csv(input_path)

    if args.label_col not in df.columns:
        raise ValueError(
            f"Label column '{args.label_col}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    group_col = args.group_col if args.group_col in df.columns else None

    feature_columns = get_feature_columns(
        df=df,
        label_col=args.label_col,
        group_col=group_col,
    )

    print(f"Loaded table shape: {df.shape}")
    print(f"Number of features: {len(feature_columns)}")
    print(f"Label column: {args.label_col}")

    if group_col is not None:
        print(f"Group column: {group_col}")
    else:
        print("No valid group column found. LOSO evaluation will be skipped.")

    evaluate_holdout_split(
        df=df,
        feature_columns=feature_columns,
        label_col=args.label_col,
    )

    if not args.skip_loso and group_col is not None:
        evaluate_leave_one_subject_out(
            df=df,
            feature_columns=feature_columns,
            label_col=args.label_col,
            group_col=group_col,
        )


if __name__ == "__main__":
    main()
