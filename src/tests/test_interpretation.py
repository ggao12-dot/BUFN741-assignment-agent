import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

import build_interpretation_prompt
import validate_interpretation


def test_required_sections_count():

    assert (
        len(
            validate_interpretation
            .REQUIRED_SECTIONS
        )
        == 7
    )


def test_build_questions():

    spec = {
        "analysis_questions": [
            {
                "id": "Q1",
                "topic": "First topic",
            },
            {
                "id": "Q2",
                "topic": "Second topic",
            },
        ]
    }

    result = (
        build_interpretation_prompt
        .build_questions(
            spec
        )
    )

    assert (
        "Q1: First topic"
        in result
    )

    assert (
        "Q2: Second topic"
        in result
    )


def test_qa_pass():

    qa = {
        "status": "passed"
    }

    build_interpretation_prompt.require_qa_pass(
        qa
    )


def test_qa_failure_blocks():

    qa = {
        "status": "failed"
    }

    try:

        build_interpretation_prompt.require_qa_pass(
            qa
        )

        assert False

    except RuntimeError:

        assert True


def test_valid_report_structure():

    sections = []

    headings = (
        validate_interpretation
        .REQUIRED_SECTIONS
    )

    for heading in headings[:6]:

        sections.append(
            f"{heading}\n\n"
            "Evidence:\n"
            "Some validated evidence.\n\n"
            "Interpretation:\n"
            "Some interpretation."
        )

    sections.append(
        headings[6]
        + "\n\n"
        + "Overall synthesis."
    )

    text = "\n\n".join(
        sections
    )

    errors, warnings = (
        validate_interpretation
        .validate_report(
            text
        )
    )

    assert errors == []


def test_missing_evidence_detected():

    text = """
## Q1 — Average Excess Returns and Sharpe Ratios

Interpretation:
Interpretation only.

## Q2 — Total and Downside Volatility

Evidence:
Evidence.

Interpretation:
Interpretation.

## Q3 — Normality and Tail Risk

Evidence:
Evidence.

Interpretation:
Interpretation.

## Q4 — Expected Shortfall versus VaR

Evidence:
Evidence.

Interpretation:
Interpretation.

## Q5 — Distribution Differences Across Periods

Evidence:
Evidence.

Interpretation:
Interpretation.

## Q6 — S&P 500 versus Fama-French Big Portfolios

Evidence:
Evidence.

Interpretation:
Interpretation.

## Overall Empirical Takeaways

Summary.
"""

    errors, warnings = (
        validate_interpretation
        .validate_report(
            text
        )
    )

    assert any(
        "Q1 missing Evidence section"
        in error
        for error in errors
    )