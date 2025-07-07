"""
Strategy Manager
Coordinates multiple trading strategies and selects the best signals
"""

import logging
from typing import Dict, List, Optional
from .base_strategy import BaseStrategy, TradingSignal
from .trend_following import TrendFollowingStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy

class StrategyManager:
    """
    Manages multiple trading strategies and combines their signals
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize strategies
        self.strategies = {
            'trend_following': TrendFollowingStrategy(config),
            'mean_reversion': MeanReversionStrategy(config),
            'momentum': MomentumStrategy(config)
        }
        
        # Strategy weights (can be adjusted based on market conditions)
        self.strategy_weights = {
            'trend_following': 0.4,
            'mean_reversion': 0.3,
            'momentum': 0.3
        }
        
        # Market regime detection
        self.current_market_regime = "sideways"  # bull, bear, sideways
        
    def analyze_all_strategies(self, 
                             market_data: Dict,
                             technical_indicators: Dict,
                             portfolio: Dict) -> Dict[str, TradingSignal]:
        """Run analysis on all strategies"""
        
        strategy_signals = {}
        
        for name, strategy in self.strategies.items():
            try:
                signal = strategy.analyze(market_data, technical_indicators, portfolio)
                strategy_signals[name] = signal
                
                self.logger.debug(f"{name} strategy: {signal.action} "
                                f"(confidence: {signal.confidence:.1f}%)")
                
            except Exception as e:
                self.logger.error(f"Error in {name} strategy: {e}")
                strategy_signals[name] = TradingSignal(
                    action="HOLD",
                    confidence=0,
                    reasoning=f"Strategy error: {str(e)}"
                )
        
        return strategy_signals
    
    def get_combined_signal(self, 
                          market_data: Dict,
                          technical_indicators: Dict,
                          portfolio: Dict) -> TradingSignal:
        """Get combined signal from all strategies"""
        
        # Validate inputs
        if not isinstance(technical_indicators, dict):
            self.logger.error(f"Invalid technical_indicators type: {type(technical_indicators)}, "
                            f"value: {technical_indicators}")
            return TradingSignal(
                action="HOLD",
                confidence=0,
                reasoning="Invalid technical indicators format"
            )
        
        if not isinstance(market_data, dict):
            self.logger.error(f"Invalid market_data type: {type(market_data)}")
            return TradingSignal(
                action="HOLD",
                confidence=0,
                reasoning="Invalid market data format"
            )
        
        # Get signals from all strategies
        strategy_signals = self.analyze_all_strategies(
            market_data, technical_indicators, portfolio
        )
        
        # Update market regime
        self._update_market_regime(technical_indicators, market_data)
        
        # Adjust strategy weights based on market regime
        adjusted_weights = self._adjust_weights_for_market_regime()
        
        # Combine signals
        combined_signal = self._combine_strategy_signals(
            strategy_signals, adjusted_weights
        )
        
        return combined_signal
    
    def _update_market_regime(self, technical_indicators: Dict, market_data: Dict):
        """Update current market regime assessment"""
        
        try:
            # Validate input types
            if not isinstance(technical_indicators, dict):
                self.logger.warning(f"Invalid technical_indicators type: {type(technical_indicators)}, "
                                  f"value: {technical_indicators}")
                self.current_market_regime = "sideways"
                return
                
            if not isinstance(market_data, dict):
                self.logger.warning(f"Invalid market_data type: {type(market_data)}")
                self.current_market_regime = "sideways"
                return
            
            # Get price changes
            price_changes = market_data.get('price_changes', {})
            if not isinstance(price_changes, dict):
                price_changes = {}
                
            change_24h = float(price_changes.get('24h', 0))
            change_5d = float(price_changes.get('5d', 0))
            
            # Get technical indicators with safe conversion
            rsi = float(technical_indicators.get('rsi', 50))
            macd = technical_indicators.get('macd', {})
            if not isinstance(macd, dict):
                macd = {}
            
            # Get Bollinger Band data - data collector uses bb_upper, bb_lower, bb_middle keys
            bollinger = {
                'upper': technical_indicators.get('bb_upper', 0),
                'lower': technical_indicators.get('bb_lower', 0),
                'middle': technical_indicators.get('bb_middle', 0)
            }
            
            # Determine regime based on multiple factors
            regime_score = 0
            
            # Price trend analysis
            if change_24h > 3 and change_5d > 10:
                regime_score += 2  # Strong bullish
            elif change_24h > 1 and change_5d > 5:
                regime_score += 1  # Moderate bullish
            elif change_24h < -3 and change_5d < -10:
                regime_score -= 2  # Strong bearish
            elif change_24h < -1 and change_5d < -5:
                regime_score -= 1  # Moderate bearish
            
            # RSI analysis
            if rsi > 60:
                regime_score += 1
            elif rsi < 40:
                regime_score -= 1
            
            # MACD analysis
            if macd:
                histogram = float(macd.get('histogram', 0))
                if histogram > 0.2:
                    regime_score += 1
                elif histogram < -0.2:
                    regime_score -= 1
            
            # Determine regime
            if regime_score >= 2:
                self.current_market_regime = "bull"
            elif regime_score <= -2:
                self.current_market_regime = "bear"
            else:
                self.current_market_regime = "sideways"
                
            self.logger.debug(f"Market regime updated to: {self.current_market_regime} "
                            f"(score: {regime_score})")
            
        except Exception as e:
            self.logger.error(f"Error updating market regime: {e}")
            self.current_market_regime = "sideways"  # Default to sideways
    
    def _adjust_weights_for_market_regime(self) -> Dict[str, float]:
        """Adjust strategy weights based on current market regime"""
        
        base_weights = self.strategy_weights.copy()
        
        # Get suitability scores for current regime
        suitability_scores = {}
        for name, strategy in self.strategies.items():
            suitability_scores[name] = strategy.get_market_regime_suitability(
                self.current_market_regime
            )
        
        # Adjust weights based on suitability
        adjusted_weights = {}
        total_weighted_suitability = 0
        
        for name in base_weights:
            weighted_suitability = base_weights[name] * suitability_scores[name]
            adjusted_weights[name] = weighted_suitability
            total_weighted_suitability += weighted_suitability
        
        # Normalize weights to sum to 1.0
        if total_weighted_suitability > 0:
            for name in adjusted_weights:
                adjusted_weights[name] /= total_weighted_suitability
        else:
            # Fallback to equal weights
            adjusted_weights = {name: 1/len(base_weights) for name in base_weights}
        
        self.logger.debug(f"Adjusted weights for {self.current_market_regime} market: "
                         f"{adjusted_weights}")
        
        return adjusted_weights
    
    def _combine_strategy_signals(self, 
                                strategy_signals: Dict[str, TradingSignal],
                                weights: Dict[str, float]) -> TradingSignal:
        """Combine multiple strategy signals into one"""
        
        # Convert actions to numeric scores
        action_scores = {"BUY": 1, "HOLD": 0, "SELL": -1}
        
        weighted_score = 0
        weighted_confidence = 0
        total_weight = 0
        position_multipliers = []
        reasoning_parts = []
        
        for strategy_name, signal in strategy_signals.items():
            weight = weights.get(strategy_name, 0)
            
            if weight > 0:
                # Weight the action score by confidence and strategy weight
                action_score = action_scores.get(signal.action, 0)
                confidence_weight = signal.confidence / 100.0
                
                weighted_score += action_score * confidence_weight * weight
                weighted_confidence += signal.confidence * weight
                total_weight += weight
                
                # Collect position multipliers
                position_multipliers.append(signal.position_size_multiplier * weight)
                
                # Collect reasoning
                reasoning_parts.append(f"{strategy_name}: {signal.reasoning}")
        
        # Normalize
        if total_weight > 0:
            final_score = weighted_score / total_weight
            final_confidence = weighted_confidence / total_weight
            final_position_multiplier = sum(position_multipliers)
        else:
            final_score = 0
            final_confidence = 0
            final_position_multiplier = 1.0
        
        # Determine final action
        if final_score > 0.3:
            final_action = "BUY"
        elif final_score < -0.3:
            final_action = "SELL"
        else:
            final_action = "HOLD"
        
        # Adjust confidence based on signal strength
        if abs(final_score) > 0.6:
            final_confidence = min(95, final_confidence * 1.1)
        elif abs(final_score) < 0.2:
            final_confidence = max(20, final_confidence * 0.8)
        
        # Create combined reasoning
        combined_reasoning = f"Combined strategy analysis ({self.current_market_regime} market): " + \
                           "; ".join(reasoning_parts)
        
        return TradingSignal(
            action=final_action,
            confidence=final_confidence,
            reasoning=combined_reasoning,
            position_size_multiplier=max(0.5, min(2.0, final_position_multiplier))
        )
    
    def get_strategy_performance(self) -> Dict:
        """Get performance metrics for each strategy"""
        
        performance = {}
        
        for name, strategy in self.strategies.items():
            performance[name] = {
                'name': strategy.name,
                'risk_level': strategy.get_risk_level(),
                'holding_period': strategy.get_expected_holding_period(),
                'market_suitability': {
                    'bull': strategy.get_market_regime_suitability('bull'),
                    'bear': strategy.get_market_regime_suitability('bear'),
                    'sideways': strategy.get_market_regime_suitability('sideways')
                },
                'current_weight': self.strategy_weights.get(name, 0)
            }
        
        return performance
    
    def update_strategy_weights(self, new_weights: Dict[str, float]):
        """Update strategy weights"""
        
        # Validate weights sum to 1.0
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            self.logger.warning(f"Strategy weights sum to {total_weight}, normalizing")
            new_weights = {k: v/total_weight for k, v in new_weights.items()}
        
        self.strategy_weights.update(new_weights)
        self.logger.info(f"Updated strategy weights: {self.strategy_weights}")
    
    def get_current_market_regime(self) -> str:
        """Get current market regime"""
        return self.current_market_regime
