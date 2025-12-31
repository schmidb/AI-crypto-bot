"""
Aggressive Strategy Manager - Day Trading Implementation
Based on the Aggressive Day Trading Plan with backtesting constraints
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy, TradingSignal
from .strategy_manager import StrategyManager

class AggressiveStrategyManager(StrategyManager):
    """
    Aggressive day trading strategy manager with bear market protection
    Implements the aggressive day trading plan with validated constraints
    """
    
    def __init__(self, config, llm_analyzer=None, news_sentiment_analyzer=None, volatility_analyzer=None):
        super().__init__(config, llm_analyzer, news_sentiment_analyzer, volatility_analyzer)
        
        # Aggressive strategy configuration based on backtesting
        self.aggressive_config = {
            'max_daily_trades': 8,              # Reduced from 15 based on backtesting
            'max_position_size': 0.05,          # 5% per trade (vs 10% original)
            'stop_loss_pct': 0.01,              # 1% stop loss (tighter)
            'profit_target_pct': 0.02,          # 2% profit target (more realistic)
            'max_daily_loss': 0.03,             # 3% max daily loss
            'max_concurrent_trades': 2,         # Max 2 positions
            'time_based_exit': 2,               # Exit after 2 hours max
            'bear_market_threshold': -5,        # 7-day decline > 5%
        }
        
        # Bear market overrides (more conservative)
        self.bear_market_overrides = {
            'max_position_size': 0.02,          # 2% in bear markets
            'max_daily_trades': 3,              # Only 3 trades in bear
            'stop_loss_pct': 0.008,             # Tighter stops
            'profit_target_pct': 0.015          # Lower targets
        }
        
        # Strategy priorities for different market conditions
        self.aggressive_strategy_priority = {
            "high_volatility": ["scalping", "volatility_breakout", "llm_strategy"],
            "trending": ["momentum", "trend_following", "llm_strategy"],
            "ranging": ["mean_reversion", "scalping", "llm_strategy"],
            "bear_market": ["llm_strategy"]  # Only LLM in bear markets
        }
        
        # More aggressive confidence thresholds
        self.aggressive_thresholds = {
            "high_volatility": {
                "scalping": {"buy": 25, "sell": 25},
                "volatility_breakout": {"buy": 30, "sell": 30},
                "llm_strategy": {"buy": 35, "sell": 35}
            },
            "trending": {
                "momentum": {"buy": 25, "sell": 25},
                "trend_following": {"buy": 30, "sell": 30},
                "llm_strategy": {"buy": 35, "sell": 35}
            },
            "ranging": {
                "mean_reversion": {"buy": 25, "sell": 25},
                "scalping": {"buy": 30, "sell": 30},
                "llm_strategy": {"buy": 35, "sell": 35}
            },
            "bear_market": {
                "llm_strategy": {"buy": 60, "sell": 40}  # Very conservative in bear
            }
        }
        
        # Track daily trading activity
        self.daily_trades = 0
        self.daily_loss = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Initialize aggressive strategies (placeholder - would implement actual strategies)
        self.aggressive_strategies = {
            'scalping': self._create_scalping_strategy(),
            'volatility_breakout': self._create_volatility_breakout_strategy(),
            'momentum': self.strategies.get('momentum'),  # Reuse existing
            'mean_reversion': self.strategies.get('mean_reversion'),  # Reuse existing
            'trend_following': self.strategies.get('trend_following'),  # Reuse existing
            'llm_strategy': self.strategies.get('llm_strategy')  # Reuse existing
        }
        
        self.logger.info("🚀 Aggressive Strategy Manager initialized with day trading constraints")
        self.logger.info(f"📊 Max daily trades: {self.aggressive_config['max_daily_trades']}")
        self.logger.info(f"💰 Max position size: {self.aggressive_config['max_position_size']*100}%")
    
    def _create_scalping_strategy(self):
        """Create conservative scalping strategy (placeholder)"""
        # This would be a full implementation of the scalping strategy
        # For now, return a mock strategy that uses existing momentum logic
        return self.strategies.get('momentum')
    
    def _create_volatility_breakout_strategy(self):
        """Create volatility breakout strategy (placeholder)"""
        # This would be a full implementation of the volatility breakout strategy
        # For now, return a mock strategy that uses existing trend following logic
        return self.strategies.get('trend_following')
    
    def detect_aggressive_market_regime(self, technical_indicators: Dict, market_data: Dict) -> str:
        """
        Enhanced market regime detection for aggressive trading
        Returns: 'high_volatility', 'trending', 'ranging', or 'bear_market'
        """
        try:
            # Get price changes
            price_changes = market_data.get('price_changes', {})
            change_24h = abs(float(price_changes.get('24h', 0)))
            change_7d = float(price_changes.get('7d', 0))  # For bear market detection
            
            # Bear market detection (critical safeguard)
            if change_7d < self.aggressive_config['bear_market_threshold']:
                self.logger.info(f"🐻 Bear market detected (7d: {change_7d:.1f}%) - switching to defensive mode")
                return "bear_market"
            
            # Get Bollinger Band width for volatility
            bb_upper = float(technical_indicators.get('bb_upper', 0))
            bb_lower = float(technical_indicators.get('bb_lower', 0))
            bb_middle = float(technical_indicators.get('bb_middle', 1))
            
            if bb_middle > 0:
                bb_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100
            else:
                bb_width_pct = 2.0
            
            # Aggressive regime detection (more sensitive to opportunities)
            if bb_width_pct > 3 or change_24h > 3:
                regime = "high_volatility"  # Scalping opportunities
            elif change_24h > 2:
                regime = "trending"  # Momentum opportunities
            else:
                regime = "ranging"  # Mean reversion opportunities
            
            self.logger.info(f"📊 Aggressive market regime: {regime} (24h: {change_24h:.1f}%, BB width: {bb_width_pct:.1f}%)")
            return regime
            
        except Exception as e:
            self.logger.warning(f"Aggressive regime detection failed: {e}, defaulting to 'ranging'")
            return "ranging"
    
    def _reset_daily_counters(self):
        """Reset daily trading counters if new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_loss = 0.0
            self.last_reset_date = current_date
            self.logger.info(f"📅 Daily counters reset for {current_date}")
    
    def _check_trading_limits(self, market_regime: str) -> Dict[str, Any]:
        """
        Check if trading limits allow new trades
        Returns dict with 'allowed' boolean and 'reason' string
        """
        self._reset_daily_counters()
        
        # Get current limits based on market regime
        if market_regime == "bear_market":
            max_trades = self.bear_market_overrides['max_daily_trades']
            max_loss = self.aggressive_config['max_daily_loss'] * 0.5  # Half loss limit in bear
        else:
            max_trades = self.aggressive_config['max_daily_trades']
            max_loss = self.aggressive_config['max_daily_loss']
        
        # Check daily trade limit
        if self.daily_trades >= max_trades:
            return {
                'allowed': False,
                'reason': f'Daily trade limit reached ({self.daily_trades}/{max_trades})'
            }
        
        # Check daily loss limit
        if self.daily_loss >= max_loss:
            return {
                'allowed': False,
                'reason': f'Daily loss limit reached ({self.daily_loss:.1%}/{max_loss:.1%})'
            }
        
        return {'allowed': True, 'reason': 'Within trading limits'}
    
    def get_aggressive_threshold(self, strategy_name: str, action: str, market_regime: str) -> float:
        """Get aggressive confidence threshold for strategy/action/regime combination"""
        
        action_key = action.lower()
        if action_key not in ["buy", "sell"]:
            action_key = "buy"
        
        try:
            threshold = self.aggressive_thresholds[market_regime][strategy_name][action_key]
            self.logger.debug(f"Aggressive threshold for {strategy_name}/{action}/{market_regime}: {threshold}%")
            return threshold
        except KeyError:
            # Fallback to lower default for aggressive trading
            default = 25 if action_key == "buy" else 25
            self.logger.debug(f"Using aggressive default threshold for {strategy_name}/{action}: {default}%")
            return default
    
    def _combine_aggressive_signals(self, 
                                  strategy_signals: Dict[str, TradingSignal],
                                  market_regime: str) -> TradingSignal:
        """
        Aggressive signal combination with faster decision making
        """
        
        # Check trading limits first
        limits_check = self._check_trading_limits(market_regime)
        if not limits_check['allowed']:
            return TradingSignal(
                action="HOLD",
                confidence=0,
                reasoning=f"Aggressive trading blocked: {limits_check['reason']}",
                position_size_multiplier=1.0
            )
        
        # Get strategy priority for current regime
        strategy_priority = self.aggressive_strategy_priority.get(market_regime, 
                                                                ["llm_strategy", "momentum", "mean_reversion"])
        
        self.logger.info(f"🎯 Aggressive strategy priority for {market_regime}: {strategy_priority}")
        
        # Try strategies in priority order with lower thresholds
        for strategy_name in strategy_priority:
            if strategy_name not in strategy_signals:
                continue
                
            signal = strategy_signals[strategy_name]
            
            # Get aggressive threshold (lower than conservative)
            threshold = self.get_aggressive_threshold(strategy_name, signal.action, market_regime)
            
            self.logger.info(f"🔍 {strategy_name}: {signal.action} ({signal.confidence:.1f}% vs {threshold}% aggressive threshold)")
            
            # Check if strategy meets aggressive threshold
            if signal.confidence >= threshold:
                
                # Apply aggressive position sizing
                position_multiplier = self._calculate_aggressive_position_size(
                    signal, market_regime, strategy_name
                )
                
                # Build aggressive reasoning
                reasoning = f"Aggressive {market_regime} strategy: {strategy_name} ({signal.confidence:.1f}%); {signal.reasoning}"
                
                self.logger.info(f"🎯 Aggressive Decision: {signal.action} from {strategy_name} (confidence: {signal.confidence:.1f}%, position: {position_multiplier:.2f}x)")
                
                # Increment daily trade counter for BUY/SELL
                if signal.action in ['BUY', 'SELL']:
                    self.daily_trades += 1
                
                return TradingSignal(
                    action=signal.action,
                    confidence=signal.confidence,
                    reasoning=reasoning,
                    position_size_multiplier=position_multiplier
                )
            else:
                self.logger.debug(f"⏭️  {strategy_name} below aggressive threshold ({signal.confidence:.1f}% < {threshold}%)")
        
        # If no strategy meets threshold, return HOLD
        avg_confidence = sum(s.confidence for s in strategy_signals.values()) / len(strategy_signals)
        
        self.logger.info(f"🛑 No strategy meets aggressive thresholds - HOLD (avg confidence: {avg_confidence:.1f}%)")
        
        return TradingSignal(
            action="HOLD",
            confidence=avg_confidence,
            reasoning=f"No strategy meets aggressive thresholds in {market_regime} market",
            position_size_multiplier=1.0
        )
    
    def _calculate_aggressive_position_size(self, signal: TradingSignal, market_regime: str, strategy_name: str) -> float:
        """
        Calculate aggressive position sizing with risk management
        """
        # Base aggressive multiplier
        base_multiplier = 1.5  # 50% larger positions than conservative
        
        # Confidence-based adjustment (higher confidence = larger position)
        confidence_multiplier = 0.5 + (signal.confidence / 100.0)  # 0.5 to 1.5
        
        # Market regime adjustment
        regime_multipliers = {
            "high_volatility": 1.2,  # Slightly larger for volatility opportunities
            "trending": 1.3,         # Larger for trend following
            "ranging": 1.0,          # Standard for mean reversion
            "bear_market": 0.5       # Much smaller in bear markets
        }
        
        regime_multiplier = regime_multipliers.get(market_regime, 1.0)
        
        # Strategy-specific adjustment
        strategy_multipliers = {
            "scalping": 0.8,         # Smaller for frequent scalping
            "volatility_breakout": 1.2,  # Larger for breakouts
            "momentum": 1.1,         # Slightly larger for momentum
            "mean_reversion": 1.0,   # Standard
            "trend_following": 1.1,  # Slightly larger for trends
            "llm_strategy": 1.0      # Standard
        }
        
        strategy_multiplier = strategy_multipliers.get(strategy_name, 1.0)
        
        # Calculate final multiplier
        final_multiplier = base_multiplier * confidence_multiplier * regime_multiplier * strategy_multiplier
        
        # Apply limits based on market regime
        if market_regime == "bear_market":
            max_multiplier = 0.8  # Very conservative in bear markets
        else:
            max_multiplier = 2.0  # Max 2x position size
        
        final_multiplier = max(0.5, min(max_multiplier, final_multiplier))
        
        self.logger.debug(f"Aggressive position sizing: base={base_multiplier}, confidence={confidence_multiplier:.2f}, "
                         f"regime={regime_multiplier}, strategy={strategy_multiplier}, final={final_multiplier:.2f}")
        
        return final_multiplier
    
    def get_combined_signal(self, market_data: Dict, technical_indicators: Dict, portfolio: Optional[Dict] = None) -> TradingSignal:
        """
        Override parent method to use aggressive strategy selection
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
        
        # Get signals from all strategies (reuse parent method)
        strategy_signals = self.analyze_all_strategies(
            market_data, technical_indicators, portfolio
        )
        
        # Enhanced aggressive market regime detection
        market_regime = self.detect_aggressive_market_regime(technical_indicators, market_data)
        self.current_market_regime = market_regime
        
        # Use aggressive signal combination
        combined_signal = self._combine_aggressive_signals(
            strategy_signals, market_regime
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
            self.logger.warning(f"Failed to record aggressive decision for performance tracking: {e}")
        
        return combined_signal
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Get current daily trading statistics"""
        self._reset_daily_counters()
        
        return {
            'daily_trades': self.daily_trades,
            'daily_loss': self.daily_loss,
            'max_daily_trades': self.aggressive_config['max_daily_trades'],
            'max_daily_loss': self.aggressive_config['max_daily_loss'],
            'trades_remaining': max(0, self.aggressive_config['max_daily_trades'] - self.daily_trades),
            'loss_budget_remaining': max(0, self.aggressive_config['max_daily_loss'] - self.daily_loss),
            'last_reset_date': self.last_reset_date.isoformat()
        }