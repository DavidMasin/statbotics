#!/usr/bin/env sh
# Railway passes the port via $PORT. Resolve it inside a shell here so it works
# regardless of whether the platform runs the start command through a shell.
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
