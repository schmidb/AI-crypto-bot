#!/usr/bin/env python3
"""
Test Complete Backtest - Run the full backtesting pipeline with fixed vectorization
"""

import pandas as pd
import numpy as np
import logging
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append('.')

from utils.performance.indicator_factory import IndicatorFactory
from utils.backtest.strategy_vectorizer import VectorizedStrategyAdapter
from utils.backtest.backtest_engine import BacktestEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_complete_backtest():
    """Run complete backtesting pipeline with all strategies"""
    
    logger.info("=== COMPLETE BACKTEST PIPELINE TEST ===")
    
    try:
        # Load historical data
        df = pd.read_parquet('data/historical/BTC-USD_hour_180d.parquet')
        logger.info(f"Loaded {len(df)} rows of historical data")
        
        # Calculate indicators
        indicator_factory = IndicatorFactory()
        indicators_df = indicator_factory.calculate_all_indicators(df, "BTC-USD")
        
        # Combine data and indicators (avoiding duplicates)
        combined_df = pd.concat([df, indicators_df], axis=1)
        # Remove duplicate columns
        combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
        logger.info(f"Combined data: {len(combined_df)} rows, {len(combined_df.columns)} columns")
        
        # Initialize vectorizer and backtest engine
        vectorizer = VectorizedStrategyAdapter()
        backtest_engine = BacktestEngine(initial_capital=10000.0, fees=0.006)
        
        # Test each strategy
        strategies = ['momentum', 'mean_reversion', 'trend_following']
        results = {}
        
        for strategy_name in strategies:
            logger.info(f"\n=== BACKTESTING {strategy_name.upper()} STRATEGY ===")
            
            try:
                # Generate signals
                signals_df = vectorizer.vectorize_strategy(strategy_name, combined_df, "BTC-USD")
                
                # Check signal quality
                buy_count = int(signals_df['buy'].sum())
                sell_count = int(signals_df['sell'].sum())
                logger.info(f"Generated {buy_count} buy signals and {sell_count} sell signals")
                
                if buy_count == 0 and sell_count == 0:
                    logger.warning(f"No signals generated for {strategy_name}, skipping backtest")
                    results[strategy_name] = {
                        'error': 'No signals generated',
                        'total_return': 0,
                        'total_trades': 0
                    }
                    continue
                
                # Run backtest
                backtest_result = backtest_engine.run_backtest(
                    data=combined_df[['open', 'high', 'low', 'close', 'volume']],  # Only OHLCV for backtest
                    signals=signals_df,
                    product_id=f"BTC-USD_{strategy_name}"
                )
                
                results[strategy_name] = backtest_result
                
                # Log key metrics
                logger.info(f"Backtest Results for {strategy_name}:")
                logger.info(f"  Total Return: {backtest_result.get('total_return', 0):.2f}%")
                logger.info(f"  Annual Return: {backtest_result.get('annual_return', 0):.2f}%")
                logger.info(f"  Sharpe Ratio: {backtest_result.get('sharpe_ratio', 0):.3f}")
                logger.info(f"  Max Drawdown: {backtest_result.get('max_drawdown', 0):.2f}%")
                logger.info(f"  Total Trades: {backtest_result.get('total_trades', 0)}")
                logger.info(f"  Win Rate: {backtest_result.get('win_rate', 0):.1f}%")
                
                if 'error' in backtest_result:
                    logger.warning(f"  Error: {backtest_result['error']}")
                
            except Exception as e:
                logger.error(f"Error backtesting {strategy_name}: {e}")
                results[strategy_name] = {
                    'error': str(e),
                    'total_return': 0,
                    'total_trades': 0
                }
        
        # Calculate buy-and-hold benchmark
        logger.info(f"\n=== CALCULATING BUY-AND-HOLD BENCHMARK ===")
        
        start_price = combined_df['close'].iloc[0]
        end_price = combined_df['close'].iloc[-1]
        buy_hold_return = ((end_price - start_price) / start_price) * 100
        
        duration_days = (combined_df.index[-1] - combined_df.index[0]).days
        buy_hold_annual = ((end_price / start_price) ** (365 / duration_days) - 1) * 100
        
        benchmark = {
            'strategy': 'buy_and_hold',
            'total_return': buy_hold_return,
            'annual_return': buy_hold_annual,
            'start_price': start_price,
            'end_price': end_price,
            'duration_days': duration_days
        }
        
        logger.info(f"Buy-and-Hold Benchmark:")
        logger.info(f"  Total Return: {buy_hold_return:.2f}%")
        logger.info(f"  Annual Return: {buy_hold_annual:.2f}%")
        logger.info(f"  Period: {duration_days} days")
        
        # Summary comparison
        logger.info(f"\n=== STRATEGY COMPARISON ===")
        
        strategy_summary = []
        for strategy_name, result in results.items():
            if 'error' not in result:
                strategy_summary.append({
                    'strategy': strategy_name,
                    'total_return': result.get('total_return', 0),
                    'annual_return': result.get('annual_return', 0),
                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                    'max_drawdown': result.get('max_drawdown', 0),
                    'total_trades': result.get('total_trades', 0),
                    'win_rate': result.get('win_rate', 0)
                })
        
        # Sort by Sharpe ratio
        strategy_summary.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        print(f"\n{'='*80}")
        print(f"BACKTESTING RESULTS SUMMARY")
        print(f"{'='*80}")
        
        if strategy_summary:
            print(f"{'Strategy':<15} {'Return':<8} {'Annual':<8} {'Sharpe':<8} {'Drawdown':<10} {'Trades':<8} {'Win%':<6}")
            print(f"{'-'*70}")
            
            for summary in strategy_summary:
                print(f"{summary['strategy']:<15} "
                      f"{summary['total_return']:>6.1f}% "
                      f"{summary['annual_return']:>6.1f}% "
                      f"{summary['sharpe_ratio']:>6.2f} "
                      f"{summary['max_drawdown']:>8.1f}% "
                      f"{summary['total_trades']:>6} "
                      f"{summary['win_rate']:>4.1f}%")
            
            print(f"{'-'*70}")
            print(f"{'buy_and_hold':<15} "
                  f"{benchmark['total_return']:>6.1f}% "
                  f"{benchmark['annual_return']:>6.1f}% "
                  f"{'N/A':>6} "
                  f"{'N/A':>8} "
                  f"{'1':>6} "
                  f"{'N/A':>4}")
            
            # Analysis
            best_strategy = strategy_summary[0]
            print(f"\n📊 ANALYSIS:")
            print(f"   Best Strategy: {best_strategy['strategy']} (Sharpe: {best_strategy['sharpe_ratio']:.2f})")
            
            outperforming = [s for s in strategy_summary if s['total_return'] > benchmark['total_return']]
            if outperforming:
                print(f"   Strategies beating buy-and-hold: {len(outperforming)}/{len(strategy_summary)}")
            else:
                print(f"   ⚠️  No strategies beat buy-and-hold ({benchmark['total_return']:.1f}%)")
                
        else:
            print(f"❌ No successful backtests completed")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"backtest_results_{timestamp}.json"
        
        full_results = {
            'timestamp': timestamp,
            'benchmark': benchmark,
            'strategies': results,
            'summary': strategy_summary,
            'data_period': {
                'start': combined_df.index[0].isoformat(),
                'end': combined_df.index[-1].isoformat(),
                'rows': len(combined_df)
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(full_results, f, indent=2, default=str)
        
        logger.info(f"\nResults saved to: {results_file}")
        
        return full_results
        
    except Exception as e:
        logger.error(f"Complete backtest failed: {e}")
        return None

if __name__ == "__main__":
    run_complete_backtest()