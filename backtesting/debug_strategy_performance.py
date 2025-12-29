#!/usr/bin/env python3
"""
Debug Strategy Performance - Investigate why all strategies are losing money
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

class StrategyPerformanceDebugger:
    """Debug individual strategy performance to identify issues"""
    
    def __init__(self):
        self.results_dir = Path("backtesting/reports/strategy_debug")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_data(self, product_id: str = "BTC-USD") -> pd.DataFrame:
        """Load historical data for analysis"""
        try:
            file_path = f"data/historical/{product_id}_hour_180d.parquet"
            
            if not Path(file_path).exists():
                logger.error(f"Data file not found: {file_path}")
                return pd.DataFrame()
            
            df = pd.read_parquet(file_path)
            
            # Use last 30 days for consistency with interval optimization
            if len(df) > 720:
                df = df.tail(720)
            
            logger.info(f"Loaded {len(df)} rows for {product_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def analyze_market_conditions(self, df: pd.DataFrame) -> Dict:
        """Analyze market conditions during the test period"""
        try:
            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]
            min_price = df['close'].min()
            max_price = df['close'].max()
            
            # Calculate various metrics
            total_return = ((end_price - start_price) / start_price) * 100
            volatility = df['close'].pct_change().std() * np.sqrt(24) * 100  # Daily volatility
            
            # Trend analysis
            price_changes = df['close'].pct_change()
            positive_days = (price_changes > 0).sum()
            negative_days = (price_changes < 0).sum()
            
            # Drawdown analysis
            cumulative_returns = (1 + price_changes).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max * 100
            max_drawdown = drawdown.min()
            
            return {
                'period_start': df.index[0].isoformat(),
                'period_end': df.index[-1].isoformat(),
                'start_price': start_price,
                'end_price': end_price,
                'min_price': min_price,
                'max_price': max_price,
                'total_return_pct': total_return,
                'volatility_pct': volatility,
                'positive_periods': int(positive_days),
                'negative_periods': int(negative_days),
                'max_drawdown_pct': max_drawdown,
                'price_range_pct': ((max_price - min_price) / start_price) * 100
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {}
    
    def analyze_individual_strategy(self, strategy_name: str, df: pd.DataFrame, indicators_df: pd.DataFrame) -> Dict:
        """Analyze individual strategy performance in detail"""
        try:
            logger.info(f"\n=== ANALYZING {strategy_name.upper()} STRATEGY ===")
            
            # Combine data
            combined_df = pd.concat([df, indicators_df], axis=1)
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
            
            # Get strategy signals
            vectorizer = VectorizedStrategyAdapter()
            
            if strategy_name == 'adaptive':
                signals_df = vectorizer.vectorize_adaptive_strategy(combined_df, "BTC-USD")
            else:
                signals_df = vectorizer.vectorize_strategy(strategy_name, combined_df, "BTC-USD")
            
            # Analyze signals
            buy_signals = signals_df[signals_df['buy'] == True]
            sell_signals = signals_df[signals_df['sell'] == True]
            
            logger.info(f"Generated {len(buy_signals)} BUY and {len(sell_signals)} SELL signals")
            
            # Analyze signal timing and market conditions
            signal_analysis = {
                'total_buy_signals': len(buy_signals),
                'total_sell_signals': len(sell_signals),
                'signal_frequency_pct': ((len(buy_signals) + len(sell_signals)) / len(combined_df)) * 100,
                'buy_signal_times': [],
                'sell_signal_times': [],
                'buy_signal_prices': [],
                'sell_signal_prices': [],
                'buy_signal_conditions': [],
                'sell_signal_conditions': []
            }
            
            # Analyze buy signals
            for idx in buy_signals.index:
                price = combined_df.loc[idx, 'close']
                signal_analysis['buy_signal_times'].append(idx.isoformat())
                signal_analysis['buy_signal_prices'].append(float(price))
                
                # Get market conditions at signal time
                conditions = {
                    'rsi': float(combined_df.loc[idx, 'rsi_14']),
                    'macd': float(combined_df.loc[idx, 'macd']),
                    'bb_position': float((price - combined_df.loc[idx, 'bb_lower']) / 
                                       (combined_df.loc[idx, 'bb_upper'] - combined_df.loc[idx, 'bb_lower'])),
                    'volume_ratio': float(combined_df.loc[idx, 'volume'] / combined_df['volume'].rolling(20).mean().loc[idx])
                }
                signal_analysis['buy_signal_conditions'].append(conditions)
            
            # Analyze sell signals
            for idx in sell_signals.index:
                price = combined_df.loc[idx, 'close']
                signal_analysis['sell_signal_times'].append(idx.isoformat())
                signal_analysis['sell_signal_prices'].append(float(price))
                
                conditions = {
                    'rsi': float(combined_df.loc[idx, 'rsi_14']),
                    'macd': float(combined_df.loc[idx, 'macd']),
                    'bb_position': float((price - combined_df.loc[idx, 'bb_lower']) / 
                                       (combined_df.loc[idx, 'bb_upper'] - combined_df.loc[idx, 'bb_lower'])),
                    'volume_ratio': float(combined_df.loc[idx, 'volume'] / combined_df['volume'].rolling(20).mean().loc[idx])
                }
                signal_analysis['sell_signal_conditions'].append(conditions)
            
            # Run backtest
            backtest_engine = BacktestEngine(initial_capital=10000.0, fees=0.006)
            backtest_result = backtest_engine.run_backtest(
                data=combined_df[['open', 'high', 'low', 'close', 'volume']],
                signals=signals_df,
                product_id=f"BTC-USD_{strategy_name}_debug"
            )
            
            # Combine results
            result = {
                'strategy_name': strategy_name,
                'signal_analysis': signal_analysis,
                'backtest_result': backtest_result
            }
            
            logger.info(f"{strategy_name}: {backtest_result.get('total_return', 0):.2f}% return, "
                       f"{backtest_result.get('total_trades', 0)} trades, "
                       f"{backtest_result.get('win_rate', 0):.1f}% win rate")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {strategy_name}: {e}")
            return {'strategy_name': strategy_name, 'error': str(e)}
    
    def analyze_signal_quality(self, results: Dict) -> Dict:
        """Analyze signal quality across all strategies"""
        try:
            analysis = {
                'signal_timing_analysis': {},
                'market_condition_analysis': {},
                'common_issues': []
            }
            
            for strategy_name, result in results.items():
                if 'error' in result or 'signal_analysis' not in result:
                    continue
                
                signal_data = result['signal_analysis']
                
                # Analyze signal timing
                if signal_data['buy_signal_prices'] and signal_data['sell_signal_prices']:
                    avg_buy_price = np.mean(signal_data['buy_signal_prices'])
                    avg_sell_price = np.mean(signal_data['sell_signal_prices'])
                    
                    analysis['signal_timing_analysis'][strategy_name] = {
                        'avg_buy_price': avg_buy_price,
                        'avg_sell_price': avg_sell_price,
                        'price_differential': avg_sell_price - avg_buy_price,
                        'signal_frequency': signal_data['signal_frequency_pct']
                    }
                
                # Analyze market conditions at signals
                if signal_data['buy_signal_conditions']:
                    buy_conditions = signal_data['buy_signal_conditions']
                    avg_buy_rsi = np.mean([c['rsi'] for c in buy_conditions])
                    avg_buy_bb_pos = np.mean([c['bb_position'] for c in buy_conditions])
                    
                    analysis['market_condition_analysis'][f'{strategy_name}_buy'] = {
                        'avg_rsi': avg_buy_rsi,
                        'avg_bb_position': avg_buy_bb_pos,
                        'rsi_range': [min(c['rsi'] for c in buy_conditions), 
                                     max(c['rsi'] for c in buy_conditions)]
                    }
                
                if signal_data['sell_signal_conditions']:
                    sell_conditions = signal_data['sell_signal_conditions']
                    avg_sell_rsi = np.mean([c['rsi'] for c in sell_conditions])
                    avg_sell_bb_pos = np.mean([c['bb_position'] for c in sell_conditions])
                    
                    analysis['market_condition_analysis'][f'{strategy_name}_sell'] = {
                        'avg_rsi': avg_sell_rsi,
                        'avg_bb_position': avg_sell_bb_pos,
                        'rsi_range': [min(c['rsi'] for c in sell_conditions), 
                                     max(c['rsi'] for c in sell_conditions)]
                    }
            
            # Identify common issues
            for strategy_name, timing in analysis['signal_timing_analysis'].items():
                if timing['price_differential'] < 0:
                    analysis['common_issues'].append(f"{strategy_name}: Selling at lower average price than buying")
                
                if timing['signal_frequency'] > 10:
                    analysis['common_issues'].append(f"{strategy_name}: High signal frequency ({timing['signal_frequency']:.1f}%) may indicate overtrading")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing signal quality: {e}")
            return {'error': str(e)}
    
    def run_comprehensive_debug(self) -> Dict:
        """Run comprehensive strategy performance debugging"""
        logger.info("🔍 Starting comprehensive strategy performance debugging")
        
        # Load data
        df = self.load_data("BTC-USD")
        if df.empty:
            return {'error': 'No data available'}
        
        # Calculate indicators
        indicator_factory = IndicatorFactory()
        indicators_df = indicator_factory.calculate_all_indicators(df, "BTC-USD")
        
        # Analyze market conditions
        market_conditions = self.analyze_market_conditions(df)
        logger.info(f"Market conditions: {market_conditions['total_return_pct']:.2f}% return, "
                   f"{market_conditions['volatility_pct']:.2f}% volatility")
        
        # Analyze individual strategies
        strategies = ['mean_reversion', 'momentum', 'trend_following', 'adaptive']
        strategy_results = {}
        
        for strategy_name in strategies:
            result = self.analyze_individual_strategy(strategy_name, df, indicators_df)
            strategy_results[strategy_name] = result
        
        # Analyze signal quality
        signal_quality_analysis = self.analyze_signal_quality(strategy_results)
        
        # Compile final results
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'market_conditions': market_conditions,
            'strategy_results': strategy_results,
            'signal_quality_analysis': signal_quality_analysis,
            'summary': self.generate_summary(market_conditions, strategy_results, signal_quality_analysis)
        }
        
        # Save results
        self.save_results(final_results)
        
        # Display summary
        self.display_summary(final_results)
        
        return final_results
    
    def generate_summary(self, market_conditions: Dict, strategy_results: Dict, signal_analysis: Dict) -> Dict:
        """Generate summary of findings"""
        try:
            summary = {
                'market_period_type': 'unknown',
                'primary_issues': [],
                'recommendations': []
            }
            
            # Classify market period
            total_return = market_conditions.get('total_return_pct', 0)
            volatility = market_conditions.get('volatility_pct', 0)
            max_drawdown = market_conditions.get('max_drawdown_pct', 0)
            
            if total_return < -5:
                summary['market_period_type'] = 'bear_market'
            elif total_return > 5:
                summary['market_period_type'] = 'bull_market'
            elif volatility > 5:
                summary['market_period_type'] = 'high_volatility'
            else:
                summary['market_period_type'] = 'sideways'
            
            # Identify primary issues
            all_negative = all(
                result.get('backtest_result', {}).get('total_return', 0) < 0 
                for result in strategy_results.values() 
                if 'backtest_result' in result
            )
            
            if all_negative:
                summary['primary_issues'].append('All strategies showing negative returns')
            
            zero_win_rates = [
                name for name, result in strategy_results.items()
                if result.get('backtest_result', {}).get('win_rate', 0) == 0
            ]
            
            if zero_win_rates:
                summary['primary_issues'].append(f'Zero win rates: {", ".join(zero_win_rates)}')
            
            # Add recommendations
            if summary['market_period_type'] == 'bear_market':
                summary['recommendations'].append('Consider defensive strategies or reduce position sizes in bear market')
            
            if 'All strategies showing negative returns' in summary['primary_issues']:
                summary['recommendations'].append('Review signal generation logic and confidence thresholds')
                summary['recommendations'].append('Consider market regime filters to avoid trading in unfavorable conditions')
            
            if zero_win_rates:
                summary['recommendations'].append('Investigate signal timing - may be entering/exiting at wrong times')
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {'error': str(e)}
    
    def save_results(self, results: Dict):
        """Save debug results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strategy_debug_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_strategy_debug.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Debug results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_summary(self, results: Dict):
        """Display debugging summary"""
        try:
            print(f"\n{'='*80}")
            print(f"STRATEGY PERFORMANCE DEBUG RESULTS")
            print(f"{'='*80}")
            
            # Market conditions
            market = results.get('market_conditions', {})
            print(f"\n📊 MARKET CONDITIONS:")
            print(f"Period: {market.get('period_start', 'N/A')[:10]} to {market.get('period_end', 'N/A')[:10]}")
            print(f"Total Return: {market.get('total_return_pct', 0):.2f}%")
            print(f"Volatility: {market.get('volatility_pct', 0):.2f}%")
            print(f"Max Drawdown: {market.get('max_drawdown_pct', 0):.2f}%")
            print(f"Price Range: ${market.get('min_price', 0):,.0f} - ${market.get('max_price', 0):,.0f}")
            
            # Strategy results
            print(f"\n📈 STRATEGY PERFORMANCE:")
            print(f"{'Strategy':<15} {'Return':<8} {'Trades':<7} {'Win Rate':<8} {'Signals':<8}")
            print(f"{'-'*55}")
            
            for name, result in results.get('strategy_results', {}).items():
                if 'backtest_result' in result:
                    br = result['backtest_result']
                    sa = result.get('signal_analysis', {})
                    total_signals = sa.get('total_buy_signals', 0) + sa.get('total_sell_signals', 0)
                    
                    print(f"{name:<15} {br.get('total_return', 0):>6.2f}% "
                          f"{br.get('total_trades', 0):>6} "
                          f"{br.get('win_rate', 0):>6.1f}% "
                          f"{total_signals:>7}")
            
            # Summary
            summary = results.get('summary', {})
            print(f"\n🎯 SUMMARY:")
            print(f"Market Type: {summary.get('market_period_type', 'unknown').replace('_', ' ').title()}")
            
            issues = summary.get('primary_issues', [])
            if issues:
                print(f"\n❌ PRIMARY ISSUES:")
                for issue in issues:
                    print(f"  • {issue}")
            
            recommendations = summary.get('recommendations', [])
            if recommendations:
                print(f"\n💡 RECOMMENDATIONS:")
                for rec in recommendations:
                    print(f"  • {rec}")
            
            # Signal quality issues
            signal_analysis = results.get('signal_quality_analysis', {})
            common_issues = signal_analysis.get('common_issues', [])
            if common_issues:
                print(f"\n⚠️  SIGNAL QUALITY ISSUES:")
                for issue in common_issues:
                    print(f"  • {issue}")
            
        except Exception as e:
            logger.error(f"Error displaying summary: {e}")

def main():
    """Run strategy performance debugging"""
    try:
        debugger = StrategyPerformanceDebugger()
        results = debugger.run_comprehensive_debug()
        
        if 'error' not in results:
            print(f"\n✅ Strategy performance debugging completed successfully!")
            return True
        else:
            print(f"\n❌ Strategy performance debugging failed: {results['error']}")
            return False
            
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"\n❌ Strategy performance debugging failed: {e}")
        return False

if __name__ == "__main__":
    main()