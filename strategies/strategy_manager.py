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
from .performance_tracker import HybridPerformanceTracker

class StrategyManager:
    """
    Manages multiple trading strategies and combines their signals
    """
    
    def __init__(self, config, llm_analyzer=None, news_sentiment_analyzer=None, volatility_analyzer=None):
        self.config = config
        self.logger = logging.getLogger("supervisor")  # Use supervisor logger for consistency
        
        self.logger.info(f"🔧 Strategy manager initializing with LLM: {llm_analyzer is not None}, News: {news_sentiment_analyzer is not None}, Volatility: {volatility_analyzer is not None}")
        
        # Initialize strategies
        self.strategies = {
            'trend_following': TrendFollowingStrategy(config),
            'mean_reversion': MeanReversionStrategy(config),
            'momentum': MomentumStrategy(config)
        }
        
        # Add LLM strategy if analyzer is provided (Phase 3 enhanced)
        if llm_analyzer:
            from .llm_strategy import LLMStrategy
            self.logger.info("🚀 Creating LLM strategy with Phase 3 enhancements...")
            self.strategies['llm_strategy'] = LLMStrategy(config, llm_analyzer, news_sentiment_analyzer)
            self.logger.info("✅ Phase 3 hybrid framework enabled with enhanced LLM strategy")
        else:
            self.logger.info("📊 Rule-based framework (no LLM analyzer provided)")
        
        # Phase 3: Initialize advanced analyzers
        self.news_sentiment_analyzer = news_sentiment_analyzer
        self.volatility_analyzer = volatility_analyzer
        
        if news_sentiment_analyzer:
            self.logger.info("📰 Phase 3: News sentiment analysis enabled")
        
        if volatility_analyzer:
            self.logger.info("📊 Phase 3: Volatility analysis enabled")
        
        # Strategy weights for hybrid framework
        if llm_analyzer:
            # Phase 3: Adaptive base weights
            self.base_strategy_weights = {
                'trend_following': 0.25,
                'mean_reversion': 0.25,
                'momentum': 0.25,
                'llm_strategy': 0.25
            }
        else:
            # Rule-based only
            self.base_strategy_weights = {
                'trend_following': 0.4,
                'mean_reversion': 0.3,
                'momentum': 0.3
            }
        
        # Current weights (will be dynamically adjusted)
        self.strategy_weights = self.base_strategy_weights.copy()
        
        # Market regime detection
        self.current_market_regime = "sideways"  # bull, bear, sideways
        
        # Initialize performance tracker (Phase 2)
        self.performance_tracker = HybridPerformanceTracker()
        
        self.logger.info(f"Strategy Manager initialized with {len(self.strategies)} strategies")
        self.logger.info(f"Base strategy weights: {self.base_strategy_weights}")
        
        # Log performance summary
        perf_summary = self.performance_tracker.get_performance_summary()
        if perf_summary["total_decisions"] > 0:
            self.logger.info(f"📊 Historical performance: {perf_summary['total_decisions']} decisions tracked")
            if "comparison" in perf_summary:
                comp = perf_summary["comparison"]
                self.logger.info(f"  LLM accuracy: {comp['llm_accuracy']:.1%}, Rule-based avg: {comp['rule_based_avg_accuracy']:.1%}")
                self.logger.info(f"  LLM advantage: {comp['llm_advantage']:+.1%}")
        
        # Phase 3: Log advanced features status
        phase3_features = []
        if news_sentiment_analyzer:
            phase3_features.append("News Sentiment")
        if volatility_analyzer:
            phase3_features.append("Volatility Analysis")
        if self.performance_tracker:
            phase3_features.append("Performance Adaptation")
        
        if phase3_features:
            self.logger.info(f"🚀 Phase 3 features active: {', '.join(phase3_features)}")
        
        # Strategy weights for hybrid framework
        if llm_analyzer:
            # Phase 1: 75% rule-based, 25% LLM
            self.strategy_weights = {
                'trend_following': 0.25,    # 25% of total (33% of rule-based)
                'mean_reversion': 0.25,     # 25% of total (33% of rule-based) 
                'momentum': 0.25,           # 25% of total (33% of rule-based)
                'llm_strategy': 0.25        # 25% of total (LLM component)
            }
        else:
            # Original weights for rule-based only
            self.strategy_weights = {
                'trend_following': 0.4,
                'mean_reversion': 0.3,
                'momentum': 0.3
            }
        
        # Market regime detection
        self.current_market_regime = "sideways"  # bull, bear, sideways
        
        self.logger.info(f"Strategy Manager initialized with {len(self.strategies)} strategies")
        self.logger.info(f"Strategy weights: {self.strategy_weights}")
        
        # Log performance summary
        perf_summary = self.performance_tracker.get_performance_summary()
        if perf_summary["total_decisions"] > 0:
            self.logger.info(f"📊 Historical performance: {perf_summary['total_decisions']} decisions tracked")
            if "comparison" in perf_summary:
                comp = perf_summary["comparison"]
                self.logger.info(f"  LLM accuracy: {comp['llm_accuracy']:.1%}, Rule-based avg: {comp['rule_based_avg_accuracy']:.1%}")
                self.logger.info(f"  LLM advantage: {comp['llm_advantage']:+.1%}")
        
    def analyze_all_strategies(self, 
                             market_data: Dict,
                             technical_indicators: Dict,
                             portfolio: Dict) -> Dict[str, TradingSignal]:
        """Run analysis on all strategies"""
        
        # Map Bollinger Band data to expected format for strategies
        mapped_indicators = technical_indicators.copy()
        if 'bb_upper' in technical_indicators:
            mapped_indicators['bollinger'] = {
                'upper': technical_indicators.get('bb_upper', 0),
                'lower': technical_indicators.get('bb_lower', 0),
                'middle': technical_indicators.get('bb_middle', 0)
            }
        
        strategy_signals = {}
        
        for name, strategy in self.strategies.items():
            try:
                signal = strategy.analyze(market_data, mapped_indicators, portfolio)
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
        
        # Adjust strategy weights based on market regime, confidence, volatility, and performance (Phase 3)
        adjusted_weights = self._adjust_weights_for_market_regime(strategy_signals, market_data)
        
        # Combine signals
        combined_signal = self._combine_strategy_signals(
            strategy_signals, adjusted_weights
        )
        
        # Record decision for performance tracking (Phase 2)
        try:
            current_price = market_data.get('price', 0)
            product_id = market_data.get('product_id', 'Unknown')
            
            if current_price > 0 and product_id != 'Unknown':
                self.performance_tracker.record_decision(
                    product_id=product_id,
                    strategy_signals=strategy_signals,
                    final_decision={
                        'action': combined_signal.action,
                        'confidence': combined_signal.confidence
                    },
                    current_price=current_price
                )
        except Exception as e:
            self.logger.warning(f"Failed to record decision for performance tracking: {e}")
        
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
    
    def _adjust_weights_for_market_regime(self, strategy_signals: Dict[str, TradingSignal] = None, market_data: Dict = None) -> Dict[str, float]:
        """Adjust strategy weights based on market regime, confidence, volatility, and performance (Phase 3)"""
        
        # Start with base weights
        base_weights = self.base_strategy_weights.copy()
        
        # If no signals provided, use original suitability-based approach
        if not strategy_signals:
            return self._get_suitability_based_weights(base_weights)
        
        # Phase 3: Start with performance-based adaptation
        adjusted_weights = self.performance_tracker.get_adaptive_weights(base_weights)
        
        # Phase 2: Confidence-based adjustments
        if 'llm_strategy' in strategy_signals:
            adjusted_weights = self._apply_confidence_adjustments(adjusted_weights, strategy_signals)
        
        # Phase 2: Market regime adjustments
        regime_adjustments = self._get_regime_weight_adjustments()
        adjusted_weights = self._apply_regime_adjustments(adjusted_weights, regime_adjustments)
        
        # Phase 3: Volatility-based adjustments
        if self.volatility_analyzer and market_data:
            adjusted_weights = self._apply_volatility_adjustments(adjusted_weights, market_data)
        
        # Normalize weights to sum to 1.0
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}
        
        # Log weight changes if significant
        if any(abs(adjusted_weights[k] - base_weights[k]) > 0.05 for k in base_weights):
            self.logger.info(f"⚖️  Phase 3 Dynamic weight adjustment:")
            for strategy in adjusted_weights:
                base = base_weights.get(strategy, 0)
                adjusted = adjusted_weights[strategy]
                if abs(adjusted - base) > 0.01:
                    self.logger.info(f"  {strategy}: {base:.1%} -> {adjusted:.1%}")
        
        return adjusted_weights
    
    def _apply_confidence_adjustments(self, weights: Dict[str, float], strategy_signals: Dict[str, TradingSignal]) -> Dict[str, float]:
        """Apply confidence-based weight adjustments"""
        
        llm_signal = strategy_signals['llm_strategy']
        rule_based_signals = {k: v for k, v in strategy_signals.items() if k != 'llm_strategy'}
        
        # Calculate average rule-based confidence
        rule_based_avg_confidence = sum(s.confidence for s in rule_based_signals.values()) / len(rule_based_signals) if rule_based_signals else 50
        llm_confidence = llm_signal.confidence
        
        confidence_diff = llm_confidence - rule_based_avg_confidence
        
        # Adjust weights based on confidence difference
        if confidence_diff > 20:  # LLM much more confident
            self.logger.info(f"🤖 LLM high confidence ({llm_confidence:.1f}% vs {rule_based_avg_confidence:.1f}%) - increasing LLM weight")
            weights['llm_strategy'] = min(0.4, weights['llm_strategy'] + 0.15)
            # Reduce rule-based weights proportionally
            reduction_per_strategy = 0.15 / 3
            for strategy in ['trend_following', 'mean_reversion', 'momentum']:
                weights[strategy] = max(0.1, weights[strategy] - reduction_per_strategy)
                
        elif confidence_diff < -20:  # Rule-based much more confident
            self.logger.info(f"📊 Rule-based high confidence ({rule_based_avg_confidence:.1f}% vs {llm_confidence:.1f}%) - increasing rule-based weight")
            weights['llm_strategy'] = max(0.1, weights['llm_strategy'] - 0.15)
            # Increase rule-based weights proportionally
            increase_per_strategy = 0.15 / 3
            for strategy in ['trend_following', 'mean_reversion', 'momentum']:
                weights[strategy] = min(0.4, weights[strategy] + increase_per_strategy)
        
        return weights
    
    def _apply_regime_adjustments(self, weights: Dict[str, float], regime_adjustments: Dict[str, float]) -> Dict[str, float]:
        """Apply market regime adjustments"""
        
        for strategy, adjustment in regime_adjustments.items():
            if strategy in weights:
                old_weight = weights[strategy]
                weights[strategy] = max(0.05, min(0.5, old_weight + adjustment))
                self.logger.debug(f"Regime adjustment for {strategy}: {old_weight:.3f} -> {weights[strategy]:.3f}")
        
        return weights
    
    def _apply_volatility_adjustments(self, weights: Dict[str, float], market_data: Dict) -> Dict[str, float]:
        """Apply volatility-based weight adjustments (Phase 3)"""
        
        try:
            # Get price data for volatility analysis
            price_data = self._extract_price_data(market_data)
            time_periods = market_data.get('price_changes', {})
            product_id = market_data.get('product_id', 'Unknown')
            
            if price_data and len(price_data) > 1:
                # Analyze volatility
                volatility_analysis = self.volatility_analyzer.analyze_volatility(
                    product_id, price_data, time_periods
                )
                
                # Get strategy adjustments
                vol_adjustments = volatility_analysis.get('strategy_adjustments', {})
                
                # Apply volatility adjustments
                for strategy in weights:
                    if strategy in vol_adjustments:
                        adjustment = vol_adjustments[strategy]
                        old_weight = weights[strategy]
                        weights[strategy] = max(0.05, min(0.5, old_weight + adjustment))
                        
                        if abs(adjustment) > 0.02:  # Log significant adjustments
                            self.logger.debug(f"Volatility adjustment for {strategy}: {old_weight:.3f} -> {weights[strategy]:.3f}")
                
                # Log volatility regime
                regime = volatility_analysis.get('regime', {})
                if regime.get('category') != 'medium':
                    self.logger.info(f"📊 Volatility regime: {regime.get('category', 'unknown')} (score: {regime.get('score', 0):.2f})")
            
        except Exception as e:
            self.logger.error(f"Error applying volatility adjustments: {e}")
        
        return weights
    
    def _extract_price_data(self, market_data: Dict) -> List[float]:
        """Extract price data for volatility analysis"""
        
        price_data = []
        
        # Get current price
        current_price = market_data.get('price', 0)
        if current_price > 0:
            price_data.append(current_price)
        
        # For now, we'll use price changes to estimate recent prices
        # In a full implementation, we'd have historical price data
        price_changes = market_data.get('price_changes', {})
        if current_price > 0 and price_changes:
            # Estimate recent prices from changes
            for period, change in [('1h', price_changes.get('1h', 0)), 
                                 ('4h', price_changes.get('4h', 0)), 
                                 ('24h', price_changes.get('24h', 0))]:
                if change is not None:
                    estimated_price = current_price / (1 + change/100)
                    price_data.append(estimated_price)
        
        return price_data
    
    def _get_suitability_based_weights(self, base_weights: Dict[str, float]) -> Dict[str, float]:
        """Original suitability-based weight adjustment (fallback)"""
        
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
        
        self.logger.debug(f"Suitability-based weights for {self.current_market_regime} market: {adjusted_weights}")
        return adjusted_weights
    
    def _get_regime_weight_adjustments(self) -> Dict[str, float]:
        """Get weight adjustments based on current market regime"""
        
        regime = self.current_market_regime.lower()
        
        # Define regime-specific strategy preferences
        regime_preferences = {
            "bull": {
                "trend_following": +0.1,    # Trend following excels in bull markets
                "momentum": +0.05,          # Momentum strategies work well
                "mean_reversion": -0.05,    # Less effective in strong trends
                "llm_strategy": 0.0         # Neutral
            },
            "bear": {
                "trend_following": +0.05,   # Still good for downtrends
                "mean_reversion": +0.1,     # Mean reversion works well in bear markets
                "momentum": -0.05,          # Momentum can be misleading
                "llm_strategy": +0.05       # LLM good at complex bear market analysis
            },
            "sideways": {
                "mean_reversion": +0.1,     # Excellent for range-bound markets
                "llm_strategy": +0.1,       # LLM excels at complex sideways analysis
                "trend_following": -0.1,    # Less effective in sideways markets
                "momentum": -0.05           # Limited effectiveness
            },
            "volatile": {
                "llm_strategy": +0.15,      # LLM best at handling volatility
                "mean_reversion": +0.05,    # Can capitalize on volatility
                "trend_following": -0.05,   # Trends less reliable
                "momentum": -0.1            # Momentum can be misleading
            }
        }
        
        adjustments = regime_preferences.get(regime, {})
        
        if adjustments:
            self.logger.debug(f"Market regime '{regime}' adjustments: {adjustments}")
        
        return adjustments
    
    def _combine_strategy_signals(self, 
                                strategy_signals: Dict[str, TradingSignal],
                                weights: Dict[str, float]) -> TradingSignal:
        """Combine multiple strategy signals with consensus requirements (Phase 2)"""
        
        # Convert actions to numeric scores
        action_scores = {"BUY": 1, "HOLD": 0, "SELL": -1}
        
        weighted_score = 0
        weighted_confidence = 0
        total_weight = 0
        position_multipliers = []
        reasoning_parts = []
        
        # Track individual strategy actions for consensus
        strategy_actions = {}
        
        for strategy_name, signal in strategy_signals.items():
            weight = weights.get(strategy_name, 0)
            strategy_actions[strategy_name] = signal.action
            
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
        
        # Determine preliminary action
        if final_score > 0.3:
            preliminary_action = "BUY"
        elif final_score < -0.3:
            preliminary_action = "SELL"
        else:
            preliminary_action = "HOLD"
        
        # Phase 2: Apply consensus requirements
        final_action, consensus_info = self._apply_consensus_requirements(
            preliminary_action, strategy_actions, weights, final_confidence
        )
        
        # Adjust confidence based on signal strength and consensus
        if abs(final_score) > 0.6:
            # Strong signal - boost confidence slightly
            final_confidence = min(95, final_confidence * 1.1)
        elif abs(final_score) < 0.1:
            # Very weak signal - reduce confidence
            final_confidence = final_confidence * 0.8
        
        # Reduce confidence if consensus was not met
        if consensus_info["consensus_override"]:
            final_confidence = final_confidence * 0.7  # Reduce confidence for overridden decisions
        
        # Create combined reasoning with hybrid breakdown and consensus info
        reasoning_parts_by_type = {"rule_based": [], "llm": []}
        
        for strategy_name, signal in strategy_signals.items():
            if strategy_name == 'llm_strategy':
                reasoning_parts_by_type["llm"].append(f"{signal.reasoning}")
            else:
                reasoning_parts_by_type["rule_based"].append(f"{strategy_name}: {signal.reasoning}")
        
        # Build combined reasoning
        combined_parts = [f"Combined hybrid analysis ({self.current_market_regime} market):"]
        
        if reasoning_parts_by_type["rule_based"]:
            combined_parts.append(f"Rule-based: {'; '.join(reasoning_parts_by_type['rule_based'])}")
        
        if reasoning_parts_by_type["llm"]:
            combined_parts.append(f"LLM: {'; '.join(reasoning_parts_by_type['llm'])}")
        
        # Add consensus information
        if consensus_info["message"]:
            combined_parts.append(f"Consensus: {consensus_info['message']}")
        
        combined_reasoning = "; ".join(combined_parts)
        
        # Log hybrid decision breakdown if LLM is present
        if 'llm_strategy' in strategy_signals:
            llm_signal = strategy_signals['llm_strategy']
            rule_based_confidence = sum(
                signal.confidence * weights.get(name, 0) 
                for name, signal in strategy_signals.items() 
                if name != 'llm_strategy'
            ) / sum(weights.get(name, 0) for name in weights if name != 'llm_strategy') if total_weight > weights.get('llm_strategy', 0) else 0
            
            self.logger.info(f"🤖 Phase 2 Hybrid Decision:")
            self.logger.info(f"  Rule-based avg: {rule_based_confidence:.1f}%")
            self.logger.info(f"  LLM: {llm_signal.action} ({llm_signal.confidence:.1f}%)")
            self.logger.info(f"  Preliminary: {preliminary_action} ({final_score:.2f})")
            self.logger.info(f"  Final: {final_action} ({final_confidence:.1f}%)")
            if consensus_info["message"]:
                self.logger.info(f"  Consensus: {consensus_info['message']}")
        
        return TradingSignal(
            action=final_action,
            confidence=final_confidence,
            reasoning=combined_reasoning,
            position_size_multiplier=max(0.5, min(2.0, final_position_multiplier))
        )
    
    def _apply_consensus_requirements(self, 
                                   preliminary_action: str, 
                                   strategy_actions: Dict[str, str], 
                                   weights: Dict[str, float],
                                   confidence: float) -> tuple:
        """Apply consensus requirements for BUY/SELL decisions"""
        
        if preliminary_action == "HOLD":
            return preliminary_action, {"consensus_override": False, "message": ""}
        
        # Count votes for each action, weighted by strategy weights
        action_votes = {"BUY": 0, "SELL": 0, "HOLD": 0}
        
        for strategy, action in strategy_actions.items():
            weight = weights.get(strategy, 0)
            action_votes[action] += weight
        
        # Calculate consensus metrics
        total_votes = sum(action_votes.values())
        action_percentage = action_votes[preliminary_action] / total_votes if total_votes > 0 else 0
        
        # Consensus requirements (Phase 2)
        consensus_threshold = 0.6  # 60% of weighted votes must agree
        
        if action_percentage >= consensus_threshold:
            # Strong consensus - proceed with action
            return preliminary_action, {
                "consensus_override": False, 
                "message": f"Strong consensus ({action_percentage:.1%} agreement)"
            }
        elif action_percentage >= 0.5:
            # Weak consensus - proceed but with caution
            return preliminary_action, {
                "consensus_override": False,
                "message": f"Weak consensus ({action_percentage:.1%} agreement)"
            }
        else:
            # No consensus - override to HOLD
            opposing_actions = [action for action in ["BUY", "SELL"] if action != preliminary_action]
            opposing_votes = sum(action_votes[action] for action in opposing_actions)
            
            return "HOLD", {
                "consensus_override": True,
                "message": f"No consensus: {preliminary_action} {action_percentage:.1%} vs others {opposing_votes/total_votes:.1%} - defaulting to HOLD"
            }
    
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
