#!/bin/bash
set -e

# Coach Raspberry Pi Setup Script
# Run this on the Pi after cloning the repo

COACH_DIR="/home/pi/coach"
cd "$COACH_DIR"

echo "==> Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv nodejs npm

echo "==> Installing uv (Python package manager)..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

echo "==> Building frontend..."
cd "$COACH_DIR/frontend"
npm ci
npm run build

echo "==> Setting up backend..."
cd "$COACH_DIR/backend"
uv sync --frozen

echo "==> Collecting static files..."
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput
DJANGO_SETTINGS_MODULE=config.settings python manage.py migrate

echo "==> Setting up environment..."
if [ ! -f "$COACH_DIR/deploy/.env" ]; then
    cp "$COACH_DIR/deploy/.env.example" "$COACH_DIR/deploy/.env"
    # Generate a random secret key
    SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
    sed -i "s/generate-a-secure-key-here/$SECRET_KEY/" "$COACH_DIR/deploy/.env"
    echo "Created .env file - please edit DJANGO_ALLOWED_HOSTS with your Pi's IP"
fi

echo "==> Installing systemd service..."
sudo cp "$COACH_DIR/deploy/coach.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable coach
sudo systemctl start coach

echo ""
echo "==> Setup complete!"
echo "    - Edit /home/pi/coach/deploy/.env with your Pi's IP address"
echo "    - Then run: sudo systemctl restart coach"
echo "    - Access the app at: http://<your-pi-ip>:8000"
