# Google Cloud Deployment Guide

This guide provides step-by-step instructions for deploying the AI Crypto Trading Bot on a Google Compute Engine (GCE) instance.

## Deployment Steps

### 1. Create a VM Instance

1. **Log in to Google Cloud Console**
2. **Navigate to Compute Engine > VM instances**
3. **Click "Create Instance"**
4. **Configure your instance:**
   - Choose a name for your instance
   - Select a region and zone (e.g., us-central1-a)
   - Choose machine type (e2-medium recommended)
   - Select Debian or Ubuntu as the boot disk
   - Allow HTTP/HTTPS traffic for web dashboard access
   - Add a firewall rule to allow TCP port 80 for dashboard access
   - This is required for accessing the comprehensive web dashboard
   - Click "Create"

### 2. Connect to Your VM Instance

You can connect to your VM instance directly from the Google Cloud Console by clicking the "SSH" button, or use the gcloud command:

```bash
# Connect via SSH using gcloud
gcloud compute ssh your-instance-name --zone=your-zone
```

### 3. Clone the Repository and Run Setup Script

```bash
# Clone the repository
git clone https://github.com/yourusername/AI-crypto-bot.git
cd AI-crypto-bot

# Run the Google Cloud setup script
bash gcp_setup/setup_gce.sh
```

The setup script will:
- Install required dependencies
- Set up a Python virtual environment
- Configure a supervisor service for the bot with proper uptime tracking
- Install Apache for the web dashboard
- Create a template .env file

### 4. Configure Your API Keys

```bash
# Edit your .env file with your API keys
nano .env
```

Add your Coinbase API credentials and Google Cloud credentials to the .env file.

### 5. Manage the Bot Service

```bash
# Check the status
sudo supervisorctl status crypto-bot

# View logs
tail -f /var/log/crypto-bot/crypto-bot.log

# Restart the service
sudo supervisorctl restart crypto-bot

# Stop the service
sudo supervisorctl stop crypto-bot
```

### 6. Service Management with Proper Uptime Tracking

The bot now supports proper uptime tracking that distinguishes between restarts and stops:

```bash
# Restart (preserves uptime)
sudo supervisorctl restart crypto-bot
# OR use the enhanced script:
sudo /usr/local/bin/crypto-bot-restart

# Stop (resets uptime)
sudo supervisorctl stop crypto-bot
# OR use the enhanced script:
sudo /usr/local/bin/crypto-bot-stop

# Enhanced management via bot_manager
python bot_manager.py supervisorctl-restart  # Explicit restart
python bot_manager.py supervisorctl-stop     # Explicit stop
python bot_manager.py status                 # Check uptime
```

### 7. Access the Dashboard

The setup script installs Apache and configures a web dashboard that you can access at:

```
http://YOUR_VM_IP/crypto-bot/
```

Make sure your firewall rules allow HTTP traffic (port 80).

### 8. Configure Firewall Rules for API Access

To enable the "Refresh Portfolio from Coinbase" functionality, you need to open port 5000 in the Google Cloud firewall:

1. **Navigate to VPC Network > Firewall in Google Cloud Console**
2. **Click "Create Firewall Rule"**
3. **Configure the rule:**
   - Name: allow-api-port-5000
   - Description: Allow access to API server on port 5000
   - Network: (select your VPC network)
   - Priority: 1000
   - Direction of traffic: Ingress
   - Action on match: Allow
   - Targets: All instances in the network (or specify your instance)
   - Source filter: IP ranges
   - Source IP ranges: 0.0.0.0/0 (to allow from anywhere, or restrict as needed)
   - Protocols and ports: Specified protocols and ports > tcp:5000
4. **Click "Create"**

This allows the dashboard to communicate with the API server running on port 5000, enabling portfolio refresh functionality.

## Uptime Management

The bot features intelligent uptime tracking:

- **Restarts preserve uptime**: `supervisorctl restart`, configuration changes, updates
- **Stops reset uptime**: `supervisorctl stop`, explicit shutdown commands
- **Crashes preserve uptime**: Automatic recovery maintains uptime continuity

### Uptime Commands

| Command | Uptime Behavior | Use Case |
|---------|----------------|----------|
| `sudo supervisorctl restart crypto-bot` | ✅ Preserves | Updates, config changes |
| `sudo supervisorctl stop crypto-bot` | ❌ Resets | Maintenance, shutdown |
| `sudo /usr/local/bin/crypto-bot-restart` | ✅ Preserves | Enhanced restart |
| `sudo /usr/local/bin/crypto-bot-stop` | ❌ Resets | Enhanced stop |
| `python bot_manager.py restart` | ✅ Preserves | Manual restart |
| `python bot_manager.py stop` | ❌ Resets | Manual stop |

## Troubleshooting

### Common Issues

1. **Service fails to start:**
   - Check logs with `tail -f /var/log/crypto-bot/crypto-bot.log`
   - Verify your API keys are correctly formatted in the .env file
   - Ensure your Google Cloud service account has the necessary permissions

2. **Dashboard not accessible:**
   - Check that Apache is running: `sudo systemctl status apache2`
   - Verify firewall rules allow HTTP traffic
   - Check Apache error logs: `sudo tail -f /var/log/apache2/error.log`

3. **High CPU or memory usage:**
   - Consider upgrading your instance type
   - Adjust the trading interval in the .env file

4. **Uptime not tracking correctly:**
   - Check bot_manager.py status for service detection
   - Verify dependencies are installed: `pip install -r requirements.txt`
   - Review supervisor logs for uptime-related messages

For additional help, please open an issue on the GitHub repository.
