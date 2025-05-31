#!/bin/bash

# Script to create AWS Secrets Manager secrets for the crypto trading bot
# Requires AWS CLI with appropriate permissions

# Exit on error
set -e

echo "Creating AWS Secrets Manager secrets for AI Crypto Trading Bot..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Create Coinbase API credentials secret
echo "Creating Coinbase API credentials secret..."
read -p "Enter your Coinbase API Key: " COINBASE_API_KEY
read -p "Enter your Coinbase API Secret: " COINBASE_API_SECRET

aws secretsmanager create-secret \
    --name crypto-bot/coinbase-api \
    --description "Coinbase API credentials for crypto trading bot" \
    --secret-string "{\"COINBASE_API_KEY\":\"$COINBASE_API_KEY\",\"COINBASE_API_SECRET\":\"$COINBASE_API_SECRET\"}"

# Create Google Cloud configuration secret
echo "Creating Google Cloud configuration secret..."
read -p "Enter your Google Cloud Project ID: " GOOGLE_CLOUD_PROJECT
read -p "Enter path to your Google Cloud service account key JSON file: " GOOGLE_CREDENTIALS_FILE

# Read the Google credentials file
GOOGLE_CREDENTIALS_JSON=$(cat "$GOOGLE_CREDENTIALS_FILE")

aws secretsmanager create-secret \
    --name crypto-bot/google-cloud \
    --description "Google Cloud configuration for crypto trading bot" \
    --secret-string "{\"GOOGLE_CLOUD_PROJECT\":\"$GOOGLE_CLOUD_PROJECT\",\"GOOGLE_APPLICATION_CREDENTIALS_JSON\":$GOOGLE_CREDENTIALS_JSON}"

# Create trading configuration secret
echo "Creating trading configuration secret..."
read -p "Enter trading pairs (comma-separated, e.g., BTC-USD,ETH-USD): " TRADING_PAIRS
read -p "Enter maximum investment per trade in USD: " MAX_INVESTMENT
read -p "Enter risk level (low, medium, high): " RISK_LEVEL
read -p "Enable simulation mode? (true/false): " SIMULATION_MODE
read -p "Enter LLM provider (vertex_ai, palm, gemini): " LLM_PROVIDER
read -p "Enter LLM model: " LLM_MODEL
read -p "Enter LLM location (e.g., us-central1): " LLM_LOCATION

aws secretsmanager create-secret \
    --name crypto-bot/trading-config \
    --description "Trading configuration for crypto trading bot" \
    --secret-string "{\"TRADING_PAIRS\":\"$TRADING_PAIRS\",\"MAX_INVESTMENT_PER_TRADE_USD\":\"$MAX_INVESTMENT\",\"RISK_LEVEL\":\"$RISK_LEVEL\",\"SIMULATION_MODE\":\"$SIMULATION_MODE\",\"LLM_PROVIDER\":\"$LLM_PROVIDER\",\"LLM_MODEL\":\"$LLM_MODEL\",\"LLM_LOCATION\":\"$LLM_LOCATION\"}"

echo ""
echo "AWS Secrets Manager secrets created successfully!"
echo ""
echo "To use these secrets in your application:"
echo "1. Ensure your EC2 instance has an IAM role with SecretsManager access"
echo "2. Use the use_secrets_manager.py script to load secrets instead of .env file"
echo ""
