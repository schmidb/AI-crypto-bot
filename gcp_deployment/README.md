# Google Cloud Platform Deployment Guide

This guide provides step-by-step instructions for deploying the AI Crypto Trading Bot on Google Cloud Platform (GCP) using Compute Engine.

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

# Run the Google Cloud Platform setup script
bash gcp_deployment/setup_gcp.sh
```

The setup script will:
- Install required dependencies
- Set up a Python virtual environment
- Configure a supervisor service for the bot with proper uptime tracking
- Install Apache for the web dashboard
- Create a template .env file
- Set up daily email reports with cron job
- Configure email settings in .env

### 4. Configure Your API Keys

```bash
# Edit your .env file with your API keys
nano .env
```

Add your API credentials to the .env file:

#### Required Configuration
```env
# Coinbase API credentials
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n

# Google Cloud AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
LLM_MODEL=gemini-3-flash-preview
LLM_LOCATION=global

# Email Configuration for Daily Reports
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
```

#### Getting Gmail App Password
1. Go to Google Account settings
2. Enable 2-factor authentication
3. Generate App Password for 'Mail'
4. Use this password in GMAIL_APP_PASSWORD

### 5. Manage the Bot Service

```bash
# Check the status
sudo supervisorctl status crypto-bot

# View logs
tail -f ~/AI-crypto-bot/logs/supervisor.log

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

The dashboard provides:
- Real-time portfolio tracking
- AI analysis and trading decisions
- Performance metrics and logs
- Live market data and trends

Make sure your firewall rules allow HTTP traffic (port 80).

### 8. Daily Email Reports

The setup automatically configures daily email reports that will be sent at 8:00 AM every day. To test the report:

```bash
cd ~/AI-crypto-bot
python3 daily_report.py
```

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

## Features Included

### Core Trading Bot
- Automated cryptocurrency trading with AI analysis
- Risk management and position sizing
- Real-time market data processing
- Portfolio tracking and rebalancing

### Web Dashboard
- Real-time portfolio visualization
- Trading history and performance metrics
- AI analysis insights
- Market data and trends

### Daily Email Reports
- Automated daily portfolio summaries
- Performance analysis and insights
- Trading activity reports
- Sent automatically at 8:00 AM daily

### Monitoring & Management
- Supervisor-based service management
- Comprehensive logging
- Uptime tracking
- Health monitoring

## Troubleshooting

### Common Issues

1. **Service fails to start:**
   - Check logs with `tail -f ~/AI-crypto-bot/logs/supervisor.log`
   - Verify your API keys are correctly formatted in the .env file
   - Ensure your Google Cloud service account has the necessary permissions

2. **Dashboard not accessible:**
   - Check that Apache is running: `sudo systemctl status apache2`
   - Verify firewall rules allow HTTP traffic
   - Check Apache error logs: `sudo tail -f /var/log/apache2/error.log`

3. **Daily reports not working:**
   - Check cron job: `crontab -l`
   - Test manually: `cd ~/AI-crypto-bot && python3 daily_report.py`
   - Check email credentials in .env file
   - Review daily report logs: `tail -f ~/AI-crypto-bot/logs/daily_report.log`

4. **High CPU or memory usage:**
   - Consider upgrading your instance type
   - Adjust the trading interval in the .env file

5. **Uptime not tracking correctly:**
   - Check bot_manager.py status for service detection
   - Verify dependencies are installed: `pip install -r requirements.txt`
   - Review supervisor logs for uptime-related messages

6. **AI analysis failures:**
   - Verify Google Cloud credentials and permissions
   - Check LLM_LOCATION is set to 'global' for preview models
   - Ensure using new google-genai library (not legacy google-generativeai)

For additional help, please open an issue on the GitHub repository.