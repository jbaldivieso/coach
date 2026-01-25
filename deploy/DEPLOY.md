# Deploying Coach to Raspberry Pi

## Initial Setup (one-time)

**On the Pi:**

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv nodejs npm

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Clone the repo
cd ~
git clone <your-repo-url> coach

# Build frontend
cd ~/coach/frontend
npm ci
npm run build

# Set up backend
cd ~/coach/backend
uv sync --frozen
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput
DJANGO_SETTINGS_MODULE=config.settings python manage.py migrate

# Create a user account
DJANGO_SETTINGS_MODULE=config.settings python manage.py createsuperuser

# Configure environment
cp ~/coach/deploy/.env.example ~/coach/deploy/.env
nano ~/coach/deploy/.env
# Set DJANGO_ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS to your Pi's IP

# Install and start the service
sudo cp ~/coach/deploy/coach.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable coach
sudo systemctl start coach
```

Access at `http://<pi-ip>:8000`

---

## Ongoing Commands

**Deploy new changes:**
```bash
cd ~/coach
git pull
cd frontend && npm ci && npm run build
cd ../backend && uv sync --frozen
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput
DJANGO_SETTINGS_MODULE=config.settings python manage.py migrate
sudo systemctl restart coach
```

**View logs:**
```bash
sudo journalctl -u coach -f
```

**Restart service:**
```bash
sudo systemctl restart coach
```

**Check status:**
```bash
sudo systemctl status coach
```

**Django shell:**
```bash
cd ~/coach/backend
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py shell
```

**Backup database:**
```bash
cp ~/coach/backend/db.sqlite3 ~/coach-backup-$(date +%Y%m%d).sqlite3
```
