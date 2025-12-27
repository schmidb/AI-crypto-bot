#!/usr/bin/env python3
"""
Sync historical data for backtesting (local storage version)
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector import DataCollector
from coinbase_client import CoinbaseClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_historical_data_local(days: int = 30, products: list = None, granularity: str = 'ONE_HOUR'):
    """Sync historical data to local storage for backtesting
    
    Args:
        days: Number of days of historical data to download
        products: List of trading pairs (e.g., ['BTC-USD', 'ETH-USD'])
        granularity: Data granularity (ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, SIX_HOUR, ONE_DAY)
    """
    
    if products is None:
        products = ['BTC-USD', 'ETH-USD']
    
    try:
        # Initialize clients
        logger.info("Initializing Coinbase client...")
        coinbase_client = CoinbaseClient()
        
        # Create data collector without GCS for local testing
        data_collector = DataCollector(coinbase_client, gcs_bucket_name=None)
        
        # Create local data directory
        data_dir = Path("./data/historical")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Syncing {days} days of {granularity} data from {start_date.date()} to {end_date.date()}")
        logger.info(f"Products: {', '.join(products)}")
        
        for product_id in products:
            try:
                logger.info(f"Fetching historical data for {product_id}...")
                
                # Fetch historical data
                df = data_collector.fetch_bulk_historical_data(
                    product_id=product_id,
                    start_date=start_date,
                    end_date=end_date,
                    granularity=granularity
                )
                
                if df.empty:
                    logger.warning(f"No data retrieved for {product_id}")
                    continue
                
                # Validate data quality
                validation = data_collector.validate_data_continuity(df)
                logger.info(f"Data quality for {product_id}: {validation['quality_score']}%")
                
                # Save to local parquet file with descriptive name
                granularity_short = granularity.replace('ONE_', '').replace('_', '').lower()
                output_file = data_dir / f"{product_id}_{granularity_short}_{days}d.parquet"
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

def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(description='Sync historical cryptocurrency data for backtesting')
    
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days of historical data to download (default: 30)')
    
    parser.add_argument('--products', type=str, default='BTC-USD,ETH-USD',
                       help='Comma-separated list of trading pairs (default: BTC-USD,ETH-USD)')
    
    parser.add_argument('--granularity', type=str, default='ONE_HOUR',
                       choices=['ONE_MINUTE', 'FIVE_MINUTE', 'FIFTEEN_MINUTE', 'ONE_HOUR', 'SIX_HOUR', 'ONE_DAY'],
                       help='Data granularity (default: ONE_HOUR)')
    
    args = parser.parse_args()
    
    # Parse products list
    products = [p.strip() for p in args.products.split(',')]
    
    # Run sync
    success = sync_historical_data_local(
        days=args.days,
        products=products,
        granularity=args.granularity
    )
    
    if success:
        print(f"\n✅ Successfully downloaded {args.days} days of {args.granularity} data")
        print(f"📊 Products: {', '.join(products)}")
        print(f"📁 Data saved to: ./data/historical/")
    else:
        print(f"\n❌ Failed to download historical data")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()