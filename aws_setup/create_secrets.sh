#!/bin/bash

# Script to create AWS Secrets Manager secrets for the crypto trading bot

# Exit on error
set -e

echo "Creating AWS Secrets Manager secrets for AI Crypto Trading Bot..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! aws sts get-caller-identity &> /dev/null; then
    echo "AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Get region
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    echo "AWS region not set. Please configure your AWS CLI with a region."
    exit 1
fi

echo "Using AWS region: $REGION"

# Create secret for Coinbase API credentials
echo "Creating Coinbase API credentials secret..."
read -p "Enter your Coinbase API Key: " COINBASE_API_KEY
read -s -p "Enter your Coinbase API Secret: " COINBASE_API_SECRET
echo

aws secretsmanager create-secret \
    --name "crypto-bot/coinbase-credentials" \
    --description "Coinbase API credentials for crypto trading bot" \
    --secret-string "{\"api_key\":\"$COINBASE_API_KEY\",\"api_secret\":\"$COINBASE_API_SECRET\"}" \
    --region $REGION

echo "Coinbase credentials secret created successfully!"

# Create secret for Google Cloud credentials
echo "Creating Google Cloud credentials secret..."
read -p "Enter path to your Google Cloud service account JSON file: " GCP_CREDS_PATH

if [ ! -f "$GCP_CREDS_PATH" ]; then
    echo "File not found: $GCP_CREDS_PATH"
    exit 1
fi

GCP_CREDS_CONTENT=$(cat "$GCP_CREDS_PATH")

aws secretsmanager create-secret \
    --name "crypto-bot/google-cloud-credentials" \
    --description "Google Cloud service account credentials for crypto trading bot" \
    --secret-string "$GCP_CREDS_CONTENT" \
    --region $REGION

echo "Google Cloud credentials secret created successfully!"

# Create secret for bot configuration
echo "Creating bot configuration secret..."
read -p "Enter your Google Cloud Project ID: " GCP_PROJECT_ID
read -p "Enter LLM Model (default: gemini-2.5-pro): " LLM_MODEL
LLM_MODEL=${LLM_MODEL:-"gemini-2.5-pro"}

aws secretsmanager create-secret \
    --name "crypto-bot/configuration" \
    --description "Configuration settings for crypto trading bot" \
    --secret-string "{\"google_cloud_project\":\"$GCP_PROJECT_ID\",\"llm_model\":\"$LLM_MODEL\"}" \
    --region $REGION

echo "Configuration secret created successfully!"

echo ""
echo "All secrets created successfully in AWS Secrets Manager!"
echo ""
echo "Secret ARNs:"
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `crypto-bot`)].{Name:Name,ARN:ARN}' --output table --region $REGION

echo ""
echo "To use these secrets in your bot, set the following environment variable:"
echo "USE_AWS_SECRETS=true"
echo ""
echo "Make sure your EC2 instance has the appropriate IAM role with the policy from iam_policy.json"
