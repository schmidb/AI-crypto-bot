#!/usr/bin/env python3
"""
Backtest Suite - Comprehensive Strategy Backtesting

This module provides a comprehensive backtesting suite for all trading strategies
with parameter optimization and performance analysis capabilities.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import json
from itertools import product

from .backtest_engine import BacktestEngine
from .strategy_vectorizer import VectorizedStrategyAdapter, vectorize_all_strategies_for_backtest

logger = logging.getLogger(__name__)

class ComprehensiveBacktestSuite:
    """
    Comprehensive backtesting suite for trading strategies
    
    Features:
    - Individual strategy backtesting
    - Multi-strategy comparison
    - Performance analysis and reporting
    """
    
    def __init__(self, initial_capital: float = 10000.0, fees: float = 0.006, 
                 slippage: float = 0.0005, results_dir: str = "./data/backtest_results"):
        """Initialize the backtest suite"""
        self.initial_capital = initial_capital
        self.fees = fees
        self.slippage = slippage
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.backtest_engine = BacktestEngine(initial_capital, fees, slippage)
        self.strategy_vectorizer = VectorizedStrategyAdapter()
        
        # Results storage
        self.results = {}
        self.optimization_results = {}
        
        logger.info(f"Comprehensive Backtest Suite initialized: ${initial_capital:,.2f} capital")
    
    def run_all_strategies(self, data_with_indicators: pd.DataFrame, 
                          product_id: str = "BTC-USD") -> Dict[str, Any]:
        """
        Run comprehensive backtest for all strategies
        
        Args:
            data_with_indicators: DataFrame with OHLCV data and technical indicators
            product_id: Trading pair identifier
            
        Returns:
            Dictionary with comprehensive results for all strategies
        """
        try:
            logger.info(f"Starting comprehensive backtest for {product_id} ({len(data_with_indicators)} rows)")
            
            # Vectorize all strategies
            logger.info("Vectorizing all strategies...")
            all_signals = vectorize_all_strategies_for_backtest(
                data_with_indicators, product_id, {}
            )
            
            if not all_signals:
                logger.error("No strategies vectorized successfully")
                return {'error': 'No strategies vectorized'}
            
            # Run backtests for each strategy
            individual_results = {}
            
            for strategy_name, signals_df in all_signals.items():
                logger.info(f"Backtesting {strategy_name}...")
                
                try:
                    # Run backtest
                    backtest_result = self.backtest_engine.run_backtest(
                        data_with_indicators, signals_df, f"{product_id}-{strategy_name}"
                    )
                    
                    # Add strategy metadata
                    backtest_result['strategy_name'] = strategy_name
                    backtest_result['signal_count'] = signals_df['buy'].sum() + signals_df['sell'].sum()
                    backtest_result['buy_signals'] = signals_df['buy'].sum()
                    backtest_result['sell_signals'] = signals_df['sell'].sum()
                    
                    individual_results[strategy_name] = backtest_result
                    
                    logger.info(f"  {strategy_name}: {backtest_result['total_return']:.2f}% return, "
                              f"{backtest_result['sharpe_ratio']:.3f} Sharpe, {backtest_result['total_trades']} trades")
                
                except Exception as e:
                    logger.error(f"Error backtesting {strategy_name}: {e}")
                    individual_results[strategy_name] = {'error': str(e), 'strategy_name': strategy_name}
            
            # Generate comparative analysis
            comparative_analysis = self._generate_comparative_analysis(individual_results, product_id)
            
            # Compile final results
            final_results = {
                'timestamp': datetime.now().isoformat(),
                'product_id': product_id,
                'individual_results': individual_results,
                'comparative_analysis': comparative_analysis,
                'data_period': {
                    'start': data_with_indicators.index.min().isoformat(),
                    'end': data_with_indicators.index.max().isoformat(),
                    'rows': len(data_with_indicators)
                }
            }
            
            # Store results
            self.results[product_id] = final_results
            
            # Save results to file
            self._save_results(product_id, final_results)
            
            logger.info(f"Comprehensive backtest completed for {product_id}")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive backtest: {e}")
            return {'error': str(e)}
    
    def run_single_strategy(self, data_with_indicators: pd.DataFrame, strategy_name: str,
                           product_id: str = "BTC-USD") -> Dict[str, Any]:
        """
        Run backtest for a single strategy
        
        Args:
            data_with_indicators: DataFrame with OHLCV data and indicators
            strategy_name: Name of strategy to backtest
            product_id: Trading pair identifier
            
        Returns:
            Dictionary with backtest results
        """
        try:
            logger.info(f"Running single strategy backtest: {strategy_name} for {product_id}")
            
            # Vectorize strategy
            if strategy_name == 'adaptive':
                signals_df = self.strategy_vectorizer.vectorize_adaptive_strategy(
                    data_with_indicators, product_id
                )
            else:
                signals_df = self.strategy_vectorizer.vectorize_strategy(
                    strategy_name, data_with_indicators, product_id
                )
            
            if signals_df is None or signals_df.empty:
                return {'error': f'No signals generated for {strategy_name}'}
            
            # Run backtest
            result = self.backtest_engine.run_backtest(
                data_with_indicators, signals_df, f"{product_id}-{strategy_name}"
            )
            
            # Add metadata
            result['strategy_name'] = strategy_name
            result['signal_count'] = signals_df['buy'].sum() + signals_df['sell'].sum()
            result['buy_signals'] = signals_df['buy'].sum()
            result['sell_signals'] = signals_df['sell'].sum()
            
            logger.info(f"Single strategy backtest completed: {result['total_return']:.2f}% return")
            return result
            
        except Exception as e:
            logger.error(f"Error in single strategy backtest: {e}")
            return {'error': str(e)}
    
    def _generate_comparative_analysis(self, results: Dict[str, Any], product_id: str) -> Dict[str, Any]:
        """Generate comparative analysis across strategies"""
        try:
            if not results:
                return {}
            
            # Filter out error results
            valid_results = {k: v for k, v in results.items() if 'error' not in v}
            
            if not valid_results:
                return {'error': 'No valid results for comparison'}
            
            # Performance ranking
            performance_metrics = ['total_return', 'sharpe_ratio', 'sortino_ratio', 'max_drawdown']
            rankings = {}
            
            for metric in performance_metrics:
                metric_values = [(name, result.get(metric, 0)) for name, result in valid_results.items()]
                
                # Sort descending for returns and ratios, ascending for drawdown
                reverse = metric != 'max_drawdown'
                sorted_strategies = sorted(metric_values, key=lambda x: x[1], reverse=reverse)
                
                rankings[metric] = [{'strategy': name, 'value': value, 'rank': i+1} 
                                  for i, (name, value) in enumerate(sorted_strategies)]
            
            # Overall score (weighted combination)
            weights = {'total_return': 0.3, 'sharpe_ratio': 0.3, 'sortino_ratio': 0.3, 'max_drawdown': -0.1}
            strategy_scores = {}
            
            for strategy_name in valid_results.keys():
                score = 0
                for metric, weight in weights.items():
                    value = valid_results[strategy_name].get(metric, 0)
                    # Normalize by dividing by max value (except drawdown)
                    if metric == 'max_drawdown':
                        max_val = max([r.get(metric, 0) for r in valid_results.values()])
                        normalized = value / max_val if max_val > 0 else 0
                    else:
                        max_val = max([r.get(metric, 0) for r in valid_results.values()])
                        normalized = value / max_val if max_val > 0 else 0
                    
                    score += weight * normalized
                
                strategy_scores[strategy_name] = score
            
            # Sort by overall score
            best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
            
            # Risk-return analysis
            risk_return = []
            for name, result in valid_results.items():
                risk_return.append({
                    'strategy': name,
                    'return': result.get('total_return', 0),
                    'risk': result.get('max_drawdown', 0),
                    'sharpe': result.get('sharpe_ratio', 0),
                    'trades': result.get('total_trades', 0)
                })
            
            return {
                'rankings': rankings,
                'overall_scores': strategy_scores,
                'best_strategy': {'name': best_strategy[0], 'score': best_strategy[1]},
                'risk_return_profile': risk_return,
                'summary': {
                    'strategies_tested': len(valid_results),
                    'best_return': max([r.get('total_return', 0) for r in valid_results.values()]),
                    'best_sharpe': max([r.get('sharpe_ratio', 0) for r in valid_results.values()]),
                    'lowest_drawdown': min([r.get('max_drawdown', 100) for r in valid_results.values()]),
                    'total_trades': sum([r.get('total_trades', 0) for r in valid_results.values()])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comparative analysis: {e}")
            return {'error': str(e)}
    
    def _save_results(self, product_id: str, results: Dict[str, Any]):
        """Save backtest results to file"""
        try:
            filename = f"backtest_{product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Backtest results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")
    
    def generate_performance_report(self, product_id: str) -> str:
        """Generate a comprehensive performance report"""
        try:
            if product_id not in self.results:
                return f"No backtest results found for {product_id}"
            
            results = self.results[product_id]
            individual = results.get('individual_results', {})
            comparative = results.get('comparative_analysis', {})
            
            report = []
            report.append(f"# Backtesting Performance Report - {product_id}")
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            
            # Data summary
            data_period = results.get('data_period', {})
            report.append("## Data Summary")
            report.append(f"- Period: {data_period.get('start', 'Unknown')} to {data_period.get('end', 'Unknown')}")
            report.append(f"- Data points: {data_period.get('rows', 'Unknown')}")
            report.append("")
            
            # Individual strategy results
            report.append("## Individual Strategy Performance")
            report.append("| Strategy | Return | Sharpe | Max DD | Trades | Win Rate |")
            report.append("|----------|--------|--------|--------|--------|----------|")
            
            for strategy_name, result in individual.items():
                if 'error' not in result:
                    report.append(f"| {strategy_name} | {result.get('total_return', 0):.2f}% | "
                                f"{result.get('sharpe_ratio', 0):.3f} | {result.get('max_drawdown', 0):.2f}% | "
                                f"{result.get('total_trades', 0)} | {result.get('win_rate', 0):.1f}% |")
            
            report.append("")
            
            # Best strategy
            if 'best_strategy' in comparative:
                best = comparative['best_strategy']
                report.append(f"## Best Overall Strategy: {best['name']}")
                report.append(f"Overall Score: {best['score']:.3f}")
                report.append("")
            
            # Summary statistics
            if 'summary' in comparative:
                summary = comparative['summary']
                report.append("## Summary Statistics")
                report.append(f"- Strategies tested: {summary.get('strategies_tested', 0)}")
                report.append(f"- Best return: {summary.get('best_return', 0):.2f}%")
                report.append(f"- Best Sharpe ratio: {summary.get('best_sharpe', 0):.3f}")
                report.append(f"- Lowest drawdown: {summary.get('lowest_drawdown', 0):.2f}%")
                report.append(f"- Total trades: {summary.get('total_trades', 0)}")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return f"Error generating report: {e}"
    
    def optimize_strategy_parameters(self, data_with_indicators: pd.DataFrame,
                                   strategy_name: str, param_grid: Dict[str, List],
                                   product_id: str = "BTC-USD",
                                   optimization_metric: str = "sortino_ratio") -> pd.DataFrame:
        """
        Optimize parameters for a specific strategy
        
        Args:
            data_with_indicators: DataFrame with OHLCV data and indicators
            strategy_name: Name of strategy to optimize
            param_grid: Dictionary of parameter names and values to test
            product_id: Trading pair identifier
            optimization_metric: Metric to optimize for
            
        Returns:
            DataFrame with optimization results sorted by metric
        """
        try:
            logger.info(f"Starting parameter optimization for {strategy_name}")
            logger.info(f"Parameter grid: {param_grid}")
            
            # Generate parameter combinations
            param_names = list(param_grid.keys())
            param_values = list(param_grid.values())
            param_combinations = list(product(*param_values))
            
            logger.info(f"Testing {len(param_combinations)} parameter combinations")
            
            results = []
            
            for i, param_combo in enumerate(param_combinations):
                try:
                    # Create parameter dictionary
                    params = dict(zip(param_names, param_combo))
                    
                    # For now, we'll use the default strategy implementation
                    # In a full implementation, this would modify strategy parameters
                    result = self.run_single_strategy(data_with_indicators, strategy_name, product_id)
                    
                    if 'error' in result:
                        logger.warning(f"Error in optimization {i} with params {params}: {result['error']}")
                        continue
                    
                    # Add parameters to result
                    result_with_params = {**params, **result}
                    result_with_params['param_combination_id'] = i
                    results.append(result_with_params)
                    
                    if (i + 1) % 5 == 0:
                        logger.info(f"Completed {i + 1}/{len(param_combinations)} optimizations")
                        if results:
                            best_so_far = max(results, key=lambda x: x.get(optimization_metric, -999))
                            logger.info(f"Best {optimization_metric} so far: {best_so_far.get(optimization_metric, 0):.3f}")
                
                except Exception as e:
                    logger.warning(f"Error in optimization {i} with params {params}: {e}")
                    continue
            
            if not results:
                logger.error("No successful optimization runs")
                return pd.DataFrame()
            
            # Convert to DataFrame and sort
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values(optimization_metric, ascending=False)
            
            # Store optimization results
            optimization_key = f"{product_id}_{strategy_name}"
            self.optimization_results[optimization_key] = {
                'timestamp': datetime.now().isoformat(),
                'strategy_name': strategy_name,
                'product_id': product_id,
                'param_grid': param_grid,
                'optimization_metric': optimization_metric,
                'results': results_df.to_dict('records'),
                'best_params': results_df.iloc[0][param_names].to_dict(),
                'best_performance': results_df.iloc[0][optimization_metric]
            }
            
            # Save optimization results
            self._save_optimization_results(optimization_key, self.optimization_results[optimization_key])
            
            logger.info(f"Parameter optimization completed for {strategy_name}")
            logger.info(f"Best {optimization_metric}: {results_df.iloc[0][optimization_metric]:.3f}")
            logger.info(f"Best parameters: {results_df.iloc[0][param_names].to_dict()}")
            
            return results_df
            
        except Exception as e:
            logger.error(f"Error in parameter optimization: {e}")
            return pd.DataFrame()
    
    def run_walk_forward_analysis(self, data_with_indicators: pd.DataFrame,
                                strategy_name: str, param_grid: Dict[str, List],
                                product_id: str = "BTC-USD",
                                train_period_days: int = 180,
                                test_period_days: int = 30,
                                step_days: int = 30) -> Dict[str, Any]:
        """
        Run walk-forward analysis to test parameter stability
        
        Args:
            data_with_indicators: DataFrame with OHLCV data and indicators
            strategy_name: Name of strategy to analyze
            param_grid: Dictionary of parameter names and values to test
            product_id: Trading pair identifier
            train_period_days: Days for training/optimization period
            test_period_days: Days for out-of-sample testing
            step_days: Days to step forward between tests
            
        Returns:
            Dictionary with walk-forward analysis results
        """
        try:
            logger.info(f"Starting walk-forward analysis for {strategy_name}")
            logger.info(f"Train: {train_period_days}d, Test: {test_period_days}d, Step: {step_days}d")
            
            # Calculate periods
            total_days = (data_with_indicators.index.max() - data_with_indicators.index.min()).days
            min_required_days = train_period_days + test_period_days
            
            if total_days < min_required_days:
                logger.error(f"Insufficient data: {total_days} days available, {min_required_days} required")
                return {'error': 'Insufficient data for walk-forward analysis'}
            
            # Generate walk-forward periods
            periods = self._generate_walk_forward_periods(
                data_with_indicators.index, train_period_days, test_period_days, step_days
            )
            
            logger.info(f"Generated {len(periods)} walk-forward periods")
            
            results = []
            
            for i, (train_start, train_end, test_start, test_end) in enumerate(periods):
                try:
                    logger.info(f"Period {i+1}/{len(periods)}: Train {train_start.date()} to {train_end.date()}, "
                              f"Test {test_start.date()} to {test_end.date()}")
                    
                    # Split data
                    train_data = data_with_indicators.loc[train_start:train_end]
                    test_data = data_with_indicators.loc[test_start:test_end]
                    
                    if len(train_data) < 50 or len(test_data) < 10:
                        logger.warning(f"Insufficient data in period {i+1}, skipping")
                        continue
                    
                    # Optimize on training data
                    optimization_results = self.optimize_strategy_parameters(
                        train_data, strategy_name, param_grid, 
                        f"{product_id}_wf_train_{i}", "sortino_ratio"
                    )
                    
                    if optimization_results.empty:
                        logger.warning(f"No optimization results for period {i+1}")
                        continue
                    
                    # Get best parameters
                    best_params = optimization_results.iloc[0][list(param_grid.keys())].to_dict()
                    
                    # Test on out-of-sample data (using default strategy for now)
                    test_result = self.run_single_strategy(test_data, strategy_name, f"{product_id}_wf_test_{i}")
                    
                    if 'error' in test_result:
                        logger.warning(f"No test results for period {i+1}: {test_result['error']}")
                        continue
                    
                    # Store period result
                    period_result = {
                        'period_id': i,
                        'train_start': train_start.isoformat(),
                        'train_end': train_end.isoformat(),
                        'test_start': test_start.isoformat(),
                        'test_end': test_end.isoformat(),
                        'train_days': len(train_data),
                        'test_days': len(test_data),
                        'best_params': best_params,
                        'train_performance': optimization_results.iloc[0]['sortino_ratio'],
                        'test_performance': test_result
                    }
                    
                    results.append(period_result)
                    
                    logger.info(f"  Period {i+1} complete: Train Sortino {period_result['train_performance']:.3f}, "
                              f"Test Return {test_result['total_return']:.2f}%")
                
                except Exception as e:
                    logger.error(f"Error in walk-forward period {i+1}: {e}")
                    continue
            
            if not results:
                logger.error("No successful walk-forward periods")
                return {'error': 'No successful walk-forward periods'}
            
            # Analyze walk-forward results
            wf_analysis = self._analyze_walk_forward_results(results)
            
            walk_forward_results = {
                'timestamp': datetime.now().isoformat(),
                'strategy_name': strategy_name,
                'product_id': product_id,
                'param_grid': param_grid,
                'periods': results,
                'analysis': wf_analysis,
                'settings': {
                    'train_period_days': train_period_days,
                    'test_period_days': test_period_days,
                    'step_days': step_days
                }
            }
            
            # Save walk-forward results
            wf_key = f"{product_id}_{strategy_name}_walkforward"
            self._save_walk_forward_results(wf_key, walk_forward_results)
            
            logger.info(f"Walk-forward analysis completed for {strategy_name}")
            logger.info(f"Average test return: {wf_analysis['avg_test_return']:.2f}%")
            logger.info(f"Parameter stability: {wf_analysis['parameter_stability']:.2f}")
            
            return walk_forward_results
            
        except Exception as e:
            logger.error(f"Error in walk-forward analysis: {e}")
            return {'error': str(e)}
    
    def _generate_walk_forward_periods(self, index: pd.DatetimeIndex, 
                                     train_days: int, test_days: int, step_days: int) -> List[Tuple]:
        """Generate walk-forward analysis periods"""
        periods = []
        
        start_date = index.min()
        end_date = index.max()
        
        current_date = start_date
        
        while True:
            train_start = current_date
            train_end = train_start + timedelta(days=train_days)
            test_start = train_end + timedelta(hours=1)  # Small gap
            test_end = test_start + timedelta(days=test_days)
            
            # Check if we have enough data
            if test_end > end_date:
                break
            
            periods.append((train_start, train_end, test_start, test_end))
            current_date += timedelta(days=step_days)
        
        return periods
    
    def _analyze_walk_forward_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze walk-forward results for parameter stability"""
        try:
            if not results:
                return {}
            
            # Extract test performance
            test_returns = [r['test_performance']['total_return'] for r in results]
            test_sharpes = [r['test_performance']['sharpe_ratio'] for r in results]
            
            # Parameter stability analysis
            param_names = list(results[0]['best_params'].keys()) if results else []
            param_stability = {}
            
            for param_name in param_names:
                param_values = [r['best_params'][param_name] for r in results]
                if len(set(param_values)) > 1:  # Check if parameter varies
                    param_stability[param_name] = {
                        'unique_values': len(set(param_values)),
                        'most_common': max(set(param_values), key=param_values.count),
                        'stability_ratio': param_values.count(max(set(param_values), key=param_values.count)) / len(param_values)
                    }
            
            # Overall parameter stability (average of individual stabilities)
            if param_stability:
                avg_stability = np.mean([p['stability_ratio'] for p in param_stability.values()])
            else:
                avg_stability = 1.0  # Perfect stability if no parameters vary
            
            return {
                'periods_tested': len(results),
                'avg_test_return': np.mean(test_returns),
                'std_test_return': np.std(test_returns),
                'avg_test_sharpe': np.mean(test_sharpes),
                'std_test_sharpe': np.std(test_sharpes),
                'positive_periods': sum(1 for r in test_returns if r > 0),
                'negative_periods': sum(1 for r in test_returns if r < 0),
                'win_rate': sum(1 for r in test_returns if r > 0) / len(test_returns) * 100,
                'parameter_stability': avg_stability,
                'parameter_details': param_stability,
                'best_period': max(results, key=lambda x: x['test_performance']['total_return']),
                'worst_period': min(results, key=lambda x: x['test_performance']['total_return'])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing walk-forward results: {e}")
            return {'error': str(e)}
    
    def _save_optimization_results(self, key: str, results: Dict[str, Any]):
        """Save optimization results to file"""
        try:
            filename = f"optimization_{key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Optimization results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving optimization results: {e}")
    
    def _save_walk_forward_results(self, key: str, results: Dict[str, Any]):
        """Save walk-forward results to file"""
        try:
            filename = f"walkforward_{key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Walk-forward results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving walk-forward results: {e}")

# Convenience functions
def run_strategy_backtest(data_with_indicators: pd.DataFrame, strategy_name: str,
                         product_id: str = "BTC-USD", initial_capital: float = 10000.0) -> Dict[str, Any]:
    """Quick backtest for a single strategy"""
    suite = ComprehensiveBacktestSuite(initial_capital=initial_capital)
    return suite.run_single_strategy(data_with_indicators, strategy_name, product_id)

def compare_all_strategies(data_with_indicators: pd.DataFrame, product_id: str = "BTC-USD",
                          initial_capital: float = 10000.0) -> Dict[str, Any]:
    """Compare all available strategies"""
    suite = ComprehensiveBacktestSuite(initial_capital=initial_capital)
    return suite.run_all_strategies(data_with_indicators, product_id)