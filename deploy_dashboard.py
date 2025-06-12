#!/usr/bin/env python3
"""
Deploy dashboard to webserver using the webserver sync utility
"""

import sys
import os
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.webserver_sync import WebServerSync

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Deploy dashboard to webserver"""
    print("🚀 Starting dashboard deployment...")
    
    try:
        # Initialize webserver sync
        sync = WebServerSync()
        
        # Force sync to deploy regardless of config setting
        print("📁 Syncing files to webserver...")
        sync.force_sync()
        
        print("✅ Dashboard deployment completed successfully!")
        print(f"📍 Dashboard should be available at your webserver path: {sync.web_path}")
        
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        logging.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
