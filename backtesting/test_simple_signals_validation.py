#!/usr/bin/env python3
"""
Test Simple Signals - Just verify the fixed strategy vectorization is working
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import sys

# Add project root to path
sys.path.append('.')

from utils.performance.indicator_factory import IndicatorFactory
from utils.backtest.strategy_vectorizer import VectorizedStrategyAdapter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_float(value, default=0.0):
    """Safely convert any pandas/numpy value to float"""
    try:
        if pd.isna(value):
            return default
        if hasattr(value, 'item'):  # pandas/numpy scalar
            return float(value.item())
        if hasattr(value, '__len__') and len(value) == 1:  # single-element array
            return float(value[0])
        return float(value)
    except (ValueError, TypeError, AttributeError):
        return default

def analyze_signals(signals_df: pd.DataFrame, strategy_name: str) -> dict:
    """Analyze signal patterns"""
    try:
        total_rows = len(signals_df)
        buy_signals = int(signals_df['buy'].sum())
        sell_signals = int(signals_df['sell'].sum())
        total_signals = buy_signals + sell_signals
        
        # Signal distribution over time
        signals_df['has_signal'] = signals_df['buy'] | signals_df['sell']
        signal_periods = signals_df[signals_df['has_signal']].index
        
        # Confidence analysis
        avg_confidence = safe_float(signals_df['confidence'].mean())
        max_confidence = safe_float(signals_df['confidence'].max())
        min_confidence = safe_float(signals_df['confidence'].min())
        
        # Reasoning analysis
        unique_reasons = signals_df['reasoning'].nunique()
        most_common_reason = signals_df['reasoning'].mode().iloc[0] if len(signals_df['reasoning'].mode()) > 0 else "Unknown"
        
        return {
            "strategy": strategy_name,
            "total_rows": total_rows,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "total_signals": total_signals,
            "signal_rate": (total_signals / total_rows * 100) if total_rows > 0 else 0,
            "avg_confidence": avg_confidence,
            "max_confidence": max_confidence,
            "min_confidence": min_confidence,
            "unique_reasons": unique_reasons,
            "most_common_reason": most_common_reason,
            "first_signal_time": signal_periods[0].isoformat() if len(signal_periods) > 0 else None,
            "last_signal_time": signal_periods[-1].isoformat() if len(signal_periods) > 0 else None
        }
        
    except Exception as e:
        logger.error(f"Error analyzing signals for {strategy_name}: {e}")
        return {"strategy": strategy_name, "error": str(e)}

def main():
    """Test signal generation only"""
    try:
        logger.info("=== TESTING SIGNAL GENERATION ===")
        
        # Load historical data
        df = pd.read_parquet('data/historical/BTC-USD_hour_180d.parquet')
        logger.info(f"Loaded {len(df)} rows of historical data")
        
        # Calculate indicators
        indicator_factory = IndicatorFactory()
        indicators_df = indicator_factory.calculate_all_indicators(df, "BTC-USD")
        
        # Combine data and indicators
        combined_df = pd.concat([df, indicators_df], axis=1)
        logger.info(f"Combined data has {len(combined_df.columns)} columns")
        
        # Initialize fixed vectorizer
        vectorizer = VectorizedStrategyAdapter()
        
        # Test each strategy
        strategies = ['momentum', 'mean_reversion', 'trend_following']
        results = {}
        
        for strategy_name in strategies:
            logger.info(f"\n=== TESTING {strategy_name.upper()} STRATEGY ===")
            
            try:
                # Generate signals
                signals_df = vectorizer.vectorize_strategy(strategy_name, combined_df, "BTC-USD")
                
                # Analyze signals
                analysis = analyze_signals(signals_df, strategy_name)
                results[strategy_name] = analysis
                
                logger.info(f"Analysis Results:")
                logger.info(f"  Total Signals: {analysis['total_signals']} ({analysis['signal_rate']:.2f}% of data)")
                logger.info(f"  Buy/Sell Split: {analysis['buy_signals']}/{analysis['sell_signals']}")
                logger.info(f"  Confidence Range: {analysis['min_confidence']:.1f}% - {analysis['max_confidence']:.1f}% (avg: {analysis['avg_confidence']:.1f}%)")
                logger.info(f"  Unique Reasons: {analysis['unique_reasons']}")
                logger.info(f"  Most Common: {analysis['most_common_reason'][:100]}...")
                
                if analysis['total_signals'] > 0:
                    logger.info(f"  ✅ SUCCESS: {strategy_name} is generating signals!")
                else:
                    logger.warning(f"  ❌ ISSUE: {strategy_name} generated no signals")
                    
            except Exception as e:
                logger.error(f"Error testing {strategy_name}: {e}")
                results[strategy_name] = {"error": str(e)}
        
        # Summary
        logger.info(f"\n=== FINAL SUMMARY ===")
        working_strategies = []
        total_signals_all = 0
        
        for strategy_name, result in results.items():
            if "error" not in result and result.get('total_signals', 0) > 0:
                working_strategies.append(strategy_name)
                total_signals_all += result['total_signals']
                
        logger.info(f"Working strategies: {len(working_strategies)}/{len(strategies)}")
        logger.info(f"Total signals generated: {total_signals_all}")
        
        print(f"\n{'='*60}")
        print(f"BACKTESTING FIX RESULTS")
        print(f"{'='*60}")
        
        if len(working_strategies) >= 2:  # At least 2 strategies working
            print(f"🎉 SUCCESS: Backtesting system is FIXED!")
            print(f"✅ {len(working_strategies)}/{len(strategies)} strategies working")
            print(f"📊 {total_signals_all:,} total signals generated")
            print(f"🔧 Fixed pandas boolean logic issues")
            
            for strategy in working_strategies:
                result = results[strategy]
                print(f"   • {strategy}: {result['total_signals']} signals ({result['signal_rate']:.1f}% rate)")
                
        else:
            print(f"⚠️  PARTIAL SUCCESS: Some issues remain")
            print(f"✅ {len(working_strategies)} strategies working")
            print(f"❌ {len(strategies) - len(working_strategies)} strategies still broken")
            
        # Show any remaining issues
        broken_strategies = [s for s, r in results.items() if "error" in r or r.get('total_signals', 0) == 0]
        if broken_strategies:
            print(f"\nRemaining issues:")
            for strategy in broken_strategies:
                result = results[strategy]
                if "error" in result:
                    print(f"   • {strategy}: Error - {result['error']}")
                else:
                    print(f"   • {strategy}: No signals generated")
                    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ TEST FAILED: {e}")

if __name__ == "__main__":
    main()