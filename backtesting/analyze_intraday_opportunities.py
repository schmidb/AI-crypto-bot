#!/usr/bin/env python3
"""
Analyze intraday trading opportunities vs our strategy performance
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_intraday_opportunities():
    """Analyze intraday volatility and trading opportunities"""
    
    # Load data
    btc_df = pd.read_parquet('data/historical/BTC-USD_hour_180d.parquet')
    eth_df = pd.read_parquet('data/historical/ETH-USD_hour_180d.parquet')
    
    print("="*80)
    print("📈 INTRADAY TRADING OPPORTUNITY ANALYSIS")
    print("="*80)
    
    for name, df in [("BTC-USD", btc_df), ("ETH-USD", eth_df)]:
        print(f"\n🪙 {name} Intraday Analysis:")
        
        # Calculate daily statistics
        df['date'] = df.index.date
        daily_stats = df.groupby('date').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Daily range analysis
        daily_stats['daily_range'] = ((daily_stats['high'] - daily_stats['low']) / daily_stats['open']) * 100
        daily_stats['daily_return'] = ((daily_stats['close'] - daily_stats['open']) / daily_stats['open']) * 100
        
        avg_daily_range = daily_stats['daily_range'].mean()
        avg_daily_return = daily_stats['daily_return'].mean()
        
        print(f"   📊 Average daily range: {avg_daily_range:.2f}%")
        print(f"   📊 Average daily return: {avg_daily_return:.2f}%")
        print(f"   📊 Range vs Return ratio: {avg_daily_range / abs(avg_daily_return) if avg_daily_return != 0 else 'N/A':.1f}x")
        
        # Intraday volatility analysis
        hourly_returns = df['close'].pct_change().dropna() * 100
        hourly_volatility = hourly_returns.std()
        
        print(f"   ⚡ Hourly volatility: {hourly_volatility:.3f}%")
        print(f"   ⚡ Daily equivalent: {hourly_volatility * np.sqrt(24):.2f}%")
        
        # Count profitable days vs range days
        profitable_days = (daily_stats['daily_return'] > 0).sum()
        high_range_days = (daily_stats['daily_range'] > avg_daily_range).sum()
        total_days = len(daily_stats)
        
        print(f"   📈 Profitable days: {profitable_days}/{total_days} ({profitable_days/total_days*100:.1f}%)")
        print(f"   📊 High volatility days: {high_range_days}/{total_days} ({high_range_days/total_days*100:.1f}%)")
        
        # Perfect day trader simulation (capture 50% of daily range)
        perfect_daily_capture = daily_stats['daily_range'] * 0.5  # Capture 50% of daily range
        perfect_cumulative = perfect_daily_capture.sum()
        
        print(f"   🎯 Perfect day trader (50% range capture): +{perfect_cumulative:.1f}%")
        
        # Realistic day trader simulation (capture 20% of daily range)
        realistic_daily_capture = daily_stats['daily_range'] * 0.2  # Capture 20% of daily range
        realistic_cumulative = realistic_daily_capture.sum()
        
        print(f"   🎯 Realistic day trader (20% range capture): +{realistic_cumulative:.1f}%")
        
        # Analyze hourly movements
        hourly_moves = df['close'].pct_change().dropna() * 100
        positive_moves = (hourly_moves > 0).sum()
        negative_moves = (hourly_moves < 0).sum()
        
        print(f"   ⏰ Hourly movements: {positive_moves} up, {negative_moves} down")
        print(f"   ⏰ Up/Down ratio: {positive_moves/negative_moves:.2f}")
        
        # Calculate what a simple mean reversion strategy could capture
        # Buy when price drops > 1%, sell when it rises > 1%
        big_moves = hourly_moves[abs(hourly_moves) > 1.0]
        mean_reversion_opportunities = len(big_moves)
        
        print(f"   🔄 Mean reversion opportunities (>1% moves): {mean_reversion_opportunities}")
        print(f"   🔄 Opportunities per day: {mean_reversion_opportunities / total_days:.1f}")

def analyze_strategy_holding_periods():
    """Analyze how long our strategies hold positions"""
    
    print("\n" + "="*80)
    print("⏱️  STRATEGY HOLDING PERIOD ANALYSIS")
    print("="*80)
    
    # This would require running a quick backtest to see signal patterns
    # For now, let's analyze what the issue might be conceptually
    
    print("\n🤔 POTENTIAL ISSUES WITH CURRENT STRATEGIES:")
    print("   1. 📊 Strategies may be holding positions too long")
    print("   2. 🎯 Not capturing intraday reversals effectively")
    print("   3. 💰 Missing quick profit-taking opportunities")
    print("   4. 🛡️  No stop-losses for quick exits")
    print("   5. 📈 Designed for trending markets, not ranging/volatile markets")
    
    print("\n💡 DAY TRADING IMPROVEMENTS NEEDED:")
    print("   • ⚡ Faster entry/exit signals (minutes, not hours)")
    print("   • 🎯 Profit-taking at 1-3% gains")
    print("   • 🛡️  Stop-losses at 1-2% losses")
    print("   • 🔄 Mean reversion on hourly timeframes")
    print("   • 📊 Scalping strategies for high-volatility periods")
    print("   • 🕐 Time-based exits (close positions before major news/weekends)")

def main():
    analyze_intraday_opportunities()
    analyze_strategy_holding_periods()
    
    print("\n" + "="*80)
    print("🎯 CONCLUSION: DAY TRADING OPPORTUNITY EXISTS!")
    print("="*80)
    print("The market shows significant intraday volatility that could be captured")
    print("with proper day trading strategies. Current strategies may be too slow.")
    print("\nNext steps:")
    print("1. 🔍 Analyze actual strategy holding periods")
    print("2. 🛠️  Develop faster entry/exit strategies")
    print("3. 📊 Add intraday scalping strategies")
    print("4. 🎯 Implement profit-taking and stop-losses")
    print("="*80)

if __name__ == "__main__":
    main()