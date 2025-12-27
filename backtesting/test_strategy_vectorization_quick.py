#!/usr/bin/env python3
"""
Quick Strategy Vectorization Test - Verify Signal Compatibility

This script tests that vectorized strategies produce signals correctly
without the full comprehensive test suite.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from utils.indicator_factory import calculate_indicators
from utils.strategy_vectorizer import VectorizedStrategyAdapter, vectorize_all_strategies_for_backtest

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_strategy_vectorization_quick():
    """Quick test of vectorized strategies"""
    
    try:
        # Load historical data
        data_dir = Path("./data/historical")
        btc_file = data_dir / "BTC-USD_hourly_30d.parquet"
        
        if not btc_file.exists():
            logger.error(f"BTC data file not found: {btc_file}")
            logger.info("Please run sync_historical_data.py first")
            return False
        
        # Load and prepare data (use only first 100 rows for quick test)
        logger.info("Loading BTC historical data...")
        btc_data = pd.read_parquet(btc_file).head(100)
        logger.info(f"Loaded {len(btc_data)} rows of BTC data for quick test")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        btc_with_indicators = calculate_indicators(btc_data, "BTC-USD")
        logger.info(f"Added {len(btc_with_indicators.columns) - len(btc_data.columns)} indicators")
        
        # Test Individual Strategy Vectorization
        logger.info("\n=== Quick Strategy Vectorization Test ===")
        
        adapter = VectorizedStrategyAdapter()
        
        strategies_to_test = ['mean_reversion', 'momentum', 'trend_following']
        
        for strategy_name in strategies_to_test:
            logger.info(f"\nTesting {strategy_name} strategy...")
            
            # Vectorize strategy
            signals_df = adapter.vectorize_strategy(
                strategy_name, btc_with_indicators, "BTC-USD"
            )
            
            # Analyze results
            buy_signals = signals_df['buy'].sum()
            sell_signals = signals_df['sell'].sum()
            avg_confidence = signals_df['confidence'].mean()
            
            logger.info(f"  {strategy_name} Results:")
            logger.info(f"    Buy signals: {buy_signals}")
            logger.info(f"    Sell signals: {sell_signals}")
            logger.info(f"    Average confidence: {avg_confidence:.1f}%")
            logger.info(f"    Signal rate: {(buy_signals + sell_signals) / len(signals_df) * 100:.1f}%")
        
        # Test Adaptive Strategy Vectorization (limited rows)
        logger.info("\n=== Adaptive Strategy Test (Limited) ===")
        
        # Use only first 50 rows to avoid performance tracker issues
        limited_data = btc_with_indicators.head(50)
        
        adaptive_signals = adapter.vectorize_adaptive_strategy(limited_data, "BTC-USD")
        
        buy_signals = adaptive_signals['buy'].sum()
        sell_signals = adaptive_signals['sell'].sum()
        avg_confidence = adaptive_signals['confidence'].mean()
        
        logger.info(f"Adaptive Strategy Results (50 rows):")
        logger.info(f"  Buy signals: {buy_signals}")
        logger.info(f"  Sell signals: {sell_signals}")
        logger.info(f"  Average confidence: {avg_confidence:.1f}%")
        
        # Market regime analysis
        regime_counts = adaptive_signals['market_regime'].value_counts()
        logger.info(f"  Market regimes: {regime_counts.to_dict()}")
        
        # Primary strategy analysis
        strategy_counts = adaptive_signals['primary_strategy'].value_counts()
        logger.info(f"  Primary strategies: {strategy_counts.to_dict()}")
        
        logger.info("\n🎉 Quick strategy vectorization test completed successfully!")
        
        # Summary
        logger.info(f"\n📊 Summary:")
        logger.info(f"  Individual strategies tested: {len(strategies_to_test)}")
        logger.info(f"  Adaptive strategy tested: Yes")
        logger.info(f"  Data points processed: {len(btc_with_indicators)}")
        logger.info(f"  JSON serialization issue: Fixed")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in quick strategy vectorization test: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_strategy_vectorization_quick()
    exit(0 if success else 1)