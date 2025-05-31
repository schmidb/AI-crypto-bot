# AWS EC2 Deployment Guide

This guide provides detailed instructions for deploying the AI Crypto Trading Bot on an AWS EC2 instance running Amazon Linux.

## Prerequisites

- AWS account with permissions to create EC2 instances
- Basic knowledge of AWS services and SSH
- SSH key pair for connecting to EC2 instances

## Step 1: Launch an EC2 Instance

1. Log in to the AWS Management Console
2. Navigate to EC2 and click "Launch Instance"
3. Choose Amazon Linux 2023 AMI
4. Select an instance type:
   - t2.micro for testing (free tier eligible)
   - t2.medium or better for production
5. Configure instance details:
   - Default VPC is fine for most cases
   - Enable auto-assign public IP
6. Add storage:
   - 8GB is sufficient for basic operation
   - Consider 16GB+ for longer-term operation with extensive logging
7. Configure security group:
   - Allow SSH (port 22) from your IP address
   - Allow HTTP (port 80) for web dashboard access
8. Review and launch the instance
9. Select your SSH key pair or create a new one
10. Launch the instance

## Step 2: Connect to Your Instance

```bash
ssh -i /path/to/your-key.pem ec2-user@your-instance-public-ip
```

## Step 3: Install and Configure the Bot

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AI-crypto-bot.git
   cd AI-crypto-bot
   ```

2. Make the setup script executable and run it:
   ```bash
   chmod +x setup_ec2.sh
   ./setup_ec2.sh
   ```

3. Configure your environment variables:
   ```bash
   nano .env
   ```
   
   Add your API keys and configuration:
   ```
   # Coinbase API credentials
   COINBASE_API_KEY=your_api_key_here
   COINBASE_API_SECRET=your_api_secret_here
   
   # Google Cloud configuration
   GOOGLE_CLOUD_PROJECT=your_project_id_here
   GOOGLE_APPLICATION_CREDENTIALS=/home/ec2-user/AI-crypto-bot/google-credentials.json
   
   # LLM configuration
   LLM_PROVIDER=vertex_ai
   LLM_MODEL=text-bison@002
   LLM_LOCATION=us-central1
   
   # Trading parameters
   TRADING_PAIRS=BTC-USD,ETH-USD
   MAX_INVESTMENT_PER_TRADE_USD=100
   RISK_LEVEL=medium
   SIMULATION_MODE=True
   ```

4. Upload your Google Cloud service account key:
   - On your local machine:
     ```bash
     scp -i /path/to/your-key.pem /path/to/your-google-credentials.json ec2-user@your-instance-public-ip:/home/ec2-user/AI-crypto-bot/google-credentials.json
     ```

5. Install and configure Apache web server:
   ```bash
   chmod +x aws_setup/install_apache.sh
   ./aws_setup/install_apache.sh
   ```

6. Start the service:
   ```bash
   sudo systemctl start crypto-bot
   ```

7. Enable the service to start on boot:
   ```bash
   sudo systemctl enable crypto-bot
   ```

## Step 4: Monitor the Bot

1. Check service status:
   ```bash
   sudo systemctl status crypto-bot
   ```

2. View logs:
   ```bash
   sudo journalctl -u crypto-bot -f
   ```

3. Check application logs:
   ```bash
   tail -f /home/ec2-user/AI-crypto-bot/logs/trading_bot.log
   ```

4. Access the web dashboard:
   - Open your browser and navigate to: `http://your-instance-public-ip/crypto-bot/`
   - Enter the username and password you set during Apache configuration

## Step 5: Set Up CloudWatch Monitoring (Optional)

1. Install and configure CloudWatch agent:
   ```bash
   chmod +x aws_setup/cloudwatch_setup.sh
   ./aws_setup/cloudwatch_setup.sh
   ```

2. Create a CloudWatch dashboard:
   ```bash
   aws cloudwatch put-dashboard --dashboard-name CryptoBotDashboard --dashboard-body file://aws_setup/cloudwatch_dashboard.json
   ```

## Troubleshooting

### Service Won't Start

1. Check for errors in the systemd journal:
   ```bash
   sudo journalctl -u crypto-bot -e
   ```

2. Verify your .env file has the correct permissions:
   ```bash
   chmod 600 .env
   ```

3. Check that your Google Cloud credentials file exists and has correct permissions:
   ```bash
   ls -la google-credentials.json
   chmod 600 google-credentials.json
   ```

### Web Dashboard Issues

1. Check Apache error logs:
   ```bash
   sudo tail -f /var/log/httpd/error_log
   ```

2. Verify Apache is running:
   ```bash
   sudo systemctl status httpd
   ```

3. Check file permissions:
   ```bash
   sudo ls -la /var/www/html/crypto-bot/
   ```

4. Restart Apache:
   ```bash
   sudo systemctl restart httpd
   ```

## Security Best Practices

1. **Use IAM roles**: Create an IAM role with the necessary permissions and attach it to your EC2 instance
2. **Regular updates**: Schedule regular updates with:
   ```bash
   sudo yum update -y
   ```
3. **Restrict access**: Update your security group to only allow HTTP access from your IP address
4. **Use AWS Secrets Manager**: Store API keys in AWS Secrets Manager and retrieve them programmatically
5. **Enable CloudWatch monitoring**: Set up CloudWatch alarms for instance metrics
