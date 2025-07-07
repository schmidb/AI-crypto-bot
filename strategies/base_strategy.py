"""
Base Strategy Class for Multi-Strategy Trading Framework
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

@dataclass
class TradingSignal:
    """Trading signal with confidence and reasoning"""
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    reasoning: str
    position_size_multiplier: float = 1.0  # Multiplier for position sizing
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, config):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"strategy.{name}")
        self.enabled = True
        self.weight = 1.0  # Strategy weight in ensemble
        
    @abstractmethod
    def analyze(self, 
                market_data: Dict,
                technical_indicators: Dict,
                portfolio: Dict) -> TradingSignal:
        """
        Analyze market conditions and generate trading signal
        
        Args:
            market_data: Current market data (price, volume, etc.)
            technical_indicators: Technical analysis indicators
            portfolio: Current portfolio state
            
        Returns:
            TradingSignal with action, confidence, and reasoning
        """
        pass
    
    @abstractmethod
    def get_market_regime_suitability(self, market_regime: str) -> float:
        """
        Return suitability score (0-1) for given market regime
        
        Args:
            market_regime: "bull", "bear", "sideways"
            
        Returns:
            Suitability score (0-1)
        """
        pass
    
    def is_applicable(self, 
                     market_data: Dict,
                     portfolio: Dict) -> bool:
        """
        Check if strategy is applicable in current conditions
        
        Returns:
            True if strategy should be used
        """
        return self.enabled
    
    def get_risk_level(self) -> str:
        """Get strategy risk level"""
        return "medium"
    
    def get_expected_holding_period(self) -> str:
        """Get expected holding period"""
        return "hours"
