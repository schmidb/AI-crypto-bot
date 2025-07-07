"""
Trading Strategies Package
Multi-strategy framework for AI crypto trading bot
"""

from .base_strategy import BaseStrategy, TradingSignal
from .trend_following import TrendFollowingStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy
from .strategy_manager import StrategyManager

__all__ = [
    'BaseStrategy',
    'TradingSignal',
    'TrendFollowingStrategy',
    'MeanReversionStrategy',
    'MomentumStrategy',
    'StrategyManager'
]
