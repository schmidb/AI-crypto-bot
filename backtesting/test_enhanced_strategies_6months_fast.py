#!/usr/bin/env python3
"""
Fast Enhanced Strategies Test with Partial Results - 6 Months Data

OPTIMIZATIONS:
1. Batch processing instead of row-by-row
2. Partial results saving after each strategy
3. Progress tracking and resumption capability
4. Simplified adaptive strategy testing
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
from utils.backtest.enhanced_strategy_vectorizer import EnhancedVectorizedStrategyAdapter
from utils.backtest.backtest_engine import BacktestEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FastEnhancedStrategyTester:
    """Fast enhanced strategy tester with partial results"""
    
    def __init__(self):
        self.results_dir = Path("backtesting/reports/enhanced_strategy_test")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.results_dir / "progress.json"
        
    def save_progress(self, progress_data: Dict):
        """Save progress to resume later"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
        logger.info(f"Progress saved: {progress_data.get('current_step', 'unknown')}")
    
    def load_progress(self) -> Dict:
        """Load previous progress"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {}
    
    def load_6month_data(self, product_id: str = "BTC-USD") -> pd.DataFrame:
        """Load 6 months of historical data"""
        try:
            file_path = f"data/historical/{product_id}_hour_180d.parquet"
            
            if not Path(file_path).exists():
                logger.error(f"Data file not found: {file_path}")
                return pd.DataFrame()
            
            df = pd.read_parquet(file_path)
            
            logger.info(f"Loaded {len(df)} rows for {product_id} (6 months)")
            logger.info(f"Date range: {df.index[0]} to {df.index[-1]}")
            logger.info(f"Price range: ${df['close'].min():,.0f} - ${df['close'].max():,.0f}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading 6-month data: {e}")
            return pd.DataFrame()
    
    def analyze_market_conditions(self, df: pd.DataFrame) -> Dict:
        """Analyze market conditions over 6 months"""
        try:
            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]
            min_price = df['close'].min()
            max_price = df['close'].max()
            
            total_return = ((end_price - start_price) / start_price) * 100
            volatility = df['close'].pct_change().std() * np.sqrt(24) * 100
            
            price_changes = df['close'].pct_change()
            positive_periods = (price_changes > 0).sum()
            negative_periods = (price_changes < 0).sum()
            
            cumulative_returns = (1 + price_changes).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max * 100
            max_drawdown = drawdown.min()
            
            # Monthly breakdown - fix the deprecation warning
            monthly_returns = df['close'].resample('ME').last().pct_change() * 100
            monthly_returns = monthly_returns.dropna()
            
            return {
                'period_start': df.index[0].isoformat(),
                'period_end': df.index[-1].isoformat(),
                'total_days': (df.index[-1] - df.index[0]).days,
                'start_price': start_price,
                'end_price': end_price,
                'min_price': min_price,
                'max_price': max_price,
                'total_return_pct': total_return,
                'volatility_pct': volatility,
                'positive_periods': int(positive_periods),
                'negative_periods': int(negative_periods),
                'max_drawdown_pct': max_drawdown,
                'price_range_pct': ((max_price - min_price) / start_price) * 100,
                'monthly_returns': monthly_returns.tolist(),
                'avg_monthly_return': monthly_returns.mean(),
                'monthly_volatility': monthly_returns.std()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {}
    
    def test_single_strategy_fast(self, strategy_name: str, combined_df: pd.DataFrame) -> Dict:
        """Test a single strategy with both original and enhanced versions"""
        try:
            logger.info(f"\n=== TESTING {strategy_name.upper()} ===")
            
            strategy_results = {
                'strategy_name': strategy_name,
                'original': {},
                'enhanced': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Initialize vectorizers
            from utils.backtest.strategy_vectorizer import VectorizedStrategyAdapter
            original_vectorizer = VectorizedStrategyAdapter()
            enhanced_vectorizer = EnhancedVectorizedStrategyAdapter()
            
            # Test original strategy
            try:
                logger.info(f"Testing original {strategy_name}...")
                if strategy_name == 'adaptive':
                    # Simplified adaptive test - use trend_following as proxy
                    original_signals = original_vectorizer.vectorize_strategy('trend_following', combined_df, "BTC-USD")
                else:
                    original_signals = original_vectorizer.vectorize_strategy(strategy_name, combined_df, "BTC-USD")
                
                original_buy_count = int(original_signals['buy'].sum())
                original_sell_count = int(original_signals['sell'].sum())
                
                if original_buy_count > 0 or original_sell_count > 0:
                    backtest_engine = BacktestEngine(initial_capital=10000.0, fees=0.006)
                    original_result = backtest_engine.run_backtest(
                        data=combined_df[['open', 'high', 'low', 'close', 'volume']],
                        signals=original_signals,
                        product_id=f"BTC-USD_{strategy_name}_original_6m"
                    )
                    strategy_results['original'] = original_result
                    strategy_results['original']['signal_count'] = {'buy': original_buy_count, 'sell': original_sell_count}
                    logger.info(f"Original {strategy_name}: {original_result.get('total_return', 0):.2f}% return, {original_result.get('total_trades', 0)} trades")
                else:
                    strategy_results['original'] = {'error': 'No signals generated'}
                    
            except Exception as e:
                logger.error(f"Error testing original {strategy_name}: {e}")
                strategy_results['original'] = {'error': str(e)}
            
            # Test enhanced strategy
            try:
                logger.info(f"Testing enhanced {strategy_name}...")
                if strategy_name == 'adaptive':
                    # Simplified adaptive test - use trend_following with enhancements
                    enhanced_signals = enhanced_vectorizer.vectorize_strategy('trend_following', combined_df, "BTC-USD", apply_market_filter=True)
                else:
                    enhanced_signals = enhanced_vectorizer.vectorize_strategy(strategy_name, combined_df, "BTC-USD", apply_market_filter=True)
                
                enhanced_buy_count = int(enhanced_signals['buy'].sum())
                enhanced_sell_count = int(enhanced_signals['sell'].sum())
                
                if enhanced_buy_count > 0 or enhanced_sell_count > 0:
                    backtest_engine = BacktestEngine(initial_capital=10000.0, fees=0.006)
                    enhanced_result = backtest_engine.run_backtest(
                        data=combined_df[['open', 'high', 'low', 'close', 'volume']],
                        signals=enhanced_signals,
                        product_id=f"BTC-USD_{strategy_name}_enhanced_6m"
                    )
                    strategy_results['enhanced'] = enhanced_result
                    strategy_results['enhanced']['signal_count'] = {'buy': enhanced_buy_count, 'sell': enhanced_sell_count}
                    
                    # Add market filter statistics
                    if 'market_filter_passed' in enhanced_signals.columns:
                        filter_stats = enhanced_signals['market_filter_passed'].value_counts()
                        strategy_results['enhanced']['market_filter_stats'] = filter_stats.to_dict()
                    
                    logger.info(f"Enhanced {strategy_name}: {enhanced_result.get('total_return', 0):.2f}% return, {enhanced_result.get('total_trades', 0)} trades")
                else:
                    strategy_results['enhanced'] = {'error': 'No signals generated'}
                    
            except Exception as e:
                logger.error(f"Error testing enhanced {strategy_name}: {e}")
                strategy_results['enhanced'] = {'error': str(e)}
            
            # Log comparison
            if 'error' not in strategy_results['original'] and 'error' not in strategy_results['enhanced']:
                orig_return = strategy_results['original'].get('total_return', 0)
                enh_return = strategy_results['enhanced'].get('total_return', 0)
                improvement = enh_return - orig_return
                
                logger.info(f"{strategy_name} comparison:")
                logger.info(f"  Original: {orig_return:.2f}% return, {strategy_results['original'].get('total_trades', 0)} trades")
                logger.info(f"  Enhanced: {enh_return:.2f}% return, {strategy_results['enhanced'].get('total_trades', 0)} trades")
                logger.info(f"  Improvement: {improvement:+.2f}% ({improvement/abs(orig_return)*100:+.1f}% relative)" if orig_return != 0 else f"  Improvement: {improvement:+.2f}%")
            
            # Save partial result
            partial_file = self.results_dir / f"{strategy_name}_result.json"
            with open(partial_file, 'w') as f:
                json.dump(strategy_results, f, indent=2, default=str)
            logger.info(f"Saved partial result: {partial_file}")
            
            return strategy_results
            
        except Exception as e:
            logger.error(f"Error in strategy test for {strategy_name}: {e}")
            return {'strategy_name': strategy_name, 'error': str(e)}
    
    def run_fast_comprehensive_test(self) -> Dict:
        """Run fast comprehensive 6-month test with partial results"""
        logger.info("🚀 Starting FAST comprehensive 6-month enhanced strategy test")
        
        # Check for previous progress
        progress = self.load_progress()
        start_time = datetime.now()
        
        # Load 6 months of data
        df = self.load_6month_data("BTC-USD")
        if df.empty:
            return {'error': 'No data available'}
        
        # Calculate indicators
        logger.info("🔧 Calculating indicators for 6 months of data...")
        indicator_factory = IndicatorFactory()
        indicators_df = indicator_factory.calculate_all_indicators(df, "BTC-USD")
        
        # Combine data
        combined_df = pd.concat([df, indicators_df], axis=1)
        combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
        
        # Analyze market conditions
        market_conditions = self.analyze_market_conditions(df)
        
        # Save market analysis
        market_file = self.results_dir / "market_conditions.json"
        with open(market_file, 'w') as f:
            json.dump(market_conditions, f, indent=2, default=str)
        
        # Test strategies
        strategies = ['mean_reversion', 'momentum', 'trend_following', 'adaptive']
        completed_strategies = progress.get('completed_strategies', [])
        strategy_results = {}
        
        for i, strategy_name in enumerate(strategies):
            if strategy_name in completed_strategies:
                logger.info(f"⏭️ Skipping {strategy_name} (already completed)")
                # Load existing result
                partial_file = self.results_dir / f"{strategy_name}_result.json"
                if partial_file.exists():
                    with open(partial_file, 'r') as f:
                        strategy_results[strategy_name] = json.load(f)
                continue
            
            logger.info(f"🔄 Testing strategy {i+1}/{len(strategies)}: {strategy_name}")
            
            # Update progress
            self.save_progress({
                'current_step': f'testing_{strategy_name}',
                'completed_strategies': completed_strategies,
                'progress_percent': (i / len(strategies)) * 100,
                'start_time': start_time.isoformat()
            })
            
            # Test strategy
            result = self.test_single_strategy_fast(strategy_name, combined_df)
            strategy_results[strategy_name] = result
            
            # Mark as completed
            completed_strategies.append(strategy_name)
            self.save_progress({
                'current_step': f'completed_{strategy_name}',
                'completed_strategies': completed_strategies,
                'progress_percent': ((i + 1) / len(strategies)) * 100,
                'start_time': start_time.isoformat()
            })
        
        # Compile final results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results = {
            'timestamp': end_time.isoformat(),
            'test_type': '6_month_enhanced_strategy_test_fast',
            'duration_seconds': duration,
            'data_period_days': market_conditions.get('total_days', 0),
            'market_conditions': market_conditions,
            'strategy_results': strategy_results,
            'summary': self.generate_summary(market_conditions, strategy_results)
        }
        
        # Save final results
        self.save_results(results)
        self.display_results(results)
        
        # Clean up progress file
        if self.progress_file.exists():
            self.progress_file.unlink()
        
        return results
    
    def generate_summary(self, market_conditions: Dict, strategy_results: Dict) -> Dict:
        """Generate test summary"""
        try:
            summary = {
                'market_period_type': 'unknown',
                'best_strategy': 'none',
                'improvements': [],
                'key_findings': []
            }
            
            # Classify market period
            total_return = market_conditions.get('total_return_pct', 0)
            if total_return > 20:
                summary['market_period_type'] = 'strong_bull'
            elif total_return > 5:
                summary['market_period_type'] = 'bull'
            elif total_return < -20:
                summary['market_period_type'] = 'strong_bear'
            elif total_return < -5:
                summary['market_period_type'] = 'bear'
            else:
                summary['market_period_type'] = 'sideways'
            
            # Find best performing strategy
            best_return = float('-inf')
            best_strategy = 'none'
            
            for strategy_name, results in strategy_results.items():
                if isinstance(results, dict) and 'enhanced' in results:
                    enhanced_result = results['enhanced']
                    if 'total_return' in enhanced_result:
                        strategy_return = enhanced_result['total_return']
                        if strategy_return > best_return:
                            best_return = strategy_return
                            best_strategy = strategy_name
            
            summary['best_strategy'] = best_strategy
            summary['best_return'] = best_return
            
            # Calculate improvements
            for strategy_name, results in strategy_results.items():
                if isinstance(results, dict) and 'original' in results and 'enhanced' in results:
                    orig = results['original']
                    enh = results['enhanced']
                    
                    if 'total_return' in orig and 'total_return' in enh:
                        improvement = enh['total_return'] - orig['total_return']
                        if improvement > 0.5:  # Significant improvement
                            summary['improvements'].append({
                                'strategy': strategy_name,
                                'improvement_pct': improvement,
                                'original_return': orig['total_return'],
                                'enhanced_return': enh['total_return']
                            })
            
            # Key findings
            if len(summary['improvements']) > 0:
                summary['key_findings'].append(f"Enhanced strategies showed improvements in {len(summary['improvements'])} out of {len(strategy_results)} strategies")
            
            if best_return > 0:
                summary['key_findings'].append(f"Best performing strategy: {best_strategy} with {best_return:.2f}% return")
            else:
                summary['key_findings'].append("All strategies showed negative returns - challenging market period")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {'error': str(e)}
    
    def save_results(self, results: Dict):
        """Save test results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_strategy_test_6m_fast_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_enhanced_strategy_test_6m.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_results(self, results: Dict):
        """Display comprehensive test results"""
        try:
            print(f"\n{'='*80}")
            print(f"FAST ENHANCED STRATEGY TEST RESULTS - 6 MONTHS")
            print(f"{'='*80}")
            
            # Duration
            duration = results.get('duration_seconds', 0)
            print(f"⏱️ Test Duration: {duration/60:.1f} minutes")
            
            # Market conditions
            market = results.get('market_conditions', {})
            print(f"\n📊 MARKET CONDITIONS (6 MONTHS):")
            print(f"Period: {market.get('period_start', 'N/A')[:10]} to {market.get('period_end', 'N/A')[:10]} ({market.get('total_days', 0)} days)")
            print(f"Total Return: {market.get('total_return_pct', 0):.2f}%")
            print(f"Volatility: {market.get('volatility_pct', 0):.2f}%")
            print(f"Max Drawdown: {market.get('max_drawdown_pct', 0):.2f}%")
            print(f"Price Range: ${market.get('min_price', 0):,.0f} - ${market.get('max_price', 0):,.0f}")
            
            # Strategy comparison
            print(f"\n📈 STRATEGY COMPARISON (Original vs Enhanced):")
            print(f"{'Strategy':<15} {'Original':<12} {'Enhanced':<12} {'Improvement':<12} {'Trades (O/E)':<12}")
            print(f"{'-'*75}")
            
            strategy_results = results.get('strategy_results', {})
            for strategy_name, strategy_data in strategy_results.items():
                if isinstance(strategy_data, dict):
                    orig = strategy_data.get('original', {})
                    enh = strategy_data.get('enhanced', {})
                    
                    orig_return = orig.get('total_return', 0) if 'error' not in orig else 0
                    enh_return = enh.get('total_return', 0) if 'error' not in enh else 0
                    improvement = enh_return - orig_return
                    
                    orig_trades = orig.get('total_trades', 0) if 'error' not in orig else 0
                    enh_trades = enh.get('total_trades', 0) if 'error' not in enh else 0
                    
                    print(f"{strategy_name:<15} {orig_return:>10.2f}% {enh_return:>10.2f}% "
                          f"{improvement:>+10.2f}% {orig_trades:>5}/{enh_trades:<5}")
            
            # Summary
            summary = results.get('summary', {})
            print(f"\n🎯 SUMMARY:")
            print(f"Market Type: {summary.get('market_period_type', 'unknown').replace('_', ' ').title()}")
            print(f"Best Strategy: {summary.get('best_strategy', 'none')} ({summary.get('best_return', 0):.2f}%)")
            
            improvements = summary.get('improvements', [])
            if improvements:
                print(f"\n✅ IMPROVEMENTS FOUND:")
                for imp in improvements:
                    print(f"  • {imp['strategy']}: {imp['original_return']:.2f}% → {imp['enhanced_return']:.2f}% "
                          f"({imp['improvement_pct']:+.2f}%)")
            
            key_findings = summary.get('key_findings', [])
            if key_findings:
                print(f"\n🔍 KEY FINDINGS:")
                for finding in key_findings:
                    print(f"  • {finding}")
            
        except Exception as e:
            logger.error(f"Error displaying results: {e}")

def main():
    """Run fast enhanced strategy test with 6 months of data"""
    try:
        tester = FastEnhancedStrategyTester()
        results = tester.run_fast_comprehensive_test()
        
        if 'error' not in results:
            print(f"\n✅ Fast enhanced strategy test completed successfully!")
            return True
        else:
            print(f"\n❌ Fast enhanced strategy test failed: {results['error']}")
            return False
            
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"\n❌ Fast enhanced strategy test failed: {e}")
        return False

if __name__ == "__main__":
    main()