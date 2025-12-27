#!/usr/bin/env python3
"""
Parameter Stability Monitor - Phase 4.4
Real-time monitoring of parameter stability and regime change detection
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

@dataclass
class ParameterAlert:
    """Parameter monitoring alert"""
    timestamp: datetime
    strategy: str
    product: str
    alert_type: str
    level: AlertLevel
    message: str
    metrics: Dict[str, Any]
    recommendations: List[str]

class MarketRegimeDetector:
    """Detect market regime changes for parameter stability monitoring"""
    
    def __init__(self):
        """Initialize regime detector"""
        self.regime_history = []
        self.current_regime = None
        self.regime_confidence = 0.0
        
    def detect_regime(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect current market regime"""
        try:
            if len(data) < 24:  # Need at least 24 hours of data
                return {
                    'regime': 'INSUFFICIENT_DATA',
                    'confidence': 0.0,
                    'characteristics': {}
                }
            
            # Calculate regime indicators
            returns = data['close'].pct_change().dropna()
            
            # Volatility (rolling 24-hour)
            volatility = returns.rolling(24).std().iloc[-1] * np.sqrt(24 * 365)
            
            # Trend strength (linear regression slope)
            prices = data['close'].iloc[-48:] if len(data) >= 48 else data['close']
            x = np.arange(len(prices))
            trend_slope = np.polyfit(x, prices, 1)[0]
            trend_strength = abs(trend_slope) / prices.mean()
            
            # Volume analysis
            volume_ma = data['volume'].rolling(24).mean().iloc[-1]
            volume_current = data['volume'].iloc[-1]
            volume_ratio = volume_current / volume_ma if volume_ma > 0 else 1.0
            
            # Price momentum
            price_change_24h = (data['close'].iloc[-1] / data['close'].iloc[-24] - 1) if len(data) >= 24 else 0
            
            # Regime classification
            regime_scores = {
                'BULL_TRENDING': 0,
                'BEAR_TRENDING': 0,
                'RANGING': 0,
                'HIGH_VOLATILITY': 0,
                'LOW_VOLATILITY': 0
            }
            
            # Bull trending indicators
            if price_change_24h > 0.02 and trend_slope > 0 and volatility < 0.6:
                regime_scores['BULL_TRENDING'] += 3
            if trend_strength > 0.001 and trend_slope > 0:
                regime_scores['BULL_TRENDING'] += 2
            if volume_ratio > 1.2:
                regime_scores['BULL_TRENDING'] += 1
            
            # Bear trending indicators
            if price_change_24h < -0.02 and trend_slope < 0 and volatility < 0.8:
                regime_scores['BEAR_TRENDING'] += 3
            if trend_strength > 0.001 and trend_slope < 0:
                regime_scores['BEAR_TRENDING'] += 2
            if volume_ratio > 1.1:
                regime_scores['BEAR_TRENDING'] += 1
            
            # Ranging indicators
            if abs(price_change_24h) < 0.01 and trend_strength < 0.0005:
                regime_scores['RANGING'] += 3
            if volatility < 0.4:
                regime_scores['RANGING'] += 2
            if volume_ratio < 0.9:
                regime_scores['RANGING'] += 1
            
            # High volatility indicators
            if volatility > 0.8:
                regime_scores['HIGH_VOLATILITY'] += 3
            if abs(price_change_24h) > 0.05:
                regime_scores['HIGH_VOLATILITY'] += 2
            if volume_ratio > 1.5:
                regime_scores['HIGH_VOLATILITY'] += 1
            
            # Low volatility indicators
            if volatility < 0.3:
                regime_scores['LOW_VOLATILITY'] += 3
            if abs(price_change_24h) < 0.005:
                regime_scores['LOW_VOLATILITY'] += 2
            if volume_ratio < 0.8:
                regime_scores['LOW_VOLATILITY'] += 1
            
            # Determine dominant regime
            dominant_regime = max(regime_scores, key=regime_scores.get)
            max_score = regime_scores[dominant_regime]
            confidence = min(1.0, max_score / 6.0)  # Normalize to 0-1
            
            regime_info = {
                'regime': dominant_regime,
                'confidence': confidence,
                'scores': regime_scores,
                'characteristics': {
                    'volatility': volatility,
                    'trend_strength': trend_strength,
                    'trend_slope': trend_slope,
                    'price_change_24h': price_change_24h,
                    'volume_ratio': volume_ratio
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Update history
            self.regime_history.append(regime_info)
            if len(self.regime_history) > 168:  # Keep 1 week of hourly data
                self.regime_history.pop(0)
            
            self.current_regime = dominant_regime
            self.regime_confidence = confidence
            
            return regime_info
            
        except Exception as e:
            logger.error(f"Failed to detect market regime: {e}")
            return {
                'regime': 'ERROR',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def detect_regime_change(self, threshold: float = 0.7) -> Optional[Dict[str, Any]]:
        """Detect if market regime has changed significantly"""
        try:
            if len(self.regime_history) < 24:  # Need at least 24 hours
                return None
            
            # Get recent regimes
            recent_regimes = [r['regime'] for r in self.regime_history[-24:]]
            older_regimes = [r['regime'] for r in self.regime_history[-48:-24]] if len(self.regime_history) >= 48 else []
            
            if not older_regimes:
                return None
            
            # Calculate regime stability
            recent_dominant = max(set(recent_regimes), key=recent_regimes.count)
            older_dominant = max(set(older_regimes), key=older_regimes.count)
            
            recent_stability = recent_regimes.count(recent_dominant) / len(recent_regimes)
            older_stability = older_regimes.count(older_dominant) / len(older_regimes)
            
            # Detect change
            regime_changed = recent_dominant != older_dominant
            stability_changed = abs(recent_stability - older_stability) > 0.3
            
            if regime_changed and recent_stability > threshold:
                return {
                    'change_detected': True,
                    'old_regime': older_dominant,
                    'new_regime': recent_dominant,
                    'old_stability': older_stability,
                    'new_stability': recent_stability,
                    'confidence': recent_stability,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to detect regime change: {e}")
            return None

class ParameterStabilityMonitor:
    """Monitor parameter stability and generate alerts"""
    
    def __init__(self, alert_thresholds: Dict[str, float] = None):
        """Initialize parameter monitor"""
        self.alert_thresholds = alert_thresholds or {
            'performance_degradation': -10.0,  # % performance drop
            'sharpe_degradation': -0.5,        # Sharpe ratio drop
            'drawdown_increase': 5.0,          # % drawdown increase
            'win_rate_drop': -0.1,             # Win rate drop
            'volatility_spike': 2.0,           # Volatility multiplier
            'regime_change_confidence': 0.7     # Regime change confidence
        }
        
        self.alerts = []
        self.performance_history = {}
        self.regime_detector = MarketRegimeDetector()
        
        # Alert storage
        self.alerts_dir = Path("./reports/alerts")
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
    
    def update_performance_history(self, strategy: str, product: str, 
                                 performance_data: Dict[str, Any]):
        """Update performance history for monitoring"""
        key = f"{strategy}_{product}"
        
        if key not in self.performance_history:
            self.performance_history[key] = []
        
        # Add timestamp
        performance_data['timestamp'] = datetime.now().isoformat()
        
        # Store performance data
        self.performance_history[key].append(performance_data)
        
        # Keep only last 30 days of data
        cutoff_date = datetime.now() - timedelta(days=30)
        self.performance_history[key] = [
            p for p in self.performance_history[key]
            if datetime.fromisoformat(p['timestamp']) > cutoff_date
        ]
    
    def check_performance_degradation(self, strategy: str, product: str) -> List[ParameterAlert]:
        """Check for performance degradation"""
        alerts = []
        key = f"{strategy}_{product}"
        
        try:
            if key not in self.performance_history or len(self.performance_history[key]) < 7:
                return alerts
            
            history = self.performance_history[key]
            
            # Compare recent vs historical performance
            recent_performance = np.mean([p.get('total_return', 0) for p in history[-3:]])
            historical_performance = np.mean([p.get('total_return', 0) for p in history[-14:-3]])
            
            performance_change = recent_performance - historical_performance
            
            if performance_change < self.alert_thresholds['performance_degradation']:
                alert = ParameterAlert(
                    timestamp=datetime.now(),
                    strategy=strategy,
                    product=product,
                    alert_type="PERFORMANCE_DEGRADATION",
                    level=AlertLevel.WARNING if performance_change > -20 else AlertLevel.CRITICAL,
                    message=f"Performance degraded by {abs(performance_change):.1f}%",
                    metrics={
                        'recent_performance': recent_performance,
                        'historical_performance': historical_performance,
                        'change': performance_change
                    },
                    recommendations=[
                        "Review recent market conditions",
                        "Consider parameter sensitivity analysis",
                        "Evaluate strategy logic for current regime"
                    ]
                )
                alerts.append(alert)
            
            # Check Sharpe ratio degradation
            recent_sharpe = np.mean([p.get('sharpe_ratio', 0) for p in history[-3:]])
            historical_sharpe = np.mean([p.get('sharpe_ratio', 0) for p in history[-14:-3]])
            sharpe_change = recent_sharpe - historical_sharpe
            
            if sharpe_change < self.alert_thresholds['sharpe_degradation']:
                alert = ParameterAlert(
                    timestamp=datetime.now(),
                    strategy=strategy,
                    product=product,
                    alert_type="SHARPE_DEGRADATION",
                    level=AlertLevel.WARNING,
                    message=f"Risk-adjusted returns degraded by {abs(sharpe_change):.2f}",
                    metrics={
                        'recent_sharpe': recent_sharpe,
                        'historical_sharpe': historical_sharpe,
                        'change': sharpe_change
                    },
                    recommendations=[
                        "Analyze risk management effectiveness",
                        "Review position sizing logic",
                        "Consider volatility-adjusted parameters"
                    ]
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check performance degradation for {strategy}/{product}: {e}")
            return alerts
    
    def check_drawdown_increase(self, strategy: str, product: str) -> List[ParameterAlert]:
        """Check for increased drawdown"""
        alerts = []
        key = f"{strategy}_{product}"
        
        try:
            if key not in self.performance_history or len(self.performance_history[key]) < 7:
                return alerts
            
            history = self.performance_history[key]
            
            # Compare recent vs historical drawdown
            recent_drawdown = np.mean([abs(p.get('max_drawdown', 0)) for p in history[-3:]])
            historical_drawdown = np.mean([abs(p.get('max_drawdown', 0)) for p in history[-14:-3]])
            
            drawdown_increase = recent_drawdown - historical_drawdown
            
            if drawdown_increase > self.alert_thresholds['drawdown_increase']:
                level = AlertLevel.CRITICAL if recent_drawdown > 20 else AlertLevel.WARNING
                
                alert = ParameterAlert(
                    timestamp=datetime.now(),
                    strategy=strategy,
                    product=product,
                    alert_type="DRAWDOWN_INCREASE",
                    level=level,
                    message=f"Drawdown increased by {drawdown_increase:.1f}% to {recent_drawdown:.1f}%",
                    metrics={
                        'recent_drawdown': recent_drawdown,
                        'historical_drawdown': historical_drawdown,
                        'increase': drawdown_increase
                    },
                    recommendations=[
                        "Implement tighter stop-losses",
                        "Reduce position sizes",
                        "Review risk management parameters",
                        "Consider strategy pause if drawdown > 25%"
                    ]
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check drawdown increase for {strategy}/{product}: {e}")
            return alerts
    
    def check_regime_change_impact(self, market_data: pd.DataFrame) -> List[ParameterAlert]:
        """Check for regime changes that might affect parameters"""
        alerts = []
        
        try:
            # Detect current regime
            regime_info = self.regime_detector.detect_regime(market_data)
            
            # Check for regime change
            regime_change = self.regime_detector.detect_regime_change()
            
            if regime_change and regime_change['change_detected']:
                confidence = regime_change['confidence']
                
                if confidence > self.alert_thresholds['regime_change_confidence']:
                    alert = ParameterAlert(
                        timestamp=datetime.now(),
                        strategy="ALL",
                        product="ALL",
                        alert_type="REGIME_CHANGE",
                        level=AlertLevel.WARNING if confidence < 0.9 else AlertLevel.CRITICAL,
                        message=f"Market regime changed from {regime_change['old_regime']} to {regime_change['new_regime']}",
                        metrics={
                            'old_regime': regime_change['old_regime'],
                            'new_regime': regime_change['new_regime'],
                            'confidence': confidence,
                            'regime_characteristics': regime_info.get('characteristics', {})
                        },
                        recommendations=[
                            "Review strategy performance in new regime",
                            "Consider parameter adjustments if underperforming",
                            "Monitor strategy effectiveness closely",
                            "Evaluate regime-specific strategy weights"
                        ]
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check regime change impact: {e}")
            return alerts
    
    def run_comprehensive_monitoring(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Run comprehensive parameter stability monitoring"""
        try:
            all_alerts = []
            
            # Check regime changes
            for product, data in market_data.items():
                regime_alerts = self.check_regime_change_impact(data)
                all_alerts.extend(regime_alerts)
            
            # Check strategy-specific issues
            strategies = ['momentum', 'mean_reversion', 'trend_following']
            products = list(market_data.keys())
            
            for strategy in strategies:
                for product in products:
                    # Check performance degradation
                    perf_alerts = self.check_performance_degradation(strategy, product)
                    all_alerts.extend(perf_alerts)
                    
                    # Check drawdown increases
                    drawdown_alerts = self.check_drawdown_increase(strategy, product)
                    all_alerts.extend(drawdown_alerts)
            
            # Store alerts
            self.alerts.extend(all_alerts)
            
            # Generate monitoring report
            monitoring_report = {
                'timestamp': datetime.now().isoformat(),
                'total_alerts': len(all_alerts),
                'alert_breakdown': {
                    'INFO': len([a for a in all_alerts if a.level == AlertLevel.INFO]),
                    'WARNING': len([a for a in all_alerts if a.level == AlertLevel.WARNING]),
                    'CRITICAL': len([a for a in all_alerts if a.level == AlertLevel.CRITICAL]),
                    'EMERGENCY': len([a for a in all_alerts if a.level == AlertLevel.EMERGENCY])
                },
                'alerts': [
                    {
                        'timestamp': alert.timestamp.isoformat(),
                        'strategy': alert.strategy,
                        'product': alert.product,
                        'type': alert.alert_type,
                        'level': alert.level.value,
                        'message': alert.message,
                        'metrics': alert.metrics,
                        'recommendations': alert.recommendations
                    }
                    for alert in all_alerts
                ],
                'regime_info': self.regime_detector.current_regime,
                'regime_confidence': self.regime_detector.regime_confidence
            }
            
            # Save monitoring report
            self.save_monitoring_report(monitoring_report)
            
            return monitoring_report
            
        except Exception as e:
            logger.error(f"Failed to run comprehensive monitoring: {e}")
            return {'error': str(e)}
    
    def save_monitoring_report(self, report: Dict[str, Any]):
        """Save monitoring report to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parameter_monitoring_{timestamp}.json"
            filepath = self.alerts_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Save as latest
            latest_filepath = self.alerts_dir / "latest_parameter_monitoring.json"
            with open(latest_filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Monitoring report saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save monitoring report: {e}")
    
    def get_critical_alerts(self, hours: int = 24) -> List[ParameterAlert]:
        """Get critical alerts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            alert for alert in self.alerts
            if alert.timestamp > cutoff_time and alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]
        ]
    
    def should_pause_strategy(self, strategy: str, product: str) -> Tuple[bool, List[str]]:
        """Determine if a strategy should be paused based on alerts"""
        reasons = []
        
        # Get recent alerts for this strategy
        recent_alerts = [
            alert for alert in self.alerts[-50:]  # Last 50 alerts
            if alert.strategy == strategy and alert.product == product
            and alert.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        # Check for emergency conditions
        emergency_alerts = [a for a in recent_alerts if a.level == AlertLevel.EMERGENCY]
        if emergency_alerts:
            reasons.append("Emergency alerts detected")
        
        # Check for multiple critical alerts
        critical_alerts = [a for a in recent_alerts if a.level == AlertLevel.CRITICAL]
        if len(critical_alerts) >= 3:
            reasons.append("Multiple critical alerts in 24 hours")
        
        # Check for severe performance degradation
        perf_alerts = [a for a in recent_alerts if a.alert_type == "PERFORMANCE_DEGRADATION"]
        severe_perf_alerts = [a for a in perf_alerts if a.metrics.get('change', 0) < -25]
        if severe_perf_alerts:
            reasons.append("Severe performance degradation (>25%)")
        
        # Check for extreme drawdown
        drawdown_alerts = [a for a in recent_alerts if a.alert_type == "DRAWDOWN_INCREASE"]
        extreme_drawdown_alerts = [a for a in drawdown_alerts if a.metrics.get('recent_drawdown', 0) > 30]
        if extreme_drawdown_alerts:
            reasons.append("Extreme drawdown detected (>30%)")
        
        should_pause = len(reasons) > 0
        return should_pause, reasons