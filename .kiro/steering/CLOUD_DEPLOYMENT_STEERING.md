# Cloud Deployment Steering Document

## Cloud Deployment Philosophy & Standards

### Multi-Cloud Support
- **Primary Platforms**: AWS EC2, Google Cloud Compute Engine
- **Deployment Automation**: Scripted setup for consistent environments
- **Service Management**: systemd (AWS) and supervisor (GCP) for process management
- **Web Dashboard**: Apache/Nginx for production web interface

### Deployment Architecture

#### AWS EC2 Deployment
- **AMI**: Amazon Linux 2023 (recommended)
- **Instance Type**: t2.medium minimum for production
- **Security Groups**: SSH (22), HTTP (80) for dashboard access
- **Service Management**: systemd with proper uptime tracking
- **Web Server**: Apache with mod_rewrite for dashboard routing

#### Google Cloud Deployment
- **OS**: Debian/Ubuntu (recommended)
- **Machine Type**: e2-medium minimum for production
- **Firewall**: Allow HTTP traffic for dashboard
- **Service Management**: supervisor with enhanced restart scripts
- **Web Server**: Apache with virtual host configuration

### Automated Setup Scripts

#### AWS Setup Script (`aws_setup/setup_ec2.sh`)
```bash
#!/bin/bash
# AWS EC2 automated setup
set -e

# Install system dependencies
sudo yum update -y
sudo yum install -y python3 python3-pip git httpd

# Create application user
sudo useradd -m -s /bin/bash crypto-bot

# Clone repository and setup virtual environment
# Install dependencies and configure service
# Setup web server and dashboard
```

#### GCP Setup Script (`gcp_setup/setup_gce.sh`)
```bash
#!/bin/bash
# Google Cloud Compute Engine automated setup
set -e

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git apache2 supervisor

# Create application user and setup environment
# Configure supervisor service
# Setup Apache virtual host
```

### Service Management Standards

#### systemd Configuration (AWS)
```ini
[Unit]
Description=AI Crypto Trading Bot
After=network.target

[Service]
Type=simple
User=crypto-bot
WorkingDirectory=/home/crypto-bot/AI-crypto-bot
Environment=PATH=/home/crypto-bot/AI-crypto-bot/venv/bin
ExecStart=/home/crypto-bot/AI-crypto-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### supervisor Configuration (GCP)
```ini
[program:crypto-bot]
command=/home/crypto-bot/AI-crypto-bot/venv/bin/python main.py
directory=/home/crypto-bot/AI-crypto-bot
user=crypto-bot
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/crypto-bot/crypto-bot.log
```

### Security Configuration

#### AWS Security Groups
```json
{
  "GroupName": "crypto-bot-security-group",
  "Description": "Security group for AI Crypto Trading Bot",
  "SecurityGroupRules": [
    {
      "IpProtocol": "tcp",
      "FromPort": 22,
      "ToPort": 22,
      "CidrIp": "0.0.0.0/0",
      "Description": "SSH access"
    },
    {
      "IpProtocol": "tcp", 
      "FromPort": 80,
      "ToPort": 80,
      "CidrIp": "0.0.0.0/0",
      "Description": "HTTP access for dashboard"
    }
  ]
}
```

#### GCP Firewall Rules
```bash
# Allow HTTP traffic for dashboard
gcloud compute firewall-rules create allow-http-crypto-bot \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP access to crypto bot dashboard"
```

### Web Server Configuration

#### Apache Virtual Host (Production)
```apache
<VirtualHost *:80>
    DocumentRoot /var/www/html
    
    # Crypto bot dashboard
    Alias /crypto-bot /var/www/html/crypto-bot
    <Directory "/var/www/html/crypto-bot">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    # Enable mod_rewrite for SPA routing
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^crypto-bot/(.*)$ /crypto-bot/index.html [L]
</VirtualHost>
```

### Environment-Specific Configuration

#### Production Environment Variables
```env
# Production-specific settings
SIMULATION_MODE=false                # Real trading enabled
NOTIFICATIONS_ENABLED=true          # Enable push notifications
LOG_LEVEL=INFO                      # Production logging level
WEBSERVER_SYNC_ENABLED=true         # Enable dashboard sync

# Performance settings
DECISION_INTERVAL_MINUTES=60        # Standard trading interval
RISK_LEVEL=MEDIUM                   # Balanced risk approach
```

#### Development Environment
```env
# Development-specific settings
SIMULATION_MODE=true                # Paper trading only
NOTIFICATIONS_ENABLED=false         # Disable notifications
LOG_LEVEL=DEBUG                     # Verbose logging
WEBSERVER_SYNC_ENABLED=false        # Disable web sync
```

### Monitoring & Logging

#### CloudWatch Integration (AWS)
```bash
# Install CloudWatch agent
sudo yum install -y amazon-cloudwatch-agent

# Configure log streaming
aws logs create-log-group --log-group-name /crypto-bot/application
aws logs create-log-stream --log-group-name /crypto-bot/application --log-stream-name main
```

#### Stackdriver Integration (GCP)
```bash
# Install logging agent
curl -sSO https://dl.google.com/cloudagents/add-logging-agent-repo.sh
sudo bash add-logging-agent-repo.sh
sudo apt-get update
sudo apt-get install -y google-fluentd
```

### Uptime Management

#### Enhanced Service Scripts
```bash
# AWS systemd enhanced restart (preserves uptime)
sudo /usr/local/bin/crypto-bot-restart() {
    echo "restart" > /tmp/crypto-bot-action
    sudo systemctl restart crypto-bot
}

# GCP supervisor enhanced restart (preserves uptime)  
sudo /usr/local/bin/crypto-bot-restart() {
    echo "restart" > /tmp/crypto-bot-action
    sudo supervisorctl restart crypto-bot
}
```

#### Uptime Tracking Integration
- **Restart Detection**: Scripts write action type to temp file
- **Uptime Preservation**: Restarts maintain cumulative uptime
- **Stop Detection**: Explicit stops reset uptime counter
- **Dashboard Display**: Shows total uptime and restart count

### Deployment Checklist

#### Pre-Deployment
- [ ] API credentials configured and validated
- [ ] Environment variables set correctly
- [ ] Security groups/firewall rules configured
- [ ] SSL certificates installed (if using HTTPS)
- [ ] Backup strategy implemented

#### Post-Deployment
- [ ] Service starts successfully
- [ ] Dashboard accessible via HTTP
- [ ] Logs are being written correctly
- [ ] Notifications working (if enabled)
- [ ] Trading functionality verified in simulation mode

### Backup & Recovery

#### Data Backup Strategy
```bash
# Backup critical data daily
#!/bin/bash
BACKUP_DIR="/home/crypto-bot/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration and data
cp -r /home/crypto-bot/AI-crypto-bot/data $BACKUP_DIR/
cp /home/crypto-bot/AI-crypto-bot/.env $BACKUP_DIR/
cp -r /home/crypto-bot/AI-crypto-bot/logs $BACKUP_DIR/

# Compress and upload to cloud storage
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
# Upload to S3/GCS bucket
```

#### Disaster Recovery
- **Configuration Backup**: Environment variables and settings
- **Data Backup**: Portfolio, trade history, performance data
- **Code Backup**: Git repository with tagged releases
- **Service Recovery**: Automated service restart procedures

### Performance Optimization

#### Resource Monitoring
```bash
# Monitor system resources
htop                    # CPU and memory usage
df -h                   # Disk usage
netstat -tulpn         # Network connections
journalctl -u crypto-bot -f  # Service logs (systemd)
tail -f /var/log/crypto-bot/crypto-bot.log  # Service logs (supervisor)
```

#### Scaling Considerations
- **Vertical Scaling**: Upgrade instance type for better performance
- **Horizontal Scaling**: Multiple instances with load balancing (future)
- **Database Scaling**: External database for high-frequency trading
- **Caching**: Redis for market data caching (future enhancement)

### Troubleshooting

#### Common Deployment Issues
1. **Service Won't Start**: Check logs, verify Python path and dependencies
2. **Dashboard Not Accessible**: Verify web server configuration and firewall rules
3. **API Connection Issues**: Check credentials and network connectivity
4. **Permission Errors**: Verify file ownership and service user permissions

#### Debugging Commands
```bash
# AWS (systemd)
sudo systemctl status crypto-bot
sudo journalctl -u crypto-bot -f
sudo systemctl restart crypto-bot

# GCP (supervisor)
sudo supervisorctl status crypto-bot
sudo tail -f /var/log/crypto-bot/crypto-bot.log
sudo supervisorctl restart crypto-bot

# Web server
sudo systemctl status apache2
sudo tail -f /var/log/apache2/error.log
```

### Maintenance Procedures

#### Regular Maintenance
- **Weekly**: Review logs for errors or warnings
- **Monthly**: Update system packages and dependencies
- **Quarterly**: Review and rotate API keys
- **Annually**: Review and update security configurations

#### Update Deployment
```bash
# Standard update procedure
cd /home/crypto-bot/AI-crypto-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Restart service (preserves uptime)
sudo /usr/local/bin/crypto-bot-restart
```

This deployment framework ensures consistent, secure, and maintainable cloud deployments across multiple platforms.