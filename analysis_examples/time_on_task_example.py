"""
Time-on-task analysis example for EEG-based workload studies.

This script provides a sanitized and self-contained example of how temporal
changes in EEG spectral features can be analyzed across task segments.

Main goals:
- summarize EEG features across temporal segments;
- normalize features within subject to reduce inter-subject variability;
- estimate temporal trends using Spearman correlation;
- compare early, middle and late task segments;
- generate simple output tables and plots.

No participant data are included. If no input CSV is provided, the script
generates synthetic feature data for demonstration purposes.

Expected input CSV format, if using real features:
    - one row per EEG window or segment;
    - subject_id column;
    - condition column;
    - segment_idx column, or window_start_seconds column;
    - numeric EEG feature columns.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal, spearmanr


RANDOM_STATE = 42

ID_COLUMNS = {
    "subject_id",
    "condition",
    "label",
    "session",
    "block",
    "segment_idx",
    "window_id",
    "window_start_sample",
    "window_end_sample",
    "window_start_seconds",
    "window_end_seconds",
    "phase",
}


def generate_synthetic_time_on_task_data(
    n_subjects: int = 15,
    n_segments: int = 6,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Generate synthetic feature data with a mild temporal drift.

    The synthetic data mimic a task in which theta and beta features tend to
    increase over time, while alpha tends to decrease, with subject-specific
    variability.
    """
    rng = np.random.default_rng(random_state)

    electrodes = ["Fz", "C3", "Cz", "C4", "Pz", "PO7", "POz", "PO8"]
    bands = ["theta", "alpha", "beta"]

    rows = []

    for subject_idx in range(1, n_subjects + 1):
        subject_id = f"S{subject_idx:02d}"
        subject_offset = rng.normal(loc=0.0, scale=0.4)

        for condition in ["low", "high"]:
            condition_offset = 0.35 if condition == "high" else 0.0

            for segment_idx in range(n_segments):
                normalized_time = segment_idx / max(n_segments - 1, 1)

                row = {
                    "subject_id": subject_id,
                    "condition": condition,
                    "segment_idx": segment_idx,
                }

                for electrode in electrodes:
                    for band in bands:
                        value = rng.normal(loc=0.0, scale=0.25)
                        value += subject_offset
                        value += condition_offset

                        if band == "theta":
                            value += 0.45 * normalized_time
                        elif band == "alpha":
                            value -= 0.35 * normalized_time
                        elif band == "beta":
                            value += 0.25 * normalized_time

                        row[f"{electrode}_{band}_logpower"] = value

                rows.append(row)

    return pd.DataFrame(rows)


def infer_segment_idx(df: pd.DataFrame, fs: int = 250, segment_seconds: int = 16) -> pd.DataFrame:
    """
    Ensure that a segment_idx column exists.

    If segment_idx is missing but window_start_seconds is available, segment_idx
    is inferred from time. Otherwise, an error is raised.
    """
    if "segment_idx" in df.columns:
        return df.copy()

    if "window_start_seconds" in df.columns:
        df = df.copy()
        df["segment_idx"] = (df["window_start_seconds"] // segment_seconds).astype(int)
        return df

    if "window_start_sample" in df.columns:
        df = df.copy()
        seconds = df["window_start_sample"] / fs
        df["segment_idx"] = (seconds // segment_seconds).astype(int)
        return df

    raise ValueError(
        "No segment_idx column found. Provide segment_idx, window_start_seconds "
        "or window_start_sample."
    )


def get_numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Select numeric feature columns, excluding identifiers and timing columns.
    """
    feature_columns = []

    for column in df.columns:
        if column in ID_COLUMNS:
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            feature_columns.append(column)

    if not feature_columns:
        raise ValueError("No numeric EEG feature columns found.")

    return feature_columns


def add_within_subject_zscores(
    df: pd.DataFrame,
    feature_columns: list[str],
    subject_col: str = "subject_id",
) -> tuple[pd.DataFrame, list[str]]:
    """
    Add within-subject z-scored versions of the selected features.

    This reduces inter-subject baseline differences before estimating temporal
    trends.
    """
    if subject_col not in df.columns:
        raise ValueError(f"Missing subject column: {subject_col}")

    df = df.copy()
    zscore_columns = []

    for feature in feature_columns:
        z_col = f"{feature}_z"
        zscore_columns.append(z_col)

        def zscore_subject(values: pd.Series) -> pd.Series:
            std = values.std(ddof=0)
            if std == 0 or np.isnan(std):
                return values * 0.0
            return (values - values.mean()) / std

        df[z_col] = df.groupby(subject_col)[feature].transform(zscore_subject)

    return df, zscore_columns


def assign_temporal_phase(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign early, middle and late labels based on segment index.
    """
    df = df.copy()

    max_segment = df["segment_idx"].max()
    if max_segment == 0:
        df["phase"] = "single"
        return df

    relative_position = df["segment_idx"] / max_segment

    conditions = [
        relative_position <= 1 / 3,
        (relative_position > 1 / 3) & (relative_position <= 2 / 3),
        relative_position > 2 / 3,
    ]

    choices = ["early", "middle", "late"]

    df["phase"] = np.select(conditions, choices, default="unknown")

    return df


def summarize_by_segment(
    df: pd.DataFrame,
    feature_columns: list[str],
    condition_col: str = "condition",
) -> pd.DataFrame:
    """
    Compute mean and standard error by condition and temporal segment.
    """
    group_cols = [condition_col, "segment_idx"]

    summary = (
        df.groupby(group_cols)[feature_columns]
        .agg(["mean", "sem"])
        .reset_index()
    )

    summary.columns = [
        "_".join(col).strip("_") if isinstance(col, tuple) else col
        for col in summary.columns
    ]

    return summary


def temporal_trend_tests(
    df: pd.DataFrame,
    feature_columns: list[str],
    condition_col: str = "condition",
) -> pd.DataFrame:
    """
    Estimate temporal monotonic trends using Spearman correlation.

    Correlation is computed between segment_idx and each feature, separately for
    each condition.
    """
    rows = []

    for condition, cond_df in df.groupby(condition_col):
        for feature in feature_columns:
            rho, p_value = spearmanr(cond_df["segment_idx"], cond_df[feature])

            rows.append(
                {
                    "condition": condition,
                    "feature": feature,
                    "spearman_rho": rho,
                    "p_value": p_value,
                    "n_samples": len(cond_df),
                }
            )

    return pd.DataFrame(rows).sort_values(["p_value", "feature"])


def early_middle_late_tests(
    df: pd.DataFrame,
    feature_columns: list[str],
    condition_col: str = "condition",
) -> pd.DataFrame:
    """
    Compare early, middle and late phases using Kruskal-Wallis tests.
    """
    rows = []

    valid_phases = ["early", "middle", "late"]

    for condition, cond_df in df.groupby(condition_col):
        for feature in feature_columns:
            samples = [
                cond_df.loc[cond_df["phase"] == phase, feature].dropna().to_numpy()
                for phase in valid_phases
            ]

            if any(len(sample) == 0 for sample in samples):
                continue

            statistic, p_value = kruskal(*samples)

            rows.append(
                {
                    "condition": condition,
                    "feature": feature,
                    "test": "Kruskal-Wallis",
                    "statistic": statistic,
                    "p_value": p_value,
                }
            )

    return pd.DataFrame(rows).sort_values(["p_value", "feature"])


def plot_feature_timecourse(
    df: pd.DataFrame,
    feature: str,
    output_path: Path,
    condition_col: str = "condition",
) -> None:
    """
    Plot the mean feature value across temporal segments for each condition.
    """
    plt.figure(figsize=(8, 5))

    for condition, cond_df in df.groupby(condition_col):
        segment_summary = (
            cond_df.groupby("segment_idx")[feature]
            .agg(["mean", "sem"])
            .reset_index()
        )

        plt.errorbar(
            segment_summary["segment_idx"],
            segment_summary["mean"],
            yerr=segment_summary["sem"],
            marker="o",
            label=str(condition),
        )

    plt.xlabel("Temporal segment")
    plt.ylabel(feature)
    plt.title(f"Time-on-task trend: {feature}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Time-on-task analysis example for EEG features."
    )

    parser.add_argument(
        "--input_csv",
        type=str,
        default=None,
        help="Optional path to a CSV feature table.",
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default="time_on_task_outputs",
        help="Directory where output tables and plots will be saved.",
    )

    parser.add_argument(
        "--condition_col",
        type=str,
        default="condition",
        help="Name of the condition column.",
    )

    parser.add_argument(
        "--subject_col",
        type=str,
        default="subject_id",
        help="Name of the subject column.",
    )

    parser.add_argument(
        "--plot_feature",
        type=str,
        default=None,
        help="Optional feature to plot. If omitted, the first z-scored feature is plotted.",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.input_csv is None:
        print("No input CSV provided. Generating synthetic time-on-task data.")
        df = generate_synthetic_time_on_task_data()
    else:
        input_path = Path(args.input_csv)

        if not input_path.exists():
            raise FileNotFoundError(f"Input CSV not found: {input_path}")

        df = pd.read_csv(input_path)

    if args.condition_col not in df.columns:
        raise ValueError(f"Missing condition column: {args.condition_col}")

    if args.subject_col not in df.columns:
        raise ValueError(f"Missing subject column: {args.subject_col}")

    df = infer_segment_idx(df)
    df = assign_temporal_phase(df)

    raw_feature_columns = get_numeric_feature_columns(df)

    df, zscore_columns = add_within_subject_zscores(
        df=df,
        feature_columns=raw_feature_columns,
        subject_col=args.subject_col,
    )

    summary = summarize_by_segment(
        df=df,
        feature_columns=zscore_columns,
        condition_col=args.condition_col,
    )

    trend_results = temporal_trend_tests(
        df=df,
        feature_columns=zscore_columns,
        condition_col=args.condition_col,
    )

    phase_results = early_middle_late_tests(
        df=df,
        feature_columns=zscore_columns,
        condition_col=args.condition_col,
    )

    summary_path = output_dir / "segment_summary.csv"
    trend_path = output_dir / "spearman_temporal_trends.csv"
    phase_path = output_dir / "early_middle_late_tests.csv"

    summary.to_csv(summary_path, index=False)
    trend_results.to_csv(trend_path, index=False)
    phase_results.to_csv(phase_path, index=False)

    feature_to_plot = args.plot_feature
    if feature_to_plot is None:
        feature_to_plot = zscore_columns[0]

    if feature_to_plot not in df.columns:
        raise ValueError(
            f"Feature '{feature_to_plot}' not found. "
            f"Available z-scored features include: {zscore_columns[:10]} ..."
        )

    plot_path = output_dir / f"{feature_to_plot}_timecourse.png"
    plot_feature_timecourse(
        df=df,
        feature=feature_to_plot,
        output_path=plot_path,
        condition_col=args.condition_col,
    )

    print(f"Loaded table shape: {df.shape}")
    print(f"Raw features: {len(raw_feature_columns)}")
    print(f"Z-scored features: {len(zscore_columns)}")
    print(f"Saved segment summary to: {summary_path}")
    print(f"Saved trend results to: {trend_path}")
    print(f"Saved phase results to: {phase_path}")
    print(f"Saved plot to: {plot_path}")

    print("\nTop temporal trends:")
    print(trend_results.head(10))


if __name__ == "__main__":
    main()
