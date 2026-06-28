# Deterministic backend build for Railway (avoids Nixpacks poetry/venv PATH
# issues). Uses the pinned requirements.txt, the same manifest the App Engine
# deploys use, so uvicorn lands on PATH.
FROM python:3.11-slim

# gcc + libpq-dev are needed to build psycopg2 from source.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway provides $PORT at runtime; shell form lets it expand.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
