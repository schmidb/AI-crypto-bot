#!/usr/bin/env python3
"""
Test script for backtesting infrastructure setup
"""

import os
import sys
from datetime import datetime, timedelta
from data_collector import DataCollector
from coinbase_client import CoinbaseClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_backtest_infrastructure():
    """Test the new backtesting infrastructure methods"""
    
    try:
        # Initialize clients
        logger.info("Initializing Coinbase client...")
        coinbase_client = CoinbaseClient()
        
        logger.info("Initializing Data collector with GCS support...")
        data_collector = DataCollector(coinbase_client)
        
        # Test 1: Check if GCS client is initialized
        logger.info(f"GCS client status: {'Initialized' if data_collector.gcs_client else 'Not available'}")
        logger.info(f"GCS bucket name: {data_collector.gcs_bucket_name}")
        logger.info(f"Local cache directory: {data_collector.local_cache_dir}")
        
        # Test 2: Try to fetch a small amount of historical data
        logger.info("Testing bulk historical data fetch (last 2 days)...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        df = data_collector.fetch_bulk_historical_data(
            product_id='BTC-USD',
            start_date=start_date,
            end_date=end_date,
            granularity='ONE_HOUR'  # Use hourly data for testing
        )
        
        if not df.empty:
            logger.info(f"Successfully fetched {len(df)} rows of historical data")
            logger.info(f"Date range: {df.index.min()} to {df.index.max()}")
            
            # Test 3: Validate data quality
            validation_results = data_collector.validate_data_continuity(df)
            logger.info(f"Data validation results: {validation_results}")
            
            # Test 4: Test GCS upload/download (if GCS is available)
            if data_collector.gcs_client:
                logger.info("Testing GCS upload/download...")
                test_path = "test/BTC-USD/ONE_HOUR/2024/12/test_data.parquet"
                
                # Upload test
                upload_success = data_collector.upload_to_gcs(df, test_path)
                logger.info(f"GCS upload test: {'Success' if upload_success else 'Failed'}")
                
                if upload_success:
                    # Download test
                    downloaded_df = data_collector.download_from_gcs(test_path, use_cache=False)
                    if not downloaded_df.empty and len(downloaded_df) == len(df):
                        logger.info("GCS download test: Success")
                    else:
                        logger.warning("GCS download test: Data mismatch")
            else:
                logger.info("Skipping GCS tests - client not available")
        else:
            logger.warning("No historical data retrieved - check API credentials")
        
        logger.info("Backtesting infrastructure test completed!")
        return True
        
    except Exception as e:
        logger.error(f"Error in backtesting infrastructure test: {e}")
        return False

if __name__ == "__main__":
    success = test_backtest_infrastructure()
    sys.exit(0 if success else 1)