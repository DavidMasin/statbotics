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
from src.data.main import update_curr_year  # noqa: E402
from src.data.tba import check_year_partial  # noqa: E402
from src.db.read import get_etags, get_events  # noqa: E402


if __name__ == "__main__":
    event_objs = get_events(year=CURR_YEAR)
    etags = get_etags(CURR_YEAR)

    if not check_year_partial(CURR_YEAR, event_objs, etags):
        print("No new TBA data for", CURR_YEAR, "- skipping update.")
    else:
        print("New TBA data found - running incremental update...")
        update_curr_year(partial=True)
        print("Incremental update complete.")
