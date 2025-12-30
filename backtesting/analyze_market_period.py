#!/usr/bin/env python3
"""
Analyze the market conditions during the backtesting period
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

def analyze_market_period():
    """Analyze the market conditions during our backtesting period"""
    
    # Load BTC data
    btc_df = pd.read_parquet('data/historical/BTC-USD_hour_180d.parquet')
    
    # Check if ETH data exists, if not use only BTC
    eth_file = 'data/historical/ETH-USD_hour_180d.parquet'
    if os.path.exists(eth_file):
        eth_df = pd.read_parquet(eth_file)
    else:
        print("⚠️ ETH 180d data not found, analyzing BTC only")
        eth_df = None
    
    print("="*80)
    print("📊 MARKET ANALYSIS FOR BACKTESTING PERIOD")
    print("="*80)
    
    # Analyze each asset
    assets = [("BTC-USD", btc_df)]
    if eth_df is not None:
        assets.append(("ETH-USD", eth_df))
    
    for name, df in assets:
        print(f"\n🪙 {name} Analysis:")
        print(f"   Period: {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}")
        print(f"   Duration: {(df.index.max() - df.index.min()).days} days")
        
        start_price = df.iloc[0]['close']
        end_price = df.iloc[-1]['close']
        market_return = ((end_price / start_price) - 1) * 100
        
        print(f"   Start price: ${start_price:,.2f}")
        print(f"   End price: ${end_price:,.2f}")
        print(f"   📈 Market return: {market_return:+.2f}%")
        
        # Calculate volatility
        daily_returns = df['close'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(24 * 365) * 100  # Annualized volatility
        print(f"   📊 Volatility (annualized): {volatility:.1f}%")
        
        # Find max drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        print(f"   📉 Max drawdown: {max_drawdown:.2f}%")
        
        # Market regime analysis
        high = df['high'].max()
        low = df['low'].min()
        current = end_price
        
        print(f"   🏔️  Period high: ${high:,.2f}")
        print(f"   🏔️  Period low: ${low:,.2f}")
        print(f"   📍 End vs high: {((current / high) - 1) * 100:+.2f}%")
        print(f"   📍 End vs low: {((current / low) - 1) * 100:+.2f}%")
        
        # Trend analysis
        if market_return > 10:
            trend = "🚀 Strong Bull Market"
        elif market_return > 0:
            trend = "📈 Bull Market"
        elif market_return > -10:
            trend = "📊 Sideways/Ranging"
        elif market_return > -30:
            trend = "📉 Bear Market"
        else:
            trend = "💥 Crash/Strong Bear"
            
        print(f"   🎯 Market regime: {trend}")
    
    print("\n" + "="*80)
    print("💡 ANALYSIS SUMMARY")
    print("="*80)
    
    btc_return = ((btc_df.iloc[-1]['close'] / btc_df.iloc[0]['close']) - 1) * 100
    
    if eth_df is not None:
        eth_return = ((eth_df.iloc[-1]['close'] / eth_df.iloc[0]['close']) - 1) * 100
        
        if btc_return < 0 and eth_return < 0:
            print("❌ BEAR MARKET PERIOD: Both BTC and ETH declined during the test period")
            print("   This explains why most strategies showed negative returns")
            print("   The strategies may be designed for different market conditions")
        elif btc_return < -20 or eth_return < -20:
            print("⚠️  CHALLENGING MARKET: Significant declines during test period")
            print("   Strategy performance should be evaluated in different market regimes")
        else:
            print("✅ MIXED MARKET: Some positive, some negative performance")
        
        print(f"\n📊 Buy & Hold Performance (for comparison):")
        print(f"   BTC: {btc_return:+.2f}%")
        print(f"   ETH: {eth_return:+.2f}%")
    else:
        if btc_return < -20:
            print("⚠️  CHALLENGING MARKET: Significant BTC decline during test period")
            print("   Strategy performance should be evaluated in different market regimes")
        else:
            print("✅ BTC MARKET: Performance varies")
        
        print(f"\n📊 Buy & Hold Performance (for comparison):")
        print(f"   BTC: {btc_return:+.2f}%")
    
    print(f"\n🤔 Strategy Implications:")
    if eth_df is not None:
        if btc_return < 0 and eth_return < 0:
            print("   • Strategies need to be tested in bull markets too")
            print("   • Consider adding short-selling capabilities")
            print("   • May need bear market specific strategies")
            print("   • Current strategies might work better in trending up markets")
    else:
        if btc_return < 0:
            print("   • BTC declined during test period")
            print("   • Strategies need to be tested in bull markets too")
            print("   • Consider adding short-selling capabilities")
            print("   • May need bear market specific strategies")
    
    print("="*80)

if __name__ == "__main__":
    analyze_market_period()