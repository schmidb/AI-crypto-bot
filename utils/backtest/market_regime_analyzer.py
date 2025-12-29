"""
Market Regime Analyzer for Backtesting

This module provides market regime detection and analysis capabilities
that mirror the live bot's AdaptiveStrategyManager regime detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketRegimeAnalyzer:
    """
    Market regime analyzer that uses the same logic as AdaptiveStrategyManager
    to ensure backtesting alignment with live bot behavior.
    """
    
    def __init__(self):
        """Initialize the market regime analyzer"""
        
        # Regime detection thresholds (same as AdaptiveStrategyManager)
        self.regime_thresholds = {
            'trending_price_change_24h': 4.0,      # >4% 24h change indicates trending
            'trending_price_change_5d': 8.0,       # >8% 5d change indicates trending
            'volatile_bb_width': 4.0,              # >4% BB width indicates volatility
            'ranging_price_change_24h': 1.5,       # <1.5% 24h change indicates ranging
            'ranging_bb_width': 2.0,               # <2% BB width indicates ranging
            'extreme_volatile_bb_width': 5.0       # >5% BB width = extreme volatility
        }
        
        # Adaptive confidence thresholds (same as AdaptiveStrategyManager)
        self.adaptive_thresholds = {
            "trending": {
                "trend_following": {"buy": 55, "sell": 50},
                "momentum": {"buy": 60, "sell": 55},
                "llm_strategy": {"buy": 65, "sell": 60},
                "mean_reversion": {"buy": 75, "sell": 75}
            },
            "ranging": {
                "mean_reversion": {"buy": 60, "sell": 60},
                "llm_strategy": {"buy": 65, "sell": 65},
                "momentum": {"buy": 70, "sell": 70},
                "trend_following": {"buy": 75, "sell": 75}
            },
            "volatile": {
                "llm_strategy": {"buy": 70, "sell": 70},
                "mean_reversion": {"buy": 75, "sell": 75},
                "trend_following": {"buy": 80, "sell": 80},
                "momentum": {"buy": 80, "sell": 80}
            }
        }
        
        # Strategy priorities by regime (same as AdaptiveStrategyManager)
        self.regime_strategy_priority = {
            "trending": ["trend_following", "momentum", "llm_strategy", "mean_reversion"],
            "ranging": ["mean_reversion", "llm_strategy", "momentum", "trend_following"], 
            "volatile": ["llm_strategy", "mean_reversion", "trend_following", "momentum"]
        }
        
        logger.info("🔍 MarketRegimeAnalyzer initialized with adaptive thresholds")
    
    def detect_market_regimes(self, data: pd.DataFrame) -> pd.Series:
        """
        Detect market regimes for entire dataset using same logic as AdaptiveStrategyManager
        
        Args:
            data: DataFrame with OHLCV data and technical indicators
            
        Returns:
            Series with regime classifications ('trending', 'ranging', 'volatile')
        """
        try:
            logger.info(f"🔍 Detecting market regimes for {len(data)} periods...")
            
            # Calculate price changes
            price_changes = self._calculate_price_changes(data)
            
            # Calculate Bollinger Band width
            bb_width_pct = self._calculate_bb_width_percentage(data)
            
            # Apply regime detection logic (same as AdaptiveStrategyManager)
            regimes = pd.Series(index=data.index, dtype=str)
            
            for i, timestamp in enumerate(data.index):
                try:
                    change_24h = abs(price_changes.loc[timestamp, '24h'])
                    change_5d = abs(price_changes.loc[timestamp, '5d'])
                    bb_width = bb_width_pct.loc[timestamp]
                    
                    # Apply same logic as AdaptiveStrategyManager.detect_market_regime_enhanced
                    if change_24h > self.regime_thresholds['trending_price_change_24h'] or \
                       change_5d > self.regime_thresholds['trending_price_change_5d']:
                        if bb_width > self.regime_thresholds['volatile_bb_width']:
                            regime = "volatile"  # High movement + high volatility
                        else:
                            regime = "trending"  # High movement + low volatility = trend
                    elif change_24h < self.regime_thresholds['ranging_price_change_24h'] and \
                         bb_width < self.regime_thresholds['ranging_bb_width']:
                        regime = "ranging"   # Low movement + low volatility = range
                    elif bb_width > self.regime_thresholds['extreme_volatile_bb_width']:
                        regime = "volatile"  # High volatility regardless of movement
                    else:
                        regime = "ranging"   # Default to ranging
                    
                    regimes.loc[timestamp] = regime
                    
                except Exception as e:
                    logger.warning(f"Error detecting regime for timestamp {timestamp}: {e}")
                    regimes.loc[timestamp] = "ranging"  # Safe default
            
            # Log regime distribution
            regime_counts = regimes.value_counts().to_dict()
            regime_percentages = {k: f"{v/len(regimes)*100:.1f}%" for k, v in regime_counts.items()}
            
            logger.info(f"🔍 Regime distribution: {regime_counts}")
            logger.info(f"🔍 Regime percentages: {regime_percentages}")
            
            return regimes
            
        except Exception as e:
            logger.error(f"Error detecting market regimes: {e}")
            # Return all 'ranging' as safe default
            return pd.Series('ranging', index=data.index)
    
    def _calculate_price_changes(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate price changes for regime detection"""
        try:
            price_changes = pd.DataFrame(index=data.index)
            close_prices = data['close']
            
            # Calculate 1h, 24h, and 5d price changes
            price_changes['1h'] = close_prices.pct_change(periods=1) * 100
            price_changes['24h'] = close_prices.pct_change(periods=24) * 100
            price_changes['5d'] = close_prices.pct_change(periods=120) * 100  # 5 days * 24 hours
            
            # Fill NaN values with 0
            price_changes = price_changes.fillna(0)
            
            return price_changes
            
        except Exception as e:
            logger.error(f"Error calculating price changes: {e}")
            # Return zeros as safe default
            return pd.DataFrame({
                '1h': 0, '24h': 0, '5d': 0
            }, index=data.index)
    
    def _calculate_bb_width_percentage(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Bollinger Band width as percentage"""
        try:
            # Try different possible column names for Bollinger Bands
            bb_upper_cols = ['bb_upper_20', 'bb_upper', 'bollinger_upper']
            bb_lower_cols = ['bb_lower_20', 'bb_lower', 'bollinger_lower']
            bb_middle_cols = ['bb_middle_20', 'bb_middle', 'bollinger_middle', 'sma_20']
            
            bb_upper = None
            bb_lower = None
            bb_middle = None
            
            # Find Bollinger Band columns
            for col in bb_upper_cols:
                if col in data.columns:
                    bb_upper = data[col]
                    break
            
            for col in bb_lower_cols:
                if col in data.columns:
                    bb_lower = data[col]
                    break
            
            for col in bb_middle_cols:
                if col in data.columns:
                    bb_middle = data[col]
                    break
            
            if bb_upper is not None and bb_lower is not None and bb_middle is not None:
                # Calculate BB width percentage (same as AdaptiveStrategyManager)
                bb_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100
                bb_width_pct = bb_width_pct.fillna(2.0)  # Default moderate volatility
            else:
                logger.warning("Bollinger Band columns not found, using default BB width")
                bb_width_pct = pd.Series(2.0, index=data.index)  # Default moderate volatility
            
            return bb_width_pct
            
        except Exception as e:
            logger.error(f"Error calculating BB width: {e}")
            return pd.Series(2.0, index=data.index)  # Safe default
    
    def get_adaptive_threshold(self, strategy_name: str, action: str, market_regime: str) -> float:
        """
        Get adaptive confidence threshold for strategy/action/regime combination
        (Same logic as AdaptiveStrategyManager)
        """
        action_key = action.lower()
        if action_key not in ["buy", "sell"]:
            action_key = "buy"  # Default
        
        try:
            threshold = self.adaptive_thresholds[market_regime][strategy_name][action_key]
            return threshold
        except KeyError:
            # Fallback to default
            default_thresholds = {"buy": 70, "sell": 70}
            return default_thresholds[action_key]
    
    def get_strategy_priorities(self, market_regime: str) -> List[str]:
        """Get strategy priorities for given market regime"""
        return self.regime_strategy_priority.get(market_regime, 
                                                ["llm_strategy", "trend_following", "mean_reversion", "momentum"])
    
    def analyze_regime_performance(self, data: pd.DataFrame, signals_df: pd.DataFrame, 
                                 portfolio_returns: pd.Series) -> Dict[str, Any]:
        """
        Analyze backtesting performance by market regime
        
        Args:
            data: Market data with regimes
            signals_df: Trading signals with regime information
            portfolio_returns: Portfolio returns series
            
        Returns:
            Dictionary with regime-specific performance metrics
        """
        try:
            logger.info("📊 Analyzing performance by market regime...")
            
            regime_analysis = {}
            
            # Detect regimes if not already in signals
            if 'market_regime' not in signals_df.columns:
                regimes = self.detect_market_regimes(data)
                signals_df = signals_df.copy()
                signals_df['market_regime'] = regimes
            
            # Analyze each regime
            for regime in ['trending', 'ranging', 'volatile']:
                regime_mask = signals_df['market_regime'] == regime
                
                if regime_mask.sum() == 0:
                    continue
                
                # Get regime-specific data
                regime_returns = portfolio_returns[regime_mask]
                regime_signals = signals_df[regime_mask]
                
                # Calculate regime performance metrics
                regime_metrics = self._calculate_regime_metrics(regime, regime_returns, regime_signals)
                regime_analysis[regime] = regime_metrics
            
            # Add overall regime distribution
            regime_distribution = signals_df['market_regime'].value_counts().to_dict()
            regime_analysis['regime_distribution'] = regime_distribution
            
            # Calculate regime transition analysis
            regime_transitions = self._analyze_regime_transitions(signals_df['market_regime'])
            regime_analysis['regime_transitions'] = regime_transitions
            
            logger.info(f"📊 Regime analysis completed for {len(regime_analysis)} regimes")
            return regime_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing regime performance: {e}")
            return {}
    
    def _calculate_regime_metrics(self, regime_name: str, returns: pd.Series, 
                                signals: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance metrics for a specific regime"""
        try:
            if len(returns) == 0:
                return {
                    'periods': 0,
                    'total_return': 0,
                    'avg_return': 0,
                    'volatility': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'buy_signals': 0,
                    'sell_signals': 0,
                    'avg_confidence': 0
                }
            
            # Return metrics
            total_return = (returns.sum()) * 100
            avg_return = returns.mean() * 100
            volatility = returns.std() * 100
            
            # Sharpe ratio (annualized, assuming hourly data)
            if volatility > 0:
                sharpe_ratio = (avg_return / volatility) * np.sqrt(24 * 365)  # Annualized
            else:
                sharpe_ratio = 0
            
            # Max drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            # Signal metrics
            buy_signals = int(signals['buy'].sum())
            sell_signals = int(signals['sell'].sum())
            avg_confidence = float(signals['confidence'].mean())
            
            return {
                'periods': len(returns),
                'total_return': total_return,
                'avg_return': avg_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'avg_confidence': avg_confidence
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {regime_name}: {e}")
            return {}
    
    def _analyze_regime_transitions(self, regimes: pd.Series) -> Dict[str, Any]:
        """Analyze transitions between market regimes"""
        try:
            transitions = {}
            transition_count = 0
            
            # Count transitions
            for i in range(1, len(regimes)):
                prev_regime = regimes.iloc[i-1]
                curr_regime = regimes.iloc[i]
                
                if prev_regime != curr_regime:
                    transition_count += 1
                    transition_key = f"{prev_regime}_to_{curr_regime}"
                    transitions[transition_key] = transitions.get(transition_key, 0) + 1
            
            # Calculate transition frequency
            total_periods = len(regimes)
            transition_frequency = transition_count / total_periods if total_periods > 0 else 0
            
            return {
                'total_transitions': transition_count,
                'transition_frequency': transition_frequency,
                'transition_types': transitions
            }
            
        except Exception as e:
            logger.error(f"Error analyzing regime transitions: {e}")
            return {}
    
    def validate_regime_detection_accuracy(self, data: pd.DataFrame, 
                                         manual_regimes: pd.Series = None) -> Dict[str, Any]:
        """
        Validate regime detection accuracy against manual classification
        
        Args:
            data: Market data
            manual_regimes: Manually classified regimes for validation
            
        Returns:
            Dictionary with validation metrics
        """
        try:
            if manual_regimes is None:
                logger.warning("No manual regimes provided for validation")
                return {}
            
            # Detect regimes automatically
            auto_regimes = self.detect_market_regimes(data)
            
            # Align series
            common_index = auto_regimes.index.intersection(manual_regimes.index)
            auto_aligned = auto_regimes.loc[common_index]
            manual_aligned = manual_regimes.loc[common_index]
            
            if len(common_index) == 0:
                logger.error("No common periods for regime validation")
                return {}
            
            # Calculate accuracy metrics
            total_periods = len(common_index)
            correct_classifications = (auto_aligned == manual_aligned).sum()
            accuracy = correct_classifications / total_periods
            
            # Per-regime accuracy
            regime_accuracy = {}
            for regime in ['trending', 'ranging', 'volatile']:
                regime_mask = manual_aligned == regime
                if regime_mask.sum() > 0:
                    regime_correct = (auto_aligned[regime_mask] == manual_aligned[regime_mask]).sum()
                    regime_accuracy[f'{regime}_accuracy'] = regime_correct / regime_mask.sum()
            
            # Confusion matrix
            confusion_matrix = {}
            for true_regime in ['trending', 'ranging', 'volatile']:
                for pred_regime in ['trending', 'ranging', 'volatile']:
                    mask = (manual_aligned == true_regime) & (auto_aligned == pred_regime)
                    confusion_matrix[f'{true_regime}_predicted_as_{pred_regime}'] = mask.sum()
            
            validation_results = {
                'total_periods': total_periods,
                'correct_classifications': correct_classifications,
                'overall_accuracy': accuracy,
                **regime_accuracy,
                'confusion_matrix': confusion_matrix
            }
            
            logger.info(f"🎯 Regime detection accuracy: {accuracy:.1%}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating regime detection: {e}")
            return {}

# Convenience function for regime analysis
def analyze_market_regimes(data: pd.DataFrame, signals_df: pd.DataFrame = None, 
                          portfolio_returns: pd.Series = None) -> Dict[str, Any]:
    """
    Convenience function for comprehensive market regime analysis
    
    Args:
        data: Market data with OHLCV and indicators
        signals_df: Trading signals (optional)
        portfolio_returns: Portfolio returns (optional)
        
    Returns:
        Dictionary with comprehensive regime analysis
    """
    analyzer = MarketRegimeAnalyzer()
    
    # Detect regimes
    regimes = analyzer.detect_market_regimes(data)
    
    results = {
        'regimes': regimes,
        'regime_distribution': regimes.value_counts().to_dict()
    }
    
    # Add performance analysis if data provided
    if signals_df is not None and portfolio_returns is not None:
        performance_analysis = analyzer.analyze_regime_performance(data, signals_df, portfolio_returns)
        results.update(performance_analysis)
    
    return results