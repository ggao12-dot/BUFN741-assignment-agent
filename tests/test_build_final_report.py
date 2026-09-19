import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import build_final_report
import run_workflow


def test_final_report_runner_registered():

    assert (
        "final_report"
        in run_workflow.STAGE_RUNNERS
    )


def test_final_report_is_last_stage():

    assert (
        run_workflow.WORKFLOW_ORDER[-1]
        == "final_report"
    )


def test_format_percent():

    result = (
        build_final_report
        .format_percent(
            0.1234
        )
    )

    assert (
        result
        == "12.34%"
    )


def test_format_number():

    result = (
        build_final_report
        .format_number(
            0.45678
        )
    )

    assert (
        result
        == "0.457"
    )


def test_statistics_formatting():

    df = pd.DataFrame(
        {
            "Sample": [
                "Full_History"
            ],
            "Asset": [
                "SP500"
            ],
            "Mean_Excess_Annualized": [
                0.08
            ],
            "Std_Annualized": [
                0.16
            ],
            "Sharpe_Ratio": [
                0.50
            ],
            "Lower_Partial_Std_Annualized": [
                0.12
            ],
            "Skewness": [
                -0.40
            ],
            "Excess_Kurtosis": [
                2.50
            ],
            "Empirical_VaR_1pct_Monthly": [
                -0.10
            ],
            "Normal_VaR_1pct_Monthly": [
                -0.08
            ],
            "Pct_Below_Mean_Minus_3SD": [
                0.50
            ],
            "Expected_Shortfall_1pct_Monthly": [
                -0.15
            ],
        }
    )

    result = (
        build_final_report
        .format_statistics_table(
            df
        )
    )

    assert (
        result.loc[
            0,
            "Mean_Excess_Annualized",
        ]
        == "8.00%"
    )

    assert (
        result.loc[
            0,
            "Sharpe_Ratio",
        ]
        == "0.500"
    )

    assert (
        result.loc[
            0,
            "Empirical_VaR_1pct_Monthly",
        ]
        == "-10.00%"
    )