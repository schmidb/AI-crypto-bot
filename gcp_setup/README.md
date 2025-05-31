# Google Compute Engine Deployment

This directory contains scripts and instructions for deploying the AI Crypto Trading Bot on Google Compute Engine.

## Quick Start

1. Create a Google Compute Engine VM instance with Debian or Ubuntu
2. Connect to your VM via SSH
3. Clone this repository
4. Run the setup script: `./gcp_setup/setup_gce.sh`
5. Configure your `.env` file with your API keys and settings
6. Start the bot: `sudo supervisorctl start crypto-bot`

## Detailed Instructions

For detailed instructions, refer to the Google Compute Engine deployment section in the main README.md file.

## Files

- `setup_gce.sh`: Setup script for deploying the bot on Google Compute Engine
- `gcp_secrets.py`: Helper module for accessing secrets from Google Cloud Secret Manager (optional)

## Using Google Cloud Secret Manager (Optional)

If you prefer to store your API keys and other sensitive information in Google Cloud Secret Manager instead of a local `.env` file:

1. Create secrets in Secret Manager:
   ```bash
   echo -n "your_api_key" | gcloud secrets create coinbase-api-key --data-file=-
   echo -n "your_api_secret" | gcloud secrets create coinbase-api-secret --data-file=-
   ```

2. Grant your VM's service account access to these secrets:
   ```bash
   gcloud secrets add-iam-policy-binding coinbase-api-key \
     --member="serviceAccount:YOUR_VM_SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   
   gcloud secrets add-iam-policy-binding coinbase-api-secret \
     --member="serviceAccount:YOUR_VM_SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. Modify your `main.py` to load secrets at startup:
   ```python
   # Add at the top of main.py
   import os
   try:
       from gcp_setup.gcp_secrets import load_secrets
       load_secrets()
   except Exception as e:
       print(f"Could not load secrets from Secret Manager: {e}")
       # Continue with .env file
   ```

## Monitoring

To monitor your bot on Google Compute Engine:

1. View logs: `tail -f ~/AI-crypto-bot/logs/supervisor.log`
2. Check status: `sudo supervisorctl status crypto-bot`
3. Set up Google Cloud Monitoring for more advanced monitoring
