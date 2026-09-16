from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import wrds


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
ARTIFACT_DIR = (
    PROJECT_ROOT
    / "validation"
    / "artifacts"
)

ARTIFACT_FILE = (
    ARTIFACT_DIR
    / "data_acquisition.json"
)


def ensure_directories():
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def connect_wrds():
    print("Connecting to WRDS...")
    print(
        "If WRDS requests MFA, "
        "approve the Duo Push."
    )

    db = wrds.Connection()

    print("WRDS connection established.")

    return db


def discover_library(
    db,
    keyword: str,
) -> list[str]:

    libraries = db.list_libraries()

    return [
        library
        for library in libraries
        if keyword.lower()
        in library.lower()
    ]


def inspect_table(
    db,
    library: str,
    table: str,
) -> pd.DataFrame:

    return db.describe_table(
        library=library,
        table=table,
    )


def query_wrds(
    db,
    sql: str,
) -> pd.DataFrame:

    return db.raw_sql(
        sql,
        date_cols=["date"],
    )


def write_artifact(
    sources: dict,
    files: dict,
):

    artifact = {
        "stage": "data_acquisition",
        "status": "passed",
        "backend": "WRDS",
        "retrieved_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "sources": sources,
        "files": files,
    }

    with ARTIFACT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            artifact,
            file,
            indent=2,
        )

        file.write("\n")


def main() -> int:

    ensure_directories()

    db = None

    try:
        db = connect_wrds()

        libraries = db.list_libraries()

        print()
        print("Relevant WRDS libraries:")

        for library in libraries:
            if (
                "ff" in library.lower()
                or "crsp" in library.lower()
            ):
                print(
                    f"  {library}"
                )

        print()
        print(
            "WRDS discovery completed."
        )

        return 0

    except Exception as exc:

        print()
        print("WRDS ACQUISITION FAILED")
        print(type(exc).__name__)
        print(str(exc))

        return 1

    finally:

        if db is not None:
            db.close()


if __name__ == "__main__":
    sys.exit(main())