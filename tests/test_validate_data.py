
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import validate_data


def test_unit_inference_percent():
    series = pd.Series(
        [1.2, -2.3, 0.8, 3.1]
    )

    result = (
        validate_data.infer_unit_from_magnitude(
            series,
            "test",
        )
    )

    assert result["inferred_unit"] == "percent"


def test_unit_inference_decimal():
    series = pd.Series(
        [0.012, -0.023, 0.008, 0.031]
    )

    result = (
        validate_data.infer_unit_from_magnitude(
            series,
            "test",
        )
    )

    assert result["inferred_unit"] == "decimal"


def test_sample_count():
    df = pd.DataFrame(
        {
            "date": [
                "2000-01",
                "2000-02",
                "2000-03",
            ]
        }
    )

    count = validate_data.sample_count(
        df,
        "2000-01",
        "2000-02",
    )

    assert count == 2


def test_alignment_keeps_common_months_only():
    ff = pd.DataFrame(
        {
            "date": [
                "2000-01",
                "2000-02",
                "2000-03",
            ],
            "Small_Growth": [1, 2, 3],
            "Small_Value": [1, 2, 3],
            "Big_Growth": [1, 2, 3],
            "Big_Value": [1, 2, 3],
        }
    )

    rf = pd.DataFrame(
        {
            "date": [
                "2000-02",
                "2000-03",
            ],
            "RF": [0.4, 0.5],
        }
    )

    sp = pd.DataFrame(
        {
            "date": [
                "2000-01",
                "2000-02",
                "2000-03",
            ],
            "index_level": [
                100,
                101,
                102,
            ],
            "return_decimal": [
                None,
                0.01,
                0.0099,
            ],
        }
    )

    aligned = (
        validate_data.align_raw_datasets(
            ff,
            rf,
            sp,
        )
    )

    assert list(
        aligned["date"]
    ) == [
        "2000-02",
        "2000-03",
    ]
