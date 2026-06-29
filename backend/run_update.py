"""Incremental update of the current year (run on a schedule during competition).

Re-checks The Blue Alliance for new events / matches / rankings for CURR_YEAR
and, if there is anything new, recomputes and writes the current year (EPA
included). This is the loop that keeps the site current as a competition runs.

  python run_update.py

Uses the same env as the web service:
  DATABASE_URL   Postgres-wire connection string.
  SKIP_GCS=True  Skip the GCS upload (no Google Cloud creds needed).

Run the full rebuild (run_full_rebuild.py) once first to create the schema and
load history; this script assumes the current year already exists in the DB.
"""

from dotenv import load_dotenv  # type: ignore

load_dotenv()

# Importing the models package registers every ORM table on Base.metadata.
import src.db.models  # noqa: F401,E402
from src.constants import CURR_YEAR  # noqa: E402
from src.data.main import run_incremental_update  # noqa: E402


if __name__ == "__main__":
    if run_incremental_update():
        print("Incremental update complete.")
    else:
        print("No new TBA data for", CURR_YEAR, "- skipping update.")
