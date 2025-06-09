#!/bin/bash
# Script to update supervisor configuration for daily log rotation

echo "Updating supervisor configuration for daily log rotation..."

# Create new supervisor configuration with daily log rotation
sudo bash -c 'cat > /etc/supervisor/conf.d/crypto-bot.conf << EOL
[program:crypto-bot]
command=/home/'$USER'/crypto-bot-env/bin/python /home/'$USER'/AI-crypto-bot/main.py
directory=/home/'$USER'/AI-crypto-bot
autostart=true
autorestart=true
startretries=10
user='$USER'
redirect_stderr=true
stdout_logfile=/home/'$USER'/AI-crypto-bot/logs/supervisor_%(ENV_TIMESTAMP)s.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=30
environment=HOME="/home/'$USER'",USER="'$USER'",TIMESTAMP="$(date +%Y%m%d)"
EOL'

echo "Reloading supervisor configuration..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart crypto-bot

echo "Supervisor configuration updated successfully!"
echo "Logs will now be rotated daily in the format: supervisor_YYYYMMDD.log"
