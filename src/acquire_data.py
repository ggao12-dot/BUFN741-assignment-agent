from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
ARTIFACT_DIR = PROJECT_ROOT / "validation" / "artifacts"

FF_PORTFOLIO_FILE = RAW_DIR / "ff_6_portfolios_2x3_monthly.csv"
FF_RF_FILE = RAW_DIR / "ff_rf_monthly.csv"
SP500_FILE = RAW_DIR / "sp500_total_return_monthly.csv"

ACQUISITION_ARTIFACT = (
    ARTIFACT_DIR / "data_acquisition.json"
)


# =========================================================
# Data sources
# =========================================================

FF_6_PORTFOLIOS_URL = (
    "https://mba.tuck.dartmouth.edu/"
    "pages/faculty/ken.french/ftp/"
    "6_Portfolios_2x3_CSV.zip"
)

FF_FACTORS_URL = (
    "https://mba.tuck.dartmouth.edu/"
    "pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_CSV.zip"
)

SP500_YAHOO_TICKER = "^SP500TR"


# =========================================================
# Basic utilities
# =========================================================

def ensure_directories() -> None:
    """Create runtime directories if necessary."""

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    """Return SHA-256 hash of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def file_metadata(path: Path) -> dict:
    """Return reproducibility metadata for a file."""

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def download_zip_text(url: str) -> str:
    """
    Download a ZIP archive containing a French Data Library
    CSV file and return the CSV contents as text.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 BUFN741 "
            "Academic Research Data Acquisition"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=60,
    )

    response.raise_for_status()

    with zipfile.ZipFile(
        io.BytesIO(response.content)
    ) as archive:

        csv_files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv")
        ]

        if not csv_files:
            raise RuntimeError(
                f"No CSV file found inside archive: {url}"
            )

        filename = csv_files[0]

        raw_bytes = archive.read(filename)

    # French files are normally plain ASCII/UTF-8 compatible.
    # latin-1 fallback prevents unusual metadata characters
    # from breaking acquisition.
    try:
        return raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw_bytes.decode("latin-1")


def is_month_code(value: str) -> bool:
    """Return True for YYYYMM strings."""

    return bool(
        re.fullmatch(
            r"\d{6}",
            value.strip(),
        )
    )


# =========================================================
# Kenneth French parsing
# =========================================================

def parse_ff_6_portfolios(
    text: str,
) -> pd.DataFrame:
    """
    Extract the monthly value-weighted 2x3 Size/BM portfolios.

    Source columns:
      SMALL LoBM  -> Small/Growth
      SMALL HiBM  -> Small/Value
      BIG LoBM    -> Big/Growth
      BIG HiBM    -> Big/Value

    Source values are retained in percent units.
    """

    rows = list(
        csv.reader(
            io.StringIO(text, newline="")
        )
    )

    section_index = None

    for i, row in enumerate(rows):
        combined = " ".join(row).strip()

        if (
            "Average Value Weighted Returns"
            in combined
            and "Monthly" in combined
        ):
            section_index = i
            break

    if section_index is None:
        raise RuntimeError(
            "Could not locate monthly value-weighted "
            "portfolio section."
        )

    header_index = None

    for i in range(
        section_index + 1,
        min(section_index + 10, len(rows)),
    ):
        row = rows[i]

        if (
            any("SMALL LoBM" in cell for cell in row)
            and any("BIG HiBM" in cell for cell in row)
        ):
            header_index = i
            break

    if header_index is None:
        raise RuntimeError(
            "Could not locate Fama-French portfolio header."
        )

    header = [
        cell.strip()
        for cell in rows[header_index]
    ]

    observations = []

    for row in rows[header_index + 1:]:

        if not row:
            continue

        date_code = row[0].strip()

        if not is_month_code(date_code):
            break

        if len(row) < len(header):
            continue

        record = dict(
            zip(
                header,
                [cell.strip() for cell in row],
            )
        )

        observations.append(record)

    if not observations:
        raise RuntimeError(
            "No monthly Fama-French portfolio observations found."
        )

    df = pd.DataFrame(observations)

    # First column has a blank header in the French file.
    date_column = df.columns[0]

    df = df.rename(
        columns={
            date_column: "date",
            "SMALL LoBM": "Small_Growth",
            "SMALL HiBM": "Small_Value",
            "BIG LoBM": "Big_Growth",
            "BIG HiBM": "Big_Value",
        }
    )

    required = [
        "date",
        "Small_Growth",
        "Small_Value",
        "Big_Growth",
        "Big_Value",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing expected portfolio columns: {missing}"
        )

    df = df[required].copy()

    df["date"] = pd.to_datetime(
        df["date"],
        format="%Y%m",
    ).dt.to_period("M").astype(str)

    for column in required[1:]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=required[1:],
        how="all",
    )

    return df


def parse_ff_rf(
    text: str,
) -> pd.DataFrame:
    """
    Extract monthly RF from the Fama-French factor file.

    RF remains in the source's percent units.
    """

    rows = list(
        csv.reader(
            io.StringIO(text, newline="")
        )
    )

    header_index = None

    for i, row in enumerate(rows):

        cleaned = [
            cell.strip()
            for cell in row
        ]

        if (
            "Mkt-RF" in cleaned
            and "SMB" in cleaned
            and "HML" in cleaned
            and "RF" in cleaned
        ):
            header_index = i
            break

    if header_index is None:
        raise RuntimeError(
            "Could not locate Fama-French factor header."
        )

    header = [
        cell.strip()
        for cell in rows[header_index]
    ]

    observations = []

    for row in rows[header_index + 1:]:

        if not row:
            continue

        date_code = row[0].strip()

        if not is_month_code(date_code):
            break

        if len(row) < len(header):
            continue

        record = dict(
            zip(
                header,
                [cell.strip() for cell in row],
            )
        )

        observations.append(record)

    if not observations:
        raise RuntimeError(
            "No monthly Fama-French factor observations found."
        )

    df = pd.DataFrame(observations)

    date_column = df.columns[0]

    df = df.rename(
        columns={
            date_column: "date",
            "RF": "RF",
        }
    )

    if "RF" not in df.columns:
        raise RuntimeError(
            "RF column not found in Fama-French factor data."
        )

    df = df[
        [
            "date",
            "RF",
        ]
    ].copy()

    df["date"] = pd.to_datetime(
        df["date"],
        format="%Y%m",
    ).dt.to_period("M").astype(str)

    df["RF"] = pd.to_numeric(
        df["RF"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["RF"]
    )

    return df


# =========================================================
# S&P 500 total-return acquisition
# =========================================================

def latest_complete_month() -> pd.Period:
    """Return the most recent fully completed calendar month."""

    today = pd.Timestamp.now(
        tz="America/New_York"
    )

    current_month = (
        today.tz_localize(None)
        .to_period("M")
    )

    return current_month - 1


def acquire_sp500_total_return() -> pd.DataFrame:
    """
    Download the Yahoo Finance S&P 500 Total Return Index.

    Monthly simple returns are calculated from the total-return
    index level.

    Return values are stored in decimal units.
    """

    ticker = yf.Ticker(
        SP500_YAHOO_TICKER
    )

    history = ticker.history(
        period="max",
        interval="1mo",
        auto_adjust=False,
        actions=False,
    )

    if history.empty:
        raise RuntimeError(
            "Yahoo Finance returned no data "
            f"for {SP500_YAHOO_TICKER}."
        )

    if "Close" not in history.columns:
        raise RuntimeError(
            "Yahoo Finance data contains no Close column."
        )

    df = history[
        ["Close"]
    ].copy()

    # Remove timezone information, if present.
    index = pd.DatetimeIndex(df.index)

    if index.tz is not None:
        index = index.tz_localize(None)

    df.index = index

    df["month"] = (
        df.index
        .to_period("M")
    )

    # Keep the last available observation for each month.
    df = (
        df
        .groupby("month", as_index=False)
        .last()
    )

    df = df.rename(
        columns={
            "Close": "index_level"
        }
    )

    last_complete = latest_complete_month()

    df = df[
        df["month"] <= last_complete
    ].copy()

    if df.empty:
        raise RuntimeError(
            "No complete monthly S&P 500 observations found."
        )

    df["return_decimal"] = (
        df["index_level"]
        .pct_change()
    )

    df["date"] = (
        df["month"]
        .astype(str)
    )

    df = df[
        [
            "date",
            "index_level",
            "return_decimal",
        ]
    ]

    return df


# =========================================================
# Acquisition functions
# =========================================================

def acquire_fama_french() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """Download and parse French portfolio and RF data."""

    print(
        "Downloading Fama-French 6 Size/BM portfolios..."
    )

    portfolio_text = download_zip_text(
        FF_6_PORTFOLIOS_URL
    )

    portfolios = parse_ff_6_portfolios(
        portfolio_text
    )

    print(
        "Downloading Fama-French factors / RF..."
    )

    factors_text = download_zip_text(
        FF_FACTORS_URL
    )

    rf = parse_ff_rf(
        factors_text
    )

    return portfolios, rf


def save_raw_data(
    portfolios: pd.DataFrame,
    rf: pd.DataFrame,
    sp500: pd.DataFrame,
) -> None:
    """Write raw acquisition outputs."""

    portfolios.to_csv(
        FF_PORTFOLIO_FILE,
        index=False,
    )

    rf.to_csv(
        FF_RF_FILE,
        index=False,
    )

    sp500.to_csv(
        SP500_FILE,
        index=False,
    )


# =========================================================
# Evidence artifact
# =========================================================

def dataframe_summary(
    df: pd.DataFrame,
) -> dict:
    """Return basic date/row information."""

    return {
        "rows": int(len(df)),
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
    }


def build_acquisition_artifact(
    portfolios: pd.DataFrame,
    rf: pd.DataFrame,
    sp500: pd.DataFrame,
) -> dict:
    """Construct machine-readable evidence of acquisition."""

    files = {
        "ff_6_portfolios_2x3": {
            **file_metadata(
                FF_PORTFOLIO_FILE
            ),
            **dataframe_summary(
                portfolios
            ),
            "source_unit": "percent",
        },
        "ff_rf": {
            **file_metadata(
                FF_RF_FILE
            ),
            **dataframe_summary(
                rf
            ),
            "source_unit": "percent",
        },
        "sp500_total_return": {
            **file_metadata(
                SP500_FILE
            ),
            **dataframe_summary(
                sp500
            ),
            "source_unit": "decimal_return",
        },
    }

    return {
        "stage": "data_acquisition",
        "status": "passed",
        "artifact_version": "1.0",
        "retrieved_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "sources": {
            "fama_french_6_portfolios": {
                "provider": (
                    "Kenneth R. French Data Library"
                ),
                "url": FF_6_PORTFOLIOS_URL,
                "dataset": (
                    "6 Portfolios Formed on "
                    "Size and Book-to-Market (2 x 3)"
                ),
            },
            "fama_french_rf": {
                "provider": (
                    "Kenneth R. French Data Library"
                ),
                "url": FF_FACTORS_URL,
                "dataset": (
                    "Fama/French 3 Factors"
                ),
                "field": "RF",
            },
            "sp500": {
                "provider": "Yahoo Finance",
                "ticker": SP500_YAHOO_TICKER,
                "dataset": (
                    "S&P 500 Total Return Index"
                ),
            },
        },
        "files": files,
        "notes": [
            (
                "Fama-French source returns are retained "
                "in percent units at the acquisition stage."
            ),
            (
                "S&P 500 monthly returns are simple returns "
                "computed from the total-return index level "
                "and retained in decimal units."
            ),
            (
                "Unit normalization is intentionally deferred "
                "to the data-validation/processing stages."
            ),
        ],
    }


def write_artifact(
    artifact: dict,
) -> None:
    """Write acquisition evidence JSON."""

    with ACQUISITION_ARTIFACT.open(
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
    portfolios: pd.DataFrame,
    rf: pd.DataFrame,
    sp500: pd.DataFrame,
) -> None:

    print()
    print("=" * 70)
    print("BUFN741 DATA ACQUISITION COMPLETE")
    print("=" * 70)

    print()
    print("Fama-French 2x3 portfolios")
    print(
        f"  Rows:  {len(portfolios)}"
    )
    print(
        f"  Range: "
        f"{portfolios['date'].iloc[0]} "
        f"to {portfolios['date'].iloc[-1]}"
    )
    print(
        "  Unit:  percent"
    )

    print()
    print("Fama-French RF")
    print(
        f"  Rows:  {len(rf)}"
    )
    print(
        f"  Range: "
        f"{rf['date'].iloc[0]} "
        f"to {rf['date'].iloc[-1]}"
    )
    print(
        "  Unit:  percent"
    )

    print()
    print("S&P 500 Total Return Index")
    print(
        f"  Rows:  {len(sp500)}"
    )
    print(
        f"  Range: "
        f"{sp500['date'].iloc[0]} "
        f"to {sp500['date'].iloc[-1]}"
    )
    print(
        "  Unit:  decimal return"
    )

    print()
    print("Evidence artifact:")
    print(
        "  validation/artifacts/"
        "data_acquisition.json"
    )

    print()
    print(
        "IMPORTANT: Acquisition is complete, "
        "but data validation has NOT yet been performed."
    )

    print("=" * 70)


# =========================================================
# Main
# =========================================================

def main() -> int:

    ensure_directories()

    try:
        portfolios, rf = acquire_fama_french()

        print(
            "Downloading S&P 500 Total Return Index..."
        )

        sp500 = acquire_sp500_total_return()

        save_raw_data(
            portfolios,
            rf,
            sp500,
        )

        artifact = build_acquisition_artifact(
            portfolios,
            rf,
            sp500,
        )

        write_artifact(
            artifact
        )

        print_summary(
            portfolios,
            rf,
            sp500,
        )

        return 0

    except Exception as exc:

        print()
        print("=" * 70)
        print("DATA ACQUISITION FAILED")
        print("=" * 70)
        print()
        print(type(exc).__name__)
        print(str(exc))
        print()

        # A failed run must never leave a stale "passed"
        # artifact behind.
        if ACQUISITION_ARTIFACT.exists():
            ACQUISITION_ARTIFACT.unlink()

        return 1


if __name__ == "__main__":
    sys.exit(main())