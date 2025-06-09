#!/usr/bin/env python3
"""
Utility script to update market data symlinks to point to the latest files
"""

import os
import glob
from pathlib import Path

def update_market_symlinks():
    """Update symlinks to point to the latest market data files"""
    
    data_dir = Path("data")
    market_data_dir = data_dir / "market_data"
    
    # Ensure market_data directory exists
    market_data_dir.mkdir(exist_ok=True)
    
    assets = ["BTC", "ETH", "SOL"]
    
    for asset in assets:
        # Find all files for this asset
        pattern = str(data_dir / f"{asset}_USD_*.json")
        files = glob.glob(pattern)
        
        if files:
            # Sort by modification time, newest first
            latest_file = max(files, key=os.path.getmtime)
            
            # Create symlink path
            symlink_path = market_data_dir / f"{asset}_USD_latest.json"
            
            # Remove existing symlink if it exists
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
            
            # Create new symlink (relative path)
            relative_path = os.path.relpath(latest_file, market_data_dir)
            symlink_path.symlink_to(relative_path)
            
            print(f"Updated {asset}_USD_latest.json -> {relative_path}")
        else:
            print(f"No data files found for {asset}")

if __name__ == "__main__":
    update_market_symlinks()
