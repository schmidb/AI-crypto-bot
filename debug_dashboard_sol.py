#!/usr/bin/env python3

import json
import os

def debug_sol_issue():
    """Debug the SOL display issue in detail"""
    
    print("=== Debugging SOL Dashboard Issue ===\n")
    
    # Check both local and web server portfolio data
    files_to_check = [
        ("Local", "dashboard/data/portfolio_data.json"),
        ("Web Server", "/var/www/html/crypto-bot/data/portfolio_data.json")
    ]
    
    for label, file_path in files_to_check:
        print(f"{label} Portfolio Data:")
        print(f"File: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found!\n")
            continue
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if "SOL" not in data:
                print(f"❌ SOL not found in data!\n")
                continue
                
            sol_data = data["SOL"]
            print(f"✅ SOL data found")
            
            # Check each field and its type
            fields = ["amount", "last_price_usd", "value_usd", "allocation"]
            for field in fields:
                if field in sol_data:
                    value = sol_data[field]
                    print(f"  {field}: {value} (type: {type(value).__name__})")
                else:
                    print(f"  {field}: MISSING")
            
            # Check if value_usd is calculated correctly
            amount = sol_data.get("amount", 0)
            price = sol_data.get("last_price_usd", 0)
            value_usd = sol_data.get("value_usd", 0)
            
            expected_value = float(amount) * float(price)
            print(f"  Expected value_usd: {amount} * {price} = {expected_value}")
            print(f"  Actual value_usd: {value_usd}")
            print(f"  Values match: {abs(float(value_usd) - expected_value) < 0.01}")
            
            # Check if it's a string vs number issue
            if isinstance(value_usd, str):
                print(f"  ⚠️  value_usd is a string: '{value_usd}'")
                try:
                    float_val = float(value_usd)
                    print(f"  String converts to float: {float_val}")
                except ValueError as e:
                    print(f"  ❌ String cannot be converted to float: {e}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error reading file: {e}\n")
    
    # Test JavaScript-like processing
    print("=== JavaScript-like Processing Test ===")
    try:
        with open("/var/www/html/crypto-bot/data/portfolio_data.json", 'r') as f:
            portfolio = json.load(f)
        
        # Simulate the JavaScript filtering
        assets = [key for key in portfolio.keys() 
                 if isinstance(portfolio[key], dict) and 
                 portfolio[key] is not None and 
                 'amount' in portfolio[key]]
        
        print(f"Filtered assets: {assets}")
        
        for asset in assets:
            if asset in portfolio:
                asset_data = portfolio[asset]
                amount = asset_data.get('amount', 0)
                value_usd = asset_data.get('value_usd', 0)
                allocation = asset_data.get('allocation', 0)
                
                # Test JavaScript-like operations
                try:
                    # Simulate JavaScript toFixed operations
                    if asset == 'SOL':
                        formatted_amount = f"{float(amount):.4f}"
                    else:
                        formatted_amount = f"{float(amount):.6f}"
                    
                    formatted_value = f"${float(value_usd):.2f}"
                    formatted_allocation = f"{float(allocation):.2f}%"
                    
                    print(f"  {asset}:")
                    print(f"    Amount: {amount} -> {formatted_amount}")
                    print(f"    Value: {value_usd} -> {formatted_value}")
                    print(f"    Allocation: {allocation} -> {formatted_allocation}")
                    
                    # Check for zero values
                    if float(value_usd) == 0:
                        print(f"    ❌ value_usd is zero!")
                    if float(allocation) == 0:
                        print(f"    ❌ allocation is zero!")
                        
                except (ValueError, TypeError) as e:
                    print(f"    ❌ Error formatting {asset}: {e}")
                
                print()
                
    except Exception as e:
        print(f"❌ Error in JavaScript simulation: {e}")

    # Check if there are any NaN or null values
    print("=== Checking for NaN/null values ===")
    try:
        with open("/var/www/html/crypto-bot/data/portfolio_data.json", 'r') as f:
            content = f.read()
        
        # Check for problematic values in the raw JSON
        problematic_values = ["null", "NaN", "undefined", "Infinity", "-Infinity"]
        for val in problematic_values:
            if val in content:
                print(f"⚠️  Found '{val}' in JSON content")
        
        # Check for empty strings or zero strings
        if '"value_usd": ""' in content or '"value_usd": "0"' in content:
            print("⚠️  Found empty or zero string for value_usd")
        if '"allocation": ""' in content or '"allocation": "0"' in content:
            print("⚠️  Found empty or zero string for allocation")
            
    except Exception as e:
        print(f"❌ Error checking raw JSON: {e}")

if __name__ == "__main__":
    debug_sol_issue()
