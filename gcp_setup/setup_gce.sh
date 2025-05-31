#!/bin/bash
# Setup script for deploying the crypto trading bot on Google Compute Engine

# Exit on error
set -e

echo "Setting up AI Crypto Trading Bot on Google Compute Engine..."

# Install required packages
echo "Installing required packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git supervisor apache2

# Create a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv ~/crypto-bot-env
source ~/crypto-bot-env/bin/activate

# Repository should be cloned manually before running this script
echo "Using existing repository..."

# Install dependencies
echo "Installing Python dependencies..."
cd ~/AI-crypto-bot
pip install -r requirements.txt

# Create directories for logs and data
mkdir -p ~/AI-crypto-bot/logs
mkdir -p ~/AI-crypto-bot/data

# Create supervisor configuration
echo "Setting up supervisor configuration..."
sudo bash -c 'cat > /etc/supervisor/conf.d/crypto-bot.conf << EOL
[program:crypto-bot]
command=/home/$SUDO_USER/crypto-bot-env/bin/python /home/$SUDO_USER/AI-crypto-bot/main.py
directory=/home/$SUDO_USER/AI-crypto-bot
autostart=true
autorestart=true
startretries=10
user=$SUDO_USER
redirect_stderr=true
stdout_logfile=/home/$SUDO_USER/AI-crypto-bot/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=HOME="/home/$SUDO_USER",USER="$SUDO_USER"
EOL'

# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Set up Apache web server for dashboard
echo "Setting up Apache web server for dashboard..."
sudo mkdir -p /var/www/html/crypto-bot
sudo chown -R $USER:$USER /var/www/html/crypto-bot

# Copy dashboard templates
if [ -d "$HOME/AI-crypto-bot/dashboard_templates" ]; then
    echo "Copying dashboard templates..."
    cp -r $HOME/AI-crypto-bot/dashboard_templates/* /var/www/html/crypto-bot/
else
    echo "Dashboard templates directory not found. Creating placeholder..."
    echo "<html><body><h1>Crypto Trading Bot Dashboard</h1><p>Dashboard will appear here after the first update cycle.</p></body></html>" > /var/www/html/crypto-bot/index.html
fi

# Set proper permissions
sudo chmod -R 755 /var/www/html/crypto-bot

# Configure firewall to allow HTTP/HTTPS traffic
echo "Configuring firewall to allow HTTP/HTTPS traffic..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 'Apache Full'
fi

echo "Setup complete! The crypto trading bot is now running as a supervised service."
echo "You can check the status with: sudo supervisorctl status crypto-bot"
echo "View logs with: tail -f ~/AI-crypto-bot/logs/supervisor.log"
echo ""
echo "Don't forget to set up your .env file with your API keys and configuration!"
