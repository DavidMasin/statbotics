# Running the full EPA rebuild on Railway

This is a runbook for doing a **full rebuild from scratch** (every team / event /
match / EPA rating for 2002 → `CURR_YEAR`) against a **Railway Postgres**
database, instead of the production CockroachDB.

It drives the same `reset_all_years()` pipeline the data service uses, via the
standalone `backend/run_full_rebuild.py` entry point (the HTTP
`/v3/data/reset_all_years` endpoint is intentionally stubbed out).

## Why this works without CockroachDB

The app's schema uses only standard column types and the upsert path uses
standard PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`, so it runs unchanged on
vanilla Postgres. Two small hooks make it Railway-friendly:

- `DATABASE_URL` (or `LOCAL_CONN_STR`) overrides the connection string and is
  normalized to the `postgresql+psycopg2://` driver (see `src/constants.py`).
- `SKIP_GCS=True` skips the current-year Google Cloud Storage upload, which
  needs GCP credentials Railway won't have (see `src/constants.py` /
  `src/data/main.py`).

The TBA API key is hardcoded in `src/tba/constants.py`, so no key env var is
needed. TBA must be reachable from wherever the job actually runs.

## 1. Provision the database

1. Create a Railway project.
2. Add the **Postgres** plugin. Railway exposes its connection string as the
   reference variable `${{Postgres.DATABASE_URL}}`.

## 2. Set environment variables (on the service that runs the job)

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `SKIP_GCS` | `True` |
| `PROD` | leave unset / `False` |

If you hit an SSL error connecting, append `?sslmode=require` to the URL.

## 3. Run the rebuild

The project root for the backend service is `backend/` (where `pyproject.toml`
lives). Nixpacks will detect Poetry and install dependencies.

**Option A — run inside Railway (recommended; DB writes stay on Railway's
private network, and TBA is reachable from Railway):**

Set the service start command (or a one-off / manual deploy command) to:

```bash
poetry run python run_full_rebuild.py
```

Because this is a one-shot job rather than a long-lived web server, run it as a
manual one-off (or a temporary service you stop once it prints
`Full rebuild complete.`) so Railway doesn't keep restarting it on exit.

**Option B — run from your own machine against the Railway DB:**

```bash
cd backend
poetry install
railway link                 # pick the project + the service holding the vars
railway run poetry run python run_full_rebuild.py
```

`railway run` injects `DATABASE_URL` and `SKIP_GCS` from Railway, executes
locally, and writes to Railway Postgres over its public URL. Requires Poetry +
TBA reachable locally.

## Notes

- `reset_all_years()` only runs on an **empty** database — it no-ops if any year
  rows already exist. Point it at a fresh Postgres (or drop the tables) to
  rebuild. The runner prints a warning if it detects existing data.
- The job wipes and recreates all tables (`clean_db()`), then fetches every
  year from TBA — expect a long run with per-year stage timings printed as it
  goes (`... TBA / AVG / Wins / EPA / Write DB`).
- 2021 is skipped by the pipeline (no standard season).
