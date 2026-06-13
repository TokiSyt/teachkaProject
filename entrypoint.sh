#!/usr/bin/env bash
set -e

# Collect static at runtime: .env is loaded here (DEBUG off), so the manifest
# storage generates staticfiles.json. The build-time collectstatic runs with
# DEBUG defaulted on (no env), producing no manifest.
python manage.py collectstatic --no-input

python manage.py migrate --no-input

exec python -m gunicorn teachkaBaseProject.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
