#!/bin/bash
set -e

# Coach GCP Deployment Script
# Run this on the GCP instance to deploy updates

COACH_DIR="/var/www/coach"

echo "==> Pulling latest changes..."
cd "$COACH_DIR"
git pull

echo "==> Building frontend..."
cd "$COACH_DIR/frontend"
npm ci
npm run build

echo "==> Updating backend..."
cd "$COACH_DIR/backend"
uv sync --frozen

echo "==> Running migrations..."
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py migrate

echo "==> Collecting static files..."
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput

echo "==> Restarting service..."
sudo systemctl restart coach

echo ""
echo "==> Deployment complete!"
echo "    Check status: sudo systemctl status coach"
echo "    View logs: sudo journalctl -u coach -f"
