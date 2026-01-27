"""
Adaptive Strategy Manager - Phase 1 Implementation
Market-regime aware strategy selection with hierarchical decision making
"""

import logging
from typing import Dict, List, Optional
from .base_strategy import BaseStrategy, TradingSignal
from .strategy_manager import StrategyManager

class AdaptiveStrategyManager(StrategyManager):
    """
    Enhanced strategy manager with market-regime adaptive decision making
    Phase 1: Hierarchical strategy selection instead of democratic voting
    """
    
    def __init__(self, config, llm_analyzer=None, news_sentiment_analyzer=None, volatility_analyzer=None):
        super().__init__(config, llm_analyzer, news_sentiment_analyzer, volatility_analyzer)
        
        # Ensure logger is set (for tests that patch parent __init__)
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(__name__)
        
        # Market regime specific strategy priorities
        self.regime_strategy_priority = {
            "trending": ["trend_following", "momentum", "llm_strategy", "mean_reversion"],
            "ranging": ["mean_reversion", "llm_strategy", "momentum", "trend_following"], 
            "volatile": ["llm_strategy", "mean_reversion", "trend_following", "momentum"],
            "bear_ranging": ["llm_strategy"]  # OPTIMIZATION 4: Only LLM in bear + low volatility
        }
        
        # OPTIMIZED: Lower confidence thresholds based on backtesting results
        self.adaptive_thresholds = {
            "trending": {
                "trend_following": {"buy": 30, "sell": 30},  # Optimized from backtesting
                "momentum": {"buy": 30, "sell": 30},
                "llm_strategy": {"buy": 35, "sell": 35},
                "mean_reversion": {"buy": 45, "sell": 45}   # Higher (discouraged)
            },
            "ranging": {
                "mean_reversion": {"buy": 30, "sell": 30},   # Optimized from backtesting
                "llm_strategy": {"buy": 35, "sell": 35},
                "momentum": {"buy": 40, "sell": 40},
                "trend_following": {"buy": 45, "sell": 45}  # Higher (discouraged)
            },
            "volatile": {
                "llm_strategy": {"buy": 35, "sell": 35},     # LLM best for volatile
                "mean_reversion": {"buy": 40, "sell": 40},
                "trend_following": {"buy": 45, "sell": 45},  # Higher (more conservative)
                "momentum": {"buy": 45, "sell": 45}
            },
            "bear_ranging": {
                "llm_strategy": {"buy": 60, "sell": 40}      # OPTIMIZATION 4: Conservative in bear markets
            }
        }
        
        # OPTIMIZED: Lower default fallback thresholds
        self.default_thresholds = {"buy": 30, "sell": 30}
        
        # Log initialization
        self.logger.info("🚀 Adaptive Strategy Manager initialized")
        self.logger.info(f"📊 Market regime priorities: {self.regime_strategy_priority}")
    
    
    def detect_market_regime_enhanced(self, technical_indicators: Dict, market_data: Dict) -> str:
        """
        Enhanced market regime detection for strategy selection
        Returns: 'trending', 'ranging', or 'volatile'
        """
        try:
            # Get price changes
            price_changes = market_data.get('price_changes', {})
            change_24h = abs(float(price_changes.get('24h', 0)))
            change_5d = abs(float(price_changes.get('5d', 0)))
            change_7d = float(price_changes.get('7d', 0))  # For bear market detection
            
            # Get Bollinger Band width for volatility
            bb_upper = float(technical_indicators.get('bb_upper', 0))
            bb_lower = float(technical_indicators.get('bb_lower', 0))
            bb_middle = float(technical_indicators.get('bb_middle', 1))
            
            if bb_middle > 0:
                bb_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100
            else:
                bb_width_pct = 2.0  # Default moderate volatility
            
            # OPTIMIZATION 4: Bear market filter - avoid trading in declining periods
            if change_7d < -5:  # 7-day decline > 5%
                self.logger.info(f"🐻 Bear market detected (7d: {change_7d:.1f}%) - reducing activity")
                # In bear markets, be more conservative
                if change_24h < 1.5 and bb_width_pct < 3:
                    regime = "bear_ranging"  # Special regime for bear + low volatility
                else:
                    regime = "volatile"  # Treat as volatile to be more conservative
            else:
                # Normal regime detection logic
                if change_24h > 4 or change_5d > 8:
                    if bb_width_pct > 4:
                        regime = "volatile"  # High movement + high volatility
                    else:
                        regime = "trending"  # High movement + low volatility = trend
                elif change_24h < 1.5 and bb_width_pct < 2:
                    regime = "ranging"   # Low movement + low volatility = range
                elif bb_width_pct > 5:
                    regime = "volatile"  # High volatility regardless of movement
                else:
                    regime = "ranging"   # Default to ranging
            
            self.logger.info(f"📊 Market regime: {regime} (24h: {change_24h:.1f}%, BB width: {bb_width_pct:.1f}%)")
            return regime
            
        except Exception as e:
            self.logger.info(f"Market regime detection failed: {e}, defaulting to 'ranging'")
            return "ranging"
    
    def get_adaptive_threshold(self, strategy_name: str, action: str, market_regime: str) -> float:
        """Get adaptive confidence threshold for strategy/action/regime combination"""
        
        action_key = action.lower()
        if action_key not in ["buy", "sell"]:
            action_key = "buy"  # Default
        
        try:
            threshold = self.adaptive_thresholds[market_regime][strategy_name][action_key]
            self.logger.info(f"Adaptive threshold for {strategy_name}/{action}/{market_regime}: {threshold}%")
            return threshold
        except KeyError:
            # Fallback to default
            default = self.default_thresholds[action_key]
            self.logger.info(f"Using default threshold for {strategy_name}/{action}: {default}%")
            return default
    
    def _combine_strategy_signals_adaptive(self, 
                                         strategy_signals: Dict[str, TradingSignal],
                                         weights: Dict[str, float],
                                         market_regime: str) -> TradingSignal:
        """
        Adaptive signal combination using hierarchical approach instead of democratic voting
        """
        
        # Get strategy priority for current market regime
        strategy_priority = self.regime_strategy_priority.get(market_regime, 
                                                            ["llm_strategy", "trend_following", "mean_reversion", "momentum"])
        
        self.logger.info(f"🎯 Strategy priority for {market_regime} market: {strategy_priority}")
        
        # Try strategies in priority order
        for strategy_name in strategy_priority:
            if strategy_name not in strategy_signals:
                continue
                
            signal = strategy_signals[strategy_name]
            
            # Get adaptive threshold for this strategy/action/regime
            threshold = self.get_adaptive_threshold(strategy_name, signal.action, market_regime)
            
            self.logger.info(f"🔍 {strategy_name}: {signal.action} ({signal.confidence:.1f}% vs {threshold}% threshold)")
            
            # Check if this strategy meets its adaptive threshold
            if signal.confidence >= threshold:
                
                # Apply confirmation logic - check if secondary strategy agrees or at least doesn't strongly disagree
                confirmation_bonus = 0
                veto_penalty = 0
                
                # Check secondary strategies for confirmation/veto
                for secondary_strategy in strategy_priority[1:3]:  # Check next 2 strategies
                    if secondary_strategy not in strategy_signals:
                        continue
                        
                    secondary_signal = strategy_signals[secondary_strategy]
                    
                    if secondary_signal.action == signal.action:
                        confirmation_bonus += 5  # Agreement bonus
                        self.logger.info(f"✅ {secondary_strategy} agrees with {signal.action}")
                    elif secondary_signal.action != "HOLD" and secondary_signal.confidence > 60:
                        veto_penalty += 10  # Strong disagreement penalty
                        self.logger.info(f"❌ {secondary_strategy} strongly disagrees ({secondary_signal.action} {secondary_signal.confidence:.1f}%)")
                
                # Calculate final confidence with bonuses/penalties
                final_confidence = signal.confidence + confirmation_bonus - veto_penalty
                final_confidence = max(0, min(95, final_confidence))  # Clamp to 0-95%
                
                # Check if still above threshold after adjustments
                if final_confidence >= threshold:
                    reasoning = f"Adaptive {market_regime} market strategy: {strategy_name} ({signal.confidence:.1f}% -> {final_confidence:.1f}%); {signal.reasoning}"
                    
                    if confirmation_bonus > 0:
                        reasoning += f"; Confirmed by secondary strategies (+{confirmation_bonus}%)"
                    if veto_penalty > 0:
                        reasoning += f"; Penalized for disagreement (-{veto_penalty}%)"
                    
                    self.logger.info(f"🎯 Decision: {signal.action} from {strategy_name} (confidence: {final_confidence:.1f}%)")
                    
                    return TradingSignal(
                        action=signal.action,
                        confidence=final_confidence,
                        reasoning=reasoning,
                        position_size_multiplier=signal.position_size_multiplier
                    )
                else:
                    self.logger.info(f"⚠️  {strategy_name} signal weakened by disagreement ({final_confidence:.1f}% < {threshold}%)")
            else:
                self.logger.info(f"⏭️  {strategy_name} below threshold ({signal.confidence:.1f}% < {threshold}%)")
        
        # If no strategy meets threshold, return HOLD with average confidence
        avg_confidence = sum(s.confidence for s in strategy_signals.values()) / len(strategy_signals) if strategy_signals else 0
        
        self.logger.info(f"🛑 No strategy meets adaptive thresholds - HOLD (avg confidence: {avg_confidence:.1f}%)")
        
        return TradingSignal(
            action="HOLD",
            confidence=avg_confidence,
            reasoning=f"No strategy meets adaptive thresholds in {market_regime} market",
            position_size_multiplier=1.0
        )
    
    def get_combined_signal(self, market_data: Dict, technical_indicators: Dict, portfolio: Optional[Dict] = None) -> TradingSignal:
        """
        Override parent method to use adaptive strategy selection
        """
        
        # Validate inputs (same as parent)
        if not isinstance(technical_indicators, dict):
            self.logger.error(f"Invalid technical_indicators type: {type(technical_indicators)}")
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
        
        # Enhanced market regime detection
        market_regime = self.detect_market_regime_enhanced(technical_indicators, market_data)
        self.current_market_regime = market_regime
        
        # Use adaptive signal combination instead of democratic voting
        combined_signal = self._combine_strategy_signals_adaptive(
            strategy_signals, self.strategy_weights, market_regime
        )
        
        # Record decision for performance tracking (same as parent)
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
            self.logger.info(f"Failed to record decision for performance tracking: {e}")
        
        return combined_signal
