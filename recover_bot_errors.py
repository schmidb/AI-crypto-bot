#!/usr/bin/env python3
"""
Error recovery script for AI Crypto Trading Bot
"""

import time
import json
import os
from datetime import datetime

def check_api_status():
    """Check if APIs are accessible"""
    print("🔍 Checking API status...")
    
    try:
        from coinbase_client import CoinbaseClient
        client = CoinbaseClient()
        
        # Try a simple API call
        accounts = client.get_accounts()
        if accounts:
            print("✅ Coinbase API is accessible")
            return True
        else:
            print("⚠️  Coinbase API returned empty response")
            return False
            
    except Exception as e:
        error_str = str(e).lower()
        if "rate limit" in error_str:
            print("⏰ Rate limit detected - waiting 60 seconds...")
            time.sleep(60)
            return False
        elif "connection" in error_str:
            print("🌐 Connection error - check internet connection")
            return False
        else:
            print(f"❌ API error: {e}")
            return False

def reset_rate_limits():
    """Reset any rate limiting flags"""
    print("🔄 Resetting rate limits...")
    
    # Remove any rate limit files if they exist
    rate_limit_files = [
        'data/cache/rate_limit.json',
        'data/cache/api_errors.json'
    ]
    
    for file_path in rate_limit_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Removed {file_path}")

def check_data_integrity():
    """Check data file integrity"""
    print("📊 Checking data integrity...")
    
    critical_files = [
        'data/portfolio/portfolio.json',
        'data/trades/trade_history.json',
        'data/cache/bot_startup.json'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    json.load(f)
                print(f"✅ {file_path} is valid")
            except json.JSONDecodeError:
                print(f"❌ {file_path} is corrupted")
                # Create backup
                backup_path = f"{file_path}.backup.{int(time.time())}"
                os.rename(file_path, backup_path)
                print(f"📦 Moved corrupted file to {backup_path}")
        else:
            print(f"⚠️  {file_path} does not exist")

def main():
    """Main recovery function"""
    print("🚑 AI Crypto Trading Bot - Error Recovery")
    print("=" * 50)
    
    # Step 1: Check API status
    api_ok = check_api_status()
    
    # Step 2: Reset rate limits
    reset_rate_limits()
    
    # Step 3: Check data integrity
    check_data_integrity()
    
    # Step 4: Recommendations
    print("\n📋 Recovery Summary:")
    if api_ok:
        print("✅ APIs are accessible")
        print("🚀 You can restart the bot now")
    else:
        print("⚠️  API issues detected")
        print("💡 Recommendations:")
        print("   • Wait a few minutes for rate limits to reset")
        print("   • Check your internet connection")
        print("   • Verify your API credentials in .env file")
        print("   • Try running the bot in simulation mode")
    
    print("\n🔧 To restart the bot:")
    print("   python3 main.py")

if __name__ == "__main__":
    main()
