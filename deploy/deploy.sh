#!/bin/bash
set -e

# Coach Deployment Script
# Run this on your server to deploy updates
#
# Usage:
#   ./deploy.sh              # Auto-detect installation directory
#   ./deploy.sh /path/to/coach  # Specify installation directory

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Determine installation directory
if [ -n "$1" ]; then
    COACH_DIR="$1"
elif [ -d "/var/www/coach" ]; then
    COACH_DIR="/var/www/coach"
elif [ -d "/home/jon/coach2" ]; then
    COACH_DIR="/home/jon/coach2"
elif [ -d "$HOME/coach" ]; then
    COACH_DIR="$HOME/coach"
else
    echo -e "${RED}Error: Could not find Coach installation directory.${NC}"
    echo "Usage: $0 [installation_directory]"
    exit 1
fi

echo -e "${GREEN}==> Using installation directory: $COACH_DIR${NC}"

# Check if directory exists and is a git repo
if [ ! -d "$COACH_DIR/.git" ]; then
    echo -e "${RED}Error: $COACH_DIR is not a git repository${NC}"
    exit 1
fi

cd "$COACH_DIR"

# Backup database before deployment
echo -e "${GREEN}==> Backing up database...${NC}"
BACKUP_DIR="$COACH_DIR/backups"
mkdir -p "$BACKUP_DIR"
if [ -f "$COACH_DIR/backend/db.sqlite3" ]; then
    BACKUP_FILE="$BACKUP_DIR/db-$(date +%Y%m%d-%H%M%S).sqlite3"
    cp "$COACH_DIR/backend/db.sqlite3" "$BACKUP_FILE"
    echo -e "${GREEN}    Database backed up to: $BACKUP_FILE${NC}"

    # Keep only the 10 most recent backups
    ls -t "$BACKUP_DIR"/db-*.sqlite3 | tail -n +11 | xargs -r rm --
fi

# Pull latest changes
echo -e "${GREEN}==> Pulling latest changes...${NC}"
git fetch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${YELLOW}    Current branch: $CURRENT_BRANCH${NC}"

# Show what will be updated
if [ "$(git rev-list HEAD..origin/$CURRENT_BRANCH --count)" -gt 0 ]; then
    echo -e "${YELLOW}    New commits to be pulled:${NC}"
    git log HEAD..origin/$CURRENT_BRANCH --oneline --no-decorate | head -5
else
    echo -e "${YELLOW}    No new commits to pull${NC}"
fi

git pull

# Build frontend
echo -e "${GREEN}==> Building frontend...${NC}"
cd "$COACH_DIR/frontend"
npm ci
npm run build

# Update backend dependencies
echo -e "${GREEN}==> Updating backend dependencies...${NC}"
cd "$COACH_DIR/backend"
uv sync --frozen

# Activate virtual environment
source .venv/bin/activate

# Run migrations
echo -e "${GREEN}==> Running database migrations...${NC}"
DJANGO_SETTINGS_MODULE=config.settings python manage.py migrate --noinput

# Collect static files
echo -e "${GREEN}==> Collecting static files...${NC}"
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput

# Restart the service
echo -e "${GREEN}==> Restarting service...${NC}"
if systemctl is-active --quiet coach; then
    sudo systemctl restart coach
    echo -e "${GREEN}    Service restarted${NC}"
else
    echo -e "${YELLOW}    Warning: coach service is not running${NC}"
    echo -e "${YELLOW}    Start it with: sudo systemctl start coach${NC}"
fi

# Show status
echo ""
echo -e "${GREEN}==> Deployment complete!${NC}"
echo ""
echo "Useful commands:"
echo "  Check status:    sudo systemctl status coach"
echo "  View logs:       sudo journalctl -u coach -f"
echo "  Restart service: sudo systemctl restart coach"
echo ""

# Optional: Show recent logs
if systemctl is-active --quiet coach; then
    echo -e "${GREEN}Recent logs (last 10 lines):${NC}"
    sudo journalctl -u coach -n 10 --no-pager
fi
