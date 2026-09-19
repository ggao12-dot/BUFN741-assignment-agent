from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPORT_FILE = (
    PROJECT_ROOT
    / "report"
    / "economic_interpretation.md"
)

ARTIFACT_FILE = (
    PROJECT_ROOT
    / "validation"
    / "artifacts"
    / "economic_interpretation.json"
)


# =========================================================
# Required report structure
# =========================================================

REQUIRED_SECTIONS = [
    "## Q1 — Average Excess Returns and Sharpe Ratios",
    "## Q2 — Total and Downside Volatility",
    "## Q3 — Normality and Tail Risk",
    "## Q4 — Expected Shortfall versus VaR",
    "## Q5 — Distribution Differences Across Periods",
    "## Q6 — S&P 500 versus Fama-French Big Portfolios",
    "## Overall Empirical Takeaways",
]


# =========================================================
# Utilities
# =========================================================

def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(65536),
            b"",
        ):

            digest.update(
                chunk
            )

    return digest.hexdigest()


# =========================================================
# Report validation
# =========================================================

def validate_report(
    text: str,
) -> tuple[list[str], list[str]]:

    errors = []
    warnings = []

    if not text.strip():

        errors.append(
            "Interpretation report is empty."
        )

        return (
            errors,
            warnings,
        )

    for section in REQUIRED_SECTIONS:

        if section not in text:

            errors.append(
                f"Missing required section: "
                f"{section}"
            )

    for number in range(
        1,
        7,
    ):

        marker = (
            f"## Q{number}"
        )

        start = text.find(
            marker
        )

        if start == -1:
            continue

        if number < 6:

            next_marker = (
                f"## Q{number + 1}"
            )

        else:

            next_marker = (
                "## Overall Empirical Takeaways"
            )

        end = text.find(
            next_marker,
            start + 1,
        )

        if end == -1:

            end = len(
                text
            )

        section_text = (
            text[start:end]
        )

        if "Evidence:" not in section_text:

            errors.append(
                f"Q{number} missing "
                f"Evidence section."
            )

        if "Interpretation:" not in section_text:

            errors.append(
                f"Q{number} missing "
                f"Interpretation section."
            )

    if len(text) < 1500:

        warnings.append(
            "Interpretation report is "
            "unusually short."
        )

    return (
        errors,
        warnings,
    )


# =========================================================
# Artifact output
# =========================================================

def write_artifact(
    artifact: dict,
) -> None:

    ARTIFACT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARTIFACT_FILE.write_text(
        json.dumps(
            artifact,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


# =========================================================
# Main
# =========================================================

def main() -> int:

    try:

        if not REPORT_FILE.is_file():

            raise FileNotFoundError(
                "report/economic_interpretation.md "
                "does not exist."
            )

        text = REPORT_FILE.read_text(
            encoding="utf-8"
        )

        errors, warnings = (
            validate_report(
                text
            )
        )

        status = (
            "passed"
            if not errors
            else "failed"
        )

        artifact = {
            "stage": (
                "economic_interpretation"
            ),
            "status": status,
            "artifact_version": "1.0",
            "agent_runtime": (
                "Codex CLI"
            ),
            "authentication": (
                "ChatGPT OAuth via Codex"
            ),
            "output_file": (
                "report/"
                "economic_interpretation.md"
            ),
            "output_sha256": (
                sha256_file(
                    REPORT_FILE
                )
            ),
            "errors": errors,
            "warnings": warnings,
        }

        write_artifact(
            artifact
        )

        print()
        print("=" * 72)
        print(
            "BUFN741 ECONOMIC INTERPRETATION QA"
        )
        print("=" * 72)

        print()
        print(
            f"Status: {status.upper()}"
        )

        print()
        print(
            "Agent runtime: Codex CLI"
        )

        print(
            "Authentication: "
            "ChatGPT OAuth via Codex"
        )

        if warnings:

            print()
            print("Warnings:")

            for warning in warnings:

                print(
                    f"  - {warning}"
                )

        if errors:

            print()
            print("Errors:")

            for error in errors:

                print(
                    f"  - {error}"
                )

        print()
        print(
            "Evidence artifact:"
        )

        print(
            "  validation/artifacts/"
            "economic_interpretation.json"
        )

        print("=" * 72)

        return (
            0
            if status == "passed"
            else 1
        )

    except Exception as exc:

        print()
        print("=" * 72)
        print(
            "INTERPRETATION VALIDATION FAILED"
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