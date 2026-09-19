from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROMPT_FILE = (
    PROJECT_ROOT
    / "report"
    / "interpretation_prompt.txt"
)

OUTPUT_REPORT = (
    PROJECT_ROOT
    / "report"
    / "economic_interpretation.md"
)


# =========================================================
# Preconditions
# =========================================================

def require_prompt_file() -> None:

    if not PROMPT_FILE.is_file():

        raise FileNotFoundError(
            "Missing prompt file: "
            "report/interpretation_prompt.txt"
        )

    if PROMPT_FILE.stat().st_size == 0:

        raise RuntimeError(
            "Interpretation prompt file is empty."
        )


def remove_old_report() -> None:
    """
    Remove stale output before running Codex.

    This prevents an old successful report from being
    mistaken for the output of the current execution.
    """

    if OUTPUT_REPORT.exists():

        OUTPUT_REPORT.unlink()


# =========================================================
# Codex execution
# =========================================================

def run_codex() -> subprocess.CompletedProcess:

    prompt_text = PROMPT_FILE.read_text(
        encoding="utf-8"
    )

    command = [
        "codex",
        "exec",
        "--sandbox",
        "workspace-write",
        "-",
    ]

    print()
    print("=" * 72)
    print("BUFN741 CODEX INTERPRETATION RUNNER")
    print("=" * 72)

    print()
    print(
        "Running Codex in non-interactive mode..."
    )

    print(
        "Sandbox: workspace-write"
    )

    print(
        "Prompt source: "
        "report/interpretation_prompt.txt"
    )

    print()

    result = subprocess.run(
        command,
        input=prompt_text,
        text=True,
        cwd=PROJECT_ROOT,
    )

    return result


# =========================================================
# Output validation
# =========================================================

def check_report_created() -> None:

    if not OUTPUT_REPORT.is_file():

        raise RuntimeError(
            "Codex completed but did not create "
            "report/economic_interpretation.md"
        )

    if OUTPUT_REPORT.stat().st_size == 0:

        raise RuntimeError(
            "Codex created an empty interpretation report."
        )


# =========================================================
# Main
# =========================================================

def main() -> int:

    try:

        require_prompt_file()

        remove_old_report()

        result = run_codex()

        if result.returncode != 0:

            raise RuntimeError(
                "Codex exited with non-zero return code: "
                f"{result.returncode}"
            )

        check_report_created()

        print()
        print("=" * 72)
        print("CODEX INTERPRETATION EXECUTION COMPLETE")
        print("=" * 72)

        print()
        print(
            "Report created:"
        )

        print(
            "  report/economic_interpretation.md"
        )

        print()
        print(
            "Next step:"
        )

        print(
            "  python src/validate_interpretation.py"
        )

        print("=" * 72)

        return 0

    except FileNotFoundError as exc:

        print()
        print("=" * 72)
        print("CODEX INTERPRETATION FAILED")
        print("=" * 72)

        print()
        print(
            "FileNotFoundError"
        )

        print(
            str(exc)
        )

        print()

        return 1

    except Exception as exc:

        print()
        print("=" * 72)
        print("CODEX INTERPRETATION FAILED")
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