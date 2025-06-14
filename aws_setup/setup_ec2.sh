#!/bin/bash

# Setup script for AI Crypto Trading Bot on Amazon Linux EC2
# This script installs dependencies and sets up the systemd service

# Exit on error
set -e

echo "Setting up AI Crypto Trading Bot on Amazon Linux EC2..."

# Update system packages
echo "Updating system packages..."
sudo yum update -y

# Install development tools
echo "Installing development tools..."
sudo yum groupinstall "Development Tools" -y
sudo yum install -y openssl-devel bzip2-devel libffi-devel

# Install Python 3.11
echo "Installing Python 3.11..."
sudo yum install -y python3.11 python3.11-pip python3.11-devel

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv ~/crypto-bot-env
source ~/crypto-bot-env/bin/activate

# Install dependencies
echo "Installing dependencies..."
cd ~/AI-crypto-bot
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f "~/AI-crypto-bot/.env" ]; then
    echo "Creating .env file template..."
    cp .env.example .env
    echo "Please edit the .env file with your API keys and configuration"
fi

# Create logs directory
echo "Creating logs directory..."
mkdir -p ~/AI-crypto-bot/logs

# Create systemd service file with proper uptime handling
echo "Creating systemd service file..."
sudo tee /etc/systemd/system/crypto-bot.service > /dev/null <<EOF
[Unit]
Description=AI Crypto Trading Bot
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/AI-crypto-bot
ExecStart=/home/ec2-user/crypto-bot-env/bin/python /home/ec2-user/AI-crypto-bot/main.py
# Use bot_manager.py stop only for explicit stops, not restarts
ExecStop=/bin/bash -c 'export BOT_RESTART_CONTEXT=stop && /home/ec2-user/crypto-bot-env/bin/python /home/ec2-user/AI-crypto-bot/bot_manager.py stop'
# Set restart context for automatic restarts
ExecReload=/bin/bash -c 'export BOT_RESTART_CONTEXT=restart && /bin/kill -TERM \$MAINPID'
Restart=on-failure
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=crypto-bot
Environment=PYTHONUNBUFFERED=1
# Graceful shutdown timeout
TimeoutStopSec=30
# Send SIGTERM first, then SIGKILL
KillMode=mixed

[Install]
WantedBy=multi-user.target
EOF

# Setup systemd service
echo "Setting up systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot.service

# Install Apache for dashboard
echo "Installing Apache web server..."
sudo yum install -y httpd
sudo systemctl enable httpd
sudo systemctl start httpd

# Create dashboard directory
sudo mkdir -p /var/www/html/crypto-bot
sudo chown -R ec2-user:ec2-user /var/www/html/crypto-bot

echo ""
echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your API keys and configuration:"
echo "   nano ~/AI-crypto-bot/.env"
echo ""
echo "2. Start the service:"
echo "   sudo systemctl start crypto-bot"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status crypto-bot"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u crypto-bot -f"
echo ""
echo "5. Access dashboard at:"
echo "   http://YOUR_EC2_IP/crypto-bot/"
echo ""
echo "Service Management Commands:"
echo "  sudo systemctl restart crypto-bot  # Restart (preserves uptime)"
echo "  sudo systemctl stop crypto-bot     # Stop (resets uptime)"
echo "  python bot_manager.py status       # Check status and uptime"
echo ""
