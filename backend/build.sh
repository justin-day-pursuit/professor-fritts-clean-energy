#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

echo "==> [1/3] Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "==> [2/3] Collecting static files..."
python manage.py collectstatic --noinput

echo "==> [3/3] Running database migrations..."
python manage.py migrate

echo "==> Build finished successfully!"
