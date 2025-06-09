#!/usr/bin/env python3

import json
import os
import sys
sys.path.append('/home/markus/AI-crypto-bot')

from utils.dashboard_updater import DashboardUpdater

def force_dashboard_update():
    """Force a complete dashboard update with current portfolio data"""
    
    print("=== Forcing Dashboard Update ===")
    
    try:
        # Load current portfolio data
        portfolio_file = "/home/markus/AI-crypto-bot/data/portfolio.json"
        if not os.path.exists(portfolio_file):
            print(f"❌ Portfolio file not found: {portfolio_file}")
            return
        
        with open(portfolio_file, 'r') as f:
            portfolio_data = json.load(f)
        
        print(f"✅ Loaded portfolio data")
        print(f"   Assets: {list(portfolio_data.keys())}")
        
        # Check SOL in source data
        if "SOL" in portfolio_data:
            sol = portfolio_data["SOL"]
            print(f"   SOL: amount={sol.get('amount', 'N/A')}, price=${sol.get('last_price_usd', 'N/A')}")
        else:
            print("   ⚠️ SOL not found in source portfolio data")
        
        # Create dashboard updater
        updater = DashboardUpdater()
        
        # Create dummy trading data
        trading_data = {
            "recent_trades": [],
            "market_data": {},
            "trading_results": {}
        }
        
        # Force update
        print("🔄 Updating dashboard...")
        updater.update_dashboard(trading_data, portfolio_data)
        
        print("✅ Dashboard update completed")
        
        # Verify the updated data
        web_portfolio_file = "/var/www/html/crypto-bot/data/portfolio_data.json"
        if os.path.exists(web_portfolio_file):
            with open(web_portfolio_file, 'r') as f:
                updated_data = json.load(f)
            
            if "SOL" in updated_data:
                sol = updated_data["SOL"]
                print(f"✅ SOL in updated dashboard data:")
                print(f"   Amount: {sol.get('amount', 'N/A')}")
                print(f"   Price: ${sol.get('last_price_usd', 'N/A')}")
                print(f"   Value: ${sol.get('value_usd', 'N/A')}")
                print(f"   Allocation: {sol.get('allocation', 'N/A')}%")
            else:
                print("❌ SOL not found in updated dashboard data")
        
    except Exception as e:
        print(f"❌ Error forcing dashboard update: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    force_dashboard_update()
