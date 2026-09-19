from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


STEPS = [
    {
        "name": "Build interpretation prompt",
        "command": [
            sys.executable,
            "src/build_interpretation_prompt.py",
        ],
    },
    {
        "name": "Run Codex interpretation agent",
        "command": [
            sys.executable,
            "src/run_codex_interpretation.py",
        ],
    },
    {
        "name": "Validate interpretation output",
        "command": [
            sys.executable,
            "src/validate_interpretation.py",
        ],
    },
]


def run_step(
    name: str,
    command: list[str],
) -> None:

    print()
    print("=" * 72)
    print(name.upper())
    print("=" * 72)
    print()

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"Stage step failed: {name}"
        )


def main() -> int:

    print()
    print("=" * 72)
    print("BUFN741 ECONOMIC INTERPRETATION STAGE")
    print("=" * 72)

    try:

        for step in STEPS:

            run_step(
                step["name"],
                step["command"],
            )

        print()
        print("=" * 72)
        print(
            "ECONOMIC INTERPRETATION STAGE PASSED"
        )
        print("=" * 72)

        print()
        print(
            "All interpretation steps completed successfully."
        )

        print()

        return 0

    except Exception as exc:

        print()
        print("=" * 72)
        print(
            "ECONOMIC INTERPRETATION STAGE FAILED"
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