#!/usr/bin/env python3
"""
One-time trading interval optimization analysis
Tests different trading intervals (15, 30, 60, 120 minutes) to find optimal setting
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging

# Import our backtesting infrastructure
from utils.backtest_suite import ComprehensiveBacktestSuite
from utils.strategy_vectorizer import VectorizedStrategyAdapter
from data_collector import DataCollector
from coinbase_client import CoinbaseClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntervalOptimizer:
    """One-time trading interval optimization analysis"""
    
    def __init__(self, data_dir: str = "./data/historical"):
        self.data_dir = Path(data_dir)
        self.results_dir = Path("./reports/interval_optimization")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize backtesting suite
        self.backtest_suite = ComprehensiveBacktestSuite()
        
        # Test intervals in minutes
        self.test_intervals = [15, 30, 60, 120]
        
        # Products to test
        self.products = ['BTC-USD', 'ETH-USD']
        
        # Strategies to test
        self.strategies = ['mean_reversion', 'momentum', 'trend_following']
        
    def load_historical_data(self, product: str, days: int = 180) -> pd.DataFrame:
        """Load historical data for a product"""
        try:
            # Look for existing data file
            data_file = self.data_dir / f"{product}_hour_{days}d.parquet"
            
            if not data_file.exists():
                logger.error(f"Historical data file not found: {data_file}")
                return pd.DataFrame()
            
            df = pd.read_parquet(data_file)
            logger.info(f"Loaded {len(df)} rows of {product} data from {data_file}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading historical data for {product}: {e}")
            return pd.DataFrame()
    
    def resample_data(self, df: pd.DataFrame, interval_minutes: int) -> pd.DataFrame:
        """Resample hourly data to different intervals"""
        try:
            if interval_minutes == 60:
                # Already hourly, return as-is
                return df
            
            # Resample to the target interval
            rule = f"{interval_minutes}T"  # T for minutes
            
            resampled = df.resample(rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            logger.info(f"Resampled from {len(df)} to {len(resampled)} rows ({interval_minutes}min intervals)")
            return resampled
            
        except Exception as e:
            logger.error(f"Error resampling data to {interval_minutes} minutes: {e}")
            return pd.DataFrame()
    
    def run_interval_backtest(self, product: str, interval_minutes: int, strategy: str) -> Dict[str, Any]:
        """Run backtest for a specific product, interval, and strategy"""
        try:
            # Load historical data
            df = self.load_historical_data(product)
            if df.empty:
                return {}
            
            # Resample to target interval
            resampled_df = self.resample_data(df, interval_minutes)
            if resampled_df.empty:
                return {}
            
            # Add indicators to the data
            from utils.performance.indicator_factory import IndicatorFactory
            indicator_factory = IndicatorFactory()
            data_with_indicators = indicator_factory.calculate_all_indicators(resampled_df, product)
            
            # Run backtest
            logger.info(f"Running backtest: {product} @ {interval_minutes}min with {strategy}")
            
            results = self.backtest_suite.run_single_strategy(
                data_with_indicators=data_with_indicators,
                strategy_name=strategy,
                product_id=product
            )
            
            if not results or 'error' in results:
                logger.warning(f"Backtest failed for {product} @ {interval_minutes}min with {strategy}: {results.get('error', 'Unknown error')}")
                return {}
            
            # Extract key metrics
            performance = results.get('performance', {})
            
            return {
                'product': product,
                'interval_minutes': interval_minutes,
                'strategy': strategy,
                'total_return': results.get('total_return', 0.0),
                'sharpe_ratio': performance.get('sharpe_ratio', 0.0),
                'sortino_ratio': performance.get('sortino_ratio', 0.0),
                'max_drawdown': performance.get('max_drawdown', 0.0),
                'win_rate': performance.get('win_rate', 0.0),
                'total_trades': results.get('signal_count', 0),
                'buy_signals': results.get('buy_signals', 0),
                'sell_signals': results.get('sell_signals', 0),
                'data_points': len(resampled_df),
                'backtest_period_days': (resampled_df.index[-1] - resampled_df.index[0]).days,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in interval backtest for {product} @ {interval_minutes}min with {strategy}: {e}")
            return {}
    
    def analyze_regime_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance across different market regimes"""
        try:
            # Group results by interval
            interval_performance = {}
            
            for result in results:
                if not result:
                    continue
                    
                interval = result['interval_minutes']
                if interval not in interval_performance:
                    interval_performance[interval] = {
                        'total_return': [],
                        'sharpe_ratio': [],
                        'sortino_ratio': [],
                        'max_drawdown': [],
                        'win_rate': [],
                        'total_trades': []
                    }
                
                # Aggregate metrics
                interval_performance[interval]['total_return'].append(result.get('total_return', 0.0))
                interval_performance[interval]['sharpe_ratio'].append(result.get('sharpe_ratio', 0.0))
                interval_performance[interval]['sortino_ratio'].append(result.get('sortino_ratio', 0.0))
                interval_performance[interval]['max_drawdown'].append(result.get('max_drawdown', 0.0))
                interval_performance[interval]['win_rate'].append(result.get('win_rate', 0.0))
                interval_performance[interval]['total_trades'].append(result.get('total_trades', 0))
            
            # Calculate aggregate statistics
            regime_analysis = {}
            
            for interval, metrics in interval_performance.items():
                regime_analysis[interval] = {
                    'avg_total_return': np.mean(metrics['total_return']),
                    'avg_sharpe_ratio': np.mean(metrics['sharpe_ratio']),
                    'avg_sortino_ratio': np.mean(metrics['sortino_ratio']),
                    'avg_max_drawdown': np.mean(metrics['max_drawdown']),
                    'avg_win_rate': np.mean(metrics['win_rate']),
                    'avg_total_trades': np.mean(metrics['total_trades']),
                    'consistency_score': 1.0 - np.std(metrics['total_return']) / (np.mean(metrics['total_return']) + 1e-6),
                    'risk_adjusted_return': np.mean(metrics['sortino_ratio']),
                    'sample_count': len(metrics['total_return'])
                }
            
            return regime_analysis
            
        except Exception as e:
            logger.error(f"Error in regime performance analysis: {e}")
            return {}
    
    def find_optimal_interval(self, regime_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Find the optimal trading interval based on multiple criteria"""
        try:
            if not regime_analysis:
                return {}
            
            # Scoring criteria (weights)
            criteria = {
                'avg_sortino_ratio': 0.35,      # Risk-adjusted returns (primary)
                'avg_total_return': 0.25,       # Absolute returns
                'consistency_score': 0.20,      # Consistency across strategies/products
                'avg_win_rate': 0.10,          # Win rate
                'avg_total_trades': 0.10        # Trading frequency (normalized)
            }
            
            # Normalize metrics for scoring
            normalized_metrics = {}
            for metric in criteria.keys():
                values = [data.get(metric, 0) for data in regime_analysis.values()]
                if metric == 'avg_total_trades':
                    # For trades, we want moderate frequency (not too high, not too low)
                    # Normalize to 0-1 where optimal is around 50-200 trades
                    normalized_values = []
                    for val in values:
                        if 50 <= val <= 200:
                            normalized_values.append(1.0)
                        elif val < 50:
                            normalized_values.append(val / 50.0)
                        else:
                            normalized_values.append(max(0.1, 200.0 / val))
                else:
                    # Standard min-max normalization
                    max_val = max(values) if values else 1
                    min_val = min(values) if values else 0
                    range_val = max_val - min_val if max_val != min_val else 1
                    normalized_values = [(val - min_val) / range_val for val in values]
                
                normalized_metrics[metric] = dict(zip(regime_analysis.keys(), normalized_values))
            
            # Calculate composite scores
            interval_scores = {}
            for interval in regime_analysis.keys():
                score = 0
                for metric, weight in criteria.items():
                    score += normalized_metrics[metric][interval] * weight
                
                interval_scores[interval] = {
                    'composite_score': score,
                    'raw_metrics': regime_analysis[interval],
                    'normalized_metrics': {metric: normalized_metrics[metric][interval] for metric in criteria.keys()}
                }
            
            # Find optimal interval
            optimal_interval = max(interval_scores.keys(), key=lambda x: interval_scores[x]['composite_score'])
            
            return {
                'optimal_interval_minutes': optimal_interval,
                'optimal_score': interval_scores[optimal_interval]['composite_score'],
                'all_scores': interval_scores,
                'scoring_criteria': criteria,
                'recommendation': self._generate_recommendation(optimal_interval, interval_scores)
            }
            
        except Exception as e:
            logger.error(f"Error finding optimal interval: {e}")
            return {}
    
    def _generate_recommendation(self, optimal_interval: int, interval_scores: Dict[str, Any]) -> str:
        """Generate human-readable recommendation"""
        try:
            current_interval = 60  # Current bot setting
            optimal_score = interval_scores[optimal_interval]['composite_score']
            current_score = interval_scores.get(current_interval, {}).get('composite_score', 0)
            
            if optimal_interval == current_interval:
                return f"✅ MAINTAIN: Current 60-minute interval is optimal (score: {optimal_score:.3f})"
            
            improvement = optimal_score - current_score
            if improvement > 0.1:  # Significant improvement threshold
                return f"🔄 CHANGE RECOMMENDED: Switch to {optimal_interval}-minute interval (improvement: +{improvement:.3f})"
            else:
                return f"⚖️ MARGINAL: {optimal_interval}-minute interval slightly better, but change may not be worth the risk (improvement: +{improvement:.3f})"
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "❌ Unable to generate recommendation due to analysis error"
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive interval optimization analysis"""
        logger.info("🚀 Starting comprehensive interval optimization analysis...")
        
        all_results = []
        
        # Test all combinations
        total_tests = len(self.test_intervals) * len(self.products) * len(self.strategies)
        current_test = 0
        
        for interval in self.test_intervals:
            for product in self.products:
                for strategy in self.strategies:
                    current_test += 1
                    logger.info(f"Progress: {current_test}/{total_tests} - Testing {product} @ {interval}min with {strategy}")
                    
                    result = self.run_interval_backtest(product, interval, strategy)
                    if result:
                        all_results.append(result)
        
        logger.info(f"Completed {len(all_results)} successful backtests out of {total_tests} attempts")
        
        # Analyze results
        regime_analysis = self.analyze_regime_performance(all_results)
        optimal_analysis = self.find_optimal_interval(regime_analysis)
        
        # Compile final results
        final_results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'test_configuration': {
                'intervals_tested': self.test_intervals,
                'products_tested': self.products,
                'strategies_tested': self.strategies,
                'data_period_days': 180
            },
            'individual_results': all_results,
            'regime_analysis': regime_analysis,
            'optimal_analysis': optimal_analysis,
            'summary': {
                'total_backtests': len(all_results),
                'successful_rate': len(all_results) / total_tests,
                'optimal_interval': optimal_analysis.get('optimal_interval_minutes', 60),
                'recommendation': optimal_analysis.get('recommendation', 'Analysis incomplete')
            }
        }
        
        return final_results
    
    def save_results(self, results: Dict[str, Any], sync_gcs: bool = False) -> str:
        """Save analysis results to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interval_optimization_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_interval_optimization.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Latest results saved to: {latest_filepath}")
            
            if sync_gcs:
                logger.info("GCS sync not implemented yet - results saved locally only")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""

def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(description='One-time trading interval optimization analysis')
    
    parser.add_argument('--intervals', type=str, default='15,30,60,120',
                       help='Comma-separated list of intervals to test in minutes (default: 15,30,60,120)')
    
    parser.add_argument('--products', type=str, default='BTC-USD,ETH-USD',
                       help='Comma-separated list of products to test (default: BTC-USD,ETH-USD)')
    
    parser.add_argument('--strategies', type=str, default='mean_reversion,momentum,trend_following',
                       help='Comma-separated list of strategies to test (default: mean_reversion,momentum,trend_following)')
    
    parser.add_argument('--sync-gcs', action='store_true',
                       help='Sync results to Google Cloud Storage')
    
    parser.add_argument('--data-dir', type=str, default='./data/historical',
                       help='Directory containing historical data files')
    
    args = parser.parse_args()
    
    # Parse arguments
    intervals = [int(x.strip()) for x in args.intervals.split(',')]
    products = [x.strip() for x in args.products.split(',')]
    strategies = [x.strip() for x in args.strategies.split(',')]
    
    # Initialize optimizer
    optimizer = IntervalOptimizer(data_dir=args.data_dir)
    optimizer.test_intervals = intervals
    optimizer.products = products
    optimizer.strategies = strategies
    
    # Run analysis
    logger.info("🎯 Starting one-time interval optimization analysis...")
    logger.info(f"📊 Testing intervals: {intervals} minutes")
    logger.info(f"💰 Testing products: {products}")
    logger.info(f"🔄 Testing strategies: {strategies}")
    
    results = optimizer.run_comprehensive_analysis()
    
    if results:
        # Save results
        filepath = optimizer.save_results(results, sync_gcs=args.sync_gcs)
        
        # Display summary
        print("\n" + "="*80)
        print("🎯 INTERVAL OPTIMIZATION ANALYSIS COMPLETE")
        print("="*80)
        
        summary = results.get('summary', {})
        optimal = results.get('optimal_analysis', {})
        
        print(f"📊 Total backtests completed: {summary.get('total_backtests', 0)}")
        print(f"✅ Success rate: {summary.get('successful_rate', 0):.1%}")
        print(f"🎯 Optimal interval: {summary.get('optimal_interval', 60)} minutes")
        print(f"💡 Recommendation: {summary.get('recommendation', 'N/A')}")
        
        if optimal.get('optimal_score'):
            print(f"📈 Optimal score: {optimal['optimal_score']:.3f}")
        
        print(f"💾 Results saved to: {filepath}")
        print("="*80)
        
        return True
    else:
        print("\n❌ Interval optimization analysis failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)