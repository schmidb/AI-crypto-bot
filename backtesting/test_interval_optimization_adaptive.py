#!/usr/bin/env python3
"""
Interval Optimization Test - Test different trading intervals with FIXED backtesting system
"""

import pandas as pd
import numpy as np
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append('.')

from utils.performance.indicator_factory import IndicatorFactory
from utils.backtest.strategy_vectorizer import VectorizedStrategyAdapter
from utils.backtest.backtest_engine import BacktestEngine
from data_collector import DataCollector

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntervalOptimizer:
    """Test different trading intervals to find optimal settings"""
    
    def __init__(self):
        self.intervals = [15, 30, 60, 120]  # minutes
        self.strategies = ['adaptive']  # Test the combined adaptive strategy like the live bot
        self.results_dir = Path("reports/interval_optimization")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_existing_data(self, product_id: str, interval_minutes: int) -> pd.DataFrame:
        """Load existing historical data files"""
        try:
            # Map interval to existing data files
            file_map = {
                15: f"data/historical/{product_id}_15min_30d.parquet",
                30: f"data/historical/{product_id}_30min_30d.parquet", 
                60: f"data/historical/{product_id}_hour_180d.parquet",  # Use existing hourly data
                120: f"data/historical/{product_id}_2hour_30d.parquet"
            }
            
            file_path = file_map.get(interval_minutes)
            
            # For now, use the existing hourly data for all intervals (as a test)
            # In production, you'd want to collect data for each specific interval
            if interval_minutes == 60:
                file_path = f"data/historical/{product_id}_hour_180d.parquet"
            else:
                # For other intervals, we'll simulate by resampling hourly data
                logger.info(f"Using hourly data resampled to {interval_minutes}min for testing")
                file_path = f"data/historical/{product_id}_hour_180d.parquet"
            
            if not Path(file_path).exists():
                logger.error(f"Data file not found: {file_path}")
                return pd.DataFrame()
            
            df = pd.read_parquet(file_path)
            
            # Limit to last 30 days for consistency
            if len(df) > 720:  # More than 30 days of hourly data
                df = df.tail(720)  # Last 30 days
            
            # Resample if needed (for testing different intervals)
            if interval_minutes != 60:
                df = self.resample_data(df, interval_minutes)
            
            logger.info(f"Loaded {len(df)} rows for {product_id} at {interval_minutes}min interval")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data for {product_id} at {interval_minutes}min: {e}")
            return pd.DataFrame()
    
    def resample_data(self, df: pd.DataFrame, target_interval_minutes: int) -> pd.DataFrame:
        """Resample hourly data to different intervals"""
        try:
            if target_interval_minutes == 60:
                return df  # Already hourly
            
            # Resample to target interval
            rule_map = {
                15: '15T',  # 15 minutes
                30: '30T',  # 30 minutes
                120: '2H'   # 2 hours
            }
            
            rule = rule_map.get(target_interval_minutes, '1H')
            
            # Resample OHLCV data
            resampled = df.resample(rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            logger.info(f"Resampled from {len(df)} to {len(resampled)} rows ({target_interval_minutes}min)")
            return resampled
            
        except Exception as e:
            logger.error(f"Error resampling data: {e}")
            return df
    
    def test_interval(self, product_id: str, interval_minutes: int, days: int = 30) -> Dict:
        """Test all strategies on a specific interval"""
        try:
            logger.info(f"\n=== TESTING {interval_minutes}MIN INTERVAL FOR {product_id} ===")
            
            # Load data for this interval
            df = self.load_existing_data(product_id, interval_minutes)
            
            if df.empty:
                return {
                    'interval_minutes': interval_minutes,
                    'product_id': product_id,
                    'error': 'No data available',
                    'strategies': {}
                }
            
            # Calculate indicators
            indicator_factory = IndicatorFactory()
            indicators_df = indicator_factory.calculate_all_indicators(df, product_id)
            
            # Combine data (avoiding duplicates)
            combined_df = pd.concat([df, indicators_df], axis=1)
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
            
            # Initialize components
            vectorizer = VectorizedStrategyAdapter()
            backtest_engine = BacktestEngine(initial_capital=10000.0, fees=0.006)
            
            # Initialize results dictionary
            strategy_results = {}
            
            # Test the adaptive strategy (like the live bot)
            for strategy_name in self.strategies:
                try:
                    logger.info(f"Testing {strategy_name} strategy...")
                    
                    if strategy_name == 'adaptive':
                        # Use the adaptive strategy like the live bot
                        signals_df = vectorizer.vectorize_adaptive_strategy(combined_df, product_id)
                    else:
                        # Individual strategy (fallback)
                        signals_df = vectorizer.vectorize_strategy(strategy_name, combined_df, product_id)
                    
                    # Check if we have signals
                    buy_count = int(signals_df['buy'].sum())
                    sell_count = int(signals_df['sell'].sum())
                    
                    if buy_count == 0 and sell_count == 0:
                        logger.warning(f"No signals for {strategy_name}")
                        strategy_results[strategy_name] = {
                            'error': 'No signals generated',
                            'total_return': 0,
                            'total_trades': 0
                        }
                        continue
                    
                    # Run backtest
                    backtest_result = backtest_engine.run_backtest(
                        data=combined_df[['open', 'high', 'low', 'close', 'volume']],
                        signals=signals_df,
                        product_id=f"{product_id}_{strategy_name}_{interval_minutes}min"
                    )
                    
                    strategy_results[strategy_name] = backtest_result
                    
                    logger.info(f"  {strategy_name}: {backtest_result.get('total_return', 0):.2f}% return, "
                              f"{backtest_result.get('total_trades', 0)} trades")
                    
                except Exception as e:
                    logger.error(f"Error testing {strategy_name}: {e}")
                    strategy_results[strategy_name] = {
                        'error': str(e),
                        'total_return': 0,
                        'total_trades': 0
                    }
            
            # Calculate buy-and-hold benchmark
            start_price = combined_df['close'].iloc[0]
            end_price = combined_df['close'].iloc[-1]
            buy_hold_return = ((end_price - start_price) / start_price) * 100
            
            return {
                'interval_minutes': interval_minutes,
                'product_id': product_id,
                'data_points': len(combined_df),
                'period_days': (combined_df.index[-1] - combined_df.index[0]).days,
                'buy_hold_return': buy_hold_return,
                'strategies': strategy_results
            }
            
        except Exception as e:
            logger.error(f"Error testing interval {interval_minutes}min: {e}")
            return {
                'interval_minutes': interval_minutes,
                'product_id': product_id,
                'error': str(e),
                'strategies': {}
            }
    
    def run_optimization(self, product_id: str = "BTC-USD", days: int = 30) -> Dict:
        """Run interval optimization for a product"""
        logger.info(f"🚀 Starting interval optimization for {product_id}")
        logger.info(f"📊 Testing intervals: {self.intervals} minutes")
        logger.info(f"📈 Testing strategy: {self.strategies[0]} (like live bot)")
        logger.info(f"📅 Period: {days} days")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'product_id': product_id,
            'test_period_days': days,
            'intervals_tested': self.intervals,
            'strategies_tested': self.strategies,
            'results': []
        }
        
        # Test each interval
        for interval_minutes in self.intervals:
            interval_result = self.test_interval(product_id, interval_minutes, days)
            results['results'].append(interval_result)
        
        # Analyze results
        analysis = self.analyze_results(results)
        results['analysis'] = analysis
        
        # Save results
        self.save_results(results)
        
        # Display summary
        self.display_summary(results)
        
        return results
    
    def analyze_results(self, results: Dict) -> Dict:
        """Analyze optimization results to find best intervals"""
        try:
            analysis = {
                'best_interval_by_strategy': {},
                'best_overall_interval': None,
                'interval_rankings': []
            }
            
            # Analyze by strategy
            for strategy_name in self.strategies:
                best_interval = None
                best_sharpe = float('-inf')
                
                for interval_result in results['results']:
                    if 'error' in interval_result:
                        continue
                        
                    strategy_result = interval_result['strategies'].get(strategy_name, {})
                    if 'error' in strategy_result:
                        continue
                    
                    sharpe = strategy_result.get('sharpe_ratio', float('-inf'))
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_interval = interval_result['interval_minutes']
                
                analysis['best_interval_by_strategy'][strategy_name] = {
                    'interval_minutes': best_interval,
                    'sharpe_ratio': best_sharpe
                }
            
            # Overall ranking by average performance
            interval_scores = {}
            
            for interval_result in results['results']:
                if 'error' in interval_result:
                    continue
                
                interval = interval_result['interval_minutes']
                scores = []
                
                for strategy_name in self.strategies:
                    strategy_result = interval_result['strategies'].get(strategy_name, {})
                    if 'error' not in strategy_result:
                        # Use Sharpe ratio as primary metric
                        sharpe = strategy_result.get('sharpe_ratio', 0)
                        scores.append(sharpe)
                
                if scores:
                    interval_scores[interval] = {
                        'avg_sharpe': np.mean(scores),
                        'strategies_tested': len(scores),
                        'total_trades': sum(interval_result['strategies'].get(s, {}).get('total_trades', 0) 
                                          for s in self.strategies)
                    }
            
            # Rank intervals
            ranked_intervals = sorted(interval_scores.items(), 
                                    key=lambda x: x[1]['avg_sharpe'], 
                                    reverse=True)
            
            analysis['interval_rankings'] = [
                {
                    'interval_minutes': interval,
                    'avg_sharpe': data['avg_sharpe'],
                    'strategies_tested': data['strategies_tested'],
                    'total_trades': data['total_trades']
                }
                for interval, data in ranked_intervals
            ]
            
            if ranked_intervals:
                analysis['best_overall_interval'] = ranked_intervals[0][0]
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            return {'error': str(e)}
    
    def save_results(self, results: Dict):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interval_optimization_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_interval_optimization.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_summary(self, results: Dict):
        """Display optimization summary"""
        try:
            print(f"\n{'='*80}")
            print(f"INTERVAL OPTIMIZATION RESULTS - {results['product_id']}")
            print(f"{'='*80}")
            
            analysis = results.get('analysis', {})
            
            if 'error' in analysis:
                print(f"❌ Analysis failed: {analysis['error']}")
                return
            
            # Display interval rankings
            rankings = analysis.get('interval_rankings', [])
            if rankings:
                print(f"\n📊 INTERVAL PERFORMANCE RANKING:")
                print(f"{'Interval':<10} {'Avg Sharpe':<12} {'Strategies':<12} {'Total Trades':<12}")
                print(f"{'-'*50}")
                
                for rank in rankings:
                    print(f"{rank['interval_minutes']:>6}min "
                          f"{rank['avg_sharpe']:>10.3f} "
                          f"{rank['strategies_tested']:>10} "
                          f"{rank['total_trades']:>11}")
                
                best_interval = analysis.get('best_overall_interval')
                if best_interval:
                    print(f"\n🏆 BEST OVERALL INTERVAL: {best_interval} minutes")
            
            # Display best by strategy
            best_by_strategy = analysis.get('best_interval_by_strategy', {})
            if best_by_strategy:
                print(f"\n📈 BEST INTERVAL BY STRATEGY:")
                for strategy, data in best_by_strategy.items():
                    interval = data.get('interval_minutes', 'N/A')
                    sharpe = data.get('sharpe_ratio', 0)
                    print(f"  {strategy:<15}: {interval:>3} min (Sharpe: {sharpe:>6.3f})")
            
            # Display detailed results
            print(f"\n📋 DETAILED RESULTS:")
            for interval_result in results['results']:
                if 'error' in interval_result:
                    print(f"\n{interval_result['interval_minutes']}min: ERROR - {interval_result['error']}")
                    continue
                
                interval = interval_result['interval_minutes']
                data_points = interval_result.get('data_points', 0)
                buy_hold = interval_result.get('buy_hold_return', 0)
                
                print(f"\n{interval}min interval ({data_points} data points, Buy&Hold: {buy_hold:.2f}%):")
                
                for strategy_name, strategy_result in interval_result['strategies'].items():
                    if 'error' in strategy_result:
                        print(f"  {strategy_name:<15}: ERROR - {strategy_result['error']}")
                    else:
                        ret = strategy_result.get('total_return', 0)
                        sharpe = strategy_result.get('sharpe_ratio', 0)
                        trades = strategy_result.get('total_trades', 0)
                        win_rate = strategy_result.get('win_rate', 0)
                        print(f"  {strategy_name:<15}: {ret:>6.2f}% return, "
                              f"Sharpe: {sharpe:>6.3f}, "
                              f"Trades: {trades:>3}, "
                              f"Win: {win_rate:>4.1f}%")
            
        except Exception as e:
            logger.error(f"Error displaying summary: {e}")

def main():
    """Run interval optimization"""
    try:
        optimizer = IntervalOptimizer()
        
        # Test with BTC-USD for 30 days
        results = optimizer.run_optimization(product_id="BTC-USD", days=30)
        
        if results:
            print(f"\n✅ Interval optimization completed successfully!")
            return True
        else:
            print(f"\n❌ Interval optimization failed!")
            return False
            
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"\n❌ Interval optimization failed: {e}")
        return False

if __name__ == "__main__":
    main()