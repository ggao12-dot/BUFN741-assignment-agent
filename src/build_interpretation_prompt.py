from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFIG_DIR = PROJECT_ROOT / "config"
TABLE_DIR = PROJECT_ROOT / "output" / "tables"
FIGURE_DIR = PROJECT_ROOT / "output" / "figures"
ARTIFACT_DIR = PROJECT_ROOT / "validation" / "artifacts"
REPORT_DIR = PROJECT_ROOT / "report"

SPEC_FILE = (
    CONFIG_DIR / "analysis_spec.yaml"
)

INSTRUCTION_FILE = (
    CONFIG_DIR / "interpretation_instructions.txt"
)

STATISTICS_FILE = (
    TABLE_DIR / "bkm_statistics_all_samples.csv"
)

QA_FILE = (
    ARTIFACT_DIR / "quality_assurance.json"
)

PROMPT_FILE = (
    REPORT_DIR / "interpretation_prompt.txt"
)


FIGURE_FILES = [
    "output/figures/histogram_normal_SP500.png",
    "output/figures/histogram_normal_Small_Growth.png",
    "output/figures/histogram_normal_Small_Value.png",
    "output/figures/histogram_normal_Big_Growth.png",
    "output/figures/histogram_normal_Big_Value.png",
    "output/figures/tail_comparison_ecdf.png",
]


# =========================================================
# Utilities
# =========================================================

def ensure_directories() -> None:
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def read_yaml(path: Path) -> dict:

    if not path.is_file():
        raise FileNotFoundError(
            f"Missing file: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return yaml.safe_load(file)


def read_json(path: Path) -> dict:

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


def read_text(path: Path) -> str:

    if not path.is_file():
        raise FileNotFoundError(
            f"Missing file: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )

    return path.read_text(
        encoding="utf-8"
    )


def load_statistics() -> pd.DataFrame:

    if not STATISTICS_FILE.is_file():
        raise FileNotFoundError(
            "Statistics table not found: "
            "output/tables/"
            "bkm_statistics_all_samples.csv"
        )

    return pd.read_csv(
        STATISTICS_FILE
    )


# =========================================================
# Preconditions
# =========================================================

def require_qa_pass(
    qa: dict,
) -> None:

    status = qa.get(
        "status"
    )

    if status != "passed":

        raise RuntimeError(
            "Quality assurance has not passed. "
            "Interpretation is blocked."
        )


def require_figures() -> None:

    missing = []

    for relative_path in FIGURE_FILES:

        path = (
            PROJECT_ROOT
            / relative_path
        )

        if not path.is_file():

            missing.append(
                relative_path
            )

    if missing:

        raise FileNotFoundError(
            "Required interpretation figures "
            f"are missing: {missing}"
        )


# =========================================================
# Assignment questions
# =========================================================

def build_questions(
    spec: dict,
) -> str:

    questions = spec.get(
        "analysis_questions",
        [],
    )

    if not questions:

        raise RuntimeError(
            "No analysis_questions found "
            "in analysis_spec.yaml."
        )

    lines = []

    for question in questions:

        question_id = question.get(
            "id",
            "UNKNOWN"
        )

        topic = question.get(
            "topic",
            ""
        )

        lines.append(
            f"{question_id}: {topic}"
        )

    return "\n".join(
        lines
    )


# =========================================================
# Prompt construction
# =========================================================

def build_prompt() -> str:

    instructions = read_text(
        INSTRUCTION_FILE
    )

    spec = read_yaml(
        SPEC_FILE
    )

    qa = read_json(
        QA_FILE
    )

    require_qa_pass(
        qa
    )

    require_figures()

    statistics = load_statistics()

    statistics_text = (
        statistics.to_csv(
            index=False,
            float_format="%.8f",
        )
    )

    questions = build_questions(
        spec
    )

    figure_text = "\n".join(
        f"- {path}"
        for path in FIGURE_FILES
    )

    qa_text = json.dumps(
        qa,
        indent=2,
    )

    prompt = f"""
You are operating inside the BUFN741 assignment research repository.

Your task is to produce:

report/economic_interpretation.md


PROJECT INTERPRETATION RULES
============================

{instructions}


ASSIGNMENT QUESTIONS
====================

{questions}


VALIDATED STATISTICAL TABLE
===========================

{statistics_text}


QUALITY ASSURANCE ARTIFACT
==========================

{qa_text}


FIGURES AVAILABLE IN THIS REPOSITORY
====================================

{figure_text}


EXECUTION INSTRUCTIONS
======================

1. Read the listed figures directly from the repository where useful.

2. Treat the supplied statistical table as numerically authoritative.

3. Do not recalculate statistics using an alternative methodology.

4. Write the final interpretation only to:

   report/economic_interpretation.md

5. Do not modify:
   - data files
   - processed data
   - statistical tables
   - figure files
   - workflow_state.json
   - validation artifacts
   - configuration files
   - source code

6. Use exactly the section structure specified in the project
   interpretation instructions.

7. Every important empirical conclusion should be traceable to:
   - a statistic,
   - a sample,
   - an asset,
   - or a supplied figure.

8. Clearly distinguish empirical evidence from economic interpretation.

9. Do not invent statistics or silently replace supplied values.

10. When finished, verify that:

    report/economic_interpretation.md

    exists and is non-empty.
""".strip()

    return prompt


# =========================================================
# Main
# =========================================================

def main() -> int:

    ensure_directories()

    try:

        prompt = build_prompt()

        PROMPT_FILE.write_text(
            prompt + "\n",
            encoding="utf-8",
        )

        print()
        print("=" * 72)
        print("BUFN741 INTERPRETATION PROMPT BUILDER")
        print("=" * 72)

        print()
        print(
            "Status: PASSED"
        )

        print()
        print(
            "Interpretation prompt created:"
        )

        print(
            "  report/interpretation_prompt.txt"
        )

        print()
        print(
            "Next step: run Codex from the "
            "repository root."
        )

        print("=" * 72)

        return 0

    except Exception as exc:

        print()
        print("=" * 72)
        print(
            "INTERPRETATION PROMPT BUILD FAILED"
        )
        print("=" * 72)

        print()
        print(
            type(exc).__name__
        )

        print(
            str(exc)
        )

        print()

        return 1


if __name__ == "__main__":
    sys.exit(main())