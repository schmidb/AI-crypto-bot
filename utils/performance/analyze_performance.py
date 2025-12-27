#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
import os

def analyze_bot_performance():
    print("🤖 AI CRYPTO BOT - 14-DAY PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    # Load portfolio data
    try:
        with open('data/portfolio.json', 'r') as f:
            portfolio = json.load(f)
    except FileNotFoundError:
        print("❌ Portfolio data not found")
        return
    
    # Portfolio Performance
    print("\n📊 PORTFOLIO PERFORMANCE")
    print("-" * 30)
    
    initial_value = portfolio.get('initial_value_eur', {}).get('amount', 0)
    current_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
    performance = ((current_value - initial_value) / initial_value * 100) if initial_value > 0 else 0
    
    print(f"Initial Value: €{initial_value:.2f}")
    print(f"Current Value: €{current_value:.2f}")
    print(f"Performance: {performance:+.2f}%")
    print(f"Absolute P&L: €{current_value - initial_value:+.2f}")
    
    # Current Allocation
    print("\n💼 CURRENT ALLOCATION")
    print("-" * 30)
    
    total_value = current_value
    for asset in ['BTC', 'ETH', 'SOL']:
        if asset in portfolio:
            amount = portfolio[asset]['amount']
            price_eur = portfolio[asset]['last_price_eur']
            value = amount * price_eur
            allocation = (value / total_value * 100) if total_value > 0 else 0
            print(f"{asset}: €{value:.2f} ({allocation:.1f}%)")
    
    eur_balance = portfolio.get('EUR', {}).get('amount', 0)
    eur_allocation = (eur_balance / total_value * 100) if total_value > 0 else 0
    print(f"EUR: €{eur_balance:.2f} ({eur_allocation:.1f}%)")
    
    # Trading Activity Analysis
    print("\n📈 TRADING ACTIVITY (Last 14 Days)")
    print("-" * 30)
    
    try:
        with open('data/trades/trade_history.json', 'r') as f:
            trades = json.load(f)
        
        cutoff_date = datetime.now() - timedelta(days=14)
        recent_trades = []
        attempted_trades = 0
        hold_decisions = 0
        
        for trade in trades:
            if 'timestamp' in trade:
                try:
                    trade_date = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))
                    if trade_date >= cutoff_date:
                        action = trade.get('action', '')
                        status = trade.get('status', '')
                        
                        if action in ['BUY', 'SELL']:
                            if status == 'completed' and trade.get('crypto_amount', 0) > 0:
                                recent_trades.append(trade)
                            elif status == 'attempted':
                                attempted_trades += 1
                        elif action == 'HOLD':
                            hold_decisions += 1
                except:
                    continue
        
        print(f"Successful Trades: {len(recent_trades)}")
        print(f"Attempted Trades: {attempted_trades}")
        print(f"HOLD Decisions: {hold_decisions}")
        print(f"Total Decisions: {len(recent_trades) + attempted_trades + hold_decisions}")
        
        if attempted_trades > 0:
            print(f"\n⚠️  ISSUE DETECTED: {attempted_trades} attempted trades failed to execute")
            
    except FileNotFoundError:
        print("❌ Trade history not found")
    
    # AI Decision Analysis
    print("\n🧠 AI DECISION ANALYSIS")
    print("-" * 30)
    
    try:
        with open('data/cache/latest_decisions.json', 'r') as f:
            decisions = json.load(f)
        
        if decisions:
            latest = decisions[0]
            print(f"Latest Decision: {latest['action']} {latest['asset']}")
            print(f"Confidence: {latest['confidence']:.1f}%")
            print(f"Market Regime: {latest.get('market_regime', 'unknown')}")
            print(f"Reasoning: {latest['reasoning'][:100]}...")
            
            # Check confidence thresholds
            confidence = latest['confidence']
            if latest['action'] == 'BUY' and confidence < 65:
                print(f"❌ BUY confidence ({confidence:.1f}%) below threshold (65%)")
            elif latest['action'] == 'SELL' and confidence < 65:
                print(f"❌ SELL confidence ({confidence:.1f}%) below threshold (65%)")
                
    except FileNotFoundError:
        print("❌ Latest decisions not found")
    
    # Recommendations
    print("\n💡 OPTIMIZATION RECOMMENDATIONS")
    print("-" * 30)
    
    if attempted_trades > len(recent_trades) * 10:  # More than 10x attempts vs successes
        print("1. 🔧 CRITICAL: Fix trade execution issues")
        print("   - Check Coinbase API credentials")
        print("   - Verify minimum trade amounts")
        print("   - Check EUR balance sufficiency")
    
    if performance < 5 and len(recent_trades) == 0:
        print("2. 📉 LOW ACTIVITY: Consider lowering confidence thresholds")
        print("   - Current: BUY=65%, SELL=65%")
        print("   - Suggested: BUY=60%, SELL=60%")
    
    if eur_allocation > 15:
        print("3. 💰 HIGH CASH: Too much EUR sitting idle")
        print(f"   - Current EUR allocation: {eur_allocation:.1f}%")
        print("   - Consider more aggressive buying when opportunities arise")
    
    print("\n4. 🎯 IMMEDIATE ACTIONS:")
    print("   - Fix trade execution mechanism")
    print("   - Lower confidence thresholds temporarily")
    print("   - Check minimum trade amounts vs available EUR")

if __name__ == "__main__":
    analyze_bot_performance()
