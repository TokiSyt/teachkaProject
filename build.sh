#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

rm -rf staticfiles
python manage.py collectstatic --no-input
python manage.py migrate