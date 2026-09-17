import math
import sys
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import analyze_statistics


def test_annualized_mean():

    series = pd.Series(
        [
            0.01,
            0.02,
            0.03,
        ]
    )

    result = (
        analyze_statistics.annualized_mean(
            series
        )
    )

    expected = (
        12.0 * 0.02
    )

    assert result == pytest.approx(
        expected
    )


def test_annualized_std():

    series = pd.Series(
        [
            0.01,
            0.02,
            0.03,
        ]
    )

    expected = (
        series.std(ddof=1)
        * math.sqrt(12.0)
    )

    result = (
        analyze_statistics.annualized_std(
            series
        )
    )

    assert result == pytest.approx(
        expected
    )


def test_sharpe_ratio():

    series = pd.Series(
        [
            0.01,
            0.02,
            0.03,
        ]
    )

    expected = (
        analyze_statistics.annualized_mean(
            series
        )
        /
        analyze_statistics.annualized_std(
            series
        )
    )

    result = (
        analyze_statistics.sharpe_ratio(
            series
        )
    )

    assert result == pytest.approx(
        expected
    )


def test_lower_partial_std():

    series = pd.Series(
        [
            -0.02,
            0.00,
            0.02,
            0.04,
        ]
    )

    mean_return = series.mean()

    downside = series[
        series < mean_return
    ]

    expected = math.sqrt(
        (
            (
                downside
                - mean_return
            )
            ** 2
        ).mean()
    ) * math.sqrt(12.0)

    result = (
        analyze_statistics
        .annualized_lower_partial_std(
            series
        )
    )

    assert result == pytest.approx(
        expected
    )


def test_normal_var():

    series = pd.Series(
        [
            -0.02,
            0.00,
            0.02,
            0.04,
        ]
    )

    expected = (
        series.mean()
        - 2.3263
        * series.std(ddof=1)
    )

    result = (
        analyze_statistics.normal_var_1pct(
            series
        )
    )

    assert result == pytest.approx(
        expected
    )


def test_expected_shortfall_not_above_var():

    series = pd.Series(
        [
            -0.20,
            -0.10,
            -0.05,
            0.00,
            0.05,
            0.10,
        ]
    )

    var = (
        analyze_statistics
        .empirical_var_1pct(
            series
        )
    )

    es = (
        analyze_statistics
        .expected_shortfall_1pct(
            series
        )
    )

    assert es <= var + 1e-12


def test_full_analysis_produces_20_rows():

    dates = pd.period_range(
        "1990-01",
        "2020-12",
        freq="M",
    ).astype(str)

    n = len(dates)

    df = pd.DataFrame(
        {
            "date": dates,
            "SP500_excess": [
                0.01
                + 0.001 * ((i % 7) - 3)
                for i in range(n)
            ],
            "Small_Growth_excess": [
                0.012
                + 0.002 * ((i % 9) - 4)
                for i in range(n)
            ],
            "Small_Value_excess": [
                0.013
                + 0.002 * ((i % 11) - 5)
                for i in range(n)
            ],
            "Big_Growth_excess": [
                0.011
                + 0.0015 * ((i % 8) - 4)
                for i in range(n)
            ],
            "Big_Value_excess": [
                0.012
                + 0.0015 * ((i % 10) - 5)
                for i in range(n)
            ],
        }
    )

    df["month"] = pd.PeriodIndex(
        df["date"],
        freq="M",
    )

    results = (
        analyze_statistics.run_analysis(
            df
        )
    )

    assert len(results) == 20

    assert (
        results["Asset"].nunique()
        == 5
    )

    assert (
        results["Sample"].nunique()
        == 4
    )