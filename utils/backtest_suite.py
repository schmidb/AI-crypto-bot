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
    return suite.run_single_strategy(strategy_name, data)

def compare_all_strategies(data: dict, **kwargs):
    """Compare all available strategies"""
    suite = ComprehensiveBacktestSuite(**kwargs)
    return suite.compare_strategies(data)

# Export main classes and functions
__all__ = [
    'ComprehensiveBacktestSuite',
    'vectorize_all_strategies_for_backtest', 
    'run_strategy_backtest',
    'compare_all_strategies'
]
