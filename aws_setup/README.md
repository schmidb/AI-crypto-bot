# AWS EC2 Deployment Guide

This guide provides step-by-step instructions for deploying the AI Crypto Trading Bot on an AWS EC2 instance.

## Deployment Steps

### 1. Launch an EC2 Instance

1. **Log in to your AWS Management Console**
2. **Navigate to EC2 and click "Launch Instance"**
3. **Configure your instance:**
   - Choose Amazon Linux 2023 AMI
   - Select an instance type (t2.medium or better recommended for production)
   - Configure security groups to allow SSH access (port 22)
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
- Create a systemd service for the bot
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

# Restart the service
sudo systemctl restart crypto-bot

# Stop the service
sudo systemctl stop crypto-bot
```

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

For additional help, please open an issue on the GitHub repository.
