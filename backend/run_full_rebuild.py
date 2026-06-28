"""One-off full EPA rebuild from 2002..CURR_YEAR.

This drives the same `reset_all_years()` pipeline the data service uses, but as a
standalone command so it can be run as a one-off job (e.g. on Railway) without
going through the HTTP layer.

  poetry run python run_full_rebuild.py

Required / useful environment variables:
  DATABASE_URL   Postgres-wire connection string (Railway Postgres, etc.).
                 Overrides the default local CockroachDB. Bare "postgres://" /
                 "postgresql://" URLs are normalized to the psycopg2 driver.
  SKIP_GCS=True  Skip the current-year GCS upload (no Google Cloud creds needed).

NOTE: reset_all_years() only runs when the database is empty (it no-ops if any
year rows already exist), so point it at a fresh database.
"""

import re

from dotenv import load_dotenv  # type: ignore

load_dotenv()

# Importing the models package registers every ORM table on Base.metadata so
# that clean_db()'s create_all() builds the full schema.
import src.db.models  # noqa: F401,E402
from src.constants import CONN_STR, SKIP_GCS  # noqa: E402
from src.data.main import reset_all_years  # noqa: E402
from src.db.read.year import get_num_years  # noqa: E402


def _redacted(conn_str: str) -> str:
    # Hide any password between "://user:" and the "@host".
    return re.sub(r"(://[^:/@]+:)[^@]*(@)", r"\1***\2", conn_str)


if __name__ == "__main__":
    print(f"CONN_STR: {_redacted(CONN_STR)}")
    print(f"SKIP_GCS: {SKIP_GCS}")

    try:
        existing = get_num_years()
    except Exception:
        existing = 0
    if existing > 0:
        print(
            f"Database already has {existing} year(s) of data. "
            "reset_all_years() only runs on an empty database — it will no-op. "
            "Point at a fresh database (or drop the tables) to rebuild."
        )

    print("Starting full rebuild (2002..CURR_YEAR)...")
    reset_all_years()
    print("Full rebuild complete.")
