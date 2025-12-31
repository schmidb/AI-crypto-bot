"""
Decision Logic Manager - Dual System Implementation
Allows switching between conservative (old) and aggressive (new) decision logic
Supports A/B testing and performance comparison
"""

import logging
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .adaptive_strategy_manager import AdaptiveStrategyManager
from .aggressive_strategy_manager import AggressiveStrategyManager
from .base_strategy import TradingSignal

class DecisionMode(Enum):
    CONSERVATIVE = "conservative"  # Current optimized system
    AGGRESSIVE = "aggressive"      # New day trading system
    HYBRID = "hybrid"             # 80% conservative, 20% aggressive
    AB_TEST = "ab_test"           # A/B testing mode

class DecisionLogicManager:
    """
    Manages switching between different decision logic systems
    Enables A/B testing and performance comparison
    """
    
    def __init__(self, config, llm_analyzer=None, news_sentiment_analyzer=None, volatility_analyzer=None):
        self.config = config
        self.logger = logging.getLogger("supervisor")
        
        # Get decision mode from environment or config
        self.decision_mode = DecisionMode(os.getenv('DECISION_MODE', 'conservative'))
        
        # Initialize both strategy managers
        self.conservative_manager = AdaptiveStrategyManager(
            config, llm_analyzer, news_sentiment_analyzer, volatility_analyzer
        )
        
        # Initialize aggressive manager (will be implemented)
        self.aggressive_manager = None
        if self.decision_mode in [DecisionMode.AGGRESSIVE, DecisionMode.HYBRID, DecisionMode.AB_TEST]:
            try:
                self.aggressive_manager = AggressiveStrategyManager(
                    config, llm_analyzer, news_sentiment_analyzer, volatility_analyzer
                )
                self.logger.info("✅ Aggressive strategy manager initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize aggressive manager: {e}")
                self.decision_mode = DecisionMode.CONSERVATIVE
                self.logger.warning("Falling back to conservative mode")
        
        # A/B testing configuration
        self.ab_test_config = {
            'conservative_allocation': 0.7,  # 70% of decisions
            'aggressive_allocation': 0.3,    # 30% of decisions
            'decision_counter': 0
        }
        
        # Performance tracking
        self.performance_log = []
        
        self.logger.info(f"🎯 Decision Logic Manager initialized in {self.decision_mode.value} mode")
    
    def get_combined_signal(self, market_data: Dict, technical_indicators: Dict, portfolio: Optional[Dict] = None) -> TradingSignal:
        """
        Get trading signal based on current decision mode
        """
        try:
            if self.decision_mode == DecisionMode.CONSERVATIVE:
                return self._get_conservative_signal(market_data, technical_indicators, portfolio)
            
            elif self.decision_mode == DecisionMode.AGGRESSIVE:
                return self._get_aggressive_signal(market_data, technical_indicators, portfolio)
            
            elif self.decision_mode == DecisionMode.HYBRID:
                return self._get_hybrid_signal(market_data, technical_indicators, portfolio)
            
            elif self.decision_mode == DecisionMode.AB_TEST:
                return self._get_ab_test_signal(market_data, technical_indicators, portfolio)
            
            else:
                self.logger.warning(f"Unknown decision mode: {self.decision_mode}, using conservative")
                return self._get_conservative_signal(market_data, technical_indicators, portfolio)
                
        except Exception as e:
            self.logger.error(f"Error in decision logic manager: {e}")
            # Fallback to conservative
            return self._get_conservative_signal(market_data, technical_indicators, portfolio)
    
    def _get_conservative_signal(self, market_data: Dict, technical_indicators: Dict, portfolio: Optional[Dict] = None) -> TradingSignal:
        """Get signal from conservative (current) strategy manager"""
        signal = self.conservative_manager.get_combined_signal(market_data, technical_indicators, portfolio)
        
        # Add metadata
        signal.metadata = {
            'decision_logic': 'conservative',
            'strategy_manager': 'adaptive',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._log_decision('conservative', signal, market_data)
        return signal
    
    def _get_aggressive_signal(self, market_data: Dict, technical_indicators: Dict, portfolio: Optional[Dict] = None) -> TradingSignal:
        """Get signal from aggressive strategy manager"""
        if not self.aggressive_manager:
            self.logger.warning("Aggressive manager not available, using conservative")
            return self._get_conservative_signal(market_data, technical_indicators, portfolio)
        
        signal = self.aggressive_manager.get_combined_signal(market_data, technical_indicators, portfolio)
        
        # Add metadata
        signal.metadata = {
            'decision_logic': 'aggressive',
            'strategy_manager': 'aggressive_day_trading',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._log_decision('aggressive', signal, market_data)
        return signal
    
    def _get_hybrid_signal(self, market_data: Dict, technical_indicators: Dict, portfolio: Optional[Dict] = None) -> TradingSignal:
        """
        Get hybrid signal: 80% conservative, 20% aggressive allocation
        Uses conservative logic but with aggressive position sizing for BUY/SELL
        """
        # Get conservative signal as base
        conservative_signal = self._get_conservative_signal(market_data, technical_indicators, portfolio)
        
        if not self.aggressive_manager:
            return conservative_signal
        
        # Get aggressive signal for comparison
        aggressive_signal = self.aggressive_manager.get_combined_signal(market_data, technical_indicators, portfolio)
        
        # Hybrid logic: Use conservative decision but aggressive position sizing if both agree
        if conservative_signal.action == aggressive_signal.action and conservative_signal.action != 'HOLD':
            # Both agree on BUY/SELL - use aggressive position sizing
            hybrid_signal = TradingSignal(
                action=conservative_signal.action,
                confidence=min(95, (conservative_signal.confidence * 0.8 + aggressive_signal.confidence * 0.2)),
                reasoning=f"Hybrid: Conservative decision ({conservative_signal.action}) confirmed by aggressive analysis. {conservative_signal.reasoning}",
                position_size_multiplier=aggressive_signal.position_size_multiplier * 0.5  # 50% of aggressive sizing
            )
        else:
            # Use conservative signal with slight confidence boost if aggressive agrees on HOLD
            confidence_boost = 5 if aggressive_signal.action == 'HOLD' else 0
            hybrid_signal = TradingSignal(
                action=conservative_signal.action,
                confidence=min(95, conservative_signal.confidence + confidence_boost),
                reasoning=f"Hybrid: Conservative decision. {conservative_signal.reasoning}",
                position_size_multiplier=conservative_signal.position_size_multiplier
            )
        
        hybrid_signal.metadata = {
            'decision_logic': 'hybrid',
            'conservative_action': conservative_signal.action,
            'aggressive_action': aggressive_signal.action,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._log_decision('hybrid', hybrid_signal, market_data)
        return hybrid_signal
    
    def _get_ab_test_signal(self, market_data: Dict, technical_indicators: Dict, portfolio: Optional[Dict] = None) -> TradingSignal:
        """
        A/B testing: Alternate between conservative and aggressive based on allocation
        """
        self.ab_test_config['decision_counter'] += 1
        
        # Determine which system to use based on allocation
        use_aggressive = (self.ab_test_config['decision_counter'] % 10) < (self.ab_test_config['aggressive_allocation'] * 10)
        
        if use_aggressive and self.aggressive_manager:
            signal = self._get_aggressive_signal(market_data, technical_indicators, portfolio)
            signal.metadata['ab_test_group'] = 'aggressive'
        else:
            signal = self._get_conservative_signal(market_data, technical_indicators, portfolio)
            signal.metadata['ab_test_group'] = 'conservative'
        
        signal.metadata['ab_test_decision'] = self.ab_test_config['decision_counter']
        
        self.logger.info(f"🧪 A/B Test Decision #{self.ab_test_config['decision_counter']}: {signal.metadata['ab_test_group']} ({signal.action})")
        
        return signal
    
    def _log_decision(self, logic_type: str, signal: TradingSignal, market_data: Dict):
        """Log decision for performance tracking"""
        try:
            decision_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'logic_type': logic_type,
                'action': signal.action,
                'confidence': signal.confidence,
                'reasoning': signal.reasoning[:200],  # Truncate for storage
                'current_price': market_data.get('price', 0),
                'product_id': market_data.get('product_id', 'Unknown')
            }
            
            self.performance_log.append(decision_log)
            
            # Keep only last 1000 decisions in memory
            if len(self.performance_log) > 1000:
                self.performance_log = self.performance_log[-1000:]
                
        except Exception as e:
            self.logger.error(f"Error logging decision: {e}")
    
    def switch_decision_mode(self, new_mode: str) -> bool:
        """
        Switch decision mode at runtime
        """
        try:
            new_decision_mode = DecisionMode(new_mode)
            
            # Initialize aggressive manager if needed
            if new_decision_mode in [DecisionMode.AGGRESSIVE, DecisionMode.HYBRID, DecisionMode.AB_TEST]:
                if not self.aggressive_manager:
                    self.aggressive_manager = AggressiveStrategyManager(
                        self.config, 
                        self.conservative_manager.llm_analyzer,
                        self.conservative_manager.news_sentiment_analyzer,
                        self.conservative_manager.volatility_analyzer
                    )
            
            old_mode = self.decision_mode.value
            self.decision_mode = new_decision_mode
            
            self.logger.info(f"🔄 Decision mode switched: {old_mode} -> {new_mode}")
            
            # Save mode change to file for persistence
            self._save_mode_change(old_mode, new_mode)
            
            return True
            
        except ValueError as e:
            self.logger.error(f"Invalid decision mode: {new_mode}")
            return False
        except Exception as e:
            self.logger.error(f"Error switching decision mode: {e}")
            return False
    
    def _save_mode_change(self, old_mode: str, new_mode: str):
        """Save mode change to file for audit trail"""
        try:
            mode_change = {
                'timestamp': datetime.utcnow().isoformat(),
                'old_mode': old_mode,
                'new_mode': new_mode,
                'changed_by': 'system'  # Could be extended to track user
            }
            
            # Append to mode changes log
            log_file = 'data/decision_mode_changes.json'
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    changes = json.load(f)
            else:
                changes = []
            
            changes.append(mode_change)
            
            # Keep only last 100 changes
            if len(changes) > 100:
                changes = changes[-100:]
            
            with open(log_file, 'w') as f:
                json.dump(changes, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving mode change: {e}")
    
    def get_performance_comparison(self) -> Dict[str, Any]:
        """
        Get performance comparison between decision logic types
        """
        try:
            # Group decisions by logic type
            logic_performance = {}
            
            for decision in self.performance_log:
                logic_type = decision['logic_type']
                if logic_type not in logic_performance:
                    logic_performance[logic_type] = {
                        'total_decisions': 0,
                        'buy_decisions': 0,
                        'sell_decisions': 0,
                        'hold_decisions': 0,
                        'avg_confidence': 0,
                        'confidence_sum': 0
                    }
                
                perf = logic_performance[logic_type]
                perf['total_decisions'] += 1
                perf[f"{decision['action'].lower()}_decisions"] += 1
                perf['confidence_sum'] += decision['confidence']
                perf['avg_confidence'] = perf['confidence_sum'] / perf['total_decisions']
            
            return {
                'performance_by_logic': logic_performance,
                'total_decisions_tracked': len(self.performance_log),
                'current_mode': self.decision_mode.value,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating performance comparison: {e}")
            return {'error': str(e)}
    
    def get_current_mode(self) -> str:
        """Get current decision mode"""
        return self.decision_mode.value
    
    def is_aggressive_available(self) -> bool:
        """Check if aggressive manager is available"""
        return self.aggressive_manager is not None