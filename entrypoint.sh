#!/usr/bin/env bash
set -e

python manage.py migrate --no-input

exec python -m gunicorn teachkaBaseProject.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
