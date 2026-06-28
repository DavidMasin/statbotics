# Deterministic backend build for Railway (avoids Nixpacks poetry/venv PATH
# issues). Uses the pinned requirements.txt, the same manifest the App Engine
# deploys use, so uvicorn lands on PATH.
FROM python:3.11-slim

# build-essential (gcc + libc6-dev headers) and libpq-dev are needed to build
# psycopg2 from source. Bare gcc is not enough on slim — it lacks stdlib.h.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# start.sh resolves $PORT in a shell, so the container starts correctly whether
# or not the platform runs the start command through a shell.
CMD ["sh", "start.sh"]
