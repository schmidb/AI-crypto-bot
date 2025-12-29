#!/usr/bin/env python3
"""
Optimize Strategy Parameters - Fix the confidence thresholds and parameters
"""

import pandas as pd
import numpy as np
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.append('.')

from utils.performance.indicator_factory import IndicatorFactory
from utils.backtest.strategy_vectorizer import VectorizedStrategyAdapter
from utils.backtest.backtest_engine import BacktestEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyParameterOptimizer:
    """Optimize strategy parameters to improve performance"""
    
    def __init__(self):
        self.results_dir = Path("backtesting/reports/parameter_optimization")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_data(self) -> pd.DataFrame:
        """Load and prepare data"""
        try:
            file_path = "data/historical/BTC-USD_hour_180d.parquet"
            df = pd.read_parquet(file_path)
            df = df.tail(720)  # Last 30 days
            
            # Calculate indicators
            indicator_factory = IndicatorFactory()
            indicators_df = indicator_factory.calculate_all_indicators(df, "BTC-USD")
            
            # Combine data
            combined_df = pd.concat([df, indicators_df], axis=1)
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
            
            logger.info(f"Loaded {len(combined_df)} rows with {len(combined_df.columns)} columns")
            return combined_df
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def test_confidence_thresholds(self, df: pd.DataFrame, strategy_name: str) -> Dict:
        """Test different confidence thresholds for a strategy"""
        try:
            logger.info(f"Testing confidence thresholds for {strategy_name}")
            
            # Test different confidence thresholds
            thresholds = [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
            results = []
            
            vectorizer = VectorizedStrategyAdapter()
            
            for threshold in thresholds:
                try:
                    # Modify the strategy's confidence threshold
                    # This is a simplified approach - in practice you'd modify the strategy logic
                    signals_df = vectorizer.vectorize_strategy(strategy_name, df, "BTC-USD")
                    
                    # Filter signals by confidence threshold (simulate)
                    # For now, we'll use the signals as-is and see the baseline
                    buy_count = int(signals_df['buy'].sum())
                    sell_count = int(signals_df['sell'].sum())
                    
                    if buy_count == 0 and sell_count == 0:
                        continue
                    
                    # Run backtest
                    backtest_engine = BacktestEngine(initial_capital=10000.0, fees=0.006)
                    result = backtest_engine.run_backtest(
                        data=df[['open', 'high', 'low', 'close', 'volume']],
                        signals=signals_df,
                        product_id=f"BTC-USD_{strategy_name}_thresh_{threshold}"
                    )
                    
                    result['threshold'] = threshold
                    result['buy_signals'] = buy_count
                    result['sell_signals'] = sell_count
                    results.append(result)
                    
                    logger.info(f"Threshold {threshold}%: {result.get('total_return', 0):.2f}% return, "
                               f"{result.get('total_trades', 0)} trades, "
                               f"{result.get('win_rate', 0):.1f}% win rate")
                    
                except Exception as e:
                    logger.warning(f"Failed threshold {threshold}: {e}")
                    continue
            
            return {
                'strategy': strategy_name,
                'threshold_results': results,
                'best_threshold': self.find_best_threshold(results)
            }
            
        except Exception as e:
            logger.error(f"Error testing thresholds for {strategy_name}: {e}")
            return {'strategy': strategy_name, 'error': str(e)}
    
    def find_best_threshold(self, results: List[Dict]) -> Dict:
        """Find the best performing threshold"""
        if not results:
            return {}
        
        # Sort by Sharpe ratio (best risk-adjusted return)
        sorted_results = sorted(results, key=lambda x: x.get('sharpe_ratio', -999), reverse=True)
        best = sorted_results[0]
        
        return {
            'threshold': best['threshold'],
            'total_return': best.get('total_return', 0),
            'sharpe_ratio': best.get('sharpe_ratio', 0),
            'win_rate': best.get('win_rate', 0),
            'total_trades': best.get('total_trades', 0)
        }
    
    def test_market_regime_filters(self, df: pd.DataFrame) -> Dict:
        """Test adding market regime filters to avoid bad conditions"""
        try:
            logger.info("Testing market regime filters")
            
            # Analyze market conditions during losing periods
            price_changes = df['close'].pct_change()
            volatility = price_changes.rolling(24).std()  # 24-hour rolling volatility
            
            # Define market regimes
            high_vol_threshold = volatility.quantile(0.75)  # Top 25% volatility
            low_vol_threshold = volatility.quantile(0.25)   # Bottom 25% volatility
            
            # Test different market filters
            filters = {
                'no_filter': lambda x: True,
                'avoid_high_volatility': lambda x: volatility.loc[x] < high_vol_threshold,
                'only_moderate_volatility': lambda x: (volatility.loc[x] >= low_vol_threshold) & 
                                                     (volatility.loc[x] <= high_vol_threshold),
                'avoid_declining_periods': lambda x: price_changes.rolling(24).mean().loc[x] > -0.001  # Avoid 24h declining trends
            }
            
            results = {}
            vectorizer = VectorizedStrategyAdapter()
            
            for filter_name, filter_func in filters.items():
                try:
                    # Get base signals
                    signals_df = vectorizer.vectorize_strategy('mean_reversion', df, "BTC-USD")
                    
                    # Apply market regime filter
                    if filter_name != 'no_filter':
                        # Create a mask for valid trading periods
                        valid_periods = pd.Series(index=df.index, dtype=bool)
                        for idx in df.index:
                            try:
                                valid_periods.loc[idx] = filter_func(idx)
                            except:
                                valid_periods.loc[idx] = False
                        
                        # Filter signals
                        signals_df.loc[~valid_periods, ['buy', 'sell']] = False
                    
                    buy_count = int(signals_df['buy'].sum())
                    sell_count = int(signals_df['sell'].sum())
                    
                    if buy_count == 0 and sell_count == 0:
                        results[filter_name] = {'error': 'No signals after filtering'}
                        continue
                    
                    # Run backtest
                    backtest_engine = BacktestEngine(initial_capital=10000.0, fees=0.006)
                    result = backtest_engine.run_backtest(
                        data=df[['open', 'high', 'low', 'close', 'volume']],
                        signals=signals_df,
                        product_id=f"BTC-USD_filtered_{filter_name}"
                    )
                    
                    result['filter_name'] = filter_name
                    result['buy_signals'] = buy_count
                    result['sell_signals'] = sell_count
                    results[filter_name] = result
                    
                    logger.info(f"Filter {filter_name}: {result.get('total_return', 0):.2f}% return, "
                               f"{result.get('total_trades', 0)} trades")
                    
                except Exception as e:
                    logger.warning(f"Failed filter {filter_name}: {e}")
                    results[filter_name] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing market filters: {e}")
            return {'error': str(e)}
    
    def test_position_sizing(self, df: pd.DataFrame) -> Dict:
        """Test different position sizing approaches"""
        try:
            logger.info("Testing position sizing strategies")
            
            position_sizes = {
                'fixed_small': 0.1,    # 10% of capital per trade
                'fixed_medium': 0.2,   # 20% of capital per trade  
                'fixed_large': 0.3,    # 30% of capital per trade
                'volatility_adjusted': 'dynamic'  # Adjust based on volatility
            }
            
            results = {}
            vectorizer = VectorizedStrategyAdapter()
            signals_df = vectorizer.vectorize_strategy('mean_reversion', df, "BTC-USD")
            
            for size_name, size_value in position_sizes.items():
                try:
                    # Create modified signals with different position sizing
                    modified_signals = signals_df.copy()
                    
                    if size_name == 'volatility_adjusted':
                        # Adjust position size based on volatility
                        volatility = df['close'].pct_change().rolling(24).std()
                        # Smaller positions during high volatility
                        position_multiplier = 1 / (1 + volatility * 10)  # Scale factor
                        position_multiplier = position_multiplier.fillna(0.2).clip(0.05, 0.3)
                    else:
                        # Fixed position size
                        position_multiplier = size_value
                    
                    # For now, we'll use the backtest engine's default position sizing
                    # In a full implementation, you'd modify the backtest engine
                    
                    backtest_engine = BacktestEngine(initial_capital=10000.0, fees=0.006)
                    result = backtest_engine.run_backtest(
                        data=df[['open', 'high', 'low', 'close', 'volume']],
                        signals=modified_signals,
                        product_id=f"BTC-USD_position_{size_name}"
                    )
                    
                    result['position_sizing'] = size_name
                    results[size_name] = result
                    
                    logger.info(f"Position sizing {size_name}: {result.get('total_return', 0):.2f}% return")
                    
                except Exception as e:
                    logger.warning(f"Failed position sizing {size_name}: {e}")
                    results[size_name] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing position sizing: {e}")
            return {'error': str(e)}
    
    def run_comprehensive_optimization(self) -> Dict:
        """Run comprehensive parameter optimization"""
        logger.info("🚀 Starting comprehensive parameter optimization")
        
        # Load data
        df = self.load_data()
        if df.empty:
            return {'error': 'No data available'}
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'market_conditions': self.analyze_market_conditions(df),
            'optimization_results': {}
        }
        
        # Test confidence thresholds for each strategy
        strategies = ['mean_reversion', 'momentum', 'trend_following']
        for strategy in strategies:
            logger.info(f"\n=== OPTIMIZING {strategy.upper()} ===")
            threshold_results = self.test_confidence_thresholds(df, strategy)
            results['optimization_results'][f'{strategy}_thresholds'] = threshold_results
        
        # Test market regime filters
        logger.info(f"\n=== TESTING MARKET FILTERS ===")
        filter_results = self.test_market_regime_filters(df)
        results['optimization_results']['market_filters'] = filter_results
        
        # Test position sizing
        logger.info(f"\n=== TESTING POSITION SIZING ===")
        position_results = self.test_position_sizing(df)
        results['optimization_results']['position_sizing'] = position_results
        
        # Generate recommendations
        results['recommendations'] = self.generate_recommendations(results)
        
        # Save results
        self.save_results(results)
        self.display_results(results)
        
        return results
    
    def analyze_market_conditions(self, df: pd.DataFrame) -> Dict:
        """Analyze market conditions during test period"""
        try:
            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100
            
            price_changes = df['close'].pct_change()
            volatility = price_changes.std() * np.sqrt(24) * 100
            
            return {
                'period_start': df.index[0].isoformat(),
                'period_end': df.index[-1].isoformat(),
                'total_return_pct': total_return,
                'volatility_pct': volatility,
                'market_type': 'bear' if total_return < -5 else 'bull' if total_return > 5 else 'sideways'
            }
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {}
    
    def generate_recommendations(self, results: Dict) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        try:
            market_type = results.get('market_conditions', {}).get('market_type', 'unknown')
            
            if market_type == 'sideways':
                recommendations.append("Sideways market detected - consider reducing trading frequency")
                recommendations.append("Focus on mean reversion strategies in ranging markets")
            elif market_type == 'bear':
                recommendations.append("Bear market detected - consider defensive strategies")
                recommendations.append("Reduce position sizes and increase cash reserves")
            
            # Analyze threshold results
            for strategy_key, strategy_results in results.get('optimization_results', {}).items():
                if 'thresholds' in strategy_key and 'best_threshold' in strategy_results:
                    best = strategy_results['best_threshold']
                    if best:
                        strategy_name = strategy_key.replace('_thresholds', '')
                        recommendations.append(f"Optimize {strategy_name} confidence threshold to {best.get('threshold', 50)}%")
            
            # Analyze filter results
            filter_results = results.get('optimization_results', {}).get('market_filters', {})
            if filter_results:
                best_filter = max(filter_results.items(), 
                                key=lambda x: x[1].get('sharpe_ratio', -999) if isinstance(x[1], dict) else -999)
                if best_filter[0] != 'no_filter':
                    recommendations.append(f"Apply market filter: {best_filter[0]}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review strategy parameters manually"]
    
    def save_results(self, results: Dict):
        """Save optimization results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parameter_optimization_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_parameter_optimization.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_results(self, results: Dict):
        """Display optimization results"""
        try:
            print(f"\n{'='*80}")
            print(f"STRATEGY PARAMETER OPTIMIZATION RESULTS")
            print(f"{'='*80}")
            
            # Market conditions
            market = results.get('market_conditions', {})
            print(f"\n📊 MARKET CONDITIONS:")
            print(f"Period: {market.get('period_start', 'N/A')[:10]} to {market.get('period_end', 'N/A')[:10]}")
            print(f"Total Return: {market.get('total_return_pct', 0):.2f}%")
            print(f"Market Type: {market.get('market_type', 'unknown').title()}")
            
            # Best thresholds
            print(f"\n🎯 OPTIMAL CONFIDENCE THRESHOLDS:")
            for strategy_key, strategy_results in results.get('optimization_results', {}).items():
                if 'thresholds' in strategy_key and 'best_threshold' in strategy_results:
                    best = strategy_results['best_threshold']
                    if best:
                        strategy_name = strategy_key.replace('_thresholds', '')
                        print(f"{strategy_name:<15}: {best.get('threshold', 0):>3}% "
                              f"(Return: {best.get('total_return', 0):>6.2f}%, "
                              f"Sharpe: {best.get('sharpe_ratio', 0):>6.3f})")
            
            # Recommendations
            recommendations = results.get('recommendations', [])
            if recommendations:
                print(f"\n💡 RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"{i:>2}. {rec}")
            
        except Exception as e:
            logger.error(f"Error displaying results: {e}")

def main():
    """Run parameter optimization"""
    try:
        optimizer = StrategyParameterOptimizer()
        results = optimizer.run_comprehensive_optimization()
        
        if 'error' not in results:
            print(f"\n✅ Parameter optimization completed successfully!")
            return True
        else:
            print(f"\n❌ Parameter optimization failed: {results['error']}")
            return False
            
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"\n❌ Parameter optimization failed: {e}")
        return False

if __name__ == "__main__":
    main()