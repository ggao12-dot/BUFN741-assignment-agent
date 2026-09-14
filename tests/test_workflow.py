import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import workflow


def test_workflow_order_starts_with_initialization():
    assert workflow.WORKFLOW_ORDER[0] == "project_initialized"


def test_workflow_order_ends_with_final_report():
    assert workflow.WORKFLOW_ORDER[-1] == "final_report"


def test_required_asset_count():
    spec = workflow.load_yaml(workflow.SPEC_FILE)

    assets = spec["data"]["assets"]

    assert len(assets) == 5


def test_required_statistics_count():
    spec = workflow.load_yaml(workflow.SPEC_FILE)

    statistics = spec["statistics"]

    assert len(statistics) == 10


def test_analysis_question_count():
    spec = workflow.load_yaml(workflow.SPEC_FILE)

    questions = spec["analysis_questions"]

    assert len(questions) == 6