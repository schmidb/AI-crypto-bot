from google.cloud import secretmanager
import os
import logging

logger = logging.getLogger(__name__)

def access_secret_version(project_id, secret_id, version_id="latest"):
    """
    Access the payload for the given secret version if one exists.
    
    Args:
        project_id: Google Cloud project ID
        secret_id: Secret ID in Secret Manager
        version_id: Version of the secret (default: "latest")
        
    Returns:
        The secret payload as a string
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}")
        raise

def load_secrets():
    """
    Load secrets from Secret Manager and set as environment variables
    """
    logger.info("Loading secrets from Google Cloud Secret Manager")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    if not project_id:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
    
    try:
        # Load Coinbase API credentials
        os.environ["COINBASE_API_KEY"] = access_secret_version(project_id, "coinbase-api-key")
        os.environ["COINBASE_API_SECRET"] = access_secret_version(project_id, "coinbase-api-secret")
        
        # Load Google Application Credentials
        service_account_key = access_secret_version(project_id, "google-application-credentials")
        
        # Write the service account key to a file
        key_path = "/tmp/service-account-key.json"
        with open(key_path, "w") as f:
            f.write(service_account_key)
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
        
        # Load other optional secrets if they exist
        try:
            os.environ["TRADING_PAIRS"] = access_secret_version(project_id, "trading-pairs")
        except:
            logger.info("trading-pairs secret not found, using default")
        
        try:
            os.environ["MAX_INVESTMENT_PER_TRADE_USD"] = access_secret_version(project_id, "max-investment")
        except:
            logger.info("max-investment secret not found, using default")
        
        try:
            os.environ["RISK_LEVEL"] = access_secret_version(project_id, "risk-level")
        except:
            logger.info("risk-level secret not found, using default")
        
        logger.info("Successfully loaded secrets from Secret Manager")
    except Exception as e:
        logger.error(f"Error loading secrets: {e}")
        raise
