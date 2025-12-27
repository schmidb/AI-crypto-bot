#!/usr/bin/env python3
"""
Simple Backtest Test - Basic Integration Test

This script tests the basic backtest integration functionality.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_backtest():
    """Test basic backtest functionality"""
    
    try:
        # Test individual imports first
        logger.info("Testing individual imports...")
        
        from utils.backtest_engine import BacktestEngine
        logger.info("✅ BacktestEngine imported successfully")
        
        from utils.strategy_vectorizer import VectorizedStrategyAdapter
        logger.info("✅ VectorizedStrategyAdapter imported successfully")
        
        from utils.indicator_factory import calculate_indicators
        logger.info("✅ calculate_indicators imported successfully")
        
        # Load historical data
        data_dir = Path("./data/historical")
        btc_file = data_dir / "BTC-USD_hourly_30d.parquet"
        
        if not btc_file.exists():
            logger.error(f"BTC data file not found: {btc_file}")
            return False
        
        # Load and prepare data (small subset)
        logger.info("Loading BTC historical data...")
        btc_data = pd.read_parquet(btc_file).head(50)
        logger.info(f"Loaded {len(btc_data)} rows of BTC data")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        btc_with_indicators = calculate_indicators(btc_data, "BTC-USD")
        logger.info(f"Added {len(btc_with_indicators.columns) - len(btc_data.columns)} indicators")
        
        # Test strategy vectorization
        logger.info("Testing strategy vectorization...")
        vectorizer = VectorizedStrategyAdapter()
        
        # Test mean reversion strategy
        signals_df = vectorizer.vectorize_strategy('mean_reversion', btc_with_indicators, "BTC-USD")
        logger.info(f"Generated signals: {signals_df['buy'].sum()} buys, {signals_df['sell'].sum()} sells")
        
        # Test backtest engine
        logger.info("Testing backtest engine...")
        engine = BacktestEngine(initial_capital=10000.0)
        
        result = engine.run_backtest(btc_with_indicators, signals_df, "BTC-USD-test")
        
        if 'error' in result:
            logger.error(f"Backtest error: {result['error']}")
            return False
        
        logger.info("Backtest Results:")
        logger.info(f"  Total Return: {result['total_return']:.2f}%")
        logger.info(f"  Sharpe Ratio: {result['sharpe_ratio']:.3f}")
        logger.info(f"  Max Drawdown: {result['max_drawdown']:.2f}%")
        logger.info(f"  Total Trades: {result['total_trades']}")
        logger.info(f"  Win Rate: {result['win_rate']:.1f}%")
        
        # Test all strategies
        logger.info("Testing all strategies...")
        strategies = ['mean_reversion', 'momentum', 'trend_following']
        
        for strategy_name in strategies:
            logger.info(f"Testing {strategy_name}...")
            signals = vectorizer.vectorize_strategy(strategy_name, btc_with_indicators, "BTC-USD")
            result = engine.run_backtest(btc_with_indicators, signals, f"BTC-USD-{strategy_name}")
            
            logger.info(f"  {strategy_name}: {result['total_return']:.2f}% return, "
                       f"{result['total_trades']} trades")
        
        # Test adaptive strategy
        logger.info("Testing adaptive strategy...")
        adaptive_signals = vectorizer.vectorize_adaptive_strategy(btc_with_indicators, "BTC-USD")
        adaptive_result = engine.run_backtest(btc_with_indicators, adaptive_signals, "BTC-USD-adaptive")
        
        logger.info(f"Adaptive strategy: {adaptive_result['total_return']:.2f}% return, "
                   f"{adaptive_result['total_trades']} trades")
        
        logger.info("\n🎉 Simple backtest test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in simple backtest test: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_simple_backtest()
    exit(0 if success else 1)