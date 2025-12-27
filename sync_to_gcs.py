#!/usr/bin/env python3
"""
Sync historical data files to Google Cloud Storage
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from data_collector import DataCollector
from coinbase_client import CoinbaseClient
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_local_files_to_gcs():
    """Sync all local historical data files to GCS"""
    
    try:
        # Initialize clients
        logger.info("Initializing clients for GCS sync...")
        coinbase_client = CoinbaseClient()
        data_collector = DataCollector(coinbase_client)
        
        if not data_collector.gcs_client:
            logger.error("GCS client not available. Check credentials and configuration.")
            return False
        
        # Find all historical data files
        data_dir = Path("./data/historical")
        parquet_files = list(data_dir.glob("*.parquet"))
        
        if not parquet_files:
            logger.warning("No parquet files found in ./data/historical/")
            return False
        
        logger.info(f"Found {len(parquet_files)} files to sync to GCS")
        
        sync_results = {
            "success": True,
            "files_synced": [],
            "errors": [],
            "total_size_mb": 0
        }
        
        for file_path in parquet_files:
            try:
                logger.info(f"Syncing {file_path.name} to GCS...")
                
                # Load the data
                df = pd.read_parquet(file_path)
                
                # Parse filename to extract product and timeframe info
                # Format: BTC-USD_hour_365d.parquet or ETH-USD_hourly_30d.parquet
                filename = file_path.stem  # Remove .parquet extension
                parts = filename.split('_')
                
                if len(parts) >= 3:
                    product_id = parts[0]  # BTC-USD or ETH-USD
                    granularity = "ONE_HOUR"  # We know it's hourly data
                    timeframe = parts[-1]  # 365d, 180d, 30d
                    
                    # Create GCS path structure
                    # Format: historical/{product}/{granularity}/{timeframe}/data.parquet
                    gcs_path = f"historical/{product_id}/{granularity}/{timeframe}/data.parquet"
                    
                    # Upload to GCS
                    success = data_collector.upload_to_gcs(df, gcs_path)
                    
                    if success:
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        sync_results["files_synced"].append({
                            "local_file": str(file_path),
                            "gcs_path": gcs_path,
                            "rows": len(df),
                            "size_mb": round(file_size_mb, 2),
                            "date_range": {
                                "start": df.index.min().isoformat(),
                                "end": df.index.max().isoformat()
                            }
                        })
                        sync_results["total_size_mb"] += file_size_mb
                        logger.info(f"✅ Successfully synced {file_path.name} ({len(df)} rows, {file_size_mb:.2f} MB)")
                    else:
                        error_msg = f"Failed to upload {file_path.name} to GCS"
                        sync_results["errors"].append(error_msg)
                        logger.error(f"❌ {error_msg}")
                else:
                    error_msg = f"Could not parse filename format: {filename}"
                    sync_results["errors"].append(error_msg)
                    logger.warning(f"⚠️ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Error processing {file_path.name}: {e}"
                sync_results["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Final results
        if sync_results["errors"]:
            sync_results["success"] = False
        
        logger.info(f"GCS sync completed!")
        logger.info(f"Files synced: {len(sync_results['files_synced'])}")
        logger.info(f"Total data synced: {sync_results['total_size_mb']:.2f} MB")
        logger.info(f"Errors: {len(sync_results['errors'])}")
        
        if sync_results["errors"]:
            logger.error("Errors encountered:")
            for error in sync_results["errors"]:
                logger.error(f"  - {error}")
        
        return sync_results["success"]
        
    except Exception as e:
        logger.error(f"Error in GCS sync: {e}")
        return False

def main():
    """Main function"""
    try:
        logger.info("Starting GCS sync for historical data...")
        success = sync_local_files_to_gcs()
        
        if success:
            print("\n✅ Successfully synced all historical data to Google Cloud Storage")
            print(f"📁 GCS Bucket: gs://intense-base-456414-u5-backtest-data/historical/")
            print("🔄 Data is now available for hybrid laptop/server backtesting workflow")
        else:
            print("\n❌ GCS sync completed with errors. Check logs for details.")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)