import sys
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import process_data


def test_normalize_units():
    df = pd.DataFrame(
        {
            "date": ["2000-01"],
            "SP500": [0.02],
            "Small_Growth": [2.0],
            "Small_Value": [3.0],
            "Big_Growth": [1.5],
            "Big_Value": [2.5],
            "RF": [0.4],
        }
    )

    result = process_data.normalize_units(df)

    assert result.loc[0, "SP500"] == pytest.approx(0.02)
    assert result.loc[0, "Small_Growth"] == pytest.approx(0.02)
    assert result.loc[0, "Small_Value"] == pytest.approx(0.03)
    assert result.loc[0, "Big_Growth"] == pytest.approx(0.015)
    assert result.loc[0, "Big_Value"] == pytest.approx(0.025)
    assert result.loc[0, "RF"] == pytest.approx(0.004)


def test_construct_excess_returns():
    df = pd.DataFrame(
        {
            "date": ["2000-01"],
            "SP500": [0.02],
            "Small_Growth": [0.03],
            "Small_Value": [0.04],
            "Big_Growth": [0.025],
            "Big_Value": [0.035],
            "RF": [0.005],
        }
    )

    result = process_data.construct_excess_returns(df)

    assert result.loc[
        0,
        "SP500_excess",
    ] == pytest.approx(0.015)

    assert result.loc[
        0,
        "Small_Growth_excess",
    ] == pytest.approx(0.025)

    assert result.loc[
        0,
        "Small_Value_excess",
    ] == pytest.approx(0.035)


def test_excess_identity_passes():
    df = pd.DataFrame(
        {
            "SP500": [0.02],
            "Small_Growth": [0.03],
            "Small_Value": [0.04],
            "Big_Growth": [0.025],
            "Big_Value": [0.035],
            "RF": [0.005],
        }
    )

    df = process_data.construct_excess_returns(df)

    errors = process_data.validate_excess_identity(df)

    assert errors == []


def test_analysis_dataset_columns():
    df = pd.DataFrame(
        {
            "date": ["2000-01"],
            "SP500": [0.02],
            "Small_Growth": [0.03],
            "Small_Value": [0.04],
            "Big_Growth": [0.025],
            "Big_Value": [0.035],
            "RF": [0.005],
        }
    )

    df = process_data.construct_excess_returns(df)

    result = process_data.build_analysis_dataset(df)

    expected = [
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

    assert list(result.columns) == expected