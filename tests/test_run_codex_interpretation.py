import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import run_codex_interpretation
import run_interpretation_stage


def test_prompt_path_name():

    assert (
        run_codex_interpretation
        .PROMPT_FILE
        .name
        == "interpretation_prompt.txt"
    )


def test_output_report_name():

    assert (
        run_codex_interpretation
        .OUTPUT_REPORT
        .name
        == "economic_interpretation.md"
    )


def test_interpretation_stage_has_three_steps():

    assert (
        len(
            run_interpretation_stage.STEPS
        )
        == 3
    )


def test_first_step_builds_prompt():

    first = (
        run_interpretation_stage
        .STEPS[0]
    )

    assert (
        "build_interpretation_prompt.py"
        in first["command"][-1]
    )


def test_second_step_runs_codex():

    second = (
        run_interpretation_stage
        .STEPS[1]
    )

    assert (
        "run_codex_interpretation.py"
        in second["command"][-1]
    )


def test_third_step_validates():

    third = (
        run_interpretation_stage
        .STEPS[2]
    )

    assert (
        "validate_interpretation.py"
        in third["command"][-1]
    )