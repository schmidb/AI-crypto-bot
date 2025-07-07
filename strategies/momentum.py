"""
Momentum Strategy
Identifies and trades with strong price momentum and breakouts
"""

from .base_strategy import BaseStrategy, TradingSignal
from typing import Dict
import numpy as np

class MomentumStrategy(BaseStrategy):
    """
    Momentum strategy using price velocity, volume, and breakout patterns
    """
    
    def __init__(self, config):
        super().__init__("Momentum", config)
        
        # Strategy parameters
        self.momentum_threshold = 0.02  # 2% price movement
        self.strong_momentum_threshold = 0.05  # 5% price movement
        self.volume_multiplier_threshold = 1.5  # 50% above average volume
        self.rsi_momentum_min = 50  # RSI above 50 for bullish momentum
        self.rsi_momentum_max = 80  # RSI below 80 to avoid extreme overbought
        self.min_confidence = 75
        
    def analyze(self, 
                market_data: Dict,
                technical_indicators: Dict,
                portfolio: Dict) -> TradingSignal:
        """Analyze momentum and generate trading signal"""
        
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
            
            # Ensure market_data is a proper dictionary
            if not isinstance(market_data, dict):
                market_data = {}
            
            # Get price data with safe conversion
            current_price = float(technical_indicators.get('current_price', 0))
            price_changes = market_data.get('price_changes', {})
            
            # Get technical indicators with safe conversion
            rsi = float(technical_indicators.get('rsi', 50))
            macd = technical_indicators.get('macd', {})
            volume_data = market_data.get('volume', {})
            
            # Ensure nested dictionaries are proper dicts
            if not isinstance(macd, dict):
                macd = {}
            if not isinstance(price_changes, dict):
                price_changes = {}
            if not isinstance(volume_data, dict):
                volume_data = {}
            
            # Calculate momentum signals
            price_momentum = self._analyze_price_momentum(price_changes)
            volume_momentum = self._analyze_volume_momentum(volume_data)
            technical_momentum = self._analyze_technical_momentum(rsi, macd)
            
            # Combine momentum signals
            combined_momentum = self._combine_momentum_signals(
                price_momentum, volume_momentum, technical_momentum
            )
            
            # Generate trading decision
            action, confidence, reasoning = self._generate_momentum_decision(
                combined_momentum, rsi, price_changes
            )
            
            # Position sizing based on momentum strength
            position_multiplier = self._calculate_momentum_position_size(combined_momentum)
            
            return TradingSignal(
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                position_size_multiplier=position_multiplier
            )
            
        except Exception as e:
            self.logger.error(f"Error in momentum analysis: {e}")
            return TradingSignal(
                action="HOLD",
                confidence=0,
                reasoning=f"Analysis error: {str(e)}"
            )
    
    def _analyze_price_momentum(self, price_changes: Dict) -> Dict:
        """Analyze price momentum across timeframes"""
        
        if not price_changes:
            return {
                "signal": "neutral",
                "strength": 0.0,
                "direction": "none",
                "reason": "No price change data"
            }
        
        # Get price changes for different timeframes
        change_1h = price_changes.get('1h', 0) / 100  # Convert percentage to decimal
        change_4h = price_changes.get('4h', 0) / 100
        change_24h = price_changes.get('24h', 0) / 100
        
        # Weight recent changes more heavily
        weighted_momentum = (change_1h * 0.5) + (change_4h * 0.3) + (change_24h * 0.2)
        
        # Determine momentum strength and direction
        abs_momentum = abs(weighted_momentum)
        
        if abs_momentum >= self.strong_momentum_threshold:
            strength = min(0.9, 0.6 + (abs_momentum - self.strong_momentum_threshold) * 10)
            signal = "strong"
        elif abs_momentum >= self.momentum_threshold:
            strength = min(0.7, 0.4 + (abs_momentum - self.momentum_threshold) * 10)
            signal = "moderate"
        else:
            strength = abs_momentum * 10  # Scale small movements
            signal = "weak"
        
        direction = "up" if weighted_momentum > 0 else "down" if weighted_momentum < 0 else "none"
        
        return {
            "signal": signal,
            "strength": strength,
            "direction": direction,
            "momentum_value": weighted_momentum,
            "reason": f"Price momentum: 1h={change_1h*100:.1f}%, 4h={change_4h*100:.1f}%, 24h={change_24h*100:.1f}%"
        }
    
    def _analyze_volume_momentum(self, volume_data: Dict) -> Dict:
        """Analyze volume momentum"""
        
        if not volume_data:
            return {
                "signal": "neutral",
                "strength": 0.3,
                "reason": "No volume data available"
            }
        
        current_volume = volume_data.get('current', 0)
        avg_volume = volume_data.get('average', 0)
        
        if not avg_volume or avg_volume == 0:
            return {
                "signal": "neutral",
                "strength": 0.3,
                "reason": "No average volume data"
            }
        
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio >= 2.0:
            return {
                "signal": "strong",
                "strength": min(0.9, 0.6 + (volume_ratio - 2.0) * 0.1),
                "reason": f"Very high volume: {volume_ratio:.1f}x average"
            }
        elif volume_ratio >= self.volume_multiplier_threshold:
            return {
                "signal": "moderate",
                "strength": 0.6 + (volume_ratio - self.volume_multiplier_threshold) * 0.2,
                "reason": f"High volume: {volume_ratio:.1f}x average"
            }
        elif volume_ratio >= 0.8:
            return {
                "signal": "normal",
                "strength": 0.4,
                "reason": f"Normal volume: {volume_ratio:.1f}x average"
            }
        else:
            return {
                "signal": "low",
                "strength": 0.2,
                "reason": f"Low volume: {volume_ratio:.1f}x average"
            }
    
    def _analyze_technical_momentum(self, rsi: float, macd: Dict) -> Dict:
        """Analyze technical momentum indicators"""
        
        momentum_signals = []
        reasons = []
        
        # RSI momentum
        if 50 <= rsi <= 80:
            rsi_strength = min(0.8, (rsi - 50) / 30 * 0.8)
            momentum_signals.append(rsi_strength)
            reasons.append(f"RSI bullish momentum at {rsi:.1f}")
        elif 20 <= rsi <= 50:
            rsi_strength = min(0.8, (50 - rsi) / 30 * 0.8)
            momentum_signals.append(-rsi_strength)
            reasons.append(f"RSI bearish momentum at {rsi:.1f}")
        else:
            momentum_signals.append(0)
            reasons.append(f"RSI extreme at {rsi:.1f}")
        
        # MACD momentum
        if macd:
            histogram = macd.get('histogram', 0)
            macd_line = macd.get('macd', 0)
            signal_line = macd.get('signal', 0)
            
            # MACD histogram momentum
            if abs(histogram) > 0.5:
                macd_strength = min(0.8, abs(histogram) * 0.8)
                momentum_signals.append(macd_strength if histogram > 0 else -macd_strength)
                reasons.append(f"Strong MACD momentum (histogram: {histogram:.2f})")
            elif abs(histogram) > 0.1:
                macd_strength = abs(histogram) * 2
                momentum_signals.append(macd_strength if histogram > 0 else -macd_strength)
                reasons.append(f"Moderate MACD momentum (histogram: {histogram:.2f})")
            else:
                momentum_signals.append(0)
                reasons.append(f"Weak MACD momentum (histogram: {histogram:.2f})")
        
        # Combine technical signals
        if momentum_signals:
            avg_momentum = np.mean(momentum_signals)
            strength = min(0.9, abs(avg_momentum))
            
            if avg_momentum > 0.3:
                signal = "bullish"
            elif avg_momentum < -0.3:
                signal = "bearish"
            else:
                signal = "neutral"
        else:
            signal = "neutral"
            strength = 0.2
            reasons = ["No technical momentum data"]
        
        return {
            "signal": signal,
            "strength": strength,
            "reason": "; ".join(reasons)
        }
    
    def _combine_momentum_signals(self, 
                                price_momentum: Dict,
                                volume_momentum: Dict,
                                technical_momentum: Dict) -> Dict:
        """Combine all momentum signals"""
        
        # Price momentum (40% weight)
        price_score = 0
        if price_momentum["direction"] == "up":
            price_score = price_momentum["strength"]
        elif price_momentum["direction"] == "down":
            price_score = -price_momentum["strength"]
        
        # Volume momentum (30% weight) - amplifies price momentum
        volume_multiplier = 1.0
        if volume_momentum["signal"] in ["strong", "moderate"]:
            volume_multiplier = 1.0 + (volume_momentum["strength"] - 0.4)
        
        # Technical momentum (30% weight)
        technical_score = 0
        if technical_momentum["signal"] == "bullish":
            technical_score = technical_momentum["strength"]
        elif technical_momentum["signal"] == "bearish":
            technical_score = -technical_momentum["strength"]
        
        # Combine scores
        combined_score = (price_score * 0.4 * volume_multiplier) + (technical_score * 0.3)
        combined_strength = min(0.95, abs(combined_score))
        
        # Determine overall signal
        if combined_score > 0.4:
            signal = "strong_bullish"
        elif combined_score > 0.2:
            signal = "bullish"
        elif combined_score < -0.4:
            signal = "strong_bearish"
        elif combined_score < -0.2:
            signal = "bearish"
        else:
            signal = "neutral"
        
        return {
            "signal": signal,
            "strength": combined_strength,
            "score": combined_score,
            "price_reason": price_momentum["reason"],
            "volume_reason": volume_momentum["reason"],
            "technical_reason": technical_momentum["reason"]
        }
    
    def _generate_momentum_decision(self, 
                                  combined_momentum: Dict,
                                  rsi: float,
                                  price_changes: Dict) -> tuple:
        """Generate final momentum trading decision"""
        
        signal = combined_momentum["signal"]
        strength = combined_momentum["strength"]
        
        # Base confidence from momentum strength
        base_confidence = strength * 70 + 20  # 20-86.5 range
        
        if signal in ["strong_bullish", "bullish"]:
            # Check for overbought conditions
            if rsi > 85:
                action = "HOLD"
                confidence = base_confidence * 0.6
                reasoning = f"Bullish momentum but RSI overbought ({rsi:.1f})"
            else:
                action = "BUY"
                confidence = min(95, base_confidence + (15 if signal == "strong_bullish" else 10))
                reasoning = f"Strong bullish momentum detected: {combined_momentum['price_reason']}"
                
        elif signal in ["strong_bearish", "bearish"]:
            # Check for oversold conditions
            if rsi < 15:
                action = "HOLD"
                confidence = base_confidence * 0.6
                reasoning = f"Bearish momentum but RSI oversold ({rsi:.1f})"
            else:
                action = "SELL"
                confidence = min(95, base_confidence + (15 if signal == "strong_bearish" else 10))
                reasoning = f"Strong bearish momentum detected: {combined_momentum['price_reason']}"
                
        else:
            action = "HOLD"
            confidence = max(25, base_confidence * 0.7)
            reasoning = f"Weak momentum: {combined_momentum['price_reason']}"
        
        return action, confidence, reasoning
    
    def _calculate_momentum_position_size(self, combined_momentum: Dict) -> float:
        """Calculate position size based on momentum strength"""
        
        signal = combined_momentum["signal"]
        strength = combined_momentum["strength"]
        
        if signal.startswith("strong_"):
            return min(1.8, 1.0 + strength * 0.8)  # Up to 1.8x for strong momentum
        elif signal in ["bullish", "bearish"]:
            return min(1.4, 0.8 + strength * 0.6)  # Up to 1.4x for moderate momentum
        else:
            return 0.6  # Reduced position for weak momentum
    
    def get_market_regime_suitability(self, market_regime: str) -> float:
        """Return suitability for market regime"""
        suitability = {
            "bull": 0.9,      # Excellent in bull markets
            "bear": 0.7,      # Good in bear markets (momentum down)
            "sideways": 0.4   # Poor in sideways markets
        }
        return suitability.get(market_regime, 0.5)
    
    def get_risk_level(self) -> str:
        return "high"
    
    def get_expected_holding_period(self) -> str:
        return "minutes"
