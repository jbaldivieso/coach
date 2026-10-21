# Deploying Coach to Google Cloud Compute Engine (Free Tier)

This guide covers deploying Coach to a GCP Compute Engine e2-micro instance with Nginx and SSL.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GCP Account Setup](#gcp-account-setup)
3. [Create a VM Instance](#create-a-vm-instance)
4. [Configure Firewall Rules](#configure-firewall-rules)
5. [Connect to Your Instance](#connect-to-your-instance)
6. [Server Setup](#server-setup)
7. [Deploy the Application](#deploy-the-application)
8. [Configure Nginx](#configure-nginx)
9. [Set Up SSL with Let's Encrypt](#set-up-ssl-with-lets-encrypt)
10. [Start Services](#start-services)
11. [Domain Setup](#domain-setup)
12. [Maintenance](#maintenance)
13. [Connect Claude](#connect-claude)
14. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- A Google account
- A domain name (for SSL) - can use free services like [FreeDNS](https://freedns.afraid.org/) or [DuckDNS](https://www.duckdns.org/)
- Basic familiarity with Linux command line

---

## GCP Account Setup

### 1. Create a GCP Account

1. Go to [cloud.google.com](https://cloud.google.com/)
2. Click "Get started for free"
3. Sign in with your Google account
4. Complete the signup process (requires a credit card for verification, but won't be charged for free tier usage)

### 2. Free Tier Eligibility

GCP offers an "Always Free" tier that includes:
- **1 e2-micro VM instance** per month (in select US regions)
- **30 GB standard persistent disk**
- **1 GB outbound data transfer** (to most destinations)

**Important:** Free tier VMs must be in one of these regions:
- `us-west1` (Oregon)
- `us-central1` (Iowa)
- `us-east1` (South Carolina)

### 3. Create a Project

1. Go to the [GCP Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click "New Project"
4. Name it `coach` (or your preference)
5. Click "Create"
6. Select the new project from the dropdown

---

## Create a VM Instance

### Using the Console

1. Navigate to **Compute Engine** > **VM instances**
2. Click **Create Instance**
3. Configure the instance:

| Setting | Value |
|---------|-------|
| Name | `coach` |
| Region | `us-central1` (Iowa) |
| Zone | `us-central1-a` |
| Machine type | `e2-micro` (2 vCPU, 1 GB memory) |
| Boot disk | Click "Change" |
| - OS | Debian |
| - Version | Debian GNU/Linux 12 (bookworm) |
| - Size | 30 GB (max free tier) |
| Firewall | Check both "Allow HTTP" and "Allow HTTPS" |

4. Click **Create**

### Using gcloud CLI (Alternative)

```bash
# Install gcloud CLI if needed: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Create the instance
gcloud compute instances create coach \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server
```

---

## Configure Firewall Rules

The default firewall rules allow HTTP (80) and HTTPS (443) if you checked those boxes. Verify they exist:

1. Go to **VPC Network** > **Firewall**
2. Ensure these rules exist:
   - `default-allow-http` - tcp:80
   - `default-allow-https` - tcp:443

If missing, create them:

```bash
# Allow HTTP
gcloud compute firewall-rules create default-allow-http \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:80 \
  --target-tags=http-server

# Allow HTTPS
gcloud compute firewall-rules create default-allow-https \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:443 \
  --target-tags=https-server
```

---

## Connect to Your Instance

### Get Your External IP

1. Go to **Compute Engine** > **VM instances**
2. Note the **External IP** address (e.g., `34.123.45.67`)

### SSH Connection Options

**Option 1: Browser SSH (easiest)**
- Click the "SSH" button next to your instance in the console

**Option 2: gcloud CLI**
```bash
gcloud compute ssh coach --zone=us-central1-a
```

**Option 3: Standard SSH**
```bash
# First, add your SSH key to the instance metadata
# Go to Compute Engine > Metadata > SSH Keys > Add SSH Key

ssh -i ~/.ssh/your_key username@EXTERNAL_IP
```

---

## Server Setup

Run these commands on your GCP instance:

### 1. Update System and Install Dependencies

```bash
# Update package list
sudo apt-get update && sudo apt-get upgrade -y

# Install essential packages
sudo apt-get install -y \
  git \
  nginx \
  certbot \
  python3-certbot-nginx \
  curl \
  build-essential

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installations
node --version  # Should show v20.x
npm --version
```

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env  # Or restart your shell
```

The backend needs Python 3.12 and Debian 12 ships 3.11. You don't need to
install it yourself: `uv sync` reads `backend/.python-version` and downloads 3.12.

### 3. Create Application Directory

```bash
# Create app directory
sudo mkdir -p /var/www/coach
sudo chown $USER:$USER /var/www/coach
```

---

## Deploy the Application

### 1. Clone the Repository

```bash
cd /var/www/coach
git clone https://github.com/YOUR_USERNAME/coach.git .
# Or use your preferred method (scp, rsync, etc.)
```

### 2. Build the Frontend

```bash
cd /var/www/coach/frontend
npm ci
npm run build
```

### 3. Set Up the Backend

```bash
cd /var/www/coach/backend

# Create virtual environment and install dependencies
uv sync --frozen

# Activate the virtual environment
source .venv/bin/activate

# Run database migrations
DJANGO_SETTINGS_MODULE=config.settings python manage.py migrate

# Collect static files
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput

# Create a superuser (for admin access)
DJANGO_SETTINGS_MODULE=config.settings python manage.py createsuperuser
```

### 4. Configure Environment Variables

```bash
# Copy the environment file
cp /var/www/coach/deploy/.env.example /var/www/coach/deploy/.env

# Generate a secure secret key and put it in DJANGO_SECRET_KEY
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
nano /var/www/coach/deploy/.env
```

`.env.example` is already set up for `coach.baldivieso.com`. On another domain,
change the host in `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`,
`CSRF_TRUSTED_ORIGINS` and `COACH_PUBLIC_URL`. `COACH_PUBLIC_URL` is required:
the OAuth and MCP metadata advertise it, and with `DJANGO_DEBUG=False` the
server won't start without it.

Only systemd and the cron job below read `.env`. The `manage.py` commands in
this guide run in your shell with the development defaults, which use the same
database.

### 5. Install the Systemd Service

```bash
# Copy and update the service file for GCP paths
sudo cp /var/www/coach/deploy/coach-gcp.service /etc/systemd/system/coach.service

# Edit if your username is different from the default
sudo nano /etc/systemd/system/coach.service

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable coach
```

---

## Configure Nginx

### 1. Create Nginx Configuration

Use the initial (HTTP-only) config first, then add SSL with Certbot:

```bash
# Copy the initial HTTP-only config
sudo cp /var/www/coach/deploy/nginx-coach-initial.conf /etc/nginx/sites-available/coach

# On a domain other than coach.baldivieso.com, change server_name
sudo nano /etc/nginx/sites-available/coach
```

Besides proxying to Gunicorn and serving `/static/`, the config does two things
the Claude connector needs. The `location ^~ /.well-known/oauth-` block lets the
OAuth discovery documents through. The `^~` modifier is what matters: it stops
nginx from checking regex locations, so the `location ~ /\.` dotfile rule can't
answer them with a 403. A plain prefix location wouldn't work, wherever it sits.
`/oauth/register/` is unauthenticated and every valid POST creates a client row,
so it gets a `limit_req` rate limit.

### 2. Enable the Site

```bash
# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Enable coach site
sudo ln -s /etc/nginx/sites-available/coach /etc/nginx/sites-enabled/coach

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Set Up SSL with Let's Encrypt

### 1. Point Your Domain to the Server

Before requesting an SSL certificate, your domain must point to your server's IP address:

1. Go to your domain registrar or DNS provider
2. Create an **A record**:
   - Host: `@` (or blank for root domain)
   - Value: Your GCP instance's external IP
   - TTL: 300 (or lowest available)
3. Optionally, create another A record for `www`:
   - Host: `www`
   - Value: Same IP address

Wait for DNS propagation (can take minutes to hours):
```bash
# Check if DNS is resolving
dig +short coach.baldivieso.com
```

### 2. Obtain SSL Certificate

```bash
# Request certificate (Certbot will automatically configure Nginx)
sudo certbot --nginx -d coach.baldivieso.com

# Follow the prompts:
# - Enter your email address
# - Agree to terms of service
# - Choose whether to redirect HTTP to HTTPS (recommended: yes)
```

Certbot rewrites `/etc/nginx/sites-available/coach` to add the certificate and
the HTTP-to-HTTPS redirect. `deploy/nginx-coach-server.conf` is a copy of that
result for `coach.baldivieso.com`. When you change the nginx config, change that
file and copy it to the server (see Deploy Updates).

### 3. Verify Auto-Renewal

```bash
# Test the renewal process
sudo certbot renew --dry-run

# Certbot automatically adds a systemd timer for renewals
sudo systemctl status certbot.timer
```

---

## Start Services

```bash
# Start the Coach backend service
sudo systemctl start coach

# Verify it's running
sudo systemctl status coach

# Check the logs
sudo journalctl -u coach -f
```

Your app should now be accessible at `https://coach.baldivieso.com`, or at
your own domain.

---

## Domain Setup

### Option 1: Use Your Own Domain

1. Purchase a domain from a registrar (Namecheap, Google Domains, Cloudflare, etc.)
2. Configure DNS as described in the SSL section

### Option 2: Free Domain with DuckDNS

1. Go to [duckdns.org](https://www.duckdns.org/)
2. Sign in with Google/GitHub/etc.
3. Create a subdomain (e.g., `mycoach.duckdns.org`)
4. Set the IP to your GCP instance's external IP
5. Use this domain for SSL setup

### Option 3: Free Subdomain with FreeDNS

1. Go to [freedns.afraid.org](https://freedns.afraid.org/)
2. Create an account
3. Add a subdomain under one of the public domains
4. Point it to your IP

---

## Maintenance

### Deploy Updates

`deploy/deploy-gcp.sh` does the whole update. It pulls, then stops before
building anything if `.env` is missing a setting that `.env.example` has, so a
new required setting can't leave the service crash-looping. Then it builds the
frontend, runs `uv sync`, `migrate` and `collectstatic`, and restarts the service.

```bash
/var/www/coach/deploy/deploy-gcp.sh
```

`git pull` doesn't touch the files systemd and nginx read, so check whether the
update changed any of them:

```bash
cd /var/www/coach && git diff --stat HEAD@{1} -- deploy/
```

- **`nginx-coach-server.conf` changed:** copy it over and reload nginx.
  ```bash
  sudo cp /var/www/coach/deploy/nginx-coach-server.conf /etc/nginx/sites-available/coach
  sudo nginx -t && sudo systemctl reload nginx
  ```
- **`coach-gcp.service` changed:** copy it over, keeping any edits you made to
  the installed copy, then run `sudo systemctl daemon-reload && sudo systemctl restart coach`.
- **The cron line below changed:** update it with `crontab -e`.

The same steps by hand:

```bash
cd /var/www/coach
git pull

# Compare .env with .env.example and add anything new
diff <(grep -oE '^[A-Z_]+=' deploy/.env.example | sort) <(grep -oE '^[A-Z_]+=' deploy/.env | sort)

cd frontend && npm ci && npm run build
cd ../backend
uv sync --frozen
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput
sudo systemctl restart coach
```

### View Logs

```bash
# Coach application logs
sudo journalctl -u coach -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Clear Old OAuth Tokens and Clients

Expired and rotated tokens from the Claude connector, and clients registered
without ever connecting, pile up otherwise. Run both nightly from cron
(`crontab -e`):

```bash
15 4 * * * cd /var/www/coach/backend && set -a && . ../deploy/.env && set +a && .venv/bin/python manage.py cleartokens && .venv/bin/python manage.py clearoauthclients
```

### Backup Database

```bash
# Create backup
cp /var/www/coach/backend/db.sqlite3 ~/coach-backup-$(date +%Y%m%d).sqlite3

# Download backup to local machine (run from local)
gcloud compute scp coach:/var/www/coach/backend/db.sqlite3 ./coach-backup.sqlite3 --zone=us-central1-a
```

### Service Commands

```bash
# Check status
sudo systemctl status coach
sudo systemctl status nginx

# Restart services
sudo systemctl restart coach
sudo systemctl restart nginx

# View service logs
sudo journalctl -u coach --since "1 hour ago"

# Django shell
cd /var/www/coach/backend && source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py shell
```

### Update SSL Certificate

Certbot handles automatic renewals, but you can manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## Connect Claude

The MCP server lives at `<COACH_PUBLIC_URL>/mcp`. In claude.ai, go to Settings →
Connectors → Add custom connector, paste `https://coach.baldivieso.com/mcp`, and
sign in with your Coach account. Each person connects with their own account and
sees only their own data.

This needs the nginx config with the `/.well-known/oauth-` block (see Configure
Nginx). To check it's live, this should return JSON, not a 403:

```bash
curl -s https://coach.baldivieso.com/.well-known/oauth-protected-resource/mcp
```

If a phone has the PWA installed from before the connector existed, open the app
and tap Update first. The old service worker answers `/oauth/authorize/` with the
app instead of the sign-in page.

Before connecting, you can test the server on your dev machine. Make an access token in the admin with scope `coach` and
resource `["<COACH_PUBLIC_URL>/mcp"]` (in debug that's
`["http://localhost:5173/mcp"]`). A token with no resource gets a 401. Then run
`npx @modelcontextprotocol/inspector` against `http://localhost:8000/mcp` with it
as the bearer token.

---

## Troubleshooting

### Check if Services are Running

```bash
# Check Coach service
sudo systemctl status coach
sudo journalctl -u coach -n 50

# Check Nginx
sudo systemctl status nginx
sudo nginx -t
```

### Port Conflicts

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Check what's using port 80/443
sudo lsof -i :80
sudo lsof -i :443
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R $USER:$USER /var/www/coach

# Check service user
grep "User=" /etc/systemd/system/coach.service
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Check Nginx SSL config
sudo nginx -t
```

### Service Won't Start

If `journalctl -u coach` shows `ImproperlyConfigured: Set COACH_PUBLIC_URL`,
add it to `/var/www/coach/deploy/.env` (see Configure Environment Variables) and
restart.

### Claude Can't Connect

Check the discovery documents first (see Connect Claude). A 403 means the
installed nginx config predates the `/.well-known/oauth-` block, so copy
`deploy/nginx-coach-server.conf` over and reload. If they load but show the wrong
host, fix `COACH_PUBLIC_URL`.

### Memory Issues on e2-micro

The e2-micro instance has only 1GB RAM. If you experience issues:

```bash
# Create a swap file
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

```

`coach-gcp.service` already runs a single Gunicorn worker, so don't add more.

### Static Files Not Loading

```bash
# Rebuild and recollect static files
cd /var/www/coach/frontend && npm run build
cd /var/www/coach/backend
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput --clear

# Check Nginx is serving static files
ls -la /var/www/coach/backend/staticfiles/
```

### Database Locked Errors

SQLite can have locking issues under concurrent load:

```bash
# Check for stale locks
lsof /var/www/coach/backend/db.sqlite3

# Restart the service
sudo systemctl restart coach
```

---

## Cost Monitoring

Even with free tier, monitor your usage:

1. Go to **Billing** > **Budgets & alerts**
2. Create a budget with email alerts at $1, $5, $10
3. Check **Compute Engine** > **VM instances** to verify your instance type

**Free tier limits (as of 2024):**
- 1 e2-micro instance
- 30 GB standard persistent disk
- 1 GB egress to most destinations (5 GB to Australia)

---

## Security Recommendations

1. **Keep system updated:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **Configure unattended upgrades:**
   ```bash
   sudo apt-get install -y unattended-upgrades
   sudo dpkg-reconfigure unattended-upgrades
   ```

3. **Set up fail2ban (optional):**
   ```bash
   sudo apt-get install -y fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

4. **Review firewall rules regularly** in GCP Console

5. **Back up your database** regularly (see Maintenance section)
