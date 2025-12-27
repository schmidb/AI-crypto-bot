# AWS Deployment Guide

Complete guide for deploying the AI crypto trading bot on Amazon Web Services using EC2.

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Basic familiarity with Linux command line
- API keys from Coinbase and Google Cloud

## Quick Deployment

### 1. Launch EC2 Instance

```bash
# Set variables
export AWS_REGION=us-east-1
export KEY_PAIR_NAME=crypto-bot-key
export INSTANCE_TYPE=t3.medium
export AMI_ID=ami-0c02fb55956c7d316  # Amazon Linux 2023

# Create key pair (if needed)
aws ec2 create-key-pair --key-name $KEY_PAIR_NAME \
    --query 'KeyMaterial' --output text > ~/.ssh/$KEY_PAIR_NAME.pem
chmod 400 ~/.ssh/$KEY_PAIR_NAME.pem

# Launch instance
aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_PAIR_NAME \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=crypto-trading-bot}]'
```

### 2. Connect and Setup

```bash
# Get instance IP
INSTANCE_IP=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=crypto-trading-bot" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

# SSH into instance
ssh -i ~/.ssh/$KEY_PAIR_NAME.pem ec2-user@$INSTANCE_IP

# Clone repository
git clone https://github.com/yourusername/AI-crypto-bot.git
cd AI-crypto-bot

# Run AWS setup script
bash aws_setup/setup_ec2.sh
```

### 3. Configure Environment

```bash
# Edit configuration
nano .env

# Add your API keys and settings
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----...
GOOGLE_CLOUD_PROJECT=your-project-id
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

## Detailed Setup Guide

### EC2 Configuration

#### Recommended Instance Types

| Use Case | Instance Type | vCPUs | Memory | Storage | Cost/Month* |
|----------|---------------|-------|---------|---------|-------------|
| Development | t3.micro | 2 | 1 GB | EBS | ~$8 |
| Production | t3.medium | 2 | 4 GB | EBS | ~$30 |
| High Volume | t3.large | 2 | 8 GB | EBS | ~$60 |

*Approximate costs for us-east-1 region

#### Security Group Configuration

```bash
# Create security group
aws ec2 create-security-group \
    --group-name crypto-bot-sg \
    --description "Security group for crypto trading bot"

# Get security group ID
SG_ID=$(aws ec2 describe-security-groups \
    --group-names crypto-bot-sg \
    --query 'SecurityGroups[0].GroupId' --output text)

# Allow SSH access
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

# Allow HTTP access for dashboard
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# Allow HTTPS access (optional)
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0
```

### IAM Role Setup

#### Create IAM Role for EC2

```bash
# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
    --role-name CryptoBotRole \
    --assume-role-policy-document file://trust-policy.json

# Create policy for CloudWatch and S3 access
cat > crypto-bot-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Attach policy to role
aws iam put-role-policy \
    --role-name CryptoBotRole \
    --policy-name CryptoBotPolicy \
    --policy-document file://crypto-bot-policy.json

# Create instance profile
aws iam create-instance-profile --instance-profile-name CryptoBotProfile

# Add role to instance profile
aws iam add-role-to-instance-profile \
    --instance-profile-name CryptoBotProfile \
    --role-name CryptoBotRole
```

### Automated Setup Script

The `aws_setup/setup_ec2.sh` script performs:

1. **System Updates**: Updates Amazon Linux packages
2. **Python Environment**: Installs Python 3.11 and creates virtual environment
3. **Dependencies**: Installs all required packages
4. **Supervisor Setup**: Configures process management
5. **Apache Setup**: Configures web server for dashboard
6. **CloudWatch Integration**: Sets up monitoring
7. **Email Configuration**: Configures daily reports

#### Manual Setup Steps

```bash
# Update system (Amazon Linux 2023)
sudo dnf update -y

# Install required packages
sudo dnf install -y python3.11 python3.11-pip git httpd supervisor

# Install Python 3.11 as default
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Create virtual environment
python3 -m venv ~/crypto-bot-env
source ~/crypto-bot-env/bin/activate

# Install dependencies
cd ~/AI-crypto-bot
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p ~/AI-crypto-bot/logs
mkdir -p ~/AI-crypto-bot/data

# Setup supervisor
sudo tee /etc/supervisord.d/crypto-bot.ini << EOF
[program:crypto-bot]
command=/home/ec2-user/crypto-bot-env/bin/python /home/ec2-user/AI-crypto-bot/main.py
directory=/home/ec2-user/AI-crypto-bot
autostart=true
autorestart=true
startretries=10
user=ec2-user
redirect_stderr=true
stdout_logfile=/home/ec2-user/AI-crypto-bot/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=HOME="/home/ec2-user",USER="ec2-user",SUPERVISOR_ENABLED="1"
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true
EOF

# Start and enable supervisor
sudo systemctl start supervisord
sudo systemctl enable supervisord
```

### CloudWatch Integration

#### Install CloudWatch Agent

```bash
# Download and install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Create CloudWatch config
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
  "metrics": {
    "namespace": "CryptoBot",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_iowait",
          "cpu_usage_user",
          "cpu_usage_system"
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ec2-user/AI-crypto-bot/logs/supervisor.log",
            "log_group_name": "crypto-bot-logs",
            "log_stream_name": "{instance_id}/supervisor.log"
          },
          {
            "file_path": "/home/ec2-user/AI-crypto-bot/logs/daily_report.log",
            "log_group_name": "crypto-bot-logs",
            "log_stream_name": "{instance_id}/daily_report.log"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config -m ec2 -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

### S3 Backup Integration

#### Setup S3 Backup

```bash
# Create S3 bucket for backups
aws s3 mb s3://crypto-bot-backups-$(date +%s)

# Create backup script with S3 sync
tee ~/backup_to_s3.sh << 'EOF'
#!/bin/bash
BUCKET_NAME="crypto-bot-backups-$(aws sts get-caller-identity --query Account --output text)"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/crypto_bot_backup_$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Copy important files
cp ~/AI-crypto-bot/.env $BACKUP_DIR/
cp -r ~/AI-crypto-bot/data/ $BACKUP_DIR/
cp -r ~/AI-crypto-bot/logs/ $BACKUP_DIR/

# Create tarball
tar -czf /tmp/crypto_bot_backup_$DATE.tar.gz -C /tmp crypto_bot_backup_$DATE

# Upload to S3
aws s3 cp /tmp/crypto_bot_backup_$DATE.tar.gz s3://$BUCKET_NAME/

# Cleanup local files
rm -rf $BACKUP_DIR /tmp/crypto_bot_backup_$DATE.tar.gz

# Keep only last 30 backups in S3
aws s3 ls s3://$BUCKET_NAME/ | sort | head -n -30 | awk '{print $4}' | \
    xargs -I {} aws s3 rm s3://$BUCKET_NAME/{}

echo "Backup completed: crypto_bot_backup_$DATE.tar.gz"
EOF

chmod +x ~/backup_to_s3.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/ec2-user/backup_to_s3.sh
```

## Load Balancer Setup (Optional)

### Application Load Balancer

```bash
# Create target group
aws elbv2 create-target-group \
    --name crypto-bot-targets \
    --protocol HTTP \
    --port 80 \
    --vpc-id vpc-xxxxxxxxx \
    --health-check-path /

# Get target group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
    --names crypto-bot-targets \
    --query 'TargetGroups[0].TargetGroupArn' --output text)

# Register instance with target group
aws elbv2 register-targets \
    --target-group-arn $TG_ARN \
    --targets Id=$INSTANCE_ID

# Create load balancer
aws elbv2 create-load-balancer \
    --name crypto-bot-alb \
    --subnets subnet-xxxxxxxx subnet-yyyyyyyy \
    --security-groups $SG_ID
```

## Auto Scaling Setup (Optional)

### Launch Template

```bash
# Create launch template
aws ec2 create-launch-template \
    --launch-template-name crypto-bot-template \
    --launch-template-data '{
        "ImageId": "'$AMI_ID'",
        "InstanceType": "'$INSTANCE_TYPE'",
        "KeyName": "'$KEY_PAIR_NAME'",
        "SecurityGroupIds": ["'$SG_ID'"],
        "IamInstanceProfile": {"Name": "CryptoBotProfile"},
        "UserData": "'$(base64 -w 0 aws_setup/user-data.sh)'"
    }'

# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name crypto-bot-asg \
    --launch-template LaunchTemplateName=crypto-bot-template,Version=1 \
    --min-size 1 \
    --max-size 3 \
    --desired-capacity 1 \
    --target-group-arns $TG_ARN \
    --availability-zones us-east-1a us-east-1b
```

## Monitoring & Alerting

### CloudWatch Alarms

```bash
# CPU utilization alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "CryptoBot-HighCPU" \
    --alarm-description "Alarm when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=InstanceId,Value=$INSTANCE_ID \
    --evaluation-periods 2

# Memory utilization alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "CryptoBot-HighMemory" \
    --alarm-description "Alarm when memory exceeds 85%" \
    --metric-name mem_used_percent \
    --namespace CryptoBot \
    --statistic Average \
    --period 300 \
    --threshold 85 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2
```

### SNS Notifications

```bash
# Create SNS topic
aws sns create-topic --name crypto-bot-alerts

# Get topic ARN
TOPIC_ARN=$(aws sns list-topics --query 'Topics[?contains(TopicArn, `crypto-bot-alerts`)].TopicArn' --output text)

# Subscribe email to topic
aws sns subscribe \
    --topic-arn $TOPIC_ARN \
    --protocol email \
    --notification-endpoint your-email@example.com

# Add SNS action to alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "CryptoBot-HighCPU" \
    --alarm-actions $TOPIC_ARN \
    # ... other alarm parameters
```

## Service Management

### Supervisor Commands

```bash
# Check status
sudo supervisorctl status crypto-bot

# Start/stop/restart
sudo supervisorctl start crypto-bot
sudo supervisorctl stop crypto-bot
sudo supervisorctl restart crypto-bot

# View logs
sudo supervisorctl tail -f crypto-bot
```

### SystemD Integration

```bash
# Enable supervisor to start on boot
sudo systemctl enable supervisord

# Check supervisor status
sudo systemctl status supervisord
```

## Security Best Practices

### Security Groups

```bash
# Restrict SSH access to your IP
MY_IP=$(curl -s ifconfig.me)
aws ec2 revoke-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr $MY_IP/32
```

### Systems Manager Session Manager

```bash
# Install SSM agent (usually pre-installed on Amazon Linux)
sudo dnf install -y amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent

# Connect via Session Manager (no SSH key needed)
aws ssm start-session --target $INSTANCE_ID
```

### Secrets Manager Integration

```bash
# Store sensitive configuration in Secrets Manager
aws secretsmanager create-secret \
    --name crypto-bot-config \
    --description "Crypto bot configuration" \
    --secret-string '{
        "COINBASE_API_KEY": "your-api-key",
        "COINBASE_API_SECRET": "your-api-secret",
        "GMAIL_APP_PASSWORD": "your-gmail-password"
    }'

# Update application to read from Secrets Manager
pip install boto3
```

## Cost Optimization

### Spot Instances

```bash
# Launch spot instance
aws ec2 request-spot-instances \
    --spot-price "0.05" \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification '{
        "ImageId": "'$AMI_ID'",
        "InstanceType": "'$INSTANCE_TYPE'",
        "KeyName": "'$KEY_PAIR_NAME'",
        "SecurityGroups": ["crypto-bot-sg"]
    }'
```

### Reserved Instances

```bash
# Purchase Reserved Instance (for long-term usage)
aws ec2 purchase-reserved-instances-offering \
    --reserved-instances-offering-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
    --instance-count 1
```

### Instance Scheduling

```bash
# Create Lambda function to start/stop instances
# Schedule with EventBridge for cost savings during off-hours
```

## Troubleshooting

### Common Issues

#### 1. Instance Launch Failures

```bash
# Check instance status
aws ec2 describe-instances --instance-ids $INSTANCE_ID

# Check system log
aws ec2 get-console-output --instance-id $INSTANCE_ID
```

#### 2. Service Connection Issues

```bash
# Check security groups
aws ec2 describe-security-groups --group-ids $SG_ID

# Test connectivity
telnet $INSTANCE_IP 80
```

#### 3. CloudWatch Agent Issues

```bash
# Check agent status
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -m ec2 -a query-config

# Restart agent
sudo systemctl restart amazon-cloudwatch-agent
```

This comprehensive guide ensures successful deployment and operation of the AI crypto trading bot on Amazon Web Services.