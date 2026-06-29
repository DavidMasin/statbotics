# Deploying Statbotics on Railway

This sets up the services the app needs on Railway:

| Service | What it is | Source |
|---------|-----------|--------|
| **db** | PostgreSQL (stands in for the production CockroachDB) | Railway Postgres plugin |
| **backend** | FastAPI app — REST API + site API | `backend/` |
| **frontend** | Next.js 13 website | `frontend/` |
| **updater** (optional) | Cron service that incrementally refreshes the current year | `backend/` (see "Keeping the site updated") |

Each service config lives next to its code (`backend/railway.json` +
`backend/Dockerfile`, `frontend/railway.json`). In Railway, set each service's
**Root Directory** to `backend` or `frontend` so it picks these up. The two
batch jobs reuse the backend image via their own profiles
(`backend/railway.rebuild.json`, `backend/railway.updater.json`) selected with
the per-service **Config File** setting.

> The Config File path is relative to the service's Root Directory (e.g.
> `railway.updater.json` when Root Directory is `backend`). If Railway resolves
> it from the repo root instead, use `backend/railway.updater.json`.

The backend talks to Postgres directly; the frontend talks to the backend's
site API. GCS is not used in this setup (see `SKIP_GCS` / `USE_BUCKET` below).

```
frontend  --HTTP /v3/site-->  backend  --SQL-->  db (Postgres)
```

## 1. db — Postgres

Add the **Postgres** plugin to the project. Railway exposes its connection
string as the reference variable `${{Postgres.DATABASE_URL}}`.

## 2. backend service

- **Root Directory:** `backend`
- **Build/Deploy:** from `backend/railway.json` → `backend/Dockerfile`. The
  Dockerfile installs the pinned `requirements.txt` (so `uvicorn` is on PATH)
  and `gcc`/`libpq-dev` (so the `psycopg2` build succeeds), and starts
  `uvicorn main:app --host 0.0.0.0 --port $PORT`. A Dockerfile is used instead
  of Nixpacks because the repo has no `poetry.lock`, which left Nixpacks in an
  ambiguous poetry/pip state where `uvicorn` wasn't on PATH.
- **Variables:**

  | Variable | Value | Notes |
  |----------|-------|-------|
  | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Overrides the connection string; normalized to the `psycopg2` driver. |
  | `SKIP_GCS` | `True` | Skip the current-year GCS upload (no GCP creds on Railway). |
  | `PROD` | leave unset | Connection comes from `DATABASE_URL` regardless. |

  The TBA API key is hardcoded in `src/tba/constants.py`, so no key var is needed.

- Railway gives the service a public domain, e.g. `https://backend-xxxx.up.railway.app`.

## 3. frontend service

- **Root Directory:** `frontend`
- **Build/Deploy:** from `frontend/railway.json` (Nixpacks runs `yarn build`;
  start command `npx next start -H 0.0.0.0 -p $PORT`).
- **Variables:**

  | Variable | Value | Notes |
  |----------|-------|-------|
  | `BACKEND_URL` | `https://<backend-domain>` | Point the site at the Railway backend's **public** domain. A missing `https://` is added and `/v3/site` is appended automatically, so the bare domain is enough. |
  | `USE_BUCKET` | `false` | Read everything from the backend instead of GCS. |
  | `NODE_OPTIONS` | `--max_old_space_size=3072` | Optional; avoids OOM on the Next build. |

  These are read at **build time** (inlined via `next.config.js`), so set them
  before/at deploy. Re-deploy the frontend if you change them.

  > Use the backend's full public URL (not the private `*.railway.internal`
  > host), since `BACKEND_URL` is also used by the browser.

## How the overrides work (code reference)

- `backend/src/constants.py` — `DATABASE_URL`/`LOCAL_CONN_STR` override `CONN_STR`
  (normalized to `postgresql+psycopg2://`); `SKIP_GCS` gates the GCS upload.
- `frontend/src/constants.tsx` — `BACKEND_URL`/`BUCKET_URL` env overrides and the
  `USE_BUCKET` flag; `next.config.js` exposes them to the build.
- `frontend/src/api/storage.tsx` + `team.tsx` — when `USE_BUCKET=false`, all
  reads skip the bucket and fall back to the backend site API.

## Loading data

A fresh deploy has an empty database. Populate it with a full rebuild — see
[`backend/RAILWAY_REBUILD.md`](backend/RAILWAY_REBUILD.md). Run it against the
**same Postgres** (`DATABASE_URL` / `SKIP_GCS=True`) before expecting the
frontend to show data. The rebuild loads every event for the current year,
including district events that are in progress (e.g. Israel district).

The cleanest way to run it is a **temporary one-off service** using the
ready-made `backend/railway.rebuild.json` profile (start command
`python run_full_rebuild.py`, never restarts):

- **Root Directory:** `backend`
- **Config File:** `railway.rebuild.json` (Settings → Config-as-code)
- **Variables:** `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `SKIP_GCS=True`

Deploy it once; it builds, runs the rebuild to completion, prints
`Full rebuild complete.`, and exits. Delete the service when it's done.

## Keeping the site updated during competition

After the one-time rebuild, run the **incremental update** on a schedule so the
site refreshes as matches happen. `backend/run_update.py` checks TBA for new
events/matches/rankings for the current year and recomputes only when there's
something new (newly created events are picked up too, not just new matches).

Set this up as a **Railway cron service** (a fourth service, separate from the
always-on `backend`) using the ready-made `backend/railway.updater.json`
profile (start command `python run_update.py`, cron `*/10 * * * *`, never
restarts):

- **Root Directory:** `backend` (same repo + Dockerfile as the backend).
- **Config File:** `railway.updater.json` (Settings → Config-as-code).
- **Variables:** `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `SKIP_GCS=True`
  (same as the backend service).

Railway starts the container on the schedule; the script runs once and exits. A
run with no new data exits in seconds; a run with new matches recomputes the
current year. To change the interval, edit `cronSchedule` in
`railway.updater.json`.

> Cron services must run to completion and exit — `run_update.py` does. Keep the
> always-on `backend` service separate from this cron service.

Tune the interval to the competition: every 5–10 minutes during event days is
plenty. There's no harm in frequent runs — they no-op when TBA is unchanged.

### Alternative: no extra service (in-process updater)

If you'd rather not run a separate service, the **backend service can update
itself**. Set one variable on the existing backend service:

| Variable | Value | Notes |
|----------|-------|-------|
| `AUTO_UPDATE_INTERVAL` | `600` | Seconds between in-process current-year updates (e.g. 600 = 10 min). `0`/unset disables it. |

The backend then runs the same incremental update on that interval in a
background thread (so it never blocks request serving), and you don't need the
cron service at all. Only enable this on a **single-process** deployment — the
backend Dockerfile runs one uvicorn process, so that's already the case here.
Don't run both the cron service and `AUTO_UPDATE_INTERVAL` at once.
