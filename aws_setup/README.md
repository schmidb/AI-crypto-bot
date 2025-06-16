# AWS EC2 Deployment Guide

This guide provides step-by-step instructions for deploying the AI Crypto Trading Bot on an AWS EC2 instance.

## Deployment Steps

### 1. Launch an EC2 Instance

1. **Log in to your AWS Management Console**
2. **Navigate to EC2 and click "Launch Instance"**
3. **Configure your instance:**
   - Choose Amazon Linux 2023 AMI
   - Select an instance type (t2.medium or better recommended for production)
   - Configure security groups to allow SSH access (port 22) and HTTP access (port 80)
   - Add an inbound rule for TCP port 80 to allow web dashboard access
   - This is required for accessing the comprehensive web dashboard
   - Launch the instance and download your key pair (.pem file)

### 2. Connect to Your EC2 Instance

```bash
# Make sure your key file has the right permissions
chmod 400 your-key.pem

# Connect to your EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip
```

### 3. Clone the Repository and Run Setup Script

```bash
# Clone the repository
git clone https://github.com/yourusername/AI-crypto-bot.git
cd AI-crypto-bot

# Run the AWS setup script
bash aws_setup/setup_ec2.sh
```

The setup script will:
- Install required dependencies
- Set up a Python virtual environment
- Create a systemd service for the bot with proper uptime tracking
- Create a template .env file

### 4. Configure Your API Keys

```bash
# Edit your .env file with your API keys
nano .env
```

Add your Coinbase API credentials and Google Cloud credentials to the .env file.

### 5. Start and Manage the Service

```bash
# Start the service
sudo systemctl start crypto-bot

# Check the status
sudo systemctl status crypto-bot

# View logs
sudo journalctl -u crypto-bot -f

# Enable auto-start on boot
sudo systemctl enable crypto-bot
```

### 6. Service Management with Proper Uptime Tracking

The bot now supports proper uptime tracking that distinguishes between restarts and stops:

```bash
# Restart (preserves uptime)
sudo systemctl restart crypto-bot

# Stop (resets uptime)
sudo systemctl stop crypto-bot

# Enhanced management via bot_manager
python bot_manager.py systemctl-restart  # Explicit restart
python bot_manager.py systemctl-stop     # Explicit stop
python bot_manager.py status             # Check uptime
```

### 7. Access Your Dashboard

Your bot dashboard will be available at:
```
http://your-ec2-ip/crypto-bot/
```

The dashboard provides:
- Real-time portfolio tracking
- AI analysis and trading decisions
- Performance metrics and logs
- Live market data and trends

## Uptime Management

The bot features intelligent uptime tracking:

- **Restarts preserve uptime**: `systemctl restart`, configuration changes, updates
- **Stops reset uptime**: `systemctl stop`, explicit shutdown commands
- **Crashes preserve uptime**: Automatic recovery maintains uptime continuity

### Uptime Commands

| Command | Uptime Behavior | Use Case |
|---------|----------------|----------|
| `sudo systemctl restart crypto-bot` | ✅ Preserves | Updates, config changes |
| `sudo systemctl stop crypto-bot` | ❌ Resets | Maintenance, shutdown |
| `python bot_manager.py restart` | ✅ Preserves | Manual restart |
| `python bot_manager.py stop` | ❌ Resets | Manual stop |

## Troubleshooting

### Common Issues

1. **Service fails to start:**
   - Check logs with `sudo journalctl -u crypto-bot -f`
   - Verify your API keys are correctly formatted in the .env file
   - Ensure your Google Cloud service account has the necessary permissions

2. **High CPU or memory usage:**
   - Consider upgrading your instance type
   - Adjust the trading interval in the .env file

3. **Network connectivity issues:**
   - Check that your security groups allow outbound connections
   - Verify that your instance has internet access

4. **Uptime not tracking correctly:**
   - Check bot_manager.py status for service detection
   - Verify dependencies are installed: `pip install -r requirements.txt`
   - Review logs for uptime-related messages

For additional help, please open an issue on the GitHub repository.
