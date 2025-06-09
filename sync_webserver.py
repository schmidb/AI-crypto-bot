#!/usr/bin/env python3
"""
Manual web server sync script
Use this to manually sync dashboard files to the web server
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.webserver_sync import WebServerSync
from utils.logger import get_supervisor_logger

def main():
    """Manually sync dashboard to web server"""
    logger = get_supervisor_logger()
    
    print("🔄 Manual Web Server Sync")
    print("=" * 40)
    
    try:
        sync = WebServerSync()
        
        if not sync.enabled:
            print("⚠️  Web server sync is disabled in .env")
            print("   Set WEBSERVER_SYNC_ENABLED=true to enable")
            response = input("Force sync anyway? (y/N): ")
            if response.lower() != 'y':
                print("❌ Sync cancelled")
                return
            
            print("🔧 Forcing sync...")
            sync.force_sync()
        else:
            print("✅ Web server sync is enabled")
            print(f"📁 Target: {sync.web_path}")
            sync.sync_to_webserver()
        
        print("🎉 Sync completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        logger.error(f"Manual sync error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
