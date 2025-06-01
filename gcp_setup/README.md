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
   - Allow HTTP/HTTPS traffic if you plan to use the dashboard
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
- Configure a supervisor service for the bot
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

### 6. Access the Dashboard

The setup script installs Apache and configures a web dashboard that you can access at:

```
http://YOUR_VM_IP/crypto-bot/
```

Make sure your firewall rules allow HTTP traffic (port 80).

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

For additional help, please open an issue on the GitHub repository.
