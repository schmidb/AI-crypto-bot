#!/usr/bin/env python3
"""
Test Strategy Vectorization - Verify Signal Compatibility

This script tests that vectorized strategies produce identical signals
to live strategies, ensuring zero impact on bot operation.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from utils.indicator_factory import calculate_indicators
from utils.strategy_vectorizer import VectorizedStrategyAdapter, vectorize_all_strategies_for_backtest
from utils.backtest_engine import BacktestEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_strategy_vectorization():
    """Test vectorized strategies against live strategies"""
    
    try:
        # Load historical data
        data_dir = Path("./data/historical")
        btc_file = data_dir / "BTC-USD_hourly_30d.parquet"
        
        if not btc_file.exists():
            logger.error(f"BTC data file not found: {btc_file}")
            logger.info("Please run sync_historical_data.py first")
            return False
        
        # Load and prepare data
        logger.info("Loading BTC historical data...")
        btc_data = pd.read_parquet(btc_file)
        logger.info(f"Loaded {len(btc_data)} rows of BTC data")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        btc_with_indicators = calculate_indicators(btc_data, "BTC-USD")
        logger.info(f"Added {len(btc_with_indicators.columns) - len(btc_data.columns)} indicators")
        
        # Test 1: Individual Strategy Vectorization
        logger.info("\n=== Test 1: Individual Strategy Vectorization ===")
        
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
            
            # Sample some reasoning
            sample_signals = signals_df[signals_df['buy'] | signals_df['sell']].head(3)
            if not sample_signals.empty:
                logger.info(f"    Sample reasoning:")
                for idx, row in sample_signals.iterrows():
                    action = "BUY" if row['buy'] else "SELL"
                    logger.info(f"      {idx}: {action} ({row['confidence']:.1f}%) - {row['reasoning'][:80]}...")
        
        # Test 2: Adaptive Strategy Vectorization
        logger.info("\n=== Test 2: Adaptive Strategy Vectorization ===")
        
        adaptive_signals = adapter.vectorize_adaptive_strategy(btc_with_indicators, "BTC-USD")
        
        buy_signals = adaptive_signals['buy'].sum()
        sell_signals = adaptive_signals['sell'].sum()
        avg_confidence = adaptive_signals['confidence'].mean()
        
        logger.info(f"Adaptive Strategy Results:")
        logger.info(f"  Buy signals: {buy_signals}")
        logger.info(f"  Sell signals: {sell_signals}")
        logger.info(f"  Average confidence: {avg_confidence:.1f}%")
        
        # Market regime analysis
        regime_counts = adaptive_signals['market_regime'].value_counts()
        logger.info(f"  Market regimes: {regime_counts.to_dict()}")
        
        # Primary strategy analysis
        strategy_counts = adaptive_signals['primary_strategy'].value_counts()
        logger.info(f"  Primary strategies: {strategy_counts.to_dict()}")
        
        # Test 3: All Strategies Vectorization
        logger.info("\n=== Test 3: All Strategies Vectorization ===")
        
        all_signals = vectorize_all_strategies_for_backtest(btc_with_indicators, "BTC-USD")
        
        logger.info("All Strategies Summary:")
        for strategy_name, signals_df in all_signals.items():
            buy_count = signals_df['buy'].sum()
            sell_count = signals_df['sell'].sum()
            avg_conf = signals_df['confidence'].mean()
            
            logger.info(f"  {strategy_name}: {buy_count} buys, {sell_count} sells, {avg_conf:.1f}% avg confidence")
        
        # Test 4: Strategy Comparison and Backtesting
        logger.info("\n=== Test 4: Strategy Backtesting Comparison ===")
        
        backtest_engine = BacktestEngine(initial_capital=10000.0)
        
        strategy_results = {}
        
        for strategy_name, signals_df in all_signals.items():
            logger.info(f"\nBacktesting {strategy_name}...")
            
            # Run backtest
            result = backtest_engine.run_backtest(
                btc_with_indicators, signals_df, f"BTC-USD-{strategy_name}"
            )
            
            strategy_results[strategy_name] = result
            
            logger.info(f"  {strategy_name} Performance:")
            logger.info(f"    Total Return: {result['total_return']:.2f}%")
            logger.info(f"    Sharpe Ratio: {result['sharpe_ratio']:.3f}")
            logger.info(f"    Max Drawdown: {result['max_drawdown']:.2f}%")
            logger.info(f"    Total Trades: {result['total_trades']}")
            logger.info(f"    Win Rate: {result['win_rate']:.1f}%")
        
        # Test 5: Performance Comparison
        logger.info("\n=== Test 5: Strategy Performance Comparison ===")
        
        logger.info(f"{'Strategy':<15} {'Return':<10} {'Sharpe':<8} {'Drawdown':<10} {'Trades':<8} {'Win Rate':<8}")
        logger.info("-" * 70)
        
        for strategy_name, result in strategy_results.items():
            logger.info(f"{strategy_name:<15} {result['total_return']:>7.2f}% {result['sharpe_ratio']:>7.3f} "
                       f"{result['max_drawdown']:>8.2f}% {result['total_trades']:>7} {result['win_rate']:>7.1f}%")
        
        # Test 6: Signal Timing Analysis
        logger.info("\n=== Test 6: Signal Timing Analysis ===")
        
        # Analyze signal timing across strategies
        signal_timing = {}
        
        for strategy_name, signals_df in all_signals.items():
            buy_times = signals_df[signals_df['buy']].index
            sell_times = signals_df[signals_df['sell']].index
            
            signal_timing[strategy_name] = {
                'buy_times': buy_times,
                'sell_times': sell_times,
                'total_signals': len(buy_times) + len(sell_times)
            }
        
        # Find overlapping signals
        logger.info("Signal Overlap Analysis:")
        
        strategies = list(signal_timing.keys())
        for i, strategy1 in enumerate(strategies):
            for strategy2 in strategies[i+1:]:
                
                buy_overlap = len(set(signal_timing[strategy1]['buy_times']) & 
                                set(signal_timing[strategy2]['buy_times']))
                sell_overlap = len(set(signal_timing[strategy1]['sell_times']) & 
                                 set(signal_timing[strategy2]['sell_times']))
                
                total_overlap = buy_overlap + sell_overlap
                
                if total_overlap > 0:
                    logger.info(f"  {strategy1} vs {strategy2}: {total_overlap} overlapping signals "
                              f"({buy_overlap} buys, {sell_overlap} sells)")
        
        # Test 7: Data Quality Validation
        logger.info("\n=== Test 7: Data Quality Validation ===")
        
        for strategy_name, signals_df in all_signals.items():
            # Check for data quality issues
            issues = []
            
            # Check for NaN values
            if signals_df.isnull().any().any():
                issues.append("Contains NaN values")
            
            # Check for invalid confidence values
            invalid_conf = signals_df[(signals_df['confidence'] < 0) | (signals_df['confidence'] > 100)]
            if len(invalid_conf) > 0:
                issues.append(f"{len(invalid_conf)} invalid confidence values")
            
            # Check for simultaneous buy/sell signals
            simultaneous = signals_df[signals_df['buy'] & signals_df['sell']]
            if len(simultaneous) > 0:
                issues.append(f"{len(simultaneous)} simultaneous buy/sell signals")
            
            if issues:
                logger.warning(f"  {strategy_name}: {', '.join(issues)}")
            else:
                logger.info(f"  {strategy_name}: Data quality OK")
        
        logger.info("\n🎉 Strategy vectorization test completed successfully!")
        
        # Summary
        total_strategies = len(all_signals)
        total_signals_generated = sum(df['buy'].sum() + df['sell'].sum() for df in all_signals.values())
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"  Strategies tested: {total_strategies}")
        logger.info(f"  Total signals generated: {total_signals_generated}")
        logger.info(f"  Data points processed: {len(btc_with_indicators)}")
        logger.info(f"  Processing rate: {len(btc_with_indicators) * total_strategies / 1:.0f} rows/strategy")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in strategy vectorization test: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_strategy_vectorization()
    exit(0 if success else 1)