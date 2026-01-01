# Google Cloud Platform Deployment

Complete guide for deploying the AI crypto trading bot on Google Cloud Platform using Compute Engine.

## Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and configured
- Basic familiarity with Linux command line
- API keys from Coinbase and Google Cloud

## Quick Deployment

### 1. Create VM Instance

```bash
# Set project and zone
export PROJECT_ID=your-project-id
export ZONE=us-central1-a
export INSTANCE_NAME=crypto-trading-bot

# Create VM instance
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=e2-medium \
    --network-interface=network-tier=PREMIUM,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=your-service-account@$PROJECT_ID.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=http-server,https-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=$INSTANCE_NAME,image=projects/debian-cloud/global/images/debian-12-bookworm-v20231212,mode=rw,size=20,type=projects/$PROJECT_ID/zones/$ZONE/disks/$INSTANCE_NAME \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=purpose=crypto-trading \
    --reservation-affinity=any
```

### 2. Connect and Setup

```bash
# SSH into the instance
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE

# Clone repository
git clone https://github.com/yourusername/AI-crypto-bot.git
cd AI-crypto-bot

# Run automated setup
bash gcp_deployment/setup_gcp.sh
```

### 3. Configure Environment

```bash
# Edit configuration
nano .env

# Add your API keys and settings
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----...
GOOGLE_CLOUD_PROJECT=your-project-id
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

## Detailed Setup Guide

### VM Configuration

#### Recommended Instance Types

| Use Case | Machine Type | vCPUs | Memory | Cost/Month* | Status |
|----------|--------------|-------|---------|-------------|---------|
| Development | e2-micro | 2 shared | 1 GB | ~$6 | ❌ **NOT for production** |
| **Current Production** | **e2-medium** | **1 dedicated** | **4 GB** | **~$25** | ✅ **Testing now** |
| High Volume/Backtesting | e2-standard-2 | 2 dedicated | 8 GB | ~$50 | 🎯 **Future upgrade** |

*Approximate costs for us-central1 region

**⚠️ Important**: e2-micro experiences severe performance issues and network outages. Not suitable for production trading.

**Current Status (Jan 1, 2026)**: Upgraded from e2-micro to e2-medium due to:
- Super slow processing on e2-micro
- Frequent network outages affecting trading
- Insufficient memory (1GB) for market data processing

See [Instance Sizing Guide](../INSTANCE_SIZING_GUIDE.md) for detailed analysis.

#### Firewall Rules

```bash
# Allow HTTP traffic for dashboard
gcloud compute firewall-rules create allow-crypto-bot-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP for crypto bot dashboard"

# Allow HTTPS traffic (optional)
gcloud compute firewall-rules create allow-crypto-bot-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS for crypto bot dashboard"
```

### Service Account Setup

#### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create crypto-bot-sa \
    --description="Service account for crypto trading bot" \
    --display-name="Crypto Bot Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:crypto-bot-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:crypto-bot-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create ~/crypto-bot-key.json \
    --iam-account=crypto-bot-sa@$PROJECT_ID.iam.gserviceaccount.com
```

### Automated Setup Script

The `gcp_deployment/setup_gcp.sh` script performs:

1. **System Updates**: Updates package lists and installs dependencies
2. **Python Environment**: Creates virtual environment with Python 3.11
3. **Dependencies**: Installs all required Python packages
4. **Supervisor Setup**: Configures process management
5. **Web Server**: Sets up Apache for dashboard
6. **Email Configuration**: Configures daily reports
7. **Cron Jobs**: Sets up automated reporting

#### Manual Setup Steps

If you prefer manual setup:

```bash
# Update system
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git supervisor apache2 python3.11 python3.11-venv

# Create virtual environment
python3.11 -m venv ~/crypto-bot-env
source ~/crypto-bot-env/bin/activate

# Install dependencies
cd ~/AI-crypto-bot
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p ~/AI-crypto-bot/logs
mkdir -p ~/AI-crypto-bot/data

# Setup supervisor configuration
sudo tee /etc/supervisor/conf.d/crypto-bot.conf << EOF
[program:crypto-bot]
command=/home/$USER/crypto-bot-env/bin/python /home/$USER/AI-crypto-bot/main.py
directory=/home/$USER/AI-crypto-bot
autostart=true
autorestart=true
startretries=10
user=$USER
redirect_stderr=true
stdout_logfile=/home/$USER/AI-crypto-bot/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=HOME="/home/$USER",USER="$USER",SUPERVISOR_ENABLED="1"
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true
EOF

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
```

### Dashboard Setup

#### Apache Configuration

```bash
# Create dashboard directory
sudo mkdir -p /var/www/html/crypto-bot
sudo chown -R $USER:$USER /var/www/html/crypto-bot

# Create virtual host (optional)
sudo tee /etc/apache2/sites-available/crypto-bot.conf << EOF
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /var/www/html/crypto-bot
    
    <Directory /var/www/html/crypto-bot>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
    
    ErrorLog \${APACHE_LOG_DIR}/crypto-bot_error.log
    CustomLog \${APACHE_LOG_DIR}/crypto-bot_access.log combined
</VirtualHost>
EOF

# Enable site (optional)
sudo a2ensite crypto-bot
sudo systemctl reload apache2
```

### SSL/HTTPS Setup (Optional)

#### Using Let's Encrypt

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-apache

# Get SSL certificate
sudo certbot --apache -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Service Management

### Supervisor Commands

```bash
# Check status
sudo supervisorctl status crypto-bot

# Start service
sudo supervisorctl start crypto-bot

# Stop service
sudo supervisorctl stop crypto-bot

# Restart service (preserves uptime)
sudo supervisorctl restart crypto-bot

# View logs
sudo supervisorctl tail -f crypto-bot

# Enhanced management scripts
sudo /usr/local/bin/crypto-bot-restart  # Restart with uptime preservation
sudo /usr/local/bin/crypto-bot-stop     # Stop with uptime reset
```

### System Service Integration

#### Create systemd service (alternative to supervisor)

```bash
sudo tee /etc/systemd/system/crypto-bot.service << EOF
[Unit]
Description=AI Crypto Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/AI-crypto-bot
Environment=PATH=/home/$USER/crypto-bot-env/bin
ExecStart=/home/$USER/crypto-bot-env/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot
```

## Monitoring & Maintenance

### Log Management

```bash
# View real-time logs
tail -f ~/AI-crypto-bot/logs/supervisor.log

# View daily report logs
tail -f ~/AI-crypto-bot/logs/daily_report.log

# Rotate logs (add to crontab)
0 0 * * 0 find ~/AI-crypto-bot/logs -name "*.log" -size +100M -exec gzip {} \;
```

### System Monitoring

```bash
# Check system resources
htop

# Check disk usage
df -h

# Check memory usage
free -h

# Check network connectivity
ping -c 4 api.coinbase.com
ping -c 4 googleapis.com
```

### Backup Strategy

```bash
# Create backup script
tee ~/backup_crypto_bot.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration and data
tar -czf $BACKUP_DIR/crypto_bot_backup_$DATE.tar.gz \
    ~/AI-crypto-bot/.env \
    ~/AI-crypto-bot/data/ \
    ~/AI-crypto-bot/logs/ \
    ~/crypto-bot-key.json

# Keep only last 7 backups
find $BACKUP_DIR -name "crypto_bot_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: crypto_bot_backup_$DATE.tar.gz"
EOF

chmod +x ~/backup_crypto_bot.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/$USER/backup_crypto_bot.sh
```

## Security Best Practices

### Firewall Configuration

```bash
# Install UFW
sudo apt-get install -y ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Enable firewall
sudo ufw enable
```

### File Permissions

```bash
# Secure configuration files
chmod 600 ~/AI-crypto-bot/.env
chmod 600 ~/crypto-bot-key.json

# Secure log directory
chmod 750 ~/AI-crypto-bot/logs
```

### Regular Updates

```bash
# Create update script
tee ~/update_crypto_bot.sh << 'EOF'
#!/bin/bash
cd ~/AI-crypto-bot

# Pull latest code
git pull origin main

# Update dependencies
source ~/crypto-bot-env/bin/activate
pip install --upgrade -r requirements.txt

# Restart service
sudo supervisorctl restart crypto-bot

echo "Update completed"
EOF

chmod +x ~/update_crypto_bot.sh
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check supervisor logs
sudo supervisorctl tail crypto-bot

# Check system logs
sudo journalctl -u supervisor -f

# Verify configuration
python -c "from config import Config; Config()"
```

#### 2. API Connection Issues

```bash
# Test Coinbase API
curl -H "Authorization: Bearer $(echo -n 'your-api-key' | base64)" \
     https://api.coinbase.com/api/v3/brokerage/accounts

# Test Google Cloud API
gcloud auth application-default print-access-token
```

#### 3. Dashboard Not Accessible

```bash
# Check Apache status
sudo systemctl status apache2

# Check firewall
sudo ufw status

# Check external IP
curl ifconfig.me
```

#### 4. Email Reports Not Working

```bash
# Test email configuration
python -c "
import smtplib
from email.mime.text import MIMEText
# Test SMTP connection
"

# Check cron jobs
crontab -l
```

### Performance Optimization

#### Resource Monitoring

```bash
# Install monitoring tools
sudo apt-get install -y htop iotop nethogs

# Monitor Python process
ps aux | grep python
top -p $(pgrep -f main.py)
```

#### Memory Optimization

```bash
# Add swap if needed
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Cost Optimization

### Instance Scheduling

```bash
# Stop instance during off-hours (if desired)
gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE

# Start instance
gcloud compute instances start $INSTANCE_NAME --zone=$ZONE

# Schedule with cron (on another machine)
# Stop at 6 PM: 0 18 * * * gcloud compute instances stop crypto-trading-bot --zone=us-central1-a
# Start at 6 AM: 0 6 * * * gcloud compute instances start crypto-trading-bot --zone=us-central1-a
```

### Preemptible Instances

```bash
# Create preemptible instance (cheaper but can be terminated)
gcloud compute instances create $INSTANCE_NAME-preemptible \
    --preemptible \
    --machine-type=e2-medium \
    # ... other options
```

This comprehensive guide ensures successful deployment and operation of the AI crypto trading bot on Google Cloud Platform.