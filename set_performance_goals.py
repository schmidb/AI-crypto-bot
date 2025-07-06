#!/usr/bin/env python3
"""
Set Performance Goals for AI Crypto Trading Bot

This script sets up default performance goals for the trading bot.
You can modify the goals below or run this script with custom parameters.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.performance_manager import PerformanceManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_default_goals():
    """Set up default performance goals for the crypto trading bot"""
    
    try:
        # Initialize performance manager
        pm = PerformanceManager()
        
        # Define default goals for crypto trading
        default_goals = [
            {
                "goal_type": "total_return",
                "target_value": 20.0,  # 20% annual return
                "timeframe": "yearly",
                "description": "Target 20% annual return (reasonable for crypto trading)"
            },
            {
                "goal_type": "monthly_return",
                "target_value": 5.0,   # 5% monthly return
                "timeframe": "monthly", 
                "description": "Target 5% monthly return (aggressive but achievable)"
            },
            {
                "goal_type": "max_drawdown",
                "target_value": -15.0,  # Keep drawdown under 15%
                "timeframe": "monthly",
                "description": "Keep maximum drawdown under 15% (risk management)"
            },
            {
                "goal_type": "win_rate",
                "target_value": 60.0,   # 60% win rate
                "timeframe": "monthly",
                "description": "Maintain 60% win rate on trades (quality over quantity)"
            },
            {
                "goal_type": "sharpe_ratio",
                "target_value": 1.5,    # Sharpe ratio > 1.5
                "timeframe": "yearly",
                "description": "Achieve Sharpe ratio > 1.5 (risk-adjusted returns)"
            }
        ]
        
        print("🎯 Setting up performance goals for AI Crypto Trading Bot...")
        print("=" * 60)
        
        # Set each goal
        for goal in default_goals:
            result = pm.set_performance_goal(
                goal_type=goal["goal_type"],
                target_value=goal["target_value"],
                timeframe=goal["timeframe"],
                description=goal["description"]
            )
            
            if result["status"] == "success":
                print(f"✅ {goal['description']}")
                print(f"   Goal: {goal['goal_type']} = {goal['target_value']}% ({goal['timeframe']})")
            else:
                print(f"❌ Failed to set goal: {goal['goal_type']}")
                print(f"   Error: {result['message']}")
            print()
        
        print("🎉 Performance goals setup complete!")
        print("\n📊 You can now view these goals in the dashboard Performance Goals section.")
        print("💡 Goals will be automatically tracked and displayed with progress indicators.")
        
    except Exception as e:
        logger.error(f"Error setting up performance goals: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    set_default_goals()
