from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACT_DIR = PROJECT_ROOT / "validation" / "artifacts"

ALIGNED_RAW_FILE = (
    PROCESSED_DIR / "aligned_raw_monthly.csv"
)

OUTPUT_FILE = (
    PROCESSED_DIR / "monthly_excess_returns.csv"
)

PROCESSING_ARTIFACT = (
    ARTIFACT_DIR / "data_processing.json"
)


# =========================================================
# Expected columns
# =========================================================

RAW_COLUMNS = [
    "date",
    "SP500",
    "Small_Growth",
    "Small_Value",
    "Big_Growth",
    "Big_Value",
    "RF",
]

ASSET_COLUMNS = [
    "SP500",
    "Small_Growth",
    "Small_Value",
    "Big_Growth",
    "Big_Value",
]

EXCESS_COLUMNS = [
    f"{asset}_excess"
    for asset in ASSET_COLUMNS
]


# =========================================================
# Utilities
# =========================================================

def ensure_directories() -> None:
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def read_aligned_raw() -> pd.DataFrame:
    if not ALIGNED_RAW_FILE.is_file():
        raise FileNotFoundError(
            "Required file not found: "
            "data/processed/aligned_raw_monthly.csv"
        )

    return pd.read_csv(
        ALIGNED_RAW_FILE
    )


def require_columns(
    df: pd.DataFrame,
    required: list[str],
) -> None:

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Aligned raw data are missing columns: {missing}"
        )


def convert_numeric(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:

    df = df.copy()

    for column in columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


# =========================================================
# Unit normalization
# =========================================================

def normalize_units(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert all return series to decimal units.

    Input conventions established in Lesson 5:
      SP500: decimal
      Fama-French portfolios: percent
      RF: percent
    """

    df = df.copy()

    ff_columns = [
        "Small_Growth",
        "Small_Value",
        "Big_Growth",
        "Big_Value",
        "RF",
    ]

    for column in ff_columns:
        df[column] = (
            df[column] / 100.0
        )

    return df


# =========================================================
# Excess return construction
# =========================================================

def construct_excess_returns(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    for asset in ASSET_COLUMNS:
        df[f"{asset}_excess"] = (
            df[asset] - df["RF"]
        )

    return df


# =========================================================
# Validation helpers
# =========================================================

def count_missing(
    df: pd.DataFrame,
    columns: list[str],
) -> dict:

    return {
        column: int(
            df[column].isna().sum()
        )
        for column in columns
    }


def range_summary(
    series: pd.Series,
) -> dict:

    clean = series.dropna()

    if clean.empty:
        return {
            "min": None,
            "max": None,
            "mean": None,
        }

    return {
        "min": float(clean.min()),
        "max": float(clean.max()),
        "mean": float(clean.mean()),
    }


def validate_decimal_scale(
    df: pd.DataFrame,
) -> tuple[list[str], list[str]]:
    """
    Detect implausible scales after normalization.

    These thresholds are deliberately broad.
    """

    errors = []
    warnings = []

    columns = (
        ASSET_COLUMNS
        + ["RF"]
        + EXCESS_COLUMNS
    )

    for column in columns:

        clean = df[column].dropna()

        if clean.empty:
            errors.append(
                f"{column} has no usable observations."
            )
            continue

        max_abs = float(
            clean.abs().max()
        )

        if max_abs > 5.0:
            errors.append(
                f"{column} has absolute values above 5.0, "
                "suggesting a unit or parsing error."
            )

        elif max_abs > 1.0:
            warnings.append(
                f"{column} contains absolute monthly returns "
                "above 100%; inspect for plausibility."
            )

    return errors, warnings


def validate_excess_identity(
    df: pd.DataFrame,
    tolerance: float = 1e-12,
) -> list[str]:
    """
    Verify exactly that:
        excess return = asset return - RF
    """

    errors = []

    for asset in ASSET_COLUMNS:

        calculated = (
            df[asset] - df["RF"]
        )

        stored = (
            df[f"{asset}_excess"]
        )

        difference = (
            calculated - stored
        ).abs()

        max_difference = float(
            difference.max()
        )

        if max_difference > tolerance:
            errors.append(
                f"{asset}_excess identity failed. "
                f"Maximum difference = {max_difference}"
            )

    return errors


def validate_dates(
    df: pd.DataFrame,
) -> list[str]:

    errors = []

    periods = pd.PeriodIndex(
        df["date"],
        freq="M",
    )

    if periods.duplicated().any():
        errors.append(
            "Duplicate months detected."
        )

    if not periods.is_monotonic_increasing:
        errors.append(
            "Dates are not sorted in ascending order."
        )

    return errors


# =========================================================
# Output construction
# =========================================================

def build_analysis_dataset(
    df: pd.DataFrame,
) -> pd.DataFrame:

    columns = [
        "date",
        "SP500",
        "Small_Growth",
        "Small_Value",
        "Big_Growth",
        "Big_Value",
        "RF",
        "SP500_excess",
        "Small_Growth_excess",
        "Small_Value_excess",
        "Big_Growth_excess",
        "Big_Value_excess",
    ]

    return df[
        columns
    ].copy()


def save_analysis_dataset(
    df: pd.DataFrame,
) -> None:

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )


# =========================================================
# Processing artifact
# =========================================================

def build_processing_artifact(
    df: pd.DataFrame,
    errors: list[str],
    warnings: list[str],
) -> dict:

    status = (
        "passed"
        if len(errors) == 0
        else "failed"
    )

    return {
        "stage": "data_processing",
        "status": status,
        "artifact_version": "1.0",
        "input_file": (
            "data/processed/aligned_raw_monthly.csv"
        ),
        "output_file": (
            "data/processed/monthly_excess_returns.csv"
        ),
        "transformations": {
            "SP500": (
                "retained in decimal units"
            ),
            "fama_french_portfolios": (
                "converted from percent to decimal "
                "by dividing by 100"
            ),
            "RF": (
                "converted from percent to decimal "
                "by dividing by 100"
            ),
            "excess_return_definition": (
                "asset_return - RF"
            ),
            "return_type": (
                "simple monthly return"
            ),
        },
        "observations": int(
            len(df)
        ),
        "first_month": (
            str(df["date"].iloc[0])
            if len(df) > 0
            else None
        ),
        "last_month": (
            str(df["date"].iloc[-1])
            if len(df) > 0
            else None
        ),
        "missing_values": count_missing(
            df,
            (
                ASSET_COLUMNS
                + ["RF"]
                + EXCESS_COLUMNS
            ),
        ),
        "ranges": {
            column: range_summary(
                df[column]
            )
            for column in (
                ASSET_COLUMNS
                + ["RF"]
                + EXCESS_COLUMNS
            )
        },
        "errors": errors,
        "warnings": warnings,
    }


def write_processing_artifact(
    artifact: dict,
) -> None:

    with PROCESSING_ARTIFACT.open(
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
    print("=" * 70)
    print("BUFN741 DATA PROCESSING")
    print("=" * 70)

    print()
    print(
        f"Status: {artifact['status'].upper()}"
    )

    print()
    print(
        f"Observations: {artifact['observations']}"
    )

    print(
        f"Sample: "
        f"{artifact['first_month']} "
        f"to {artifact['last_month']}"
    )

    print()
    print("Transformations:")
    print(
        "  Fama-French portfolio returns: "
        "percent -> decimal"
    )
    print(
        "  RF: percent -> decimal"
    )
    print(
        "  S&P 500: retained as decimal"
    )
    print(
        "  Excess returns: asset return - RF"
    )

    if artifact["warnings"]:

        print()
        print("Warnings:")

        for warning in artifact["warnings"]:
            print(
                f"  - {warning}"
            )

    if artifact["errors"]:

        print()
        print("Errors:")

        for error in artifact["errors"]:
            print(
                f"  - {error}"
            )

    print()
    print("Canonical analysis dataset:")
    print(
        "  data/processed/"
        "monthly_excess_returns.csv"
    )

    print()
    print("Processing artifact:")
    print(
        "  validation/artifacts/"
        "data_processing.json"
    )

    print("=" * 70)


# =========================================================
# Main
# =========================================================

def main() -> int:

    ensure_directories()

    try:
        df = read_aligned_raw()

        require_columns(
            df,
            RAW_COLUMNS,
        )

        df = convert_numeric(
            df,
            [
                "SP500",
                "Small_Growth",
                "Small_Value",
                "Big_Growth",
                "Big_Value",
                "RF",
            ],
        )

        df = normalize_units(
            df
        )

        df = construct_excess_returns(
            df
        )

        analysis_df = build_analysis_dataset(
            df
        )

        errors = []
        warnings = []

        errors.extend(
            validate_dates(
                analysis_df
            )
        )

        scale_errors, scale_warnings = (
            validate_decimal_scale(
                analysis_df
            )
        )

        errors.extend(
            scale_errors
        )

        warnings.extend(
            scale_warnings
        )

        errors.extend(
            validate_excess_identity(
                analysis_df
            )
        )

        missing = count_missing(
            analysis_df,
            (
                ASSET_COLUMNS
                + ["RF"]
                + EXCESS_COLUMNS
            ),
        )

        if any(
            count > 0
            for count in missing.values()
        ):
            warnings.append(
                "One or more analysis columns contain "
                "missing observations."
            )

        save_analysis_dataset(
            analysis_df
        )

        artifact = build_processing_artifact(
            analysis_df,
            errors,
            warnings,
        )

        write_processing_artifact(
            artifact
        )

        print_summary(
            artifact
        )

        return (
            0
            if artifact["status"] == "passed"
            else 1
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print("DATA PROCESSING FAILED")
        print("=" * 70)

        print()
        print(type(exc).__name__)
        print(str(exc))
        print()

        if PROCESSING_ARTIFACT.exists():
            PROCESSING_ARTIFACT.unlink()

        return 1


if __name__ == "__main__":
    sys.exit(main())