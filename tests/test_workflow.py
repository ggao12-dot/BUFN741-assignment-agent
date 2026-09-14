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



def test_previous_stage_logic():
    assert workflow.previous_stage(
        "data_validation"
    ) == "data_acquisition"


def test_first_stage_has_no_previous_stage():
    assert workflow.previous_stage(
        "project_initialized"
    ) is None


def test_invalid_stage_artifact_fails(tmp_path, monkeypatch):
    fake_artifact = {
        "stage": "data_acquisition",
        "status": "failed",
    }

    artifact_dir = tmp_path / "validation" / "artifacts"
    artifact_dir.mkdir(parents=True)

    artifact_path = (
        artifact_dir / "data_acquisition.json"
    )

    artifact_path.write_text(
        __import__("json").dumps(fake_artifact),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        workflow,
        "PROJECT_ROOT",
        tmp_path,
    )

    ok, errors = workflow.validate_stage_artifact(
        "data_acquisition"
    )

    assert ok is False
    assert len(errors) > 0