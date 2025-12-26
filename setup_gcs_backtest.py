#!/usr/bin/env python3
"""
Setup Google Cloud Storage for backtesting infrastructure
"""

import os
import sys
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_gcs_bucket():
    """Set up GCS bucket for backtesting data"""
    
    try:
        # Get project ID from environment (use existing GOOGLE_CLOUD_PROJECT)
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'ai-crypto-bot')
        bucket_name = f"{project_id}-backtest-data"
        
        logger.info(f"Setting up GCS bucket: {bucket_name}")
        logger.info(f"Using project ID: {project_id}")
        
        # Initialize GCS client
        try:
            client = storage.Client(project=project_id)
            logger.info("GCS client initialized successfully")
        except DefaultCredentialsError:
            logger.error("GCS credentials not found. Please run: gcloud auth application-default login")
            return False
        
        # Check if bucket exists
        bucket = client.bucket(bucket_name)
        
        if bucket.exists():
            logger.info(f"Bucket {bucket_name} already exists")
        else:
            # Create bucket
            logger.info(f"Creating bucket {bucket_name}...")
            bucket = client.create_bucket(bucket_name, location='US')
            logger.info(f"Bucket {bucket_name} created successfully")
        
        # Set up lifecycle policy for cost optimization
        logger.info("Setting up lifecycle policy...")
        
        lifecycle_rule = {
            'action': {'type': 'SetStorageClass', 'storageClass': 'NEARLINE'},
            'condition': {'age': 30}  # Move to Nearline after 30 days
        }
        
        lifecycle_rule_archive = {
            'action': {'type': 'SetStorageClass', 'storageClass': 'COLDLINE'},
            'condition': {'age': 730}  # Move to Coldline after 2 years
        }
        
        bucket.lifecycle_rules = [lifecycle_rule, lifecycle_rule_archive]
        bucket.patch()
        
        logger.info("Lifecycle policy configured successfully")
        
        # Test bucket access
        logger.info("Testing bucket access...")
        test_blob = bucket.blob('test/access_test.txt')
        test_blob.upload_from_string('Bucket access test successful')
        
        # Verify the test file
        if test_blob.exists():
            logger.info("Bucket access test: SUCCESS")
            # Clean up test file
            test_blob.delete()
        else:
            logger.warning("Bucket access test: FAILED")
            return False
        
        logger.info(f"GCS setup completed successfully!")
        logger.info(f"Bucket name: {bucket_name}")
        logger.info(f"Project ID: {project_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up GCS bucket: {e}")
        return False

def check_gcs_credentials():
    """Check if GCS credentials are properly configured"""
    
    try:
        client = storage.Client()
        # Try to list buckets to verify credentials
        buckets = list(client.list_buckets())
        logger.info(f"GCS credentials verified. Found {len(buckets)} buckets in project.")
        return True
    except DefaultCredentialsError:
        logger.error("GCS credentials not configured.")
        logger.info("To set up credentials, run: gcloud auth application-default login")
        return False
    except Exception as e:
        logger.error(f"Error checking GCS credentials: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting GCS setup for backtesting infrastructure...")
    
    # Check credentials first
    if not check_gcs_credentials():
        logger.error("Please configure GCS credentials before running setup")
        sys.exit(1)
    
    # Set up bucket
    success = setup_gcs_bucket()
    
    if success:
        logger.info("GCS setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("GCS setup failed!")
        sys.exit(1)