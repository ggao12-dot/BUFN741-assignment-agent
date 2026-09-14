from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SPEC_FILE = PROJECT_ROOT / "config" / "analysis_spec.yaml"
STATE_FILE = PROJECT_ROOT / "workflow_state.json"
RULES_FILE = PROJECT_ROOT / "config" / "workflow_rules.yaml"
ASSIGNMENT_FILE = PROJECT_ROOT / "assignment" / "Assignment_1.docx"


REQUIRED_DIRECTORIES = [
    "assignment",
    "config",
    "data/raw",
    "data/processed",
    "src",
    "tests",
    "validation",
    "output/tables",
    "output/figures",
    "report",
    "logs",
]


WORKFLOW_ORDER = [
    "project_initialized",
    "data_acquisition",
    "data_validation",
    "data_processing",
    "statistical_analysis",
    "figure_generation",
    "quality_assurance",
    "economic_interpretation",
    "final_report",
]


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def load_yaml(path: Path) -> dict:
    """Load and return a YAML file."""
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_json(path: Path) -> dict:
    """Load and return a JSON file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)

def save_json(path: Path, data: dict) -> None:
    """Write dictionary data to JSON."""
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")

def check_required_directories() -> tuple[bool, list[str]]:
    """Check whether all required project directories exist."""
    missing = []

    for directory in REQUIRED_DIRECTORIES:
        path = PROJECT_ROOT / directory

        if not path.is_dir():
            missing.append(directory)

    return len(missing) == 0, missing


def check_required_files() -> tuple[bool, list[str]]:
    """Check whether core project files exist."""
    required_files = [
        SPEC_FILE,
        STATE_FILE,
        RULES_FILE,
        ASSIGNMENT_FILE,
    ]

    missing = []

    for path in required_files:
        if not path.is_file():
            missing.append(str(path.relative_to(PROJECT_ROOT)))

    return len(missing) == 0, missing

def validate_spec(spec: dict) -> tuple[bool, list[str]]:
    """Perform basic structural validation of analysis_spec.yaml."""
    errors = []

    required_top_level_sections = [
        "project",
        "data",
        "analysis_variable",
        "samples",
        "statistics",
        "validation",
        "figures",
        "analysis_questions",
        "human_escalation",
        "reproducibility",
    ]

    for section in required_top_level_sections:
        if section not in spec:
            errors.append(f"Missing specification section: {section}")

    assets = spec.get("data", {}).get("assets", [])

    if len(assets) != 5:
        errors.append(
            f"Expected 5 test assets, found {len(assets)}."
        )

    statistics = spec.get("statistics", [])

    if len(statistics) != 10:
        errors.append(
            f"Expected 10 required statistics, found {len(statistics)}."
        )

    questions = spec.get("analysis_questions", [])

    if len(questions) != 6:
        errors.append(
            f"Expected 6 analysis questions, found {len(questions)}."
        )

    return len(errors) == 0, errors


def validate_state(state: dict) -> tuple[bool, list[str]]:
    """Perform basic validation of workflow_state.json."""
    errors = []

    if "current_stage" not in state:
        errors.append("workflow_state.json has no current_stage.")

    if "stages" not in state:
        errors.append("workflow_state.json has no stages section.")
        return False, errors

    for stage in WORKFLOW_ORDER:
        if stage not in state["stages"]:
            errors.append(f"Workflow state missing stage: {stage}")

    return len(errors) == 0, errors


def determine_next_stage(state: dict) -> str | None:
    """
    Return the first workflow stage that is not complete.

    Return None if every stage is complete.
    """
    stages = state["stages"]

    for stage in WORKFLOW_ORDER:
        status = stages[stage].get("status")

        if status != "complete":
            return stage

    return None

def check_stage_artifacts(
    stage: str,
    rules: dict,
) -> tuple[bool, list[str]]:
    """Check whether all required artifacts for a stage exist."""

    stage_rules = rules.get("stages", {}).get(stage)

    if stage_rules is None:
        return False, [f"No workflow rules defined for stage: {stage}"]

    required_artifacts = stage_rules.get(
        "required_artifacts",
        [],
    )

    missing = []

    for artifact in required_artifacts:
        path = PROJECT_ROOT / artifact

        if not path.is_file():
            missing.append(artifact)

    return len(missing) == 0, missing

def previous_stage(stage: str) -> str | None:
    """Return the workflow stage immediately preceding the given stage."""

    index = WORKFLOW_ORDER.index(stage)

    if index == 0:
        return None

    return WORKFLOW_ORDER[index - 1]

def previous_stage_complete(
    stage: str,
    state: dict,
) -> bool:
    """Check whether the immediately preceding stage is complete."""

    prev = previous_stage(stage)

    if prev is None:
        return True

    return (
        state["stages"][prev].get("status")
        == "complete"
    )

def load_stage_artifact(stage: str) -> dict | None:
    """Load a stage validation artifact if it exists."""

    path = (
        PROJECT_ROOT
        / "validation"
        / "artifacts"
        / f"{stage}.json"
    )

    if not path.is_file():
        return None

    return load_json(path)


def validate_stage_artifact(
    stage: str,
) -> tuple[bool, list[str]]:
    """Validate the contents of a stage evidence artifact."""

    errors = []

    artifact = load_stage_artifact(stage)

    if artifact is None:
        return False, [
            f"No evidence artifact found for {stage}."
        ]

    if artifact.get("stage") != stage:
        errors.append(
            f"Artifact stage mismatch: "
            f"expected {stage}, "
            f"found {artifact.get('stage')}."
        )

    if artifact.get("status") != "passed":
        errors.append(
            "Artifact status must be 'passed'."
        )

    return len(errors) == 0, errors

def complete_stage(
    stage: str,
    state: dict,
    rules: dict,
) -> tuple[bool, str]:
    """
    Attempt to mark a workflow stage complete.

    Completion is permitted only if:
    1. the stage is valid;
    2. the previous stage is complete;
    3. all required artifacts exist;
    4. the stage artifact itself is valid.
    """

    if stage not in WORKFLOW_ORDER:
        return False, f"Unknown workflow stage: {stage}"

    if state["stages"][stage].get("status") == "complete":
        return False, f"Stage already complete: {stage}"

    if not previous_stage_complete(stage, state):
        prev = previous_stage(stage)

        return (
            False,
            f"Cannot complete {stage}: "
            f"previous stage {prev} is not complete.",
        )

    artifacts_ok, missing = check_stage_artifacts(
        stage,
        rules,
    )

    if not artifacts_ok:
        message = (
            f"Cannot complete {stage}: "
            "required artifacts are missing:\n"
        )

        for artifact in missing:
            message += f"  - {artifact}\n"

        return False, message.rstrip()

    artifact_valid, artifact_errors = validate_stage_artifact(
        stage
    )

    if not artifact_valid:
        message = (
            f"Cannot complete {stage}: "
            "artifact validation failed:\n"
        )

        for error in artifact_errors:
            message += f"  - {error}\n"

        return False, message.rstrip()

    state["stages"][stage]["status"] = "complete"
    state["current_stage"] = stage
    state["last_successful_stage"] = stage

    save_json(STATE_FILE, state)

    return True, f"Stage completed successfully: {stage}"

def build_status_report(spec: dict, state: dict) -> dict:
    """Create a machine-readable project status report."""

    next_stage = determine_next_stage(state)

    return {
        "project": state["project"],
        "workflow_version": state["workflow_version"],
        "current_stage": state["current_stage"],
        "next_stage": next_stage,
        "human_attention_required": state.get(
            "human_attention_required",
            False,
        ),
        "human_attention_reason": state.get(
            "human_attention_reason"
        ),
        "research_design": {
            "asset_count": len(spec["data"]["assets"]),
            "sample_count": len(spec["samples"]),
            "statistic_count": len(spec["statistics"]),
        },
    }


def print_header() -> None:
    print()
    print("=" * 60)
    print("BUFN741 Assignment Agent")
    print("=" * 60)


# ---------------------------------------------------------
# Main workflow inspection
# ---------------------------------------------------------

def main() -> int:
    json_mode = "--json" in sys.argv

    command = None
    command_stage = None

    # -----------------------------------------------------
    # Parse commands
    # -----------------------------------------------------

    if len(sys.argv) >= 2:
        if sys.argv[1] == "complete":
            command = "complete"

            if len(sys.argv) < 3:
                print(
                    "Usage: python src/workflow.py "
                    "complete <stage>"
                )
                return 1

            command_stage = sys.argv[2]

    # -----------------------------------------------------
    # Human-readable header
    # -----------------------------------------------------

    if not json_mode:
        print_header()
        print(f"Project root: {PROJECT_ROOT}")
        print()

    # -----------------------------------------------------
    # Check repository structure
    # -----------------------------------------------------

    directories_ok, missing_directories = check_required_directories()
    files_ok, missing_files = check_required_files()

    if not json_mode:
        print("PROJECT STRUCTURE")
        print("-" * 60)

        if directories_ok:
            print("[PASS] Required directories found.")
        else:
            print("[FAIL] Missing directories:")
            for directory in missing_directories:
                print(f"       - {directory}")

        if files_ok:
            print("[PASS] Required project files found.")
        else:
            print("[FAIL] Missing files:")
            for filename in missing_files:
                print(f"       - {filename}")

        print()

    if not directories_ok or not files_ok:
        if json_mode:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": "project_structure_invalid",
                        "missing_directories": missing_directories,
                        "missing_files": missing_files,
                    },
                    indent=2,
                )
            )
        else:
            print("Project validation failed.")
            print("Repair the project structure before proceeding.")

        return 1

    # -----------------------------------------------------
    # Load analysis specification
    # -----------------------------------------------------

    try:
        spec = load_yaml(SPEC_FILE)
    except Exception as exc:
        if json_mode:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": "spec_load_failed",
                        "message": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print("[FAIL] Could not read analysis_spec.yaml")
            print(f"       {exc}")

        return 1

    # -----------------------------------------------------
    # Load workflow state
    # -----------------------------------------------------

    try:
        state = load_json(STATE_FILE)
    except Exception as exc:
        if json_mode:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": "state_load_failed",
                        "message": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print("[FAIL] Could not read workflow_state.json")
            print(f"       {exc}")

        return 1

    # -----------------------------------------------------
    # Load workflow rules
    # -----------------------------------------------------

    try:
        rules = load_yaml(RULES_FILE)
    except Exception as exc:
        if json_mode:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": "rules_load_failed",
                        "message": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print("[FAIL] Could not read workflow_rules.yaml")
            print(f"       {exc}")

        return 1

    # -----------------------------------------------------
    # Validate research specification
    # -----------------------------------------------------

    spec_ok, spec_errors = validate_spec(spec)

    if not json_mode:
        print("RESEARCH SPECIFICATION")
        print("-" * 60)

        if spec_ok:
            print("[PASS] analysis_spec.yaml is structurally valid.")
        else:
            print("[FAIL] Specification problems:")
            for error in spec_errors:
                print(f"       - {error}")

        print()

    # -----------------------------------------------------
    # Validate workflow state
    # -----------------------------------------------------

    state_ok, state_errors = validate_state(state)

    if not json_mode:
        print("WORKFLOW STATE")
        print("-" * 60)

        if state_ok:
            print("[PASS] workflow_state.json is structurally valid.")
        else:
            print("[FAIL] Workflow-state problems:")
            for error in state_errors:
                print(f"       - {error}")

        print()

    # -----------------------------------------------------
    # Stop if validation failed
    # -----------------------------------------------------

    if not spec_ok or not state_ok:
        if json_mode:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": "workflow_validation_failed",
                        "spec_errors": spec_errors,
                        "state_errors": state_errors,
                    },
                    indent=2,
                )
            )
        else:
            print("Workflow validation failed.")

        return 1

    # -----------------------------------------------------
    # Execute "complete <stage>" command
    # -----------------------------------------------------

    if command == "complete":
        success, message = complete_stage(
            command_stage,
            state,
            rules,
        )

        if json_mode:
            print(
                json.dumps(
                    {
                        "success": success,
                        "stage": command_stage,
                        "message": message,
                    },
                    indent=2,
                )
            )
        else:
            print(message)

        return 0 if success else 1

    # -----------------------------------------------------
    # Machine-readable JSON status mode
    # -----------------------------------------------------

    if json_mode:
        report = build_status_report(spec, state)
        print(json.dumps(report, indent=2))
        return 0

    # -----------------------------------------------------
    # Human-readable workflow status
    # -----------------------------------------------------

    current_stage = state["current_stage"]
    next_stage = determine_next_stage(state)

    human_attention = state.get(
        "human_attention_required",
        False,
    )

    human_reason = state.get(
        "human_attention_reason"
    )

    print("WORKFLOW STATUS")
    print("-" * 60)

    print(f"Current stage: {current_stage}")

    if next_stage is None:
        print("Next stage:    WORKFLOW COMPLETE")
    else:
        print(f"Next stage:    {next_stage}")

    print()

    if human_attention:
        print("Human attention required: YES")

        if human_reason:
            print(f"Reason: {human_reason}")
    else:
        print("Human attention required: NO")

    print()

    # -----------------------------------------------------
    # Summary of research specification
    # -----------------------------------------------------

    assets = spec["data"]["assets"]
    samples = spec["samples"]
    statistics = spec["statistics"]

    print("RESEARCH DESIGN SUMMARY")
    print("-" * 60)

    print(f"Assets:     {len(assets)}")
    print(f"Samples:    {len(samples)}")
    print(f"Statistics: {len(statistics)}")

    print()

    print("Assets:")
    for asset in assets:
        print(f"  - {asset['id']}")

    print()
    print("=" * 60)

    if next_stage:
        print(f"READY FOR NEXT STAGE: {next_stage}")
    else:
        print("WORKFLOW COMPLETE")

    print("=" * 60)
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())