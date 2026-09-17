import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import quality_assurance


def test_artifact_passed():

    artifact = {
        "status": "passed"
    }

    assert (
        quality_assurance
        .artifact_passed(
            artifact
        )
        is True
    )


def test_artifact_failed():

    artifact = {
        "status": "failed"
    }

    assert (
        quality_assurance
        .artifact_passed(
            artifact
        )
        is False
    )


def test_statistics_row_count():

    rows = []

    for sample in [
        "Full_History",
        "1990_2000",
        "2001_2010",
        "2011_Present",
    ]:

        for asset in [
            "SP500",
            "Small_Growth",
            "Small_Value",
            "Big_Growth",
            "Big_Value",
        ]:

            rows.append(
                {
                    "Sample": sample,
                    "Asset": asset,
                    "Usable_Months": 100,
                    "Mean_Excess_Annualized": 0.10,
                    "Std_Annualized": 0.20,
                    "Sharpe_Ratio": 0.50,
                    "Lower_Partial_Std_Annualized": 0.15,
                    "Skewness": -0.20,
                    "Excess_Kurtosis": 1.00,
                    "Empirical_VaR_1pct_Monthly": -0.10,
                    "Normal_VaR_1pct_Monthly": -0.08,
                    "Pct_Below_Mean_Minus_3SD": 0.50,
                    "Expected_Shortfall_1pct_Monthly": -0.15,
                }
            )

    df = pd.DataFrame(
        rows
    )

    errors, warnings, metadata = (
        quality_assurance
        .check_statistics_table(
            df
        )
    )

    assert errors == []

    assert (
        metadata["rows"]
        == 20
    )

    assert (
        metadata["asset_count"]
        == 5
    )

    assert (
        metadata["sample_count"]
        == 4
    )


def test_expected_shortfall_violation_detected():

    rows = []

    for sample in [
        "Full_History",
        "1990_2000",
        "2001_2010",
        "2011_Present",
    ]:

        for asset in [
            "SP500",
            "Small_Growth",
            "Small_Value",
            "Big_Growth",
            "Big_Value",
        ]:

            rows.append(
                {
                    "Sample": sample,
                    "Asset": asset,
                    "Usable_Months": 100,
                    "Mean_Excess_Annualized": 0.10,
                    "Std_Annualized": 0.20,
                    "Sharpe_Ratio": 0.50,
                    "Lower_Partial_Std_Annualized": 0.15,
                    "Skewness": -0.20,
                    "Excess_Kurtosis": 1.00,
                    "Empirical_VaR_1pct_Monthly": -0.10,
                    "Normal_VaR_1pct_Monthly": -0.08,
                    "Pct_Below_Mean_Minus_3SD": 0.50,
                    "Expected_Shortfall_1pct_Monthly": -0.15,
                }
            )

    df = pd.DataFrame(
        rows
    )

    # Deliberately violate ES <= VaR
    df.loc[
        0,
        "Expected_Shortfall_1pct_Monthly",
    ] = -0.05

    errors, _, _ = (
        quality_assurance
        .check_statistics_table(
            df
        )
    )

    assert any(
        "Expected shortfall"
        in error
        for error in errors
    )


def test_fixed_sample_counts():

    rows = []

    for asset in [
        "SP500",
        "Small_Growth",
        "Small_Value",
        "Big_Growth",
        "Big_Value",
    ]:

        rows.append(
            {
                "Sample": "1990_2000",
                "Asset": asset,
                "Usable_Months": 132,
            }
        )

        rows.append(
            {
                "Sample": "2001_2010",
                "Asset": asset,
                "Usable_Months": 120,
            }
        )

    df = pd.DataFrame(
        rows
    )

    errors, warnings = (
        quality_assurance
        .check_fixed_sample_counts(
            df
        )
    )

    assert errors == []


def test_sample_consistency():

    validation = {
        "common_sample": {
            "first_month": "1990-01",
            "last_month": "2026-07",
            "rows": 439,
        }
    }

    processing = {
        "first_month": "1990-01",
        "last_month": "2026-07",
        "observations": 439,
    }

    figures = {
        "sample": {
            "first_month": "1990-01",
            "last_month": "2026-07",
            "rows": 439,
        }
    }

    dataset = {
        "first_month": "1990-01",
        "last_month": "2026-07",
        "rows": 439,
    }

    errors, warnings = (
        quality_assurance
        .check_sample_consistency(
            validation,
            processing,
            figures,
            dataset,
        )
    )

    assert errors == []