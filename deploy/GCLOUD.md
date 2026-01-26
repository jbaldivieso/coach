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
13. [Troubleshooting](#troubleshooting)

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

### 2. Install Python 3.12 and uv

```bash
# Install Python 3.12 (Debian 12 has 3.11 by default)
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true

# On Debian 12, Python 3.11 is available, but we need 3.12
# Build from source if not available in repos
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env  # Or restart your shell
```

**Note:** If Python 3.12 is required and not available, you can either:
- Use Python 3.11 (modify `pyproject.toml` if needed)
- Build Python 3.12 from source (see Troubleshooting section)

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
# Copy and edit the environment file
cp /var/www/coach/deploy/.env.example /var/www/coach/deploy/.env

# Generate a secure secret key
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'

# Edit the environment file
nano /var/www/coach/deploy/.env
```

Update `.env` with your domain (replace `yourdomain.com`):

```bash
DJANGO_SETTINGS_MODULE=config.settings
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=YOUR_GENERATED_SECRET_KEY
DJANGO_ALLOWED_HOSTS=coach.baldivieso.com

# For HTTPS (after SSL setup)
CORS_ALLOWED_ORIGINS=https://coach.baldivieso.com
CSRF_TRUSTED_ORIGINS=https://coach.baldivieso.com
```

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

# Edit the config to set your domain
sudo nano /etc/nginx/sites-available/coach
# Replace 'yourdomain.com' with your actual domain
```

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
dig +short yourdomain.com
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

Your app should now be accessible at `https://yourdomain.com`!

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

```bash
cd /var/www/coach

# Pull latest changes
git pull

# Rebuild frontend
cd frontend && npm ci && npm run build

# Update backend
cd ../backend
uv sync --frozen
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput

# Restart service
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
```

### Update SSL Certificate

Certbot handles automatic renewals, but you can manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

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

### Python 3.12 Not Available

If Python 3.12 isn't available in your distribution:

```bash
# Option 1: Use pyenv
curl https://pyenv.run | bash
# Follow the output instructions to add to ~/.bashrc
exec "$SHELL"
pyenv install 3.12.0
pyenv global 3.12.0

# Option 2: Build from source
sudo apt-get install -y build-essential zlib1g-dev libncurses5-dev \
  libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev \
  libsqlite3-dev wget libbz2-dev

cd /tmp
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
tar -xf Python-3.12.0.tgz
cd Python-3.12.0
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall
```

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

# Reduce Gunicorn workers in coach.service to 1
sudo nano /etc/systemd/system/coach.service
# Change --workers 2 to --workers 1
sudo systemctl daemon-reload
sudo systemctl restart coach
```

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
