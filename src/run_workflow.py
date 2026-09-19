from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

import yaml

import workflow


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STATE_FILE = (
    PROJECT_ROOT
    / "workflow_state.json"
)

RULES_FILE = (
    PROJECT_ROOT
    / "config"
    / "workflow_rules.yaml"
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
)

LOG_FILE = (
    LOG_DIR
    / "workflow_supervisor.log"
)


# =========================================================
# Stage → authorized execution module
# =========================================================

STAGE_RUNNERS = {
    "data_acquisition": [
        sys.executable,
        "src/acquire_data.py",
    ],
    "data_validation": [
        sys.executable,
        "src/validate_data.py",
    ],
    "data_processing": [
        sys.executable,
        "src/process_data.py",
    ],
    "statistical_analysis": [
        sys.executable,
        "src/analyze_statistics.py",
    ],
    "figure_generation": [
        sys.executable,
        "src/generate_figures.py",
    ],
    "quality_assurance": [
        sys.executable,
        "src/quality_assurance.py",
    ],
    "economic_interpretation": [
        sys.executable,
        "src/run_interpretation_stage.py",
    ],
}


# =========================================================
# Workflow order
# =========================================================

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


# =========================================================
# Logging
# =========================================================

def configure_logging() -> None:

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                LOG_FILE,
                encoding="utf-8",
            ),
            logging.StreamHandler(
                sys.stdout
            ),
        ],
    )


# =========================================================
# File utilities
# =========================================================

def load_json(
    path: Path,
) -> dict:

    if not path.is_file():

        raise FileNotFoundError(
            f"Missing file: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def save_json(
    path: Path,
    data: dict,
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
        )

        file.write("\n")


def load_yaml(
    path: Path,
) -> dict:

    if not path.is_file():

        raise FileNotFoundError(
            f"Missing file: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return yaml.safe_load(
            file
        )


# =========================================================
# State helpers
# =========================================================

def stage_status(
    state: dict,
    stage: str,
) -> str:

    return (
        state
        .get("stages", {})
        .get(stage, {})
        .get(
            "status",
            "unknown",
        )
    )


def determine_next_stage(
    state: dict,
) -> str | None:
    """
    Return the first stage that has not yet completed.
    """

    for stage in WORKFLOW_ORDER:

        if stage_status(
            state,
            stage,
        ) != "complete":

            return stage

    return None


def mark_human_attention(
    reason: str,
) -> None:

    state = load_json(
        STATE_FILE
    )

    state[
        "human_attention_required"
    ] = True

    state[
        "human_attention_reason"
    ] = reason

    save_json(
        STATE_FILE,
        state,
    )


def clear_human_attention() -> None:

    state = load_json(
        STATE_FILE
    )

    state[
        "human_attention_required"
    ] = False

    state[
        "human_attention_reason"
    ] = None

    save_json(
        STATE_FILE,
        state,
    )


# =========================================================
# Artifact validation
# =========================================================

def expected_artifact(
    stage: str,
    rules: dict,
) -> Path | None:

    stage_rules = (
        rules
        .get("stages", {})
        .get(stage, {})
    )

    artifact = (
        stage_rules.get(
            "required_artifact"
        )
    )

    if not artifact:

        return None

    return (
        PROJECT_ROOT
        / artifact
    )


def validate_artifact(
    stage: str,
    rules: dict,
) -> tuple[bool, str]:

    artifact_path = (
        expected_artifact(
            stage,
            rules,
        )
    )

    if artifact_path is None:

        return (
            True,
            "No artifact required.",
        )

    if not artifact_path.is_file():

        return (
            False,
            (
                "Required artifact missing: "
                f"{artifact_path.relative_to(PROJECT_ROOT)}"
            ),
        )

    try:

        artifact = load_json(
            artifact_path
        )

    except Exception as exc:

        return (
            False,
            (
                "Artifact could not be read: "
                f"{exc}"
            ),
        )

    if (
        artifact.get("stage")
        != stage
    ):

        return (
            False,
            (
                "Artifact stage mismatch: "
                f"expected {stage!r}, "
                f"found "
                f"{artifact.get('stage')!r}"
            ),
        )

    if (
        artifact.get("status")
        != "passed"
    ):

        return (
            False,
            (
                "Artifact did not pass: "
                f"status="
                f"{artifact.get('status')!r}"
            ),
        )

    return (
        True,
        str(
            artifact_path.relative_to(
                PROJECT_ROOT
            )
        ),
    )


# =========================================================
# Stage execution
# =========================================================

def run_stage(
    stage: str,
) -> int:

    command = (
        STAGE_RUNNERS.get(
            stage
        )
    )

    if command is None:

        raise RuntimeError(
            f"No authorized runner configured "
            f"for stage: {stage}"
        )

    logging.info(
        "Starting stage: %s",
        stage,
    )

    logging.info(
        "Command: %s",
        " ".join(command),
    )

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    logging.info(
        "Stage %s returned code %s",
        stage,
        result.returncode,
    )

    return result.returncode


# =========================================================
# Controlled stage completion
# =========================================================

def complete_stage(
    stage: str,
) -> None:
    """
    Delegate stage transition to the existing
    workflow controller rather than editing the
    completion status here.
    """

    command = [
        sys.executable,
        "src/workflow.py",
        "complete",
        stage,
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"Workflow controller refused "
            f"completion of stage: {stage}"
        )


# =========================================================
# One supervisor iteration
# =========================================================

def execute_next_stage(
    dry_run: bool = False,
) -> str:
    """
    Execute at most one incomplete stage.

    Returns:
        completed
        stopped
        finished
    """

    state = load_json(
        STATE_FILE
    )

    rules = load_yaml(
        RULES_FILE
    )

    if state.get(
        "human_attention_required",
        False,
    ):

        reason = state.get(
            "human_attention_reason"
        )

        logging.warning(
            "Human attention required: %s",
            reason,
        )

        return "stopped"

    stage = determine_next_stage(
        state
    )

    if stage is None:

        logging.info(
            "Workflow already complete."
        )

        return "finished"

    if stage == "project_initialized":

        raise RuntimeError(
            "Project initialization is "
            "not complete."
        )

    if stage not in STAGE_RUNNERS:

        logging.info(
            "No runner configured for "
            "stage '%s'.",
            stage,
        )

        return "stopped"

    logging.info(
        "Next stage: %s",
        stage,
    )

    if dry_run:

        logging.info(
            "DRY RUN — would execute: %s",
            " ".join(
                STAGE_RUNNERS[
                    stage
                ]
            ),
        )

        return "stopped"

    return_code = run_stage(
        stage
    )

    if return_code != 0:

        reason = (
            f"Stage {stage} failed "
            f"with exit code {return_code}."
        )

        mark_human_attention(
            reason
        )

        logging.error(
            reason
        )

        return "stopped"

    valid, message = (
        validate_artifact(
            stage,
            rules,
        )
    )

    if not valid:

        reason = (
            f"Stage {stage} produced "
            f"invalid evidence: {message}"
        )

        mark_human_attention(
            reason
        )

        logging.error(
            reason
        )

        return "stopped"

    logging.info(
        "Artifact passed: %s",
        message,
    )

    try:

        complete_stage(
            stage
        )

    except Exception as exc:

        reason = (
            f"Stage {stage} executed "
            f"successfully but workflow "
            f"transition failed: {exc}"
        )

        mark_human_attention(
            reason
        )

        logging.error(
            reason
        )

        return "stopped"

    logging.info(
        "Stage completed: %s",
        stage,
    )

    return "completed"


# =========================================================
# Supervisor loop
# =========================================================

def run_supervisor(
    once: bool = False,
    dry_run: bool = False,
) -> int:

    logging.info(
        "BUFN741 workflow supervisor started."
    )

    while True:

        result = execute_next_stage(
            dry_run=dry_run
        )

        if result == "completed":

            if once:

                logging.info(
                    "--once requested; stopping."
                )

                return 0

            continue

        if result == "finished":

            logging.info(
                "All workflow stages complete."
            )

            return 0

        if result == "stopped":

            state = load_json(
                STATE_FILE
            )

            next_stage = determine_next_stage(
                state
            )

            if (
                next_stage
                and next_stage
                not in STAGE_RUNNERS
                and not state.get(
                    "human_attention_required",
                    False,
                )
            ):

                logging.info(
                    "Supervisor stopped normally "
                    "before unimplemented stage: %s",
                    next_stage,
                )

                return 0

            return 1


# =========================================================
# CLI
# =========================================================

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Execute the BUFN741 workflow "
            "under controlled stage gates."
        )
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "Execute at most one stage."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show the next stage without "
            "executing it."
        ),
    )

    parser.add_argument(
        "--clear-attention",
        action="store_true",
        help=(
            "Clear a previously recorded "
            "human-attention condition."
        ),
    )

    return parser.parse_args()


def main() -> int:

    configure_logging()

    args = parse_args()

    try:

        if args.clear_attention:

            clear_human_attention()

            logging.info(
                "Human-attention flag cleared."
            )

            return 0

        return run_supervisor(
            once=args.once,
            dry_run=args.dry_run,
        )

    except KeyboardInterrupt:

        logging.warning(
            "Supervisor interrupted by user."
        )

        return 130

    except Exception as exc:

        logging.exception(
            "Supervisor failed: %s",
            exc,
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())