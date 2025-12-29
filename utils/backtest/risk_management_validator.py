"""
Risk Management Validator for Backtesting

This module validates risk management features by testing them against
historical scenarios and ensuring they work as expected in backtesting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
from datetime import datetime, timedelta
import sys

# Add project root to path for imports
sys.path.append('.')

from utils.trading.capital_manager import CapitalManager
from config import Config

logger = logging.getLogger(__name__)

class RiskManagementValidator:
    """
    Validates risk management features in backtesting environment
    to ensure they work correctly and prevent excessive losses.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the risk management validator"""
        self.config = config or Config()
        
        # Initialize capital manager (same as live bot)
        try:
            self.capital_manager = CapitalManager(self.config)
            logger.info("✅ CapitalManager initialized for risk validation")
        except Exception as e:
            logger.error(f"Failed to initialize CapitalManager: {e}")
            raise
        
        # Risk validation thresholds
        self.validation_thresholds = {
            'max_single_trade_percent': 35.0,  # Max 35% of portfolio in single trade
            'min_eur_reserve_percent': 12.0,   # Min 12% EUR reserve
            'max_drawdown_percent': 20.0,      # Max 20% drawdown before intervention
            'min_trade_amount': 5.0,           # Min €5 trade size
            'max_position_concentration': 75.0  # Max 75% in single asset
        }
        
        # Track validation results
        self.validation_results = []
        
        logger.info("🛡️ RiskManagementValidator initialized")
    
    def validate_trade_size(self, action: str, asset: str, portfolio: Dict, 
                          requested_size: float) -> Dict[str, Any]:
        """
        Validate a proposed trade size against risk management rules
        
        Args:
            action: Trade action (BUY/SELL)
            asset: Asset symbol (BTC, ETH, etc.)
            portfolio: Current portfolio state
            requested_size: Requested trade size in base currency
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Use capital manager to calculate safe trade size
            safe_size, reason = self.capital_manager.calculate_safe_trade_size(
                action, asset, portfolio, requested_size
            )
            
            # Determine if trade is approved
            approved = safe_size > 0
            
            # Calculate risk metrics
            portfolio_value = portfolio.get('portfolio_value_eur', {}).get('amount', 10000)
            trade_percent = (requested_size / portfolio_value) * 100 if portfolio_value > 0 else 0
            
            # Risk assessment
            if trade_percent > self.validation_thresholds['max_single_trade_percent']:
                risk_level = 'high'
            elif trade_percent > 20:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'approved': approved,
                'safe_trade_size': safe_size,
                'requested_size': requested_size,
                'size_reduction': requested_size - safe_size,
                'trade_percent': trade_percent,
                'risk_level': risk_level,
                'reason': reason,
                'validation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating trade size: {e}")
            return {
                'approved': False,
                'safe_trade_size': 0.0,
                'requested_size': requested_size,
                'size_reduction': requested_size,
                'trade_percent': 0.0,
                'risk_level': 'high',
                'reason': f'Validation error: {str(e)}',
                'error': str(e)
            }
    
    def validate_position_sizing(self, portfolio_states: List[Dict], 
                                trade_signals: List[Dict]) -> Dict[str, Any]:
        """
        Validate position sizing logic against risk management rules
        
        Args:
            portfolio_states: List of portfolio states over time
            trade_signals: List of trade signals with proposed sizes
            
        Returns:
            Dictionary with validation results
        """
        try:
            logger.info("🧪 Validating position sizing logic...")
            
            violations = []
            approved_trades = 0
            blocked_trades = 0
            
            for i, (portfolio, signal) in enumerate(zip(portfolio_states, trade_signals)):
                try:
                    # Extract trade details
                    action = signal.get('action', 'HOLD')
                    asset = signal.get('asset', 'BTC')
                    proposed_size = signal.get('proposed_size', 0)
                    
                    if action == 'HOLD' or proposed_size <= 0:
                        continue
                    
                    # Calculate safe trade size using capital manager
                    safe_size, reason = self.capital_manager.calculate_safe_trade_size(
                        action, asset, portfolio, proposed_size
                    )
                    
                    # Check for violations
                    portfolio_value = portfolio.get('portfolio_value_eur', {}).get('amount', 10000)
                    trade_percent = (proposed_size / portfolio_value) * 100
                    
                    if safe_size <= 0:
                        blocked_trades += 1
                        if 'insufficient' not in reason.lower():
                            violations.append({
                                'type': 'blocked_trade',
                                'index': i,
                                'action': action,
                                'asset': asset,
                                'proposed_size': proposed_size,
                                'reason': reason,
                                'trade_percent': trade_percent
                            })
                    else:
                        approved_trades += 1
                        
                        # Check if trade size exceeds maximum allowed percentage
                        if trade_percent > self.validation_thresholds['max_single_trade_percent']:
                            violations.append({
                                'type': 'oversized_trade',
                                'index': i,
                                'action': action,
                                'asset': asset,
                                'proposed_size': proposed_size,
                                'safe_size': safe_size,
                                'trade_percent': trade_percent,
                                'max_allowed_percent': self.validation_thresholds['max_single_trade_percent']
                            })
                
                except Exception as e:
                    logger.warning(f"Error validating trade {i}: {e}")
                    continue
            
            # Calculate validation metrics
            total_trades = approved_trades + blocked_trades
            block_rate = blocked_trades / total_trades if total_trades > 0 else 0
            violation_rate = len(violations) / total_trades if total_trades > 0 else 0
            
            results = {
                'total_trades_evaluated': total_trades,
                'approved_trades': approved_trades,
                'blocked_trades': blocked_trades,
                'block_rate': block_rate,
                'violations': violations,
                'violation_count': len(violations),
                'violation_rate': violation_rate,
                'position_sizing_effective': violation_rate < 0.05  # Less than 5% violations
            }
            
            logger.info(f"📊 Position sizing validation:")
            logger.info(f"   Total trades: {total_trades}")
            logger.info(f"   Approved: {approved_trades}")
            logger.info(f"   Blocked: {blocked_trades} ({block_rate:.1%})")
            logger.info(f"   Violations: {len(violations)} ({violation_rate:.1%})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating position sizing: {e}")
            return {'error': str(e)}
    
    def validate_portfolio_constraints(self, portfolio_history: List[Dict]) -> Dict[str, Any]:
        """
        Validate portfolio constraint enforcement (EUR reserves, concentration limits)
        """
        try:
            logger.info("🧪 Validating portfolio constraints...")
            
            violations = []
            
            for i, portfolio in enumerate(portfolio_history):
                try:
                    # Calculate portfolio metrics
                    total_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
                    eur_amount = portfolio.get('EUR', {}).get('amount', 0)
                    
                    if total_value <= 0:
                        continue
                    
                    # Check EUR reserve constraint
                    eur_percent = (eur_amount / total_value) * 100
                    if eur_percent < self.validation_thresholds['min_eur_reserve_percent']:
                        violations.append({
                            'type': 'insufficient_eur_reserve',
                            'index': i,
                            'eur_percent': eur_percent,
                            'min_required_percent': self.validation_thresholds['min_eur_reserve_percent'],
                            'total_value': total_value,
                            'eur_amount': eur_amount
                        })
                    
                    # Check asset concentration limits
                    for asset in ['BTC', 'ETH', 'SOL']:
                        if asset in portfolio:
                            asset_data = portfolio[asset]
                            if isinstance(asset_data, dict):
                                asset_amount = asset_data.get('amount', 0)
                                asset_price = asset_data.get('last_price_eur', 0)
                                asset_value = asset_amount * asset_price
                                asset_percent = (asset_value / total_value) * 100
                                
                                if asset_percent > self.validation_thresholds['max_position_concentration']:
                                    violations.append({
                                        'type': 'excessive_concentration',
                                        'index': i,
                                        'asset': asset,
                                        'asset_percent': asset_percent,
                                        'max_allowed_percent': self.validation_thresholds['max_position_concentration'],
                                        'asset_value': asset_value,
                                        'total_value': total_value
                                    })
                
                except Exception as e:
                    logger.warning(f"Error validating portfolio {i}: {e}")
                    continue
            
            # Calculate results
            total_snapshots = len(portfolio_history)
            violation_rate = len(violations) / total_snapshots if total_snapshots > 0 else 0
            
            results = {
                'total_snapshots': total_snapshots,
                'violations': violations,
                'violation_count': len(violations),
                'violation_rate': violation_rate,
                'constraints_effective': violation_rate < 0.1  # Less than 10% violations
            }
            
            logger.info(f"📊 Portfolio constraints validation:")
            logger.info(f"   Total snapshots: {total_snapshots}")
            logger.info(f"   Violations: {len(violations)} ({violation_rate:.1%})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating portfolio constraints: {e}")
            return {'error': str(e)}
    
    def validate_drawdown_protection(self, portfolio_values: pd.Series, 
                                   trade_history: List[Dict]) -> Dict[str, Any]:
        """
        Validate drawdown protection mechanisms
        """
        try:
            logger.info("🧪 Validating drawdown protection...")
            
            if portfolio_values.empty:
                return {'error': 'No portfolio values provided'}
            
            # Calculate drawdowns
            running_max = portfolio_values.expanding().max()
            drawdowns = (portfolio_values - running_max) / running_max * 100
            max_drawdown = drawdowns.min()
            
            # Find drawdown periods
            drawdown_periods = []
            in_drawdown = False
            drawdown_start = None
            
            for i, dd in enumerate(drawdowns):
                if dd < -5.0 and not in_drawdown:  # Start of significant drawdown
                    in_drawdown = True
                    drawdown_start = i
                elif dd >= -1.0 and in_drawdown:  # End of drawdown
                    in_drawdown = False
                    drawdown_periods.append({
                        'start_index': drawdown_start,
                        'end_index': i,
                        'duration': i - drawdown_start,
                        'max_drawdown': drawdowns.iloc[drawdown_start:i+1].min()
                    })
            
            # Check if trading was reduced during drawdowns
            drawdown_protection_active = False
            for period in drawdown_periods:
                period_trades = [
                    t for t in trade_history 
                    if period['start_index'] <= t.get('index', 0) <= period['end_index']
                ]
                
                if len(period_trades) == 0:
                    drawdown_protection_active = True
                    break
            
            # Validate protection effectiveness
            excessive_drawdowns = [p for p in drawdown_periods 
                                 if p['max_drawdown'] < -self.validation_thresholds['max_drawdown_percent']]
            
            results = {
                'max_drawdown_percent': max_drawdown,
                'drawdown_periods': len(drawdown_periods),
                'excessive_drawdowns': len(excessive_drawdowns),
                'drawdown_protection_active': drawdown_protection_active,
                'protection_effective': len(excessive_drawdowns) == 0,
                'drawdown_details': drawdown_periods[:5]  # First 5 periods for analysis
            }
            
            logger.info(f"📊 Drawdown protection validation:")
            logger.info(f"   Max drawdown: {max_drawdown:.2f}%")
            logger.info(f"   Drawdown periods: {len(drawdown_periods)}")
            logger.info(f"   Excessive drawdowns: {len(excessive_drawdowns)}")
            logger.info(f"   Protection active: {drawdown_protection_active}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating drawdown protection: {e}")
            return {'error': str(e)}
    
    def validate_trade_size_limits(self, trade_history: List[Dict]) -> Dict[str, Any]:
        """
        Validate minimum and maximum trade size enforcement
        """
        try:
            logger.info("🧪 Validating trade size limits...")
            
            violations = []
            valid_trades = 0
            
            for i, trade in enumerate(trade_history):
                try:
                    trade_amount = trade.get('trade_amount_base', 0)
                    action = trade.get('action', 'HOLD')
                    
                    if action == 'HOLD' or trade_amount <= 0:
                        continue
                    
                    # Check minimum trade size
                    if trade_amount < self.validation_thresholds['min_trade_amount']:
                        violations.append({
                            'type': 'undersized_trade',
                            'index': i,
                            'trade_amount': trade_amount,
                            'min_required': self.validation_thresholds['min_trade_amount'],
                            'action': action
                        })
                    else:
                        valid_trades += 1
                
                except Exception as e:
                    logger.warning(f"Error validating trade {i}: {e}")
                    continue
            
            total_trades = valid_trades + len(violations)
            violation_rate = len(violations) / total_trades if total_trades > 0 else 0
            
            results = {
                'total_trades': total_trades,
                'valid_trades': valid_trades,
                'violations': violations,
                'violation_count': len(violations),
                'violation_rate': violation_rate,
                'size_limits_effective': violation_rate < 0.05
            }
            
            logger.info(f"📊 Trade size limits validation:")
            logger.info(f"   Total trades: {total_trades}")
            logger.info(f"   Valid trades: {valid_trades}")
            logger.info(f"   Violations: {len(violations)} ({violation_rate:.1%})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating trade size limits: {e}")
            return {'error': str(e)}
    
    def run_comprehensive_validation(self, backtest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run comprehensive risk management validation
        
        Args:
            backtest_data: Dictionary containing:
                - portfolio_history: List of portfolio states
                - trade_history: List of executed trades
                - portfolio_values: Series of portfolio values over time
                - trade_signals: List of trade signals with proposed sizes
                
        Returns:
            Comprehensive validation results
        """
        try:
            logger.info("🛡️ Running comprehensive risk management validation...")
            
            # Extract data
            portfolio_history = backtest_data.get('portfolio_history', [])
            trade_history = backtest_data.get('trade_history', [])
            portfolio_values = backtest_data.get('portfolio_values', pd.Series())
            trade_signals = backtest_data.get('trade_signals', [])
            
            # Run individual validations
            validation_results = {}
            
            # Position sizing validation
            if portfolio_history and trade_signals:
                validation_results['position_sizing'] = self.validate_position_sizing(
                    portfolio_history, trade_signals
                )
            
            # Portfolio constraints validation
            if portfolio_history:
                validation_results['portfolio_constraints'] = self.validate_portfolio_constraints(
                    portfolio_history
                )
            
            # Drawdown protection validation
            if not portfolio_values.empty and trade_history:
                validation_results['drawdown_protection'] = self.validate_drawdown_protection(
                    portfolio_values, trade_history
                )
            
            # Trade size limits validation
            if trade_history:
                validation_results['trade_size_limits'] = self.validate_trade_size_limits(
                    trade_history
                )
            
            # Calculate overall risk management effectiveness
            effectiveness_scores = []
            for validation_name, results in validation_results.items():
                if 'error' not in results:
                    # Extract effectiveness indicators
                    if 'position_sizing_effective' in results:
                        effectiveness_scores.append(1.0 if results['position_sizing_effective'] else 0.0)
                    elif 'constraints_effective' in results:
                        effectiveness_scores.append(1.0 if results['constraints_effective'] else 0.0)
                    elif 'protection_effective' in results:
                        effectiveness_scores.append(1.0 if results['protection_effective'] else 0.0)
                    elif 'size_limits_effective' in results:
                        effectiveness_scores.append(1.0 if results['size_limits_effective'] else 0.0)
            
            overall_effectiveness = np.mean(effectiveness_scores) if effectiveness_scores else 0.0
            
            # Compile final results
            final_results = {
                'validation_timestamp': datetime.now().isoformat(),
                'validations_run': list(validation_results.keys()),
                'individual_results': validation_results,
                'overall_effectiveness_score': overall_effectiveness,
                'risk_management_grade': self._calculate_grade(overall_effectiveness),
                'recommendations': self._generate_recommendations(validation_results)
            }
            
            logger.info(f"🛡️ Risk management validation completed:")
            logger.info(f"   Overall effectiveness: {overall_effectiveness:.1%}")
            logger.info(f"   Grade: {final_results['risk_management_grade']}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive risk validation: {e}")
            return {'error': str(e)}
    
    def _calculate_grade(self, effectiveness_score: float) -> str:
        """Calculate letter grade based on effectiveness score"""
        if effectiveness_score >= 0.95:
            return "A+ (Excellent)"
        elif effectiveness_score >= 0.90:
            return "A (Very Good)"
        elif effectiveness_score >= 0.80:
            return "B (Good)"
        elif effectiveness_score >= 0.70:
            return "C (Acceptable)"
        elif effectiveness_score >= 0.60:
            return "D (Needs Improvement)"
        else:
            return "F (Poor)"
    
    def _generate_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        for validation_name, results in validation_results.items():
            if 'error' in results:
                recommendations.append(f"Fix {validation_name} validation errors")
                continue
            
            if validation_name == 'position_sizing':
                if results.get('violation_rate', 0) > 0.05:
                    recommendations.append("Review position sizing logic - too many violations")
                if results.get('block_rate', 0) > 0.5:
                    recommendations.append("Position sizing may be too conservative - high block rate")
            
            elif validation_name == 'portfolio_constraints':
                if results.get('violation_rate', 0) > 0.1:
                    recommendations.append("Strengthen portfolio constraint enforcement")
            
            elif validation_name == 'drawdown_protection':
                if results.get('excessive_drawdowns', 0) > 0:
                    recommendations.append("Improve drawdown protection mechanisms")
                if not results.get('protection_effective', True):
                    recommendations.append("Drawdown protection not activating properly")
            
            elif validation_name == 'trade_size_limits':
                if results.get('violation_rate', 0) > 0.05:
                    recommendations.append("Enforce minimum trade size limits more strictly")
        
        if not recommendations:
            recommendations.append("Risk management is working effectively")
        
        return recommendations
        