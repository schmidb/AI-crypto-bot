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

# Install Miniconda
echo "Installing Miniconda..."
mkdir -p ~/downloads
cd ~/downloads
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda3
rm miniconda.sh

# Initialize conda
echo "Initializing conda..."
$HOME/miniconda3/bin/conda init bash
source ~/.bashrc

# Create conda environment
echo "Creating conda environment..."
conda create -y -n crypto-bot python=3.9
conda activate crypto-bot

# Clone repository (if not already done)
if [ ! -d "$HOME/AI-crypto-bot" ]; then
    echo "Cloning repository..."
    cd $HOME
    git clone https://github.com/yourusername/AI-crypto-bot.git
fi

# Install dependencies
echo "Installing dependencies..."
cd $HOME/AI-crypto-bot
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f "$HOME/AI-crypto-bot/.env" ]; then
    echo "Creating .env file template..."
    cp .env.example .env
    echo "Please edit the .env file with your API keys and configuration"
fi

# Create logs directory
echo "Creating logs directory..."
mkdir -p $HOME/AI-crypto-bot/logs

# Setup systemd service
echo "Setting up systemd service..."
sudo cp crypto-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot.service

echo ""
echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your API keys and configuration:"
echo "   nano $HOME/AI-crypto-bot/.env"
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
