# 🌐 Domain Setup for Crypto Bot Dashboard

## Current Status
- **IP Access**: http://34.29.9.115/crypto-bot/ ✅ Working
- **Domain Access**: Not configured ❌

## 🚀 Quick Setup Options

### **Option 1: Free DuckDNS Domain (5 minutes)**

1. **Go to**: https://www.duckdns.org
2. **Sign in** with Google/GitHub
3. **Create subdomain**: `aicryptobot.duckdns.org` (or your choice)
4. **Set IP**: `34.29.9.115`
5. **Get token** from DuckDNS dashboard

**Then run on server:**
```bash
# Install DuckDNS updater
echo "url='https://www.duckdns.org/update?domains=aicryptobot&token=YOUR_TOKEN&ip='" | sudo tee /etc/cron.d/duckdns
echo "*/5 * * * * root curl -s \$url" | sudo tee -a /etc/cron.d/duckdns
```

### **Option 2: Cloudflare Domain ($8/year)**

1. **Buy domain** at cloudflare.com
2. **Add A record**: `crypto.yourdomain.com` → `34.29.9.115`
3. **Enable proxy** (orange cloud) for SSL

### **Option 3: Google Cloud DNS (If using GCP)**

```bash
# Create DNS zone
gcloud dns managed-zones create crypto-bot-zone --dns-name="crypto-bot.example.com." --description="Crypto Bot Dashboard"

# Add A record
gcloud dns record-sets transaction start --zone=crypto-bot-zone
gcloud dns record-sets transaction add 34.29.9.115 --name="crypto-bot.example.com." --ttl=300 --type=A --zone=crypto-bot-zone
gcloud dns record-sets transaction execute --zone=crypto-bot-zone
```

## 🔧 Apache Configuration for Domain

Once you have a domain, update Apache:

```bash
# Create virtual host
sudo tee /etc/apache2/sites-available/crypto-bot.conf << 'EOF'
<VirtualHost *:80>
    ServerName your-domain.com
    ServerAlias www.your-domain.com
    DocumentRoot /var/www/html/crypto-bot
    
    <Directory /var/www/html/crypto-bot>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog ${APACHE_LOG_DIR}/crypto-bot_error.log
    CustomLog ${APACHE_LOG_DIR}/crypto-bot_access.log combined
</VirtualHost>
EOF

# Enable site
sudo a2ensite crypto-bot.conf
sudo systemctl reload apache2
```

## 🔒 SSL Setup (HTTPS)

After domain is working:

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-apache

# Get SSL certificate
sudo certbot --apache -d your-domain.com -d www.your-domain.com

# Auto-renewal (already configured by certbot)
sudo systemctl status certbot.timer
```

## 📋 Recommended: DuckDNS Setup

**Easiest option for immediate use:**

1. **Visit**: https://www.duckdns.org
2. **Choose name**: `aicryptobot` (becomes `aicryptobot.duckdns.org`)
3. **Set IP**: `34.29.9.115`
4. **Copy token**
5. **Run setup script** (see below)

## 🎯 Current Working URLs

**IP-based (working now):**
- Main: http://34.29.9.115/crypto-bot/
- Performance: http://34.29.9.115/crypto-bot/performance.html
- Logs: http://34.29.9.115/crypto-bot/logs.html

**After domain setup:**
- Main: https://aicryptobot.duckdns.org/
- Performance: https://aicryptobot.duckdns.org/performance.html
- Logs: https://aicryptobot.duckdns.org/logs.html

## 🚨 Important Notes

1. **IP may change**: Google Cloud VMs can get new IPs on restart
2. **Static IP recommended**: Reserve static IP in GCP console
3. **Firewall rules**: Ensure HTTP/HTTPS ports are open
4. **DNS propagation**: May take 5-60 minutes for domain to work globally

## 🔧 Troubleshooting

**Domain not working?**
```bash
# Check DNS resolution
nslookup your-domain.com

# Check Apache config
sudo apache2ctl configtest

# Check site is enabled
sudo a2ensite crypto-bot.conf
sudo systemctl reload apache2
```

**SSL issues?**
```bash
# Check certificate status
sudo certbot certificates

# Renew if needed
sudo certbot renew --dry-run
```
