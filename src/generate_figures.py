from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib

# Important for Linux server / non-GUI execution.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURE_DIR = PROJECT_ROOT / "output" / "figures"
ARTIFACT_DIR = PROJECT_ROOT / "validation" / "artifacts"

INPUT_FILE = (
    PROCESSED_DIR / "monthly_excess_returns.csv"
)

ARTIFACT_FILE = (
    ARTIFACT_DIR / "figure_generation.json"
)


# =========================================================
# Research design
# =========================================================

ASSETS = {
    "SP500": {
        "column": "SP500_excess",
        "label": "S&P 500",
    },
    "Small_Growth": {
        "column": "Small_Growth_excess",
        "label": "Small / Growth",
    },
    "Small_Value": {
        "column": "Small_Value_excess",
        "label": "Small / Value",
    },
    "Big_Growth": {
        "column": "Big_Growth_excess",
        "label": "Big / Growth",
    },
    "Big_Value": {
        "column": "Big_Value_excess",
        "label": "Big / Value",
    },
}


EXPECTED_FIGURE_COUNT = 11


# =========================================================
# Utilities
# =========================================================

def ensure_directories() -> None:
    FIGURE_DIR.mkdir(
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

    df = pd.read_csv(
        INPUT_FILE
    )

    required = [
        "date",
        *[
            info["column"]
            for info in ASSETS.values()
        ],
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

    df["date"] = pd.to_datetime(
        df["date"],
        format="%Y-%m",
    )

    for info in ASSETS.values():
        column = info["column"]

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return (
        df.sort_values("date")
        .reset_index(drop=True)
    )


def save_figure(
    fig: plt.Figure,
    path: Path,
) -> None:

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)


# =========================================================
# Time-series figures
# =========================================================

def identify_extreme_months(
    df: pd.DataFrame,
    column: str,
    n: int = 4,
) -> pd.DataFrame:
    """
    Return the n observations with the largest
    absolute monthly excess returns.
    """

    clean = df[
        [
            "date",
            column,
        ]
    ].dropna()

    if len(clean) <= n:
        return clean.copy()

    indices = (
        clean[column]
        .abs()
        .nlargest(n)
        .index
    )

    return (
        clean.loc[indices]
        .sort_values("date")
        .copy()
    )


def create_time_series_figure(
    df: pd.DataFrame,
    asset_id: str,
    column: str,
    label: str,
) -> Path:

    fig, ax = plt.subplots(
        figsize=(11, 5.5)
    )

    ax.plot(
        df["date"],
        df[column],
        linewidth=0.9,
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    ax.set_title(
        f"{label}: Monthly Excess Returns"
    )

    ax.set_xlabel(
        "Month"
    )

    ax.set_ylabel(
        "Monthly excess return"
    )

    ax.yaxis.set_major_formatter(
        PercentFormatter(
            xmax=1.0,
            decimals=0,
        )
    )

    ax.grid(
        alpha=0.25,
    )

    extremes = identify_extreme_months(
        df,
        column,
        n=4,
    )

    offsets = [
        (8, 12),
        (8, -18),
        (8, 12),
        (8, -18),
    ]

    for i, (_, row) in enumerate(
        extremes.iterrows()
    ):

        offset = offsets[
            i % len(offsets)
        ]

        ax.scatter(
            row["date"],
            row[column],
            s=28,
            zorder=3,
        )

        ax.annotate(
            row["date"].strftime(
                "%Y-%m"
            ),
            xy=(
                row["date"],
                row[column],
            ),
            xytext=offset,
            textcoords="offset points",
            fontsize=8,
            arrowprops={
                "arrowstyle": "-",
                "linewidth": 0.6,
            },
        )

    path = (
        FIGURE_DIR
        / f"time_series_{asset_id}.png"
    )

    save_figure(
        fig,
        path,
    )

    return path


# =========================================================
# Histogram + fitted normal distribution
# =========================================================

def normal_pdf(
    x: np.ndarray,
    mean: float,
    std: float,
) -> np.ndarray:

    if std <= 0:
        return np.full_like(
            x,
            np.nan,
            dtype=float,
        )

    coefficient = (
        1.0
        /
        (
            std
            * math.sqrt(
                2.0 * math.pi
            )
        )
    )

    exponent = (
        -0.5
        * (
            (x - mean)
            / std
        )
        ** 2
    )

    return (
        coefficient
        * np.exp(exponent)
    )


def create_histogram_figure(
    df: pd.DataFrame,
    asset_id: str,
    column: str,
    label: str,
) -> Path:

    series = (
        df[column]
        .dropna()
        .astype(float)
    )

    if len(series) < 2:
        raise RuntimeError(
            f"Not enough observations for histogram: "
            f"{asset_id}"
        )

    mean = float(
        series.mean()
    )

    std = float(
        series.std(ddof=1)
    )

    fig, ax = plt.subplots(
        figsize=(8.5, 5.5)
    )

    ax.hist(
        series,
        bins="auto",
        density=True,
        alpha=0.6,
        label="Empirical distribution",
    )

    x = np.linspace(
        float(series.min()),
        float(series.max()),
        500,
    )

    fitted_density = normal_pdf(
        x,
        mean,
        std,
    )

    ax.plot(
        x,
        fitted_density,
        linewidth=2,
        label="Fitted normal distribution",
    )

    ax.set_title(
        f"{label}: Empirical vs. Normal Distribution"
    )

    ax.set_xlabel(
        "Monthly excess return"
    )

    ax.set_ylabel(
        "Density"
    )

    ax.xaxis.set_major_formatter(
        PercentFormatter(
            xmax=1.0,
            decimals=0,
        )
    )

    ax.legend()

    ax.grid(
        alpha=0.20,
    )

    path = (
        FIGURE_DIR
        / f"histogram_normal_{asset_id}.png"
    )

    save_figure(
        fig,
        path,
    )

    return path


# =========================================================
# Common tail comparison
# =========================================================

def empirical_cdf(
    series: pd.Series,
) -> tuple[np.ndarray, np.ndarray]:

    values = np.sort(
        series.dropna()
        .astype(float)
        .to_numpy()
    )

    n = len(values)

    if n == 0:
        raise RuntimeError(
            "Cannot construct ECDF from empty series."
        )

    probabilities = (
        np.arange(
            1,
            n + 1,
        )
        / n
    )

    return values, probabilities


def create_tail_comparison(
    df: pd.DataFrame,
) -> Path:

    fig, ax = plt.subplots(
        figsize=(9, 6)
    )

    pooled_values = []

    for asset_id, info in ASSETS.items():

        series = (
            df[info["column"]]
            .dropna()
        )

        x, y = empirical_cdf(
            series
        )

        pooled_values.extend(
            series.tolist()
        )

        ax.plot(
            x,
            y,
            linewidth=1.4,
            label=info["label"],
        )

    pooled = np.asarray(
        pooled_values,
        dtype=float,
    )

    if len(pooled) == 0:
        raise RuntimeError(
            "No observations available "
            "for tail comparison."
        )

    left_limit = float(
        np.min(pooled)
    )

    right_limit = float(
        np.quantile(
            pooled,
            0.15,
        )
    )

    ax.set_xlim(
        left_limit,
        right_limit,
    )

    ax.set_ylim(
        0,
        0.16,
    )

    ax.set_title(
        "Left-Tail Comparison of Monthly Excess Returns"
    )

    ax.set_xlabel(
        "Monthly excess return"
    )

    ax.set_ylabel(
        "Empirical cumulative probability"
    )

    ax.xaxis.set_major_formatter(
        PercentFormatter(
            xmax=1.0,
            decimals=0,
        )
    )

    ax.yaxis.set_major_formatter(
        PercentFormatter(
            xmax=1.0,
            decimals=0,
        )
    )

    ax.legend()

    ax.grid(
        alpha=0.25,
    )

    path = (
        FIGURE_DIR
        / "tail_comparison_ecdf.png"
    )

    save_figure(
        fig,
        path,
    )

    return path


# =========================================================
# Figure generation
# =========================================================

def generate_all_figures(
    df: pd.DataFrame,
) -> list[Path]:

    files = []

    for asset_id, info in ASSETS.items():

        files.append(
            create_time_series_figure(
                df,
                asset_id,
                info["column"],
                info["label"],
            )
        )

    for asset_id, info in ASSETS.items():

        files.append(
            create_histogram_figure(
                df,
                asset_id,
                info["column"],
                info["label"],
            )
        )

    files.append(
        create_tail_comparison(
            df
        )
    )

    return files


# =========================================================
# Figure QA
# =========================================================

def validate_figure_files(
    paths: list[Path],
) -> tuple[list[str], list[str]]:

    errors = []
    warnings = []

    if len(paths) != EXPECTED_FIGURE_COUNT:
        errors.append(
            f"Expected {EXPECTED_FIGURE_COUNT} figures, "
            f"generated {len(paths)}."
        )

    filenames = [
        path.name
        for path in paths
    ]

    if len(set(filenames)) != len(filenames):
        errors.append(
            "Duplicate figure filenames detected."
        )

    for path in paths:

        if not path.is_file():
            errors.append(
                f"Figure file missing: "
                f"{path.name}"
            )
            continue

        size = path.stat().st_size

        if size == 0:
            errors.append(
                f"Figure file is empty: "
                f"{path.name}"
            )

        elif size < 5000:
            warnings.append(
                f"Figure file is unusually small: "
                f"{path.name} ({size} bytes)"
            )

    for asset_id in ASSETS:

        time_file = (
            FIGURE_DIR
            / f"time_series_{asset_id}.png"
        )

        histogram_file = (
            FIGURE_DIR
            / f"histogram_normal_{asset_id}.png"
        )

        if not time_file.is_file():
            errors.append(
                f"Missing time-series figure for "
                f"{asset_id}."
            )

        if not histogram_file.is_file():
            errors.append(
                f"Missing histogram figure for "
                f"{asset_id}."
            )

    tail_file = (
        FIGURE_DIR
        / "tail_comparison_ecdf.png"
    )

    if not tail_file.is_file():
        errors.append(
            "Missing common tail-comparison figure."
        )

    return errors, warnings


# =========================================================
# Evidence artifact
# =========================================================

def build_artifact(
    df: pd.DataFrame,
    figure_paths: list[Path],
    errors: list[str],
    warnings: list[str],
) -> dict:

    status = (
        "passed"
        if len(errors) == 0
        else "failed"
    )

    return {
        "stage": "figure_generation",
        "status": status,
        "artifact_version": "1.0",
        "input_file": (
            "data/processed/"
            "monthly_excess_returns.csv"
        ),
        "sample": {
            "first_month": (
                df["date"]
                .min()
                .strftime("%Y-%m")
            ),
            "last_month": (
                df["date"]
                .max()
                .strftime("%Y-%m")
            ),
            "rows": int(
                len(df)
            ),
        },
        "requirements": {
            "time_series_figures": 5,
            "histogram_normal_figures": 5,
            "common_tail_figures": 1,
            "expected_total": (
                EXPECTED_FIGURE_COUNT
            ),
        },
        "figures": [
            {
                "file": str(
                    path.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "bytes": int(
                    path.stat().st_size
                )
                if path.is_file()
                else None,
            }
            for path in figure_paths
        ],
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
    artifact: dict,
) -> None:

    print()
    print("=" * 72)
    print("BUFN741 FIGURE GENERATION")
    print("=" * 72)

    print()
    print(
        f"Status: {artifact['status'].upper()}"
    )

    print()
    print(
        f"Sample: "
        f"{artifact['sample']['first_month']} "
        f"to "
        f"{artifact['sample']['last_month']}"
    )

    print(
        f"Observations: "
        f"{artifact['sample']['rows']}"
    )

    print()
    print("Figures:")

    for figure in artifact[
        "figures"
    ]:

        print(
            f"  {figure['file']} "
            f"({figure['bytes']} bytes)"
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
    print(
        "Evidence artifact:"
    )

    print(
        "  validation/artifacts/"
        "figure_generation.json"
    )

    print("=" * 72)


# =========================================================
# Main
# =========================================================

def main() -> int:

    ensure_directories()

    try:

        df = read_analysis_data()

        figure_paths = (
            generate_all_figures(
                df
            )
        )

        errors, warnings = (
            validate_figure_files(
                figure_paths
            )
        )

        artifact = build_artifact(
            df,
            figure_paths,
            errors,
            warnings,
        )

        write_artifact(
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
        print("=" * 72)
        print("FIGURE GENERATION FAILED")
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