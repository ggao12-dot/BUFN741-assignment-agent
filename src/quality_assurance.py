from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_DIR = PROJECT_ROOT / "validation" / "artifacts"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLE_DIR = PROJECT_ROOT / "output" / "tables"
FIGURE_DIR = PROJECT_ROOT / "output" / "figures"

ACQUISITION_ARTIFACT = (
    ARTIFACT_DIR / "data_acquisition.json"
)

VALIDATION_ARTIFACT = (
    ARTIFACT_DIR / "data_validation.json"
)

PROCESSING_ARTIFACT = (
    ARTIFACT_DIR / "data_processing.json"
)

STATISTICAL_ARTIFACT = (
    ARTIFACT_DIR / "statistical_analysis.json"
)

FIGURE_ARTIFACT = (
    ARTIFACT_DIR / "figure_generation.json"
)

QA_ARTIFACT = (
    ARTIFACT_DIR / "quality_assurance.json"
)

ANALYSIS_DATA_FILE = (
    PROCESSED_DIR / "monthly_excess_returns.csv"
)

STATISTICS_FILE = (
    TABLE_DIR / "bkm_statistics_all_samples.csv"
)


EXPECTED_ASSETS = 5
EXPECTED_SAMPLES = 4
EXPECTED_STATISTIC_ROWS = 20
EXPECTED_FIGURES = 11


# =========================================================
# Utilities
# =========================================================

def load_json(path: Path) -> dict:
    """Load a JSON artifact."""

    if not path.is_file():
        raise FileNotFoundError(
            f"Required artifact missing: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def read_csv(path: Path) -> pd.DataFrame:
    """Read a required CSV file."""

    if not path.is_file():
        raise FileNotFoundError(
            f"Required file missing: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )

    return pd.read_csv(path)


def artifact_passed(
    artifact: dict,
) -> bool:

    return (
        artifact.get("status")
        == "passed"
    )


# =========================================================
# Artifact checks
# =========================================================

def check_stage_artifact_statuses(
    artifacts: dict[str, dict],
) -> tuple[list[str], list[str]]:

    errors = []
    warnings = []

    for name, artifact in artifacts.items():

        status = artifact.get(
            "status"
        )

        if status != "passed":
            errors.append(
                f"{name} artifact status is "
                f"{status!r}, not 'passed'."
            )

    return errors, warnings


# =========================================================
# Analysis dataset QA
# =========================================================

def check_analysis_dataset(
    df: pd.DataFrame,
) -> tuple[list[str], list[str], dict]:

    errors = []
    warnings = []

    required_columns = [
        "date",
        "SP500_excess",
        "Small_Growth_excess",
        "Small_Value_excess",
        "Big_Growth_excess",
        "Big_Value_excess",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(
            "Analysis dataset missing columns: "
            f"{missing_columns}"
        )

        return errors, warnings, {}

    periods = pd.PeriodIndex(
        df["date"],
        freq="M",
    )

    if periods.duplicated().any():
        errors.append(
            "Analysis dataset contains duplicate months."
        )

    if not periods.is_monotonic_increasing:
        errors.append(
            "Analysis dataset dates are not sorted."
        )

    excess_columns = required_columns[1:]

    missing_counts = {
        column: int(
            df[column].isna().sum()
        )
        for column in excess_columns
    }

    if any(
        count > 0
        for count in missing_counts.values()
    ):
        warnings.append(
            "Analysis dataset contains missing "
            "excess-return observations."
        )

    metadata = {
        "rows": int(
            len(df)
        ),
        "first_month": (
            str(periods.min())
            if len(periods) > 0
            else None
        ),
        "last_month": (
            str(periods.max())
            if len(periods) > 0
            else None
        ),
        "missing_values": (
            missing_counts
        ),
    }

    return (
        errors,
        warnings,
        metadata,
    )


# =========================================================
# Cross-stage sample consistency
# =========================================================

def check_sample_consistency(
    validation_artifact: dict,
    processing_artifact: dict,
    figure_artifact: dict,
    dataset_metadata: dict,
) -> tuple[list[str], list[str]]:

    errors = []
    warnings = []

    validation_sample = (
        validation_artifact.get(
            "common_sample",
            {},
        )
    )

    validation_start = (
        validation_sample.get(
            "first_month"
        )
    )

    validation_end = (
        validation_sample.get(
            "last_month"
        )
    )

    validation_rows = (
        validation_sample.get(
            "rows"
        )
    )

    processing_start = (
        processing_artifact.get(
            "first_month"
        )
    )

    processing_end = (
        processing_artifact.get(
            "last_month"
        )
    )

    processing_rows = (
        processing_artifact.get(
            "observations"
        )
    )

    figure_sample = (
        figure_artifact.get(
            "sample",
            {},
        )
    )

    figure_start = (
        figure_sample.get(
            "first_month"
        )
    )

    figure_end = (
        figure_sample.get(
            "last_month"
        )
    )

    figure_rows = (
        figure_sample.get(
            "rows"
        )
    )

    dataset_start = (
        dataset_metadata.get(
            "first_month"
        )
    )

    dataset_end = (
        dataset_metadata.get(
            "last_month"
        )
    )

    dataset_rows = (
        dataset_metadata.get(
            "rows"
        )
    )

    start_values = {
        validation_start,
        processing_start,
        figure_start,
        dataset_start,
    }

    start_values.discard(None)

    if len(start_values) > 1:
        errors.append(
            "Start-month inconsistency across "
            f"pipeline stages: {sorted(start_values)}"
        )

    end_values = {
        validation_end,
        processing_end,
        figure_end,
        dataset_end,
    }

    end_values.discard(None)

    if len(end_values) > 1:
        errors.append(
            "End-month inconsistency across "
            f"pipeline stages: {sorted(end_values)}"
        )

    row_values = {
        validation_rows,
        processing_rows,
        figure_rows,
        dataset_rows,
    }

    row_values.discard(None)

    if len(row_values) > 1:
        errors.append(
            "Observation-count inconsistency across "
            f"pipeline stages: {sorted(row_values)}"
        )

    return errors, warnings


# =========================================================
# Statistical-output QA
# =========================================================

def check_statistics_table(
    results: pd.DataFrame,
) -> tuple[list[str], list[str], dict]:

    errors = []
    warnings = []

    if len(results) != EXPECTED_STATISTIC_ROWS:
        errors.append(
            f"Expected {EXPECTED_STATISTIC_ROWS} "
            f"statistical rows, found {len(results)}."
        )

    if "Asset" not in results.columns:
        errors.append(
            "Statistics table has no Asset column."
        )

    if "Sample" not in results.columns:
        errors.append(
            "Statistics table has no Sample column."
        )

    if errors:
        return errors, warnings, {}

    asset_count = int(
        results[
            "Asset"
        ].nunique()
    )

    sample_count = int(
        results[
            "Sample"
        ].nunique()
    )

    if asset_count != EXPECTED_ASSETS:
        errors.append(
            f"Expected {EXPECTED_ASSETS} assets, "
            f"found {asset_count}."
        )

    if sample_count != EXPECTED_SAMPLES:
        errors.append(
            f"Expected {EXPECTED_SAMPLES} samples, "
            f"found {sample_count}."
        )

    required_statistics = [
        "Mean_Excess_Annualized",
        "Std_Annualized",
        "Sharpe_Ratio",
        "Lower_Partial_Std_Annualized",
        "Skewness",
        "Excess_Kurtosis",
        "Empirical_VaR_1pct_Monthly",
        "Normal_VaR_1pct_Monthly",
        "Pct_Below_Mean_Minus_3SD",
        "Expected_Shortfall_1pct_Monthly",
    ]

    missing_statistics = [
        column
        for column
        in required_statistics
        if column not in results.columns
    ]

    if missing_statistics:
        errors.append(
            "Missing statistical columns: "
            f"{missing_statistics}"
        )

        return errors, warnings, {}

    if (
        results[
            required_statistics
        ]
        .isna()
        .any()
        .any()
    ):
        warnings.append(
            "One or more reported statistics are missing."
        )

    invalid_std = results[
        results[
            "Std_Annualized"
        ] < 0
    ]

    if not invalid_std.empty:
        errors.append(
            "Negative standard deviation detected."
        )

    invalid_lpsd = results[
        results[
            "Lower_Partial_Std_Annualized"
        ] < 0
    ]

    if not invalid_lpsd.empty:
        errors.append(
            "Negative lower partial standard deviation detected."
        )

    invalid_es = results[
        results[
            "Expected_Shortfall_1pct_Monthly"
        ]
        >
        results[
            "Empirical_VaR_1pct_Monthly"
        ]
        + 1e-12
    ]

    if not invalid_es.empty:
        errors.append(
            "Expected shortfall is above empirical VaR "
            "for one or more asset-sample rows."
        )

    metadata = {
        "rows": int(
            len(results)
        ),
        "asset_count": (
            asset_count
        ),
        "sample_count": (
            sample_count
        ),
    }

    return (
        errors,
        warnings,
        metadata,
    )


# =========================================================
# Fixed-period count QA
# =========================================================

def check_fixed_sample_counts(
    results: pd.DataFrame,
) -> tuple[list[str], list[str]]:

    errors = []
    warnings = []

    expected_counts = {
        "1990_2000": 132,
        "2001_2010": 120,
    }

    for sample_name, expected in (
        expected_counts.items()
    ):

        subset = results[
            results["Sample"]
            == sample_name
        ]

        if subset.empty:
            errors.append(
                f"Missing sample: {sample_name}"
            )
            continue

        counts = set(
            subset[
                "Usable_Months"
            ].astype(int)
        )

        if counts != {expected}:
            errors.append(
                f"{sample_name} should contain "
                f"{expected} usable months for each asset; "
                f"found {sorted(counts)}."
            )

    return errors, warnings


# =========================================================
# Figure QA
# =========================================================

def check_figures(
    figure_artifact: dict,
) -> tuple[list[str], list[str], dict]:

    errors = []
    warnings = []

    figures = (
        figure_artifact.get(
            "figures",
            [],
        )
    )

    if len(figures) != EXPECTED_FIGURES:
        errors.append(
            f"Expected {EXPECTED_FIGURES} figures, "
            f"artifact reports {len(figures)}."
        )

    existing = 0

    for figure in figures:

        relative_path = (
            figure.get(
                "file"
            )
        )

        if not relative_path:
            errors.append(
                "Figure artifact contains an entry "
                "with no file path."
            )
            continue

        path = (
            PROJECT_ROOT
            / relative_path
        )

        if not path.is_file():
            errors.append(
                f"Figure missing: {relative_path}"
            )
            continue

        existing += 1

        if path.stat().st_size == 0:
            errors.append(
                f"Figure is empty: {relative_path}"
            )

    metadata = {
        "artifact_figure_count": (
            len(figures)
        ),
        "existing_figure_count": (
            existing
        ),
    }

    return (
        errors,
        warnings,
        metadata,
    )


# =========================================================
# Statistical artifact consistency
# =========================================================

def check_statistical_artifact(
    artifact: dict,
    table_metadata: dict,
) -> tuple[list[str], list[str]]:

    errors = []
    warnings = []

    artifact_rows = artifact.get(
        "actual_result_rows"
    )

    table_rows = (
        table_metadata.get(
            "rows"
        )
    )

    if (
        artifact_rows is not None
        and table_rows is not None
        and artifact_rows != table_rows
    ):
        errors.append(
            "Statistical artifact row count does not "
            "match actual statistics table."
        )

    artifact_assets = artifact.get(
        "asset_count"
    )

    table_assets = (
        table_metadata.get(
            "asset_count"
        )
    )

    if (
        artifact_assets is not None
        and table_assets is not None
        and artifact_assets != table_assets
    ):
        errors.append(
            "Statistical artifact asset count does not "
            "match statistics table."
        )

    return errors, warnings


# =========================================================
# QA artifact
# =========================================================

def write_qa_artifact(
    artifact: dict,
) -> None:

    with QA_ARTIFACT.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            artifact,
            file,
            indent=2,
        )

        file.write("\n")


# =========================================================
# Human-readable summary
# =========================================================

def print_summary(
    artifact: dict,
) -> None:

    print()
    print("=" * 72)
    print("BUFN741 QUALITY ASSURANCE")
    print("=" * 72)

    print()
    print(
        f"Status: {artifact['status'].upper()}"
    )

    print()
    print("Checks:")

    for check_name, result in artifact[
        "checks"
    ].items():

        print(
            f"  {check_name}: "
            f"{result['status'].upper()}"
        )

    if artifact["warnings"]:

        print()
        print("Warnings:")

        for warning in artifact[
            "warnings"
        ]:

            print(
                f"  - {warning}"
            )

    if artifact["errors"]:

        print()
        print("Errors:")

        for error in artifact[
            "errors"
        ]:

            print(
                f"  - {error}"
            )

    print()
    print("Evidence artifact:")
    print(
        "  validation/artifacts/"
        "quality_assurance.json"
    )

    print("=" * 72)


# =========================================================
# Main
# =========================================================

def main() -> int:

    errors = []
    warnings = []
    checks = {}

    try:

        artifacts = {
            "data_acquisition": (
                load_json(
                    ACQUISITION_ARTIFACT
                )
            ),
            "data_validation": (
                load_json(
                    VALIDATION_ARTIFACT
                )
            ),
            "data_processing": (
                load_json(
                    PROCESSING_ARTIFACT
                )
            ),
            "statistical_analysis": (
                load_json(
                    STATISTICAL_ARTIFACT
                )
            ),
            "figure_generation": (
                load_json(
                    FIGURE_ARTIFACT
                )
            ),
        }

        # -------------------------------------------------
        # 1. Stage artifact statuses
        # -------------------------------------------------

        e, w = (
            check_stage_artifact_statuses(
                artifacts
            )
        )

        errors.extend(e)
        warnings.extend(w)

        checks[
            "stage_artifact_statuses"
        ] = {
            "status": (
                "passed"
                if not e
                else "failed"
            )
        }

        # -------------------------------------------------
        # 2. Analysis dataset
        # -------------------------------------------------

        analysis_df = read_csv(
            ANALYSIS_DATA_FILE
        )

        e, w, dataset_metadata = (
            check_analysis_dataset(
                analysis_df
            )
        )

        errors.extend(e)
        warnings.extend(w)

        checks[
            "analysis_dataset"
        ] = {
            "status": (
                "passed"
                if not e
                else "failed"
            ),
            "metadata": (
                dataset_metadata
            ),
        }

        # -------------------------------------------------
        # 3. Cross-stage sample consistency
        # -------------------------------------------------

        e, w = (
            check_sample_consistency(
                artifacts[
                    "data_validation"
                ],
                artifacts[
                    "data_processing"
                ],
                artifacts[
                    "figure_generation"
                ],
                dataset_metadata,
            )
        )

        errors.extend(e)
        warnings.extend(w)

        checks[
            "sample_consistency"
        ] = {
            "status": (
                "passed"
                if not e
                else "failed"
            )
        }

        # -------------------------------------------------
        # 4. Statistical table
        # -------------------------------------------------

        statistics_df = read_csv(
            STATISTICS_FILE
        )

        e, w, statistics_metadata = (
            check_statistics_table(
                statistics_df
            )
        )

        errors.extend(e)
        warnings.extend(w)

        checks[
            "statistics_table"
        ] = {
            "status": (
                "passed"
                if not e
                else "failed"
            ),
            "metadata": (
                statistics_metadata
            ),
        }

        # -------------------------------------------------
        # 5. Fixed-period observation counts
        # -------------------------------------------------

        e, w = (
            check_fixed_sample_counts(
                statistics_df
            )
        )

        errors.extend(e)
        warnings.extend(w)

        checks[
            "fixed_sample_counts"
        ] = {
            "status": (
                "passed"
                if not e
                else "failed"
            )
        }

        # -------------------------------------------------
        # 6. Statistical artifact/table consistency
        # -------------------------------------------------

        e, w = (
            check_statistical_artifact(
                artifacts[
                    "statistical_analysis"
                ],
                statistics_metadata,
            )
        )

        errors.extend(e)
        warnings.extend(w)

        checks[
            "statistical_artifact_consistency"
        ] = {
            "status": (
                "passed"
                if not e
                else "failed"
            )
        }

        # -------------------------------------------------
        # 7. Figures
        # -------------------------------------------------

        e, w, figure_metadata = (
            check_figures(
                artifacts[
                    "figure_generation"
                ]
            )
        )

        errors.extend(e)
        warnings.extend(w)

        checks[
            "figures"
        ] = {
            "status": (
                "passed"
                if not e
                else "failed"
            ),
            "metadata": (
                figure_metadata
            ),
        }

        # -------------------------------------------------
        # Final QA verdict
        # -------------------------------------------------

        status = (
            "passed"
            if len(errors) == 0
            else "failed"
        )

        artifact = {
            "stage": (
                "quality_assurance"
            ),
            "status": status,
            "artifact_version": "1.0",
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
        }

        write_qa_artifact(
            artifact
        )

        print_summary(
            artifact
        )

        return (
            0
            if status == "passed"
            else 1
        )

    except Exception as exc:

        print()
        print("=" * 72)
        print("QUALITY ASSURANCE FAILED")
        print("=" * 72)

        print()
        print(type(exc).__name__)
        print(str(exc))
        print()

        if QA_ARTIFACT.exists():
            QA_ARTIFACT.unlink()

        return 1


if __name__ == "__main__":
    sys.exit(main())