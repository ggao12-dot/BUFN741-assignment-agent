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

    # In normal human-readable mode, print the header.
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
    # Load configuration
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
    # Validate specification
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
    # Machine-readable JSON mode
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