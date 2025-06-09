#!/usr/bin/env python3
"""
Test script for portfolio refresh functionality
"""

import os
import sys
import json
from utils.portfolio import Portfolio
from coinbase_client import CoinbaseClient

def test_portfolio_refresh():
    """Test the portfolio refresh functionality"""
    
    print("Testing portfolio refresh functionality...")
    
    # Create portfolio instance
    portfolio = Portfolio()
    
    # Create Coinbase client
    client = CoinbaseClient()
    
    print("\n1. Current portfolio before refresh:")
    current_data = portfolio.to_dict()
    for asset, data in current_data.items():
        if isinstance(data, dict) and 'amount' in data:
            amount = data['amount']
            if amount > 0:
                if asset == 'USD':
                    print(f"   {asset}: ${amount:.2f}")
                else:
                    price = data.get('last_price_usd', 0)
                    value = amount * price
                    print(f"   {asset}: {amount:.8f} (${value:.2f} @ ${price:.2f})")
    
    print("\n2. Getting fresh portfolio data from Coinbase...")
    try:
        coinbase_portfolio = client.get_portfolio()
        
        if coinbase_portfolio:
            print("   Coinbase portfolio data:")
            for asset, data in coinbase_portfolio.items():
                if isinstance(data, dict) and 'amount' in data:
                    amount = data['amount']
                    if amount > 0:
                        if asset == 'USD':
                            print(f"   {asset}: ${amount:.2f}")
                        else:
                            price = data.get('last_price_usd', 0)
                            value = amount * price
                            print(f"   {asset}: {amount:.8f} (${value:.2f} @ ${price:.2f})")
            
            print("\n3. Updating portfolio with Coinbase data...")
            result = portfolio.update_from_exchange(coinbase_portfolio)
            print(f"   Update result: {result}")
            
            print("\n4. Portfolio after refresh:")
            updated_data = portfolio.to_dict()
            for asset, data in updated_data.items():
                if isinstance(data, dict) and 'amount' in data:
                    amount = data['amount']
                    if amount > 0:
                        if asset == 'USD':
                            print(f"   {asset}: ${amount:.2f}")
                        else:
                            price = data.get('last_price_usd', 0)
                            value = amount * price
                            print(f"   {asset}: {amount:.8f} (${value:.2f} @ ${price:.2f})")
        else:
            print("   Failed to get portfolio data from Coinbase")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_portfolio_refresh()
