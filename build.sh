#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Clear Python bytecode cache to ensure fresh code is used
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Build Tailwind CSS
cd theme/static_src
npm install
npm run build
cd ../..

rm -rf staticfiles
python manage.py collectstatic --no-input
python manage.py migrate