#!/usr/bin/env python3
"""
Auto-download EUR historical data for health checks
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector import DataCollector
from coinbase_client import CoinbaseClient

def ensure_eur_data_available(days: int = 7):
    """Ensure EUR historical data is available for health checks"""
    
    products = ['BTC-EUR', 'ETH-EUR']
    data_dir = Path("data/historical")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if we have recent enough data
    for product in products:
        file_path = data_dir / f"{product}_hour_{days}d.parquet"
        
        needs_download = True
        if file_path.exists():
            # Check if file is recent (less than 4 hours old)
            file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_age.total_seconds() < 4 * 3600:  # 4 hours
                print(f"✅ {product} data is recent enough")
                needs_download = False
        
        if needs_download:
            print(f"📥 Downloading fresh {product} data...")
            try:
                client = CoinbaseClient()
                collector = DataCollector(client)
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days + 1)
                
                df = collector.fetch_bulk_historical_data(
                    product_id=product,
                    start_date=start_date,
                    end_date=end_date,
                    granularity='ONE_HOUR'
                )
                
                if df is not None and not df.empty:
                    df.to_parquet(file_path)
                    print(f"✅ Saved {len(df)} hours to {file_path}")
                else:
                    print(f"❌ No data received for {product}")
                    
            except Exception as e:
                print(f"❌ Error downloading {product}: {e}")

if __name__ == "__main__":
    ensure_eur_data_available()
