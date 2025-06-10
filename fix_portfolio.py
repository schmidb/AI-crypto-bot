#!/usr/bin/env python3
"""
Script to fix the portfolio with reasonable starting values
"""
import json
import os
from datetime import datetime

def fix_portfolio():
    portfolio_file = "data/portfolio/portfolio.json"
    
    # Create reasonable starting portfolio
    # Based on your initial value of $333.81, let's distribute it:
    # 30% BTC, 30% ETH, 20% SOL, 20% USD
    
    current_prices = {
        'BTC': 109400.0,  # Approximate current price
        'ETH': 2670.0,    # Approximate current price  
        'SOL': 158.0      # Approximate current price
    }
    
    total_value = 333.81
    
    # Calculate amounts
    btc_value = total_value * 0.30  # $100.14
    eth_value = total_value * 0.30  # $100.14
    sol_value = total_value * 0.20  # $66.76
    usd_value = total_value * 0.20  # $66.76
    
    btc_amount = btc_value / current_prices['BTC']
    eth_amount = eth_value / current_prices['ETH']
    sol_amount = sol_value / current_prices['SOL']
    
    portfolio_data = {
        "portfolio_value_usd": total_value,
        "initial_value_usd": total_value,
        "last_updated": datetime.utcnow().isoformat(),
        "trades_executed": 0.0,
        "USD": {
            "amount": usd_value,
            "initial_amount": usd_value
        },
        "BTC": {
            "amount": round(btc_amount, 8),
            "initial_amount": round(btc_amount, 8),
            "last_price_usd": current_prices['BTC']
        },
        "ETH": {
            "amount": round(eth_amount, 6),
            "initial_amount": round(eth_amount, 6),
            "last_price_usd": current_prices['ETH']
        },
        "SOL": {
            "amount": round(sol_amount, 4),
            "initial_amount": round(sol_amount, 4),
            "last_price_usd": current_prices['SOL']
        }
    }
    
    # Ensure directory exists
    os.makedirs("data/portfolio", exist_ok=True)
    
    # Write portfolio
    with open(portfolio_file, 'w') as f:
        json.dump(portfolio_data, f, indent=2)
    
    print("Portfolio fixed successfully!")
    print(f"Total Value: ${total_value:.2f}")
    print(f"BTC: {btc_amount:.8f} (~${btc_value:.2f})")
    print(f"ETH: {eth_amount:.6f} (~${eth_value:.2f})")
    print(f"SOL: {sol_amount:.4f} (~${sol_value:.2f})")
    print(f"USD: ${usd_value:.2f}")
    
    return portfolio_data

if __name__ == "__main__":
    fix_portfolio()
