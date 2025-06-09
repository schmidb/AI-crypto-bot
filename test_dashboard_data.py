#!/usr/bin/env python3

import json
import os

def test_dashboard_data():
    """Test if dashboard data files contain correct SOL information"""
    
    # Check local dashboard data
    local_portfolio_file = "dashboard/data/portfolio_data.json"
    web_portfolio_file = "/var/www/html/crypto-bot/data/portfolio_data.json"
    
    print("=== Testing Dashboard Data ===")
    
    for file_path, label in [(local_portfolio_file, "Local"), (web_portfolio_file, "Web Server")]:
        print(f"\n{label} Portfolio Data ({file_path}):")
        
        if not os.path.exists(file_path):
            print(f"  ❌ File not found: {file_path}")
            continue
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            print(f"  ✅ File loaded successfully")
            
            # Check SOL data
            if "SOL" in data:
                sol_data = data["SOL"]
                print(f"  ✅ SOL found in portfolio")
                print(f"     Amount: {sol_data.get('amount', 'N/A')}")
                print(f"     Price: ${sol_data.get('last_price_usd', 'N/A')}")
                print(f"     Value: ${sol_data.get('value_usd', 'N/A')}")
                print(f"     Allocation: {sol_data.get('allocation', 'N/A')}%")
                
                # Check if all required fields are present and non-zero
                required_fields = ['amount', 'last_price_usd', 'value_usd', 'allocation']
                missing_or_zero = []
                
                for field in required_fields:
                    value = sol_data.get(field, 0)
                    if value == 0 or value is None:
                        missing_or_zero.append(field)
                
                if missing_or_zero:
                    print(f"  ⚠️  Fields with zero/missing values: {missing_or_zero}")
                else:
                    print(f"  ✅ All SOL fields have valid values")
            else:
                print(f"  ❌ SOL not found in portfolio data")
                print(f"     Available assets: {list(data.keys())}")
                
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
    
    # Test the JavaScript filtering logic
    print(f"\n=== Testing Asset Filtering Logic ===")
    try:
        with open(web_portfolio_file, 'r') as f:
            portfolio = json.load(f)
        
        # Simulate the JavaScript filtering logic
        assets = [key for key in portfolio.keys() 
                 if isinstance(portfolio[key], dict) and 
                 portfolio[key] is not None and 
                 'amount' in portfolio[key]]
        
        print(f"Assets that would be displayed: {assets}")
        
        for asset in assets:
            if asset in portfolio:
                amount = portfolio[asset].get('amount', 0)
                value_usd = portfolio[asset].get('value_usd', 0)
                allocation = portfolio[asset].get('allocation', 0)
                
                print(f"  {asset}: amount={amount}, value=${value_usd}, allocation={allocation}%")
                
    except Exception as e:
        print(f"Error testing filtering logic: {e}")

if __name__ == "__main__":
    test_dashboard_data()
