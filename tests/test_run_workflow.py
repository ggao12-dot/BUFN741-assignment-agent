import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import run_workflow


def make_state(
    completed_through: str,
) -> dict:

    stages = {}

    completed = True

    for stage in (
        run_workflow
        .WORKFLOW_ORDER
    ):

        stages[stage] = {
            "status": (
                "complete"
                if completed
                else "not_started"
            )
        }

        if stage == completed_through:

            completed = False

    return {
        "project": (
            "BUFN741 Group Assignment 1"
        ),
        "stages": stages,
        "human_attention_required": False,
        "human_attention_reason": None,
    }


def test_next_stage_after_initialization():

    state = make_state(
        "project_initialized"
    )

    result = (
        run_workflow
        .determine_next_stage(
            state
        )
    )

    assert (
        result
        == "data_acquisition"
    )


def test_next_stage_after_processing():

    state = make_state(
        "data_processing"
    )

    result = (
        run_workflow
        .determine_next_stage(
            state
        )
    )

    assert (
        result
        == "statistical_analysis"
    )


def test_next_stage_after_qa():

    state = make_state(
        "quality_assurance"
    )

    result = (
        run_workflow
        .determine_next_stage(
            state
        )
    )

    assert (
        result
        == "economic_interpretation"
    )


def test_next_stage_after_interpretation():

    state = make_state(
        "economic_interpretation"
    )

    result = (
        run_workflow
        .determine_next_stage(
            state
        )
    )

    assert (
        result
        == "final_report"
    )


def test_all_complete():

    state = make_state(
        "final_report"
    )

    result = (
        run_workflow
        .determine_next_stage(
            state
        )
    )

    assert result is None


def test_stage_runner_mapping():

    expected = {
        "data_acquisition",
        "data_validation",
        "data_processing",
        "statistical_analysis",
        "figure_generation",
        "quality_assurance",
        "economic_interpretation",
        "final_report",
    }

    assert (
        set(
            run_workflow
            .STAGE_RUNNERS
            .keys()
        )
        == expected
    )


def test_final_report_authorized():

    assert (
        "final_report"
        in run_workflow
        .STAGE_RUNNERS
    )


def test_final_report_runner():

    runner = (
        run_workflow
        .STAGE_RUNNERS[
            "final_report"
        ]
    )

    assert (
        runner[-1]
        == "src/build_final_report.py"
    )