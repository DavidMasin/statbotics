# Deploying Statbotics on Railway

This sets up the three services the app needs on Railway:

| Service | What it is | Source |
|---------|-----------|--------|
| **db** | PostgreSQL (stands in for the production CockroachDB) | Railway Postgres plugin |
| **backend** | FastAPI app — REST API + site API | `backend/` |
| **frontend** | Next.js 13 website | `frontend/` |

Each service config lives next to its code (`backend/railway.json`,
`backend/nixpacks.toml`, `frontend/railway.json`). In Railway, set each
service's **Root Directory** to `backend` or `frontend` so it picks these up.

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
- **Build/Deploy:** from `backend/railway.json` (Nixpacks; start command
  `uvicorn main:app --host 0.0.0.0 --port $PORT`). `backend/nixpacks.toml` adds
  `libpq-dev` so the `psycopg2` build succeeds.
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
  | `BACKEND_URL` | `https://<backend-domain>/v3/site` | Point the site at the Railway backend. **Must include the `/v3/site` suffix.** |
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
frontend to show data.
