#!/usr/bin/env python3
"""
Strategy Vectorizer Import Bridge

This module provides backward compatibility by importing from the correct location.
"""

# Import from the actual location
from .backtest.strategy_vectorizer import *

# Export all
__all__ = ['VectorizedStrategyAdapter', 'vectorize_all_strategies_for_backtest']
