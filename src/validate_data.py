
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

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACT_DIR = PROJECT_ROOT / "validation" / "artifacts"

FF_PORTFOLIO_FILE = RAW_DIR / "ff_6_portfolios_2x3_monthly.csv"
FF_RF_FILE = RAW_DIR / "ff_rf_monthly.csv"
SP500_FILE = RAW_DIR / "sp500_total_return_monthly.csv"

VALIDATION_ARTIFACT = ARTIFACT_DIR / "data_validation.json"
ALIGNED_RAW_FILE = PROCESSED_DIR / "aligned_raw_monthly.csv"


# =========================================================
# Expected columns
# =========================================================

FF_PORTFOLIO_COLUMNS = [
    "date",
    "Small_Growth",
    "Small_Value",
    "Big_Growth",
    "Big_Value",
]

FF_RF_COLUMNS = [
    "date",
    "RF",
]

SP500_COLUMNS = [
    "date",
    "index_level",
    "return_decimal",
]


# =========================================================
# Utilities
# =========================================================

def ensure_directories() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(
            f"Required raw data file not found: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )

    return pd.read_csv(path)


def require_columns(
    df: pd.DataFrame,
    expected: list[str],
    dataset_name: str,
) -> None:
    missing = [
        column
        for column in expected
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"{dataset_name} is missing required columns: {missing}"
        )


def parse_month_column(
    df: pd.DataFrame,
    dataset_name: str,
) -> pd.DataFrame:
    df = df.copy()

    try:
        df["month"] = pd.PeriodIndex(
            df["date"],
            freq="M",
        )
    except Exception as exc:
        raise RuntimeError(
            f"{dataset_name}: could not parse date column "
            f"as monthly periods."
        ) from exc

    return df


def count_duplicate_months(
    df: pd.DataFrame,
) -> int:
    return int(
        df["month"].duplicated().sum()
    )


def count_missing_values(
    df: pd.DataFrame,
    columns: list[str],
) -> dict:
    return {
        column: int(df[column].isna().sum())
        for column in columns
    }


def month_range_summary(
    df: pd.DataFrame,
) -> dict:
    return {
        "rows": int(len(df)),
        "first_month": (
            str(df["month"].min())
            if len(df) > 0
            else None
        ),
        "last_month": (
            str(df["month"].max())
            if len(df) > 0
            else None
        ),
    }


def detect_month_gaps(
    df: pd.DataFrame,
) -> list[str]:
    if df.empty:
        return []

    expected = pd.period_range(
        start=df["month"].min(),
        end=df["month"].max(),
        freq="M",
    )

    observed = set(df["month"])

    gaps = [
        str(month)
        for month in expected
        if month not in observed
    ]

    return gaps


def numeric_range(
    series: pd.Series,
) -> dict:
    clean = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if clean.empty:
        return {
            "min": None,
            "max": None,
            "mean_abs": None,
        }

    return {
        "min": float(clean.min()),
        "max": float(clean.max()),
        "mean_abs": float(clean.abs().mean()),
    }


# =========================================================
# Unit diagnostics
# =========================================================

def infer_unit_from_magnitude(
    series: pd.Series,
    dataset_name: str,
) -> dict:
    """
    Infer whether a return series is likely stored in
    percent or decimal units.

    This is only a diagnostic heuristic.
    """

    clean = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if clean.empty:
        return {
            "dataset": dataset_name,
            "inferred_unit": "unknown",
            "confidence": "low",
            "reason": "No usable observations.",
        }

    median_abs = float(
        clean.abs().median()
    )

    p95_abs = float(
        clean.abs().quantile(0.95)
    )

    if median_abs > 0.2:
        inferred = "percent"
        confidence = "high"
    elif median_abs < 0.10:
        inferred = "decimal"
        confidence = "high"
    else:
        inferred = "ambiguous"
        confidence = "low"

    return {
        "dataset": dataset_name,
        "inferred_unit": inferred,
        "confidence": confidence,
        "median_absolute_value": median_abs,
        "p95_absolute_value": p95_abs,
    }


# =========================================================
# Dataset validation
# =========================================================

def validate_ff_portfolios(
    df: pd.DataFrame,
) -> dict:
    require_columns(
        df,
        FF_PORTFOLIO_COLUMNS,
        "Fama-French portfolios",
    )

    df = parse_month_column(
        df,
        "Fama-French portfolios",
    )

    return {
        "summary": month_range_summary(df),
        "duplicate_months": count_duplicate_months(df),
        "missing_values": count_missing_values(
            df,
            FF_PORTFOLIO_COLUMNS[1:],
        ),
        "month_gaps": detect_month_gaps(df),
        "ranges": {
            column: numeric_range(df[column])
            for column in FF_PORTFOLIO_COLUMNS[1:]
        },
        "unit_checks": {
            column: infer_unit_from_magnitude(
                df[column],
                f"Fama-French {column}",
            )
            for column in FF_PORTFOLIO_COLUMNS[1:]
        },
    }


def validate_ff_rf(
    df: pd.DataFrame,
) -> dict:
    require_columns(
        df,
        FF_RF_COLUMNS,
        "Fama-French RF",
    )

    df = parse_month_column(
        df,
        "Fama-French RF",
    )

    return {
        "summary": month_range_summary(df),
        "duplicate_months": count_duplicate_months(df),
        "missing_values": count_missing_values(
            df,
            ["RF"],
        ),
        "month_gaps": detect_month_gaps(df),
        "range": numeric_range(df["RF"]),
        "unit_check": infer_unit_from_magnitude(
            df["RF"],
            "Fama-French RF",
        ),
    }


def validate_sp500(
    df: pd.DataFrame,
) -> dict:
    require_columns(
        df,
        SP500_COLUMNS,
        "S&P 500 total-return data",
    )

    df = parse_month_column(
        df,
        "S&P 500 total-return data",
    )

    return {
        "summary": month_range_summary(df),
        "duplicate_months": count_duplicate_months(df),
        "missing_values": count_missing_values(
            df,
            [
                "index_level",
                "return_decimal",
            ],
        ),
        "month_gaps": detect_month_gaps(df),
        "return_range": numeric_range(
            df["return_decimal"]
        ),
        "unit_check": infer_unit_from_magnitude(
            df["return_decimal"],
            "S&P 500 total-return return_decimal",
        ),
    }


# =========================================================
# Alignment
# =========================================================

def align_raw_datasets(
    ff_portfolios: pd.DataFrame,
    rf: pd.DataFrame,
    sp500: pd.DataFrame,
) -> pd.DataFrame:

    ff = parse_month_column(
        ff_portfolios,
        "Fama-French portfolios",
    )

    rf = parse_month_column(
        rf,
        "Fama-French RF",
    )

    sp = parse_month_column(
        sp500,
        "S&P 500 total-return data",
    )

    ff = ff[
        [
            "month",
            "Small_Growth",
            "Small_Value",
            "Big_Growth",
            "Big_Value",
        ]
    ]

    rf = rf[
        [
            "month",
            "RF",
        ]
    ]

    sp = sp[
        [
            "month",
            "return_decimal",
        ]
    ].rename(
        columns={
            "return_decimal": "SP500"
        }
    )

    merged = (
        ff.merge(
            rf,
            on="month",
            how="inner",
        )
        .merge(
            sp,
            on="month",
            how="inner",
        )
        .sort_values("month")
        .reset_index(drop=True)
    )

    merged["date"] = (
        merged["month"]
        .astype(str)
    )

    return merged[
        [
            "date",
            "SP500",
            "Small_Growth",
            "Small_Value",
            "Big_Growth",
            "Big_Value",
            "RF",
        ]
    ]


# =========================================================
# Sample counts
# =========================================================

def sample_count(
    df: pd.DataFrame,
    start: str | None,
    end: str | None,
) -> int:

    periods = pd.PeriodIndex(
        df["date"],
        freq="M",
    )

    mask = pd.Series(
        True,
        index=df.index,
    )

    if start is not None:
        mask &= periods >= pd.Period(
            start,
            freq="M",
        )

    if end is not None:
        mask &= periods <= pd.Period(
            end,
            freq="M",
        )

    return int(mask.sum())


def build_sample_counts(
    aligned: pd.DataFrame,
) -> dict:

    if aligned.empty:
        return {}

    first_month = aligned["date"].iloc[0]
    last_month = aligned["date"].iloc[-1]

    return {
        "full_history": {
            "start": first_month,
            "end": last_month,
            "usable_months": int(len(aligned)),
        },
        "1990_2000": {
            "start": "1990-01",
            "end": "2000-12",
            "usable_months": sample_count(
                aligned,
                "1990-01",
                "2000-12",
            ),
        },
        "2001_2010": {
            "start": "2001-01",
            "end": "2010-12",
            "usable_months": sample_count(
                aligned,
                "2001-01",
                "2010-12",
            ),
        },
        "2011_present": {
            "start": "2011-01",
            "end": last_month,
            "usable_months": sample_count(
                aligned,
                "2011-01",
                last_month,
            ),
        },
    }


# =========================================================
# Validation verdict
# =========================================================

def determine_validation_status(
    ff_result: dict,
    rf_result: dict,
    sp_result: dict,
    aligned: pd.DataFrame,
) -> tuple[str, list[str], list[str]]:

    errors = []
    warnings = []

    if ff_result["duplicate_months"] > 0:
        errors.append(
            "Fama-French portfolio data contain duplicate months."
        )

    if rf_result["duplicate_months"] > 0:
        errors.append(
            "Fama-French RF data contain duplicate months."
        )

    if sp_result["duplicate_months"] > 0:
        errors.append(
            "S&P 500 data contain duplicate months."
        )

    if aligned.empty:
        errors.append(
            "No common monthly observations exist across datasets."
        )

    ff_units = {
        result["inferred_unit"]
        for result
        in ff_result["unit_checks"].values()
    }

    if ff_units != {"percent"}:
        warnings.append(
            "Fama-French portfolio unit inference "
            "was not uniformly percent."
        )

    if (
        rf_result["unit_check"]["inferred_unit"]
        != "percent"
    ):
        warnings.append(
            "RF unit inference was not percent."
        )

    if (
        sp_result["unit_check"]["inferred_unit"]
        != "decimal"
    ):
        warnings.append(
            "S&P 500 unit inference was not decimal."
        )

    if ff_result["month_gaps"]:
        warnings.append(
            "Fama-French portfolio series contains "
            "one or more month gaps."
        )

    if rf_result["month_gaps"]:
        warnings.append(
            "Fama-French RF series contains "
            "one or more month gaps."
        )

    if sp_result["month_gaps"]:
        warnings.append(
            "S&P 500 series contains "
            "one or more month gaps."
        )

    status = (
        "passed"
        if len(errors) == 0
        else "failed"
    )

    return status, errors, warnings


# =========================================================
# Output
# =========================================================

def save_aligned_raw(
    aligned: pd.DataFrame,
) -> None:
    aligned.to_csv(
        ALIGNED_RAW_FILE,
        index=False,
    )


def write_validation_artifact(
    artifact: dict,
) -> None:

    with VALIDATION_ARTIFACT.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            artifact,
            file,
            indent=2,
        )

        file.write("\n")


def print_summary(
    artifact: dict,
) -> None:

    print()
    print("=" * 70)
    print("BUFN741 DATA VALIDATION")
    print("=" * 70)

    print()
    print(
        f"Status: {artifact['status'].upper()}"
    )

    common = artifact["common_sample"]

    print()
    print("Common sample:")
    print(
        f"  Start: {common['first_month']}"
    )
    print(
        f"  End:   {common['last_month']}"
    )
    print(
        f"  Rows:  {common['rows']}"
    )

    print()
    print("Sample counts:")

    for name, sample in artifact[
        "sample_counts"
    ].items():

        print(
            f"  {name}: "
            f"{sample['usable_months']} months"
        )

    if artifact["warnings"]:
        print()
        print("Warnings:")

        for warning in artifact["warnings"]:
            print(f"  - {warning}")

    if artifact["errors"]:
        print()
        print("Errors:")

        for error in artifact["errors"]:
            print(f"  - {error}")

    print()
    print(
        "Aligned raw file:"
    )
    print(
        "  data/processed/aligned_raw_monthly.csv"
    )

    print()
    print(
        "Validation artifact:"
    )
    print(
        "  validation/artifacts/data_validation.json"
    )

    print("=" * 70)


# =========================================================
# Main
# =========================================================

def main() -> int:

    ensure_directories()

    try:
        ff_portfolios = read_csv(
            FF_PORTFOLIO_FILE
        )

        rf = read_csv(
            FF_RF_FILE
        )

        sp500 = read_csv(
            SP500_FILE
        )

        ff_result = validate_ff_portfolios(
            ff_portfolios
        )

        rf_result = validate_ff_rf(
            rf
        )

        sp_result = validate_sp500(
            sp500
        )

        aligned = align_raw_datasets(
            ff_portfolios,
            rf,
            sp500,
        )

        save_aligned_raw(
            aligned
        )

        status, errors, warnings = (
            determine_validation_status(
                ff_result,
                rf_result,
                sp_result,
                aligned,
            )
        )

        common_sample = {
            "rows": int(len(aligned)),
            "first_month": (
                aligned["date"].iloc[0]
                if len(aligned) > 0
                else None
            ),
            "last_month": (
                aligned["date"].iloc[-1]
                if len(aligned) > 0
                else None
            ),
        }

        sample_counts = build_sample_counts(
            aligned
        )

        artifact = {
            "stage": "data_validation",
            "status": status,
            "artifact_version": "1.0",
            "datasets": {
                "fama_french_portfolios": ff_result,
                "fama_french_rf": rf_result,
                "sp500_total_return": sp_result,
            },
            "common_sample": common_sample,
            "sample_counts": sample_counts,
            "unit_conclusion": {
                "fama_french_portfolios": (
                    "percent"
                ),
                "fama_french_rf": (
                    "percent"
                ),
                "sp500": (
                    "decimal"
                ),
                "normalization_required": True,
            },
            "dividend_treatment": {
                "fama_french_portfolios": (
                    "Portfolio returns from Kenneth "
                    "French Data Library."
                ),
                "sp500": (
                    "Monthly simple returns computed "
                    "from S&P 500 Total Return Index."
                ),
                "comparability_intent": (
                    "Both equity return sources include "
                    "dividend effects."
                ),
            },
            "errors": errors,
            "warnings": warnings,
        }

        write_validation_artifact(
            artifact
        )

        print_summary(
            artifact
        )

        return 0 if status == "passed" else 1

    except Exception as exc:

        print()
        print("=" * 70)
        print("DATA VALIDATION FAILED")
        print("=" * 70)

        print()
        print(type(exc).__name__)
        print(str(exc))
        print()

        if VALIDATION_ARTIFACT.exists():
            VALIDATION_ARTIFACT.unlink()

        return 1


if __name__ == "__main__":
    sys.exit(main())
