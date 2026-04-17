#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Clear Python bytecode cache to ensure fresh code is used
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Build Tailwind CSS
# Keep a backup of the committed CSS in case the build produces a bad output
CSS_OUT="static/css/dist/styles.css"
CSS_BACKUP="static/css/dist/styles.css.bak"
cp "$CSS_OUT" "$CSS_BACKUP"

cd theme/static_src
unset NODE_ENV
npm install

# Run build; if it fails, the backup will be restored below
NODE_ENV=production ./node_modules/.bin/tailwindcss \
  --postcss \
  -i ./src/styles.css \
  -o ../../static/css/dist/styles.css \
  --minify || true

cd ../..

BUILT_SIZE=$(wc -c < "$CSS_OUT")
echo "CSS build output: $BUILT_SIZE bytes"

# Check for DaisyUI component classes as a sanity check
HAS_BTN=$(grep -c '\.btn{' "$CSS_OUT" || true)
echo "DaisyUI .btn{ occurrences in built CSS: $HAS_BTN"

# Restore committed version if build is too small OR missing DaisyUI component classes
if [ "$BUILT_SIZE" -lt 120000 ] || [ "$HAS_BTN" -lt 1 ]; then
  echo "CSS build looks bad (size=$BUILT_SIZE, btn=$HAS_BTN) — restoring committed version"
  cp "$CSS_BACKUP" "$CSS_OUT"
  echo "Restored: $(wc -c < "$CSS_OUT") bytes"
else
  echo "CSS build looks good — using freshly built version"
fi
rm -f "$CSS_BACKUP"

rm -rf staticfiles
python manage.py collectstatic --no-input
python manage.py migrate
