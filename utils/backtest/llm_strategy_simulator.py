"""
LLM Strategy Simulator for Backtesting

This module simulates LLM responses for backtesting without making actual API calls.
It uses rule-based logic that mimics the LLM's decision-making patterns based on
technical indicators and market conditions.
"""

import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class LLMStrategySimulator:
    """
    Simulates LLM trading decisions for backtesting without API calls.
    
    Uses sophisticated rule-based logic that mimics the patterns and decision-making
    style of the actual LLM analyzer based on technical indicators and market conditions.
    """
    
    def __init__(self, trading_style: str = "day_trading", seed: int = 42):
        """
        Initialize the LLM strategy simulator
        
        Args:
            trading_style: Trading style (day_trading, swing_trading, long_term)
            seed: Random seed for consistent simulation results
        """
        self.trading_style = trading_style
        random.seed(seed)
        np.random.seed(seed)
        
        # LLM-like decision patterns based on trading style
        self.style_patterns = {
            "day_trading": {
                "confidence_base": 65,
                "volatility_preference": 0.8,  # Prefers higher volatility
                "trend_sensitivity": 0.9,     # Very sensitive to short-term trends
                "risk_tolerance": 0.7,        # Moderate risk tolerance
                "bb_weight": 0.35,            # Higher weight on Bollinger Bands
                "rsi_weight": 0.35,           # Higher weight on RSI
                "macd_weight": 0.30           # Lower weight on MACD
            },
            "swing_trading": {
                "confidence_base": 70,
                "volatility_preference": 0.6,  # Moderate volatility preference
                "trend_sensitivity": 0.7,     # Moderate trend sensitivity
                "risk_tolerance": 0.6,        # Moderate risk tolerance
                "bb_weight": 0.30,            # Balanced weights
                "rsi_weight": 0.35,
                "macd_weight": 0.35
            },
            "long_term": {
                "confidence_base": 75,
                "volatility_preference": 0.4,  # Lower volatility preference
                "trend_sensitivity": 0.5,     # Less sensitive to short-term moves
                "risk_tolerance": 0.5,        # Lower risk tolerance
                "bb_weight": 0.25,            # Lower weight on short-term indicators
                "rsi_weight": 0.30,
                "macd_weight": 0.45           # Higher weight on trend indicators
            }
        }
        
        self.pattern = self.style_patterns.get(trading_style, self.style_patterns["day_trading"])
        
        # LLM-like reasoning templates
        self.reasoning_templates = {
            "bullish": [
                "Strong upward momentum indicated by technical indicators",
                "Price action showing bullish divergence with volume confirmation",
                "Multiple timeframe analysis suggests continued upward movement",
                "Market structure remains intact with higher highs and higher lows",
                "Technical breakout above key resistance levels"
            ],
            "bearish": [
                "Technical indicators showing weakening momentum",
                "Price action displaying bearish divergence patterns",
                "Multiple resistance levels creating selling pressure",
                "Market structure deteriorating with lower highs and lower lows",
                "Volume patterns suggesting distribution phase"
            ],
            "neutral": [
                "Mixed signals from technical indicators require patience",
                "Market consolidation phase with unclear directional bias",
                "Waiting for clearer technical confirmation before positioning",
                "Current risk-reward ratio not favorable for new positions",
                "Market in transition phase between major moves"
            ]
        }
        
        logger.info(f"🤖 LLM Strategy Simulator initialized for {trading_style}")
    
    def analyze_market(self, market_data: Dict, technical_indicators: Dict, 
                      additional_context: Dict = None) -> Dict[str, Any]:
        """
        Simulate LLM market analysis based on technical indicators
        
        Args:
            market_data: Market data dictionary
            technical_indicators: Technical indicators dictionary
            additional_context: Additional context (unused in simulation)
            
        Returns:
            Dictionary with simulated LLM analysis results
        """
        try:
            # Extract key data
            current_price = float(market_data.get('current_price', market_data.get('price', 50000)))
            product_id = market_data.get('product_id', 'BTC-EUR')
            
            # Analyze technical indicators
            technical_analysis = self._analyze_technical_indicators(technical_indicators)
            
            # Determine market conditions
            market_conditions = self._assess_market_conditions(market_data, technical_indicators)
            
            # Generate trading decision
            decision_data = self._generate_trading_decision(
                technical_analysis, market_conditions, current_price
            )
            
            # Create LLM-style response
            llm_response = {
                'decision': decision_data['action'].upper(),
                'confidence': decision_data['confidence'],
                'reasoning': decision_data['reasoning'],
                'risk_assessment': decision_data['risk_assessment'],
                'technical_indicators': technical_analysis,
                'market_conditions': market_conditions,
                'timeframe_analysis': {
                    'short_term_trend': decision_data['short_term_trend'],
                    'momentum_strength': decision_data['momentum_strength'],
                    'entry_timing': decision_data['entry_timing']
                },
                'simulated': True,  # Mark as simulated
                'trading_style': self.trading_style
            }
            
            logger.debug(f"🤖 LLM Simulation: {decision_data['action'].upper()} "
                        f"({decision_data['confidence']}%) for {product_id}")
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Error in LLM simulation: {e}")
            return self._get_fallback_response()
    
    def _analyze_technical_indicators(self, indicators: Dict) -> Dict[str, Any]:
        """Analyze technical indicators with LLM-like logic"""
        try:
            analysis = {}
            
            # RSI Analysis
            rsi_value = indicators.get('rsi', 50.0)
            if rsi_value < 30:
                rsi_signal = "oversold"
                rsi_strength = "strong"
            elif rsi_value < 45:
                rsi_signal = "oversold"
                rsi_strength = "moderate"
            elif rsi_value > 70:
                rsi_signal = "overbought"
                rsi_strength = "strong"
            elif rsi_value > 55:
                rsi_signal = "overbought"
                rsi_strength = "moderate"
            else:
                rsi_signal = "neutral"
                rsi_strength = "weak"
            
            analysis['rsi'] = {
                'value': rsi_value,
                'signal': rsi_signal,
                'strength': rsi_strength,
                'weight': self.pattern['rsi_weight']
            }
            
            # MACD Analysis
            macd_value = indicators.get('macd', 0.0)
            macd_signal = indicators.get('macd_signal', 0.0)
            macd_histogram = macd_value - macd_signal
            
            if macd_histogram > 0 and macd_value > macd_signal:
                macd_trend = "bullish"
                macd_strength = "strong" if abs(macd_histogram) > 100 else "moderate"
            elif macd_histogram < 0 and macd_value < macd_signal:
                macd_trend = "bearish"
                macd_strength = "strong" if abs(macd_histogram) > 100 else "moderate"
            else:
                macd_trend = "neutral"
                macd_strength = "weak"
            
            analysis['macd'] = {
                'macd_line': macd_value,
                'signal_line': macd_signal,
                'histogram': macd_histogram,
                'signal': macd_trend,
                'strength': macd_strength,
                'weight': self.pattern['macd_weight']
            }
            
            # Bollinger Bands Analysis
            bb_upper = indicators.get('bb_upper', 0)
            bb_lower = indicators.get('bb_lower', 0)
            bb_middle = indicators.get('bb_middle', 0)
            current_price = indicators.get('current_price', bb_middle)
            
            if bb_middle > 0 and bb_upper > bb_lower:
                bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
                bb_width = ((bb_upper - bb_lower) / bb_middle) * 100
                
                if bb_position > 0.8:
                    bb_signal = "breakout_upper"
                    bb_strength = "strong"
                elif bb_position < 0.2:
                    bb_signal = "breakout_lower"
                    bb_strength = "strong"
                elif bb_width < 2:
                    bb_signal = "squeeze"
                    bb_strength = "moderate"
                else:
                    bb_signal = "normal"
                    bb_strength = "weak"
            else:
                bb_signal = "normal"
                bb_strength = "weak"
                bb_position = 0.5
                bb_width = 3.0
            
            analysis['bollinger_bands'] = {
                'signal': bb_signal,
                'position': bb_position,
                'width': bb_width,
                'strength': bb_strength,
                'weight': self.pattern['bb_weight']
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing technical indicators: {e}")
            return self._get_default_technical_analysis()
    
    def _assess_market_conditions(self, market_data: Dict, indicators: Dict) -> Dict[str, Any]:
        """Assess overall market conditions"""
        try:
            # Price changes
            price_changes = market_data.get('price_changes', {})
            change_24h = float(price_changes.get('24h', 0))
            change_5d = float(price_changes.get('5d', 0))
            
            # Trend assessment
            if change_24h > 2 and change_5d > 5:
                trend = "bullish"
            elif change_24h < -2 and change_5d < -5:
                trend = "bearish"
            else:
                trend = "sideways"
            
            # Volatility assessment
            bb_width = indicators.get('bb_width', 3.0)
            if isinstance(bb_width, (int, float)):
                if bb_width > 5:
                    volatility = "high"
                elif bb_width > 3:
                    volatility = "moderate"
                else:
                    volatility = "low"
            else:
                volatility = "moderate"
            
            # Volume assessment (simulated)
            volume_factor = random.uniform(0.8, 1.2)  # Simulate volume variation
            if volume_factor > 1.1:
                volume = "above_average"
            elif volume_factor < 0.9:
                volume = "below_average"
            else:
                volume = "average"
            
            return {
                'trend': trend,
                'volatility': volatility,
                'volume': volume,
                'price_change_24h': change_24h,
                'price_change_5d': change_5d
            }
            
        except Exception as e:
            logger.error(f"Error assessing market conditions: {e}")
            return {
                'trend': 'sideways',
                'volatility': 'moderate',
                'volume': 'average',
                'price_change_24h': 0.0,
                'price_change_5d': 0.0
            }
    
    def _generate_trading_decision(self, technical_analysis: Dict, 
                                 market_conditions: Dict, current_price: float) -> Dict[str, Any]:
        """Generate trading decision based on analysis"""
        try:
            # Calculate weighted scores
            bullish_score = 0
            bearish_score = 0
            
            # RSI contribution
            rsi_data = technical_analysis.get('rsi', {})
            rsi_weight = rsi_data.get('weight', 0.33)
            if rsi_data.get('signal') == 'oversold':
                bullish_score += rsi_weight * (1.0 if rsi_data.get('strength') == 'strong' else 0.6)
            elif rsi_data.get('signal') == 'overbought':
                bearish_score += rsi_weight * (1.0 if rsi_data.get('strength') == 'strong' else 0.6)
            
            # MACD contribution
            macd_data = technical_analysis.get('macd', {})
            macd_weight = macd_data.get('weight', 0.33)
            if macd_data.get('signal') == 'bullish':
                bullish_score += macd_weight * (1.0 if macd_data.get('strength') == 'strong' else 0.6)
            elif macd_data.get('signal') == 'bearish':
                bearish_score += macd_weight * (1.0 if macd_data.get('strength') == 'strong' else 0.6)
            
            # Bollinger Bands contribution
            bb_data = technical_analysis.get('bollinger_bands', {})
            bb_weight = bb_data.get('weight', 0.33)
            if bb_data.get('signal') == 'breakout_lower':
                bullish_score += bb_weight * 0.8
            elif bb_data.get('signal') == 'breakout_upper':
                bearish_score += bb_weight * 0.8
            elif bb_data.get('signal') == 'squeeze':
                # Squeeze adds to whichever direction trend is pointing
                if market_conditions.get('trend') == 'bullish':
                    bullish_score += bb_weight * 0.4
                elif market_conditions.get('trend') == 'bearish':
                    bearish_score += bb_weight * 0.4
            
            # Market conditions adjustment
            trend = market_conditions.get('trend', 'sideways')
            if trend == 'bullish':
                bullish_score += 0.2
            elif trend == 'bearish':
                bearish_score += 0.2
            
            # Volatility adjustment (based on trading style preference)
            volatility = market_conditions.get('volatility', 'moderate')
            volatility_multiplier = 1.0
            if volatility == 'high':
                volatility_multiplier = self.pattern['volatility_preference']
            elif volatility == 'low':
                volatility_multiplier = 1.0 - self.pattern['volatility_preference'] * 0.5
            
            bullish_score *= volatility_multiplier
            bearish_score *= volatility_multiplier
            
            # Determine action and confidence
            score_diff = abs(bullish_score - bearish_score)
            max_score = max(bullish_score, bearish_score)
            
            if bullish_score > bearish_score and score_diff > 0.3:
                action = 'BUY'
                base_confidence = min(85, self.pattern['confidence_base'] + (score_diff * 30))
            elif bearish_score > bullish_score and score_diff > 0.3:
                action = 'SELL'
                base_confidence = min(85, self.pattern['confidence_base'] + (score_diff * 30))
            else:
                action = 'HOLD'
                base_confidence = max(20, 50 - (score_diff * 20))
            
            # Add some randomness to simulate LLM variability
            confidence_noise = random.uniform(-5, 5)
            final_confidence = max(0, min(100, base_confidence + confidence_noise))
            
            # Generate reasoning
            reasoning = self._generate_reasoning(action, technical_analysis, market_conditions)
            
            # Assess risk
            risk_assessment = self._assess_risk(market_conditions, final_confidence)
            
            # Determine additional metrics
            short_term_trend = self._determine_short_term_trend(technical_analysis, market_conditions)
            momentum_strength = self._determine_momentum_strength(technical_analysis)
            entry_timing = self._determine_entry_timing(final_confidence, market_conditions)
            
            return {
                'action': action,
                'confidence': round(final_confidence, 1),
                'reasoning': reasoning,
                'risk_assessment': risk_assessment,
                'short_term_trend': short_term_trend,
                'momentum_strength': momentum_strength,
                'entry_timing': entry_timing,
                'bullish_score': round(bullish_score, 2),
                'bearish_score': round(bearish_score, 2)
            }
            
        except Exception as e:
            logger.error(f"Error generating trading decision: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': [f"Error in decision generation: {str(e)}"],
                'risk_assessment': 'high',
                'short_term_trend': 'neutral',
                'momentum_strength': 'weak',
                'entry_timing': 'poor'
            }
    
    def _generate_reasoning(self, action: str, technical_analysis: Dict, 
                          market_conditions: Dict) -> List[str]:
        """Generate LLM-style reasoning for the decision"""
        try:
            reasoning = []
            
            # Base reasoning based on action
            if action == 'BUY':
                base_reasons = random.sample(self.reasoning_templates['bullish'], 2)
            elif action == 'SELL':
                base_reasons = random.sample(self.reasoning_templates['bearish'], 2)
            else:
                base_reasons = random.sample(self.reasoning_templates['neutral'], 2)
            
            reasoning.extend(base_reasons)
            
            # Add specific technical reasoning
            rsi_data = technical_analysis.get('rsi', {})
            if rsi_data.get('signal') in ['oversold', 'overbought']:
                reasoning.append(f"RSI at {rsi_data.get('value', 50):.1f} indicates {rsi_data.get('signal')} conditions")
            
            macd_data = technical_analysis.get('macd', {})
            if macd_data.get('signal') != 'neutral':
                reasoning.append(f"MACD showing {macd_data.get('signal')} momentum with histogram at {macd_data.get('histogram', 0):.2f}")
            
            bb_data = technical_analysis.get('bollinger_bands', {})
            if bb_data.get('signal') != 'normal':
                reasoning.append(f"Bollinger Bands indicating {bb_data.get('signal')} pattern")
            
            # Add market condition reasoning
            trend = market_conditions.get('trend', 'sideways')
            volatility = market_conditions.get('volatility', 'moderate')
            if trend != 'sideways':
                reasoning.append(f"Market trend remains {trend} with {volatility} volatility environment")
            
            # Limit to 3-4 reasons to match LLM style
            return reasoning[:4]
            
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return ["Technical analysis suggests cautious approach", "Market conditions require careful monitoring"]
    
    def _assess_risk(self, market_conditions: Dict, confidence: float) -> str:
        """Assess risk level based on market conditions and confidence"""
        try:
            volatility = market_conditions.get('volatility', 'moderate')
            trend = market_conditions.get('trend', 'sideways')
            
            risk_score = 0
            
            # Volatility contribution
            if volatility == 'high':
                risk_score += 2
            elif volatility == 'low':
                risk_score -= 1
            
            # Trend contribution
            if trend == 'sideways':
                risk_score += 1
            
            # Confidence contribution
            if confidence < 50:
                risk_score += 2
            elif confidence > 75:
                risk_score -= 1
            
            # Determine risk level with consistent thresholds
            if risk_score >= 3:
                return 'high'
            elif risk_score <= 0:
                return 'low'
            else:
                return 'medium'
                
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return 'medium'
    
    def _determine_short_term_trend(self, technical_analysis: Dict, market_conditions: Dict) -> str:
        """Determine short-term trend"""
        try:
            macd_signal = technical_analysis.get('macd', {}).get('signal', 'neutral')
            market_trend = market_conditions.get('trend', 'sideways')
            
            if macd_signal == 'bullish' or market_trend == 'bullish':
                return 'bullish'
            elif macd_signal == 'bearish' or market_trend == 'bearish':
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Error determining short-term trend: {e}")
            return 'neutral'
    
    def _determine_momentum_strength(self, technical_analysis: Dict) -> str:
        """Determine momentum strength"""
        try:
            macd_strength = technical_analysis.get('macd', {}).get('strength', 'weak')
            rsi_strength = technical_analysis.get('rsi', {}).get('strength', 'weak')
            
            strong_count = sum([1 for strength in [macd_strength, rsi_strength] if strength == 'strong'])
            moderate_count = sum([1 for strength in [macd_strength, rsi_strength] if strength == 'moderate'])
            
            if strong_count >= 1:
                return 'strong'
            elif moderate_count >= 1:
                return 'moderate'
            else:
                return 'weak'
                
        except Exception as e:
            logger.error(f"Error determining momentum strength: {e}")
            return 'weak'
    
    def _determine_entry_timing(self, confidence: float, market_conditions: Dict) -> str:
        """Determine entry timing quality"""
        try:
            volatility = market_conditions.get('volatility', 'moderate')
            
            if confidence > 75 and volatility in ['moderate', 'high']:
                return 'excellent'
            elif confidence > 60:
                return 'good'
            else:
                return 'poor'
                
        except Exception as e:
            logger.error(f"Error determining entry timing: {e}")
            return 'poor'
    
    def _get_default_technical_analysis(self) -> Dict[str, Any]:
        """Get default technical analysis when calculation fails"""
        return {
            'rsi': {
                'value': 50.0,
                'signal': 'neutral',
                'strength': 'weak',
                'weight': self.pattern['rsi_weight']
            },
            'macd': {
                'macd_line': 0.0,
                'signal_line': 0.0,
                'histogram': 0.0,
                'signal': 'neutral',
                'strength': 'weak',
                'weight': self.pattern['macd_weight']
            },
            'bollinger_bands': {
                'signal': 'normal',
                'position': 0.5,
                'width': 3.0,
                'strength': 'weak',
                'weight': self.pattern['bb_weight']
            }
        }
    
    def _get_fallback_response(self) -> Dict[str, Any]:
        """Get fallback response when simulation fails"""
        return {
            'decision': 'HOLD',
            'confidence': 0,
            'reasoning': ['Simulation error occurred', 'Defaulting to safe HOLD position'],
            'risk_assessment': 'high',
            'technical_indicators': self._get_default_technical_analysis(),
            'market_conditions': {
                'trend': 'sideways',
                'volatility': 'moderate',
                'volume': 'average'
            },
            'timeframe_analysis': {
                'short_term_trend': 'neutral',
                'momentum_strength': 'weak',
                'entry_timing': 'poor'
            },
            'simulated': True,
            'trading_style': self.trading_style,
            'error': True
        }

# Convenience function for quick LLM simulation
def simulate_llm_analysis(market_data: Dict, technical_indicators: Dict, 
                         trading_style: str = "day_trading") -> Dict[str, Any]:
    """
    Quick function to simulate LLM analysis
    
    Args:
        market_data: Market data dictionary
        technical_indicators: Technical indicators dictionary
        trading_style: Trading style for simulation
        
    Returns:
        Simulated LLM analysis results
    """
    simulator = LLMStrategySimulator(trading_style=trading_style)
    return simulator.analyze_market(market_data, technical_indicators)