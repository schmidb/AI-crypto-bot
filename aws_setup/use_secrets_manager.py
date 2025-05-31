#!/usr/bin/env python3
"""
Script to load secrets from AWS Secrets Manager instead of .env file
This provides better security for API keys and credentials
"""

import boto3
import json
import os
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def get_secret(secret_name, region_name="us-east-1"):
    """
    Retrieve a secret from AWS Secrets Manager
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        region_name: AWS region where the secret is stored
        
    Returns:
        Secret value as dictionary
    """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        raise e
    else:
        # Decrypts secret using the associated KMS key
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)
        else:
            logger.error(f"Secret {secret_name} does not contain SecretString")
            return {}

def load_secrets_to_env():
    """
    Load secrets from AWS Secrets Manager and set as environment variables
    """
    try:
        # Load Coinbase API credentials
        coinbase_secrets = get_secret("crypto-bot/coinbase-api")
        if coinbase_secrets:
            os.environ["COINBASE_API_KEY"] = coinbase_secrets.get("COINBASE_API_KEY", "")
            os.environ["COINBASE_API_SECRET"] = coinbase_secrets.get("COINBASE_API_SECRET", "")
            logger.info("Loaded Coinbase API credentials from Secrets Manager")
        
        # Load Google Cloud configuration
        google_secrets = get_secret("crypto-bot/google-cloud")
        if google_secrets:
            os.environ["GOOGLE_CLOUD_PROJECT"] = google_secrets.get("GOOGLE_CLOUD_PROJECT", "")
            
            # For Google credentials, we'll save the JSON to a file
            if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in google_secrets:
                creds_path = "/home/ec2-user/AI-crypto-bot/google-credentials.json"
                with open(creds_path, "w") as f:
                    f.write(google_secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
                os.chmod(creds_path, 0o600)  # Secure permissions
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                logger.info("Saved Google Cloud credentials to file")
        
        # Load trading configuration
        trading_secrets = get_secret("crypto-bot/trading-config")
        if trading_secrets:
            for key, value in trading_secrets.items():
                os.environ[key] = str(value)
            logger.info("Loaded trading configuration from Secrets Manager")
            
        return True
    except Exception as e:
        logger.error(f"Error loading secrets: {e}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load secrets
    success = load_secrets_to_env()
    
    if success:
        print("Successfully loaded secrets from AWS Secrets Manager")
    else:
        print("Failed to load secrets from AWS Secrets Manager")
