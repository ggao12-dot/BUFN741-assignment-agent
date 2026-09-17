from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLE_DIR = PROJECT_ROOT / "output" / "tables"
ARTIFACT_DIR = PROJECT_ROOT / "validation" / "artifacts"

INPUT_FILE = (
    PROCESSED_DIR / "monthly_excess_returns.csv"
)

LONG_OUTPUT_FILE = (
    TABLE_DIR / "bkm_statistics_all_samples.csv"
)

ARTIFACT_FILE = (
    ARTIFACT_DIR / "statistical_analysis.json"
)


# =========================================================
# Research design
# =========================================================

ASSETS = {
    "SP500": "SP500_excess",
    "Small_Growth": "Small_Growth_excess",
    "Small_Value": "Small_Value_excess",
    "Big_Growth": "Big_Growth_excess",
    "Big_Value": "Big_Value_excess",
}


SAMPLES = {
    "Full_History": {
        "start": None,
        "end": None,
    },
    "1990_2000": {
        "start": "1990-01",
        "end": "2000-12",
    },
    "2001_2010": {
        "start": "2001-01",
        "end": "2010-12",
    },
    "2011_Present": {
        "start": "2011-01",
        "end": None,
    },
}


Z_01 = -2.3263


# =========================================================
# Utilities
# =========================================================

def ensure_directories() -> None:
    TABLE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def read_analysis_data() -> pd.DataFrame:
    if not INPUT_FILE.is_file():
        raise FileNotFoundError(
            "Required file not found: "
            "data/processed/monthly_excess_returns.csv"
        )

    df = pd.read_csv(INPUT_FILE)

    required = [
        "date",
        *ASSETS.values(),
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Analysis dataset is missing columns: {missing}"
        )

    df["month"] = pd.PeriodIndex(
        df["date"],
        freq="M",
    )

    return df


# =========================================================
# Sample construction
# =========================================================

def select_sample(
    df: pd.DataFrame,
    start: str | None,
    end: str | None,
) -> pd.DataFrame:

    mask = pd.Series(
        True,
        index=df.index,
    )

    if start is not None:
        mask &= (
            df["month"]
            >= pd.Period(start, freq="M")
        )

    if end is not None:
        mask &= (
            df["month"]
            <= pd.Period(end, freq="M")
        )

    return (
        df.loc[mask]
        .copy()
        .sort_values("month")
        .reset_index(drop=True)
    )


# =========================================================
# Individual statistics
# =========================================================

def annualized_mean(
    series: pd.Series,
) -> float:
    """
    Annualized arithmetic mean excess return.

    Assignment definition:
        12 × monthly arithmetic mean
    """

    return float(
        12.0 * series.mean()
    )


def annualized_std(
    series: pd.Series,
) -> float:
    """
    Annualized sample standard deviation.

    Assignment definition:
        monthly sample SD × sqrt(12)
    """

    return float(
        series.std(ddof=1)
        * math.sqrt(12.0)
    )


def sharpe_ratio(
    series: pd.Series,
) -> float:

    ann_mean = annualized_mean(
        series
    )

    ann_std = annualized_std(
        series
    )

    if ann_std == 0:
        return float("nan")

    return float(
        ann_mean / ann_std
    )


def annualized_lower_partial_std(
    series: pd.Series,
) -> float:
    """
    Downside dispersion relative to the sample mean.

    Assignment definition:

        sqrt(
            average(
                (r - sample_mean)^2
                conditional on r < sample_mean
            )
        )
        × sqrt(12)
    """

    mean_return = series.mean()

    downside = series[
        series < mean_return
    ]

    if downside.empty:
        return float("nan")

    downside_variance = (
        (
            downside - mean_return
        ) ** 2
    ).mean()

    return float(
        math.sqrt(downside_variance)
        * math.sqrt(12.0)
    )


def sample_skewness(
    series: pd.Series,
) -> float:

    return float(
        series.skew()
    )


def excess_kurtosis(
    series: pd.Series,
) -> float:
    """
    Pandas Series.kurt() reports Fisher excess kurtosis:
        Normal distribution = 0
    """

    return float(
        series.kurt()
    )


def empirical_var_1pct(
    series: pd.Series,
) -> float:
    """
    Empirical 1st percentile of monthly excess returns.
    """

    return float(
        series.quantile(
            0.01,
            interpolation="linear",
        )
    )


def normal_var_1pct(
    series: pd.Series,
) -> float:
    """
    Normal-theory 1% VaR cutoff:

        mean + z_0.01 × monthly SD

    where z_0.01 ≈ -2.3263.
    """

    monthly_mean = series.mean()

    monthly_sd = series.std(
        ddof=1
    )

    return float(
        monthly_mean
        + Z_01 * monthly_sd
    )


def pct_below_mean_minus_3sd(
    series: pd.Series,
) -> float:

    mean_return = series.mean()

    monthly_sd = series.std(
        ddof=1
    )

    cutoff = (
        mean_return
        - 3.0 * monthly_sd
    )

    frequency = (
        series < cutoff
    ).mean()

    return float(
        100.0 * frequency
    )


def expected_shortfall_1pct(
    series: pd.Series,
) -> float:
    """
    Average monthly excess return at or below
    the empirical 1% VaR cutoff.
    """

    cutoff = empirical_var_1pct(
        series
    )

    tail = series[
        series <= cutoff
    ]

    if tail.empty:
        return float("nan")

    return float(
        tail.mean()
    )


# =========================================================
# Complete asset statistics
# =========================================================

def calculate_statistics(
    series: pd.Series,
) -> dict:

    clean = (
        pd.to_numeric(
            series,
            errors="coerce",
        )
        .dropna()
    )

    if len(clean) < 2:
        raise RuntimeError(
            "At least two usable observations are required."
        )

    return {
        "Mean_Excess_Annualized": (
            annualized_mean(clean)
        ),
        "Std_Annualized": (
            annualized_std(clean)
        ),
        "Sharpe_Ratio": (
            sharpe_ratio(clean)
        ),
        "Lower_Partial_Std_Annualized": (
            annualized_lower_partial_std(clean)
        ),
        "Skewness": (
            sample_skewness(clean)
        ),
        "Excess_Kurtosis": (
            excess_kurtosis(clean)
        ),
        "Empirical_VaR_1pct_Monthly": (
            empirical_var_1pct(clean)
        ),
        "Normal_VaR_1pct_Monthly": (
            normal_var_1pct(clean)
        ),
        "Pct_Below_Mean_Minus_3SD": (
            pct_below_mean_minus_3sd(clean)
        ),
        "Expected_Shortfall_1pct_Monthly": (
            expected_shortfall_1pct(clean)
        ),
    }


# =========================================================
# Full analysis
# =========================================================

def run_analysis(
    df: pd.DataFrame,
) -> pd.DataFrame:

    rows = []

    for sample_name, sample_rule in SAMPLES.items():

        sample_df = select_sample(
            df,
            sample_rule["start"],
            sample_rule["end"],
        )

        if sample_df.empty:
            raise RuntimeError(
                f"Sample contains no observations: "
                f"{sample_name}"
            )

        first_month = str(
            sample_df["month"].iloc[0]
        )

        last_month = str(
            sample_df["month"].iloc[-1]
        )

        for asset_name, column in ASSETS.items():

            clean = (
                pd.to_numeric(
                    sample_df[column],
                    errors="coerce",
                )
                .dropna()
            )

            stats = calculate_statistics(
                clean
            )

            row = {
                "Sample": sample_name,
                "Asset": asset_name,
                "Start_Month": first_month,
                "End_Month": last_month,
                "Usable_Months": int(
                    len(clean)
                ),
                **stats,
            }

            rows.append(row)

    return pd.DataFrame(rows)


# =========================================================
# Validation
# =========================================================

def validate_results(
    results: pd.DataFrame,
) -> tuple[list[str], list[str]]:

    errors = []
    warnings = []

    expected_rows = (
        len(ASSETS)
        * len(SAMPLES)
    )

    if len(results) != expected_rows:
        errors.append(
            f"Expected {expected_rows} asset-period rows, "
            f"found {len(results)}."
        )

    expected_pairs = {
        (sample, asset)
        for sample in SAMPLES
        for asset in ASSETS
    }

    actual_pairs = set(
        zip(
            results["Sample"],
            results["Asset"],
        )
    )

    missing_pairs = (
        expected_pairs
        - actual_pairs
    )

    if missing_pairs:
        errors.append(
            "Missing asset-period combinations: "
            f"{sorted(missing_pairs)}"
        )

    statistic_columns = [
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

    for column in statistic_columns:

        if results[column].isna().any():
            warnings.append(
                f"{column} contains one or more missing values."
            )

    # ES should generally be no greater than the empirical
    # VaR cutoff because it averages observations at or below it.
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
            "Expected shortfall exceeds empirical VaR "
            "for one or more rows."
        )

    invalid_sd = results[
        results["Std_Annualized"] < 0
    ]

    if not invalid_sd.empty:
        errors.append(
            "Negative annualized standard deviation detected."
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

    return errors, warnings


# =========================================================
# Output tables
# =========================================================

def save_combined_table(
    results: pd.DataFrame,
) -> None:

    results.to_csv(
        LONG_OUTPUT_FILE,
        index=False,
    )


def save_sample_tables(
    results: pd.DataFrame,
) -> list[str]:

    output_files = []

    for sample_name in SAMPLES:

        sample_table = (
            results[
                results["Sample"]
                == sample_name
            ]
            .copy()
            .reset_index(drop=True)
        )

        path = (
            TABLE_DIR
            / f"bkm_statistics_{sample_name}.csv"
        )

        sample_table.to_csv(
            path,
            index=False,
        )

        output_files.append(
            str(
                path.relative_to(
                    PROJECT_ROOT
                )
            )
        )

    return output_files


# =========================================================
# Evidence artifact
# =========================================================

def build_artifact(
    results: pd.DataFrame,
    errors: list[str],
    warnings: list[str],
    sample_files: list[str],
) -> dict:

    status = (
        "passed"
        if len(errors) == 0
        else "failed"
    )

    sample_metadata = {}

    for sample_name in SAMPLES:

        subset = results[
            results["Sample"]
            == sample_name
        ]

        sample_metadata[
            sample_name
        ] = {
            "start_month": (
                str(
                    subset[
                        "Start_Month"
                    ].iloc[0]
                )
                if len(subset) > 0
                else None
            ),
            "end_month": (
                str(
                    subset[
                        "End_Month"
                    ].iloc[0]
                )
                if len(subset) > 0
                else None
            ),
            "asset_count": int(
                len(subset)
            ),
            "usable_months_by_asset": {
                row["Asset"]: int(
                    row["Usable_Months"]
                )
                for _, row
                in subset.iterrows()
            },
        }

    return {
        "stage": "statistical_analysis",
        "status": status,
        "artifact_version": "1.0",
        "input_file": (
            "data/processed/"
            "monthly_excess_returns.csv"
        ),
        "combined_output_file": (
            "output/tables/"
            "bkm_statistics_all_samples.csv"
        ),
        "sample_output_files": (
            sample_files
        ),
        "asset_count": len(ASSETS),
        "sample_count": len(SAMPLES),
        "expected_result_rows": (
            len(ASSETS) * len(SAMPLES)
        ),
        "actual_result_rows": int(
            len(results)
        ),
        "statistics_per_row": 10,
        "definitions": {
            "annualized_mean": (
                "12 × monthly arithmetic mean"
            ),
            "annualized_std": (
                "sqrt(12) × monthly sample standard deviation"
            ),
            "sharpe_ratio": (
                "annualized mean excess return / "
                "annualized standard deviation"
            ),
            "lower_partial_std": (
                "sqrt(mean((r - sample_mean)^2 "
                "conditional on r < sample_mean)) "
                "× sqrt(12)"
            ),
            "skewness": (
                "sample skewness of monthly excess returns"
            ),
            "excess_kurtosis": (
                "Fisher excess kurtosis; normal = 0"
            ),
            "empirical_var_1pct": (
                "empirical 1st percentile"
            ),
            "normal_var_1pct": (
                "monthly mean - 2.3263 × monthly sample SD"
            ),
            "pct_below_mean_minus_3sd": (
                "percentage of monthly returns below "
                "mean - 3 × monthly SD"
            ),
            "expected_shortfall": (
                "average return among observations "
                "at or below empirical 1% VaR"
            ),
        },
        "samples": sample_metadata,
        "errors": errors,
        "warnings": warnings,
    }


def write_artifact(
    artifact: dict,
) -> None:

    with ARTIFACT_FILE.open(
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
    results: pd.DataFrame,
    artifact: dict,
) -> None:

    print()
    print("=" * 72)
    print("BUFN741 STATISTICAL ANALYSIS")
    print("=" * 72)

    print()
    print(
        f"Status: {artifact['status'].upper()}"
    )

    print()
    print(
        f"Assets:          {len(ASSETS)}"
    )
    print(
        f"Samples:         {len(SAMPLES)}"
    )
    print(
        f"Asset-periods:   {len(results)}"
    )
    print(
        "Statistics/row: 10"
    )

    print()
    print("Sample coverage:")

    for sample_name, info in artifact[
        "samples"
    ].items():

        months = list(
            info[
                "usable_months_by_asset"
            ].values()
        )

        unique_counts = sorted(
            set(months)
        )

        print(
            f"  {sample_name}: "
            f"{info['start_month']} "
            f"to {info['end_month']} "
            f"| usable months {unique_counts}"
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
    print("Combined table:")
    print(
        "  output/tables/"
        "bkm_statistics_all_samples.csv"
    )

    print()
    print("Individual sample tables:")

    for path in artifact[
        "sample_output_files"
    ]:
        print(
            f"  {path}"
        )

    print()
    print("Evidence artifact:")
    print(
        "  validation/artifacts/"
        "statistical_analysis.json"
    )

    print("=" * 72)


# =========================================================
# Main
# =========================================================

def main() -> int:

    ensure_directories()

    try:

        df = read_analysis_data()

        results = run_analysis(
            df
        )

        errors, warnings = (
            validate_results(
                results
            )
        )

        save_combined_table(
            results
        )

        sample_files = (
            save_sample_tables(
                results
            )
        )

        artifact = build_artifact(
            results,
            errors,
            warnings,
            sample_files,
        )

        write_artifact(
            artifact
        )

        print_summary(
            results,
            artifact,
        )

        return (
            0
            if artifact["status"] == "passed"
            else 1
        )

    except Exception as exc:

        print()
        print("=" * 72)
        print("STATISTICAL ANALYSIS FAILED")
        print("=" * 72)

        print()
        print(type(exc).__name__)
        print(str(exc))
        print()

        if ARTIFACT_FILE.exists():
            ARTIFACT_FILE.unlink()

        return 1


if __name__ == "__main__":
    sys.exit(main())