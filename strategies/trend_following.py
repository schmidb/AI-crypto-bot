"""
Trend Following Strategy
Identifies and follows strong market trends using multiple timeframes
"""

from .base_strategy import BaseStrategy, TradingSignal
from typing import Dict, List
import numpy as np

class TrendFollowingStrategy(BaseStrategy):
    """
    Trend following strategy using moving averages and momentum indicators
    """
    
    def __init__(self, config):
        super().__init__("TrendFollowing", config)
        
        # Strategy parameters
        self.fast_ma_period = 10
        self.slow_ma_period = 21
        self.momentum_period = 14
        self.trend_strength_threshold = 0.6
        self.min_confidence = 75
        
    def analyze(self, 
                market_data: Dict,
                technical_indicators: Dict,
                portfolio: Dict) -> TradingSignal:
        """Analyze trend and generate trading signal"""
        
        try:
            # Convert numpy types to Python types for safety
            if hasattr(technical_indicators, 'item'):
                # Handle case where technical_indicators is a numpy scalar
                self.logger.warning("Received numpy scalar instead of dict for technical_indicators")
                return TradingSignal(
                    action="HOLD",
                    confidence=50,
                    reasoning="Invalid technical indicators format"
                )
            
            # Ensure we have a proper dictionary
            if not isinstance(technical_indicators, dict):
                self.logger.warning(f"Invalid technical_indicators type: {type(technical_indicators)}")
                return TradingSignal(
                    action="HOLD",
                    confidence=50,
                    reasoning="Invalid technical indicators format"
                )
            
            # Get technical indicators with safe conversion
            rsi = float(technical_indicators.get('rsi', 50))
            macd = technical_indicators.get('macd', {})
            
            # Get Bollinger Band data - data collector uses bb_upper, bb_lower, bb_middle keys
            bollinger = {
                'upper': technical_indicators.get('bb_upper', 0),
                'lower': technical_indicators.get('bb_lower', 0),
                'middle': technical_indicators.get('bb_middle', 0)
            }
            
            # Ensure macd is a dictionary
            if not isinstance(macd, dict):
                macd = {}
            
            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(technical_indicators)
            trend_direction = self._determine_trend_direction(technical_indicators)
            
            # Generate base confidence
            base_confidence = self._calculate_base_confidence(
                trend_strength, trend_direction, technical_indicators
            )
            
            # Determine action
            if trend_direction == "up" and trend_strength > self.trend_strength_threshold:
                if rsi < 70:  # Not overbought
                    action = "BUY"
                    confidence = min(95, base_confidence + 10)
                    reasoning = f"Strong uptrend detected (strength: {trend_strength:.2f}), RSI not overbought"
                else:
                    action = "HOLD"
                    confidence = base_confidence * 0.7
                    reasoning = f"Uptrend detected but RSI overbought ({rsi:.1f})"
                    
            elif trend_direction == "down" and trend_strength > self.trend_strength_threshold:
                if rsi > 30:  # Not oversold
                    action = "SELL"
                    confidence = min(95, base_confidence + 10)
                    reasoning = f"Strong downtrend detected (strength: {trend_strength:.2f}), RSI not oversold"
                else:
                    action = "HOLD"
                    confidence = base_confidence * 0.7
                    reasoning = f"Downtrend detected but RSI oversold ({rsi:.1f})"
                    
            else:
                action = "HOLD"
                confidence = max(30, base_confidence * 0.5)
                reasoning = f"Weak trend (strength: {trend_strength:.2f}) or unclear direction"
            
            # Position sizing based on trend strength
            position_multiplier = min(1.5, 0.5 + trend_strength)
            
            return TradingSignal(
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                position_size_multiplier=position_multiplier
            )
            
        except Exception as e:
            self.logger.error(f"Error in trend following analysis: {e}")
            return TradingSignal(
                action="HOLD",
                confidence=0,
                reasoning=f"Analysis error: {str(e)}"
            )
    
    def _calculate_trend_strength(self, indicators: Dict) -> float:
        """Calculate trend strength (0-1)"""
        
        strength_factors = []
        
        # MACD trend strength - access individual MACD values from data collector
        macd_line = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_histogram = indicators.get('macd_histogram', 0)
        
        # Strong MACD signal based on histogram
        if abs(macd_histogram) > 0.5:
            strength_factors.append(0.8)
        elif abs(macd_histogram) > 0.2:
            strength_factors.append(0.6)
        else:
            strength_factors.append(0.3)
        
        # RSI momentum strength
        rsi = indicators.get('rsi', 50)
        if rsi > 60 or rsi < 40:
            strength_factors.append(0.7)
        elif rsi > 55 or rsi < 45:
            strength_factors.append(0.5)
        else:
            strength_factors.append(0.2)
        
        # Bollinger Band position - access individual BB values
        current_price = indicators.get('current_price', 0)
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        bb_middle = indicators.get('bb_middle', 0)
        
        if current_price and bb_upper and bb_lower:
                # Position relative to bands
                band_position = (current_price - bb_lower) / (bb_upper - bb_lower)
                if band_position > 0.8 or band_position < 0.2:
                    strength_factors.append(0.8)
                elif band_position > 0.7 or band_position < 0.3:
                    strength_factors.append(0.6)
                else:
                    strength_factors.append(0.4)
        
        # Average strength
        return np.mean(strength_factors) if strength_factors else 0.3
    
    def _determine_trend_direction(self, indicators: Dict) -> str:
        """Determine trend direction"""
        
        direction_signals = []
        
        # MACD direction - access individual MACD values from data collector
        macd_histogram = indicators.get('macd_histogram', 0)
        if macd_histogram > 0.1:
            direction_signals.append(1)  # Up
        elif macd_histogram < -0.1:
            direction_signals.append(-1)  # Down
        else:
            direction_signals.append(0)  # Neutral
        
        # RSI direction
        rsi = indicators.get('rsi', 50)
        if rsi > 55:
            direction_signals.append(1)
        elif rsi < 45:
            direction_signals.append(-1)
        else:
            direction_signals.append(0)
        
        # Price vs Bollinger middle
        current_price = indicators.get('current_price', 0)
        bb_middle = indicators.get('bb_middle', 0)
        if current_price and bb_middle:
            if current_price > bb_middle * 1.01:
                direction_signals.append(1)
            elif current_price < bb_middle * 0.99:
                direction_signals.append(-1)
            else:
                direction_signals.append(0)
        
        # Determine overall direction
        avg_signal = np.mean(direction_signals) if direction_signals else 0
        
        if avg_signal > 0.3:
            return "up"
        elif avg_signal < -0.3:
            return "down"
        else:
            return "sideways"
    
    def _calculate_base_confidence(self, 
                                 trend_strength: float,
                                 trend_direction: str,
                                 indicators: Dict) -> float:
        """Calculate base confidence level"""
        
        # Start with trend strength
        confidence = trend_strength * 60  # 0-60 base
        
        # Add direction clarity bonus
        if trend_direction in ["up", "down"]:
            confidence += 20
        
        # Technical indicator alignment bonus
        rsi = indicators.get('rsi', 50)
        macd_histogram = indicators.get('macd_histogram', 0)
        
        alignment_score = 0
        
        # RSI alignment
        if trend_direction == "up" and 40 < rsi < 70:
            alignment_score += 1
        elif trend_direction == "down" and 30 < rsi < 60:
            alignment_score += 1
        
        # MACD alignment
        if trend_direction == "up" and macd_histogram > 0:
            alignment_score += 1
        elif trend_direction == "down" and macd_histogram < 0:
            alignment_score += 1
        
        # Alignment bonus
        confidence += alignment_score * 5
        
        return min(95, max(20, confidence))
    
    def get_market_regime_suitability(self, market_regime: str) -> float:
        """Return suitability for market regime"""
        suitability = {
            "bull": 0.9,      # Excellent in bull markets
            "bear": 0.8,      # Good in bear markets (short selling)
            "sideways": 0.3   # Poor in sideways markets
        }
        return suitability.get(market_regime, 0.5)
    
    def get_risk_level(self) -> str:
        return "medium"
    
    def get_expected_holding_period(self) -> str:
        return "hours"
