#!/bin/bash

# Setup CloudWatch monitoring for the crypto trading bot
# This script installs and configures the CloudWatch agent

# Exit on error
set -e

echo "Setting up CloudWatch monitoring for AI Crypto Trading Bot..."

# Install CloudWatch agent
echo "Installing CloudWatch agent..."
sudo yum install -y amazon-cloudwatch-agent

# Create CloudWatch agent configuration
echo "Creating CloudWatch agent configuration..."
cat > /tmp/cloudwatch-config.json << 'EOL'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ec2-user/AI-crypto-bot/logs/trading_bot.log",
            "log_group_name": "crypto-bot-logs",
            "log_stream_name": "{instance_id}-trading-bot",
            "retention_in_days": 14
          },
          {
            "file_path": "/var/log/messages",
            "log_group_name": "crypto-bot-system-logs",
            "log_stream_name": "{instance_id}-system",
            "retention_in_days": 7
          }
        ]
      }
    }
  },
  "metrics": {
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_user",
          "cpu_usage_system"
        ],
        "metrics_collection_interval": 60,
        "totalcpu": true
      },
      "disk": {
        "measurement": [
          "used_percent",
          "inodes_free"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "/"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      },
      "swap": {
        "measurement": [
          "swap_used_percent"
        ],
        "metrics_collection_interval": 60
      }
    },
    "append_dimensions": {
      "InstanceId": "${aws:InstanceId}"
    }
  }
}
EOL

# Apply the configuration
echo "Applying CloudWatch agent configuration..."
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/tmp/cloudwatch-config.json

# Start the CloudWatch agent
echo "Starting CloudWatch agent..."
sudo systemctl start amazon-cloudwatch-agent

# Enable CloudWatch agent to start on boot
echo "Enabling CloudWatch agent to start on boot..."
sudo systemctl enable amazon-cloudwatch-agent

# Create a CloudWatch dashboard (requires AWS CLI with proper permissions)
echo "Note: To create a CloudWatch dashboard, run the following command with proper AWS CLI credentials:"
echo "aws cloudwatch put-dashboard --dashboard-name CryptoBotDashboard --dashboard-body file://cloudwatch_dashboard.json"

echo ""
echo "CloudWatch monitoring setup completed!"
echo ""
echo "You can now view logs and metrics in the CloudWatch console:"
echo "- Log groups: crypto-bot-logs and crypto-bot-system-logs"
echo "- Metrics: Under 'CWAgent' namespace"
echo ""
