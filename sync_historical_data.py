#!/usr/bin/env python3
"""
Sync historical data for backtesting (local storage version)
"""

import os
import sys
from datetime import datetime, timedelta
from data_collector import DataCollector
from coinbase_client import CoinbaseClient
import pandas as pd
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_historical_data_local():
    """Sync historical data to local storage for backtesting"""
    
    try:
        # Initialize clients
        logger.info("Initializing Coinbase client...")
        coinbase_client = CoinbaseClient()
        
        # Create data collector without GCS for local testing
        data_collector = DataCollector(coinbase_client, gcs_bucket_name=None)
        
        # Create local data directory
        data_dir = Path("./data/historical")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define products and time range
        products = ['BTC-USD', 'ETH-USD']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Start with 30 days for testing
        
        logger.info(f"Syncing data from {start_date.date()} to {end_date.date()}")
        
        for product_id in products:
            try:
                logger.info(f"Fetching historical data for {product_id}...")
                
                # Fetch historical data (hourly for now to avoid rate limits)
                df = data_collector.fetch_bulk_historical_data(
                    product_id=product_id,
                    start_date=start_date,
                    end_date=end_date,
                    granularity='ONE_HOUR'
                )
                
                if df.empty:
                    logger.warning(f"No data retrieved for {product_id}")
                    continue
                
                # Validate data quality
                validation = data_collector.validate_data_continuity(df)
                logger.info(f"Data quality for {product_id}: {validation['quality_score']}%")
                
                # Save to local parquet file
                output_file = data_dir / f"{product_id}_hourly_30d.parquet"
                df.to_parquet(output_file, compression='gzip')
                
                logger.info(f"Saved {len(df)} rows to {output_file}")
                
                # Display sample data
                logger.info(f"Sample data for {product_id}:")
                logger.info(f"  Date range: {df.index.min()} to {df.index.max()}")
                logger.info(f"  Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                logger.info(f"  Latest close: ${df['close'].iloc[-1]:.2f}")
                
            except Exception as e:
                logger.error(f"Error processing {product_id}: {e}")
                continue
        
        logger.info("Historical data sync completed!")
        
        # List all created files
        logger.info("Created files:")
        for file in data_dir.glob("*.parquet"):
            size_mb = file.stat().st_size / (1024 * 1024)
            logger.info(f"  {file.name}: {size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in historical data sync: {e}")
        return False

if __name__ == "__main__":
    success = sync_historical_data_local()
    sys.exit(0 if success else 1)