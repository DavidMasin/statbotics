import os
from typing import List

# GLOBAL

PROD = os.getenv("PROD", "False") == "True"

# 8001 emulates the data server
BACKEND_URL = "https://api.statbotics.io" if PROD else "http://localhost:8001"

# DB

CRDB_USER = os.getenv("CRDB_USER", "")
CRDB_PWD = os.getenv("CRDB_PWD", "")
CRDB_HOST = os.getenv("CRDB_HOST", "")


def _normalize_db_url(url: str) -> str:
    # Managed Postgres providers (Railway, Heroku, ...) hand out bare
    # "postgres://" / "postgresql://" URLs; SQLAlchemy needs an explicit driver.
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix) :]
    return url


# An explicit DATABASE_URL (or LOCAL_CONN_STR) overrides everything else. This
# is how a Railway Postgres / other Postgres-wire instance is used in place of
# the CockroachDB on :26257, for both local dev and one-off rebuild jobs.
_DB_OVERRIDE = os.getenv("DATABASE_URL") or os.getenv("LOCAL_CONN_STR")

CONN_STR = (
    _normalize_db_url(_DB_OVERRIDE)
    if _DB_OVERRIDE
    else (
        (
            "cockroachdb://"
            + CRDB_USER
            + ":"
            + CRDB_PWD
            + "@"
            + CRDB_HOST
            + "/statbotics3?sslmode=verify-full&sslrootcert=root.crt"
        )
        if PROD
        else "cockroachdb://root@localhost:26257/statbotics3?sslmode=disable"
    )
)

# Skip the GCS upload of current-year results (e.g. when running a DB-only
# rebuild on an environment without Google Cloud credentials).
SKIP_GCS = os.getenv("SKIP_GCS", "False") == "True"

# Seconds between in-process incremental updates of the current year. When > 0,
# the API server runs the update loop itself (no separate cron service needed).
# 0 disables it. Only set this on a single-process deployment.
try:
    AUTO_UPDATE_INTERVAL = int(os.getenv("AUTO_UPDATE_INTERVAL", "0"))
except ValueError:
    AUTO_UPDATE_INTERVAL = 0

# API

AUTH_KEY_BLACKLIST: List[str] = []

# CONFIG

CURR_YEAR = 2026
CURR_WEEK = 8

# MISC

EPS = 1e-6
