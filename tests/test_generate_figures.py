import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import generate_figures


def test_normal_pdf_at_mean():

    x = np.array(
        [0.0]
    )

    result = (
        generate_figures.normal_pdf(
            x,
            mean=0.0,
            std=1.0,
        )
    )

    expected = (
        1.0
        /
        np.sqrt(
            2.0 * np.pi
        )
    )

    assert result[0] == pytest.approx(
        expected
    )


def test_empirical_cdf():

    series = pd.Series(
        [
            0.03,
            -0.01,
            0.02,
        ]
    )

    x, y = (
        generate_figures.empirical_cdf(
            series
        )
    )

    assert list(x) == pytest.approx(
        [
            -0.01,
            0.02,
            0.03,
        ]
    )

    assert list(y) == pytest.approx(
        [
            1 / 3,
            2 / 3,
            1.0,
        ]
    )


def test_identify_extreme_months():

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2000-01-01",
                    "2000-02-01",
                    "2000-03-01",
                    "2000-04-01",
                ]
            ),
            "return": [
                0.01,
                -0.10,
                0.03,
                0.08,
            ],
        }
    )

    result = (
        generate_figures.identify_extreme_months(
            df,
            "return",
            n=2,
        )
    )

    values = sorted(
        result[
            "return"
        ].tolist()
    )

    assert values == pytest.approx(
        [
            -0.10,
            0.08,
        ]
    )


def test_expected_figure_count():

    assert (
        generate_figures
        .EXPECTED_FIGURE_COUNT
        == 11
    )


def test_asset_count():

    assert len(
        generate_figures.ASSETS
    ) == 5


def test_save_figure(
    tmp_path,
):

    fig, ax = plt.subplots()

    ax.plot(
        [1, 2, 3],
        [1, 4, 9],
    )

    path = (
        tmp_path
        / "test.png"
    )

    generate_figures.save_figure(
        fig,
        path,
    )

    assert path.is_file()

    assert (
        path.stat().st_size
        > 0
    )