#!/usr/bin/env python3
"""
Backtest Suite Import Bridge

This module provides backward compatibility by importing from the correct location.
"""

# Import all classes and functions from the actual backtest suite
from .backtest.backtest_suite import ComprehensiveBacktestSuite
from .backtest.strategy_vectorizer import vectorize_all_strategies_for_backtest

# Import additional functions that might be expected
try:
    from .backtest.backtest_engine import BacktestEngine
except ImportError:
    pass

def run_strategy_backtest(strategy_name: str, data: dict, **kwargs):
    """Run a single strategy backtest"""
    suite = ComprehensiveBacktestSuite(**kwargs)
    # Use the first asset's data for backtesting
    asset_name = list(data.keys())[0]
    data_df = data[asset_name]
    return suite.run_single_strategy(data_df, strategy_name, asset_name)

def compare_all_strategies(data: dict, **kwargs):
    """Compare all available strategies"""
    suite = ComprehensiveBacktestSuite(**kwargs)
    # Use the first asset's data for comparison
    asset_name = list(data.keys())[0]
    data_df = data[asset_name]
    return suite.run_all_strategies(data_df, asset_name)

# Export main classes and functions
__all__ = [
    'ComprehensiveBacktestSuite',
    'vectorize_all_strategies_for_backtest', 
    'run_strategy_backtest',
    'compare_all_strategies'
]
