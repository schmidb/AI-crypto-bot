#!/usr/bin/env python3
"""
Setup lifecycle policy for GCS backtesting bucket
"""

import os
import sys
from google.cloud import storage
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_lifecycle_policy():
    """Set up lifecycle policy for the backtesting bucket"""
    
    try:
        # Get project ID from environment
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'ai-crypto-bot')
        bucket_name = f"{project_id}-backtest-data"
        
        logger.info(f"Setting up lifecycle policy for bucket: {bucket_name}")
        
        # Initialize GCS client
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            logger.error(f"Bucket {bucket_name} does not exist!")
            return False
        
        # Define lifecycle rules
        lifecycle_rules = [
            {
                'action': {'type': 'SetStorageClass', 'storageClass': 'NEARLINE'},
                'condition': {'age': 30}  # Move to Nearline after 30 days
            },
            {
                'action': {'type': 'SetStorageClass', 'storageClass': 'COLDLINE'},
                'condition': {'age': 730}  # Move to Coldline after 2 years
            }
        ]
        
        logger.info("Applying lifecycle rules:")
        logger.info("  - Move to NEARLINE storage after 30 days")
        logger.info("  - Move to COLDLINE storage after 2 years")
        
        # Apply lifecycle rules
        bucket.lifecycle_rules = lifecycle_rules
        bucket.patch()
        
        logger.info("✅ Lifecycle policy applied successfully!")
        
        # Verify the policy was set
        bucket.reload()
        lifecycle_rules_list = list(bucket.lifecycle_rules)
        if lifecycle_rules_list:
            logger.info(f"✅ Verified: {len(lifecycle_rules_list)} lifecycle rules active")
            for i, rule in enumerate(lifecycle_rules_list, 1):
                action = rule.get('action', {})
                condition = rule.get('condition', {})
                logger.info(f"  Rule {i}: {action.get('type')} to {action.get('storageClass')} after {condition.get('age')} days")
        else:
            logger.warning("⚠️ No lifecycle rules found after setting")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up lifecycle policy: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting GCS lifecycle policy setup...")
    
    success = setup_lifecycle_policy()
    
    if success:
        logger.info("🎉 Lifecycle policy setup completed successfully!")
        logger.info("💰 This will help optimize storage costs for long-term historical data")
        sys.exit(0)
    else:
        logger.error("❌ Lifecycle policy setup failed!")
        sys.exit(1)