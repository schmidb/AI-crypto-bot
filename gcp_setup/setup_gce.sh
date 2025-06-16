#!/bin/bash
# Setup script for deploying the crypto trading bot on Google Compute Engine

# Exit on error
set -e

echo "Setting up AI Crypto Trading Bot on Google Compute Engine..."

# Install required packages
echo "Installing required packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git supervisor apache2 python3.11 python3.11-venv

# Create a virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv ~/crypto-bot-env
source ~/crypto-bot-env/bin/activate

# Repository should be cloned manually before running this script
echo "Using existing repository..."

# Install dependencies
echo "Installing Python dependencies..."
cd ~/AI-crypto-bot
pip install --upgrade pip
pip install -r requirements.txt

# Create directories for logs and data
mkdir -p ~/AI-crypto-bot/logs
mkdir -p ~/AI-crypto-bot/data

# Create .env file if it doesn't exist
if [ ! -f "~/AI-crypto-bot/.env" ]; then
    echo "Creating .env file template..."
    cp .env.example .env
    echo "Please edit the .env file with your API keys and configuration"
fi

# Create supervisor configuration with proper uptime handling
echo "Setting up supervisor configuration..."
sudo bash -c 'cat > /etc/supervisor/conf.d/crypto-bot.conf << EOL
[program:crypto-bot]
command=/home/'$USER'/crypto-bot-env/bin/python /home/'$USER'/AI-crypto-bot/main.py
directory=/home/'$USER'/AI-crypto-bot
autostart=true
autorestart=true
startretries=10
user='$USER'
redirect_stderr=true
stdout_logfile=/home/'$USER'/AI-crypto-bot/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=HOME="/home/'$USER'",USER="'$USER'",SUPERVISOR_ENABLED="1"
# Graceful shutdown with SIGTERM
stopsignal=TERM
stopwaitsecs=30
# Custom stop command for explicit stops
stopasgroup=true
killasgroup=true
EOL'

# Create supervisor stop script for explicit stops
echo "Creating supervisor stop script..."
sudo bash -c 'cat > /usr/local/bin/crypto-bot-stop << EOL
#!/bin/bash
export BOT_RESTART_CONTEXT=stop
/home/'$USER'/crypto-bot-env/bin/python /home/'$USER'/AI-crypto-bot/bot_manager.py stop
EOL'

sudo chmod +x /usr/local/bin/crypto-bot-stop

# Create supervisor restart script for restarts
echo "Creating supervisor restart script..."
sudo bash -c 'cat > /usr/local/bin/crypto-bot-restart << EOL
#!/bin/bash
export BOT_RESTART_CONTEXT=restart
supervisorctl restart crypto-bot
EOL'

sudo chmod +x /usr/local/bin/crypto-bot-restart

# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Set up Apache web server for dashboard
echo "Setting up Apache web server for dashboard..."
sudo mkdir -p /var/www/html/crypto-bot
sudo chown -R $USER:$USER /var/www/html/crypto-bot

# Create placeholder dashboard
echo "Creating placeholder dashboard..."
echo "<html><body><h1>Crypto Trading Bot Dashboard</h1><p>Dashboard will appear here after the first update cycle.</p></body></html>" > /var/www/html/crypto-bot/index.html

# Set proper permissions
sudo chmod -R 755 /var/www/html/crypto-bot

# Configure firewall to allow HTTP/HTTPS traffic
echo "Configuring firewall to allow HTTP/HTTPS traffic..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 'Apache Full'
fi

# Enable and start Apache
sudo systemctl enable apache2
sudo systemctl start apache2

echo ""
echo "Setup complete! The crypto trading bot is now running as a supervised service."
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your API keys and configuration:"
echo "   nano ~/AI-crypto-bot/.env"
echo ""
echo "2. Check service status:"
echo "   sudo supervisorctl status crypto-bot"
echo ""
echo "3. View logs:"
echo "   tail -f ~/AI-crypto-bot/logs/supervisor.log"
echo ""
echo "4. Access dashboard at:"
echo "   http://YOUR_VM_IP/crypto-bot/"
echo ""
echo "Service Management Commands:"
echo "  sudo /usr/local/bin/crypto-bot-restart  # Restart (preserves uptime)"
echo "  sudo /usr/local/bin/crypto-bot-stop     # Stop (resets uptime)"
echo "  sudo supervisorctl restart crypto-bot   # Restart (preserves uptime)"
echo "  sudo supervisorctl stop crypto-bot      # Stop (resets uptime)"
echo "  python bot_manager.py status            # Check status and uptime"
echo ""
