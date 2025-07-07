"""
Mean Reversion Strategy
Identifies oversold/overbought conditions and trades against the trend
"""

from .base_strategy import BaseStrategy, TradingSignal
from typing import Dict
import numpy as np

class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy using RSI, Bollinger Bands, and price deviation
    """
    
    def __init__(self, config):
        super().__init__("MeanReversion", config)
        
        # Strategy parameters
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.rsi_extreme_oversold = 20
        self.rsi_extreme_overbought = 80
        self.bollinger_threshold = 0.1  # 10% outside bands
        self.min_confidence = 70
        
    def analyze(self, 
                market_data: Dict,
                technical_indicators: Dict,
                portfolio: Dict) -> TradingSignal:
        """Analyze mean reversion opportunities"""
        
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
            
            # Get Bollinger Band data - data collector uses bb_upper, bb_lower, bb_middle keys
            bollinger = {
                'upper': technical_indicators.get('bb_upper', 0),
                'lower': technical_indicators.get('bb_lower', 0),
                'middle': technical_indicators.get('bb_middle', 0)
            }
            
            current_price = float(technical_indicators.get('current_price', 0))
            
            # Calculate mean reversion signals
            rsi_signal = self._analyze_rsi_reversion(rsi)
            bollinger_signal = self._analyze_bollinger_reversion(bollinger, current_price)
            
            # Combine signals
            combined_signal = self._combine_signals(rsi_signal, bollinger_signal)
            
            # Generate trading decision
            action, confidence, reasoning = self._generate_decision(
                combined_signal, rsi, bollinger, current_price
            )
            
            # Position sizing based on signal strength
            position_multiplier = self._calculate_position_size(combined_signal)
            
            return TradingSignal(
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                position_size_multiplier=position_multiplier
            )
            
        except Exception as e:
            self.logger.error(f"Error in mean reversion analysis: {e}")
            return TradingSignal(
                action="HOLD",
                confidence=0,
                reasoning=f"Analysis error: {str(e)}"
            )
    
    def _analyze_rsi_reversion(self, rsi: float) -> Dict:
        """Analyze RSI for mean reversion signals"""
        
        if rsi <= self.rsi_extreme_oversold:
            return {
                "signal": "strong_buy",
                "strength": 0.9,
                "reason": f"RSI extremely oversold at {rsi:.1f}"
            }
        elif rsi <= self.rsi_oversold:
            return {
                "signal": "buy",
                "strength": 0.7,
                "reason": f"RSI oversold at {rsi:.1f}"
            }
        elif rsi >= self.rsi_extreme_overbought:
            return {
                "signal": "strong_sell",
                "strength": 0.9,
                "reason": f"RSI extremely overbought at {rsi:.1f}"
            }
        elif rsi >= self.rsi_overbought:
            return {
                "signal": "sell",
                "strength": 0.7,
                "reason": f"RSI overbought at {rsi:.1f}"
            }
        else:
            return {
                "signal": "neutral",
                "strength": 0.2,
                "reason": f"RSI neutral at {rsi:.1f}"
            }
    
    def _analyze_bollinger_reversion(self, bollinger: Dict, current_price: float) -> Dict:
        """Analyze Bollinger Bands for mean reversion signals"""
        
        if not bollinger or not current_price:
            return {
                "signal": "neutral",
                "strength": 0.0,
                "reason": "No Bollinger Band data"
            }
        
        upper_band = bollinger.get('upper', 0)
        lower_band = bollinger.get('lower', 0)
        middle_band = bollinger.get('middle', 0)
        
        if not all([upper_band, lower_band, middle_band]):
            return {
                "signal": "neutral",
                "strength": 0.0,
                "reason": "Incomplete Bollinger Band data"
            }
        
        # Calculate position relative to bands
        band_width = upper_band - lower_band
        
        # Price below lower band (oversold)
        if current_price < lower_band:
            deviation = (lower_band - current_price) / band_width
            if deviation > self.bollinger_threshold:
                return {
                    "signal": "strong_buy",
                    "strength": min(0.9, 0.6 + deviation * 2),
                    "reason": f"Price {deviation*100:.1f}% below lower Bollinger Band"
                }
            else:
                return {
                    "signal": "buy",
                    "strength": 0.6,
                    "reason": "Price below lower Bollinger Band"
                }
        
        # Price above upper band (overbought)
        elif current_price > upper_band:
            deviation = (current_price - upper_band) / band_width
            if deviation > self.bollinger_threshold:
                return {
                    "signal": "strong_sell",
                    "strength": min(0.9, 0.6 + deviation * 2),
                    "reason": f"Price {deviation*100:.1f}% above upper Bollinger Band"
                }
            else:
                return {
                    "signal": "sell",
                    "strength": 0.6,
                    "reason": "Price above upper Bollinger Band"
                }
        
        # Price near middle band
        else:
            distance_from_middle = abs(current_price - middle_band) / band_width
            return {
                "signal": "neutral",
                "strength": max(0.1, 0.4 - distance_from_middle),
                "reason": f"Price near middle band ({distance_from_middle*100:.1f}% from center)"
            }
    
    def _combine_signals(self, rsi_signal: Dict, bollinger_signal: Dict) -> Dict:
        """Combine RSI and Bollinger signals"""
        
        # Signal mapping
        signal_values = {
            "strong_buy": 2,
            "buy": 1,
            "neutral": 0,
            "sell": -1,
            "strong_sell": -2
        }
        
        rsi_value = signal_values.get(rsi_signal["signal"], 0)
        bollinger_value = signal_values.get(bollinger_signal["signal"], 0)
        
        # Weighted combination (RSI 60%, Bollinger 40%)
        combined_value = (rsi_value * 0.6) + (bollinger_value * 0.4)
        combined_strength = (rsi_signal["strength"] * 0.6) + (bollinger_signal["strength"] * 0.4)
        
        # Determine combined signal
        if combined_value >= 1.5:
            signal = "strong_buy"
        elif combined_value >= 0.5:
            signal = "buy"
        elif combined_value <= -1.5:
            signal = "strong_sell"
        elif combined_value <= -0.5:
            signal = "sell"
        else:
            signal = "neutral"
        
        return {
            "signal": signal,
            "strength": combined_strength,
            "rsi_reason": rsi_signal["reason"],
            "bollinger_reason": bollinger_signal["reason"]
        }
    
    def _generate_decision(self, 
                         combined_signal: Dict,
                         rsi: float,
                         bollinger: Dict,
                         current_price: float) -> tuple:
        """Generate final trading decision"""
        
        signal = combined_signal["signal"]
        strength = combined_signal["strength"]
        
        # Base confidence from signal strength
        base_confidence = strength * 80  # 0-72 base confidence
        
        if signal in ["strong_buy", "buy"]:
            action = "BUY"
            confidence = min(95, base_confidence + 15)
            reasoning = f"Mean reversion BUY signal: {combined_signal['rsi_reason']}, {combined_signal['bollinger_reason']}"
            
        elif signal in ["strong_sell", "sell"]:
            action = "SELL"
            confidence = min(95, base_confidence + 15)
            reasoning = f"Mean reversion SELL signal: {combined_signal['rsi_reason']}, {combined_signal['bollinger_reason']}"
            
        else:
            action = "HOLD"
            confidence = max(20, base_confidence)
            reasoning = f"No clear mean reversion signal: {combined_signal['rsi_reason']}, {combined_signal['bollinger_reason']}"
        
        # Adjust confidence based on signal alignment
        if signal.startswith("strong_"):
            confidence = min(95, confidence + 10)
        
        return action, confidence, reasoning
    
    def _calculate_position_size(self, combined_signal: Dict) -> float:
        """Calculate position size multiplier based on signal strength"""
        
        signal = combined_signal["signal"]
        strength = combined_signal["strength"]
        
        if signal.startswith("strong_"):
            return min(1.5, 0.8 + strength * 0.7)
        elif signal in ["buy", "sell"]:
            return min(1.2, 0.6 + strength * 0.6)
        else:
            return 0.5  # Small position for neutral signals
    
    def get_market_regime_suitability(self, market_regime: str) -> float:
        """Return suitability for market regime"""
        suitability = {
            "bull": 0.6,      # Moderate in bull markets
            "bear": 0.6,      # Moderate in bear markets
            "sideways": 0.9   # Excellent in sideways markets
        }
        return suitability.get(market_regime, 0.5)
    
    def get_risk_level(self) -> str:
        return "medium"
    
    def get_expected_holding_period(self) -> str:
        return "hours"
