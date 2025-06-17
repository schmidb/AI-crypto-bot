"""
Performance Dashboard Updater

Integrates performance tracking data with the dashboard system.
Updates performance data files for dashboard consumption.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.performance_tracker import PerformanceTracker
from utils.performance_calculator import PerformanceCalculator

logger = logging.getLogger(__name__)


class PerformanceDashboardUpdater:
    """
    Updates dashboard with performance tracking data
    
    Integrates the performance tracking system with the existing dashboard
    by generating JSON data files that the dashboard can consume.
    """
    
    def __init__(self, dashboard_data_path: str = "data/dashboard/"):
        """
        Initialize the performance dashboard updater
        
        Args:
            dashboard_data_path: Path to dashboard data directory
        """
        self.dashboard_data_path = Path(dashboard_data_path)
        self.performance_data_file = self.dashboard_data_path / "performance_data.json"
        
        # Initialize performance components
        self.tracker = PerformanceTracker()
        self.calculator = PerformanceCalculator()
        
        # Ensure dashboard data directory exists
        self.dashboard_data_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Performance dashboard updater initialized: {dashboard_data_path}")
    
    def update_performance_data(self) -> bool:
        """
        Update all performance data for dashboard consumption
        
        Returns:
            bool: True if update successful
        """
        try:
            if not self.tracker.is_tracking_enabled():
                logger.warning("Performance tracking not enabled, skipping dashboard update")
                return False
            
            # Generate comprehensive performance data
            performance_data = self._generate_performance_data()
            
            # Save to dashboard data file
            with open(self.performance_data_file, 'w') as f:
                json.dump(performance_data, f, indent=2)
            
            logger.info("Performance dashboard data updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update performance dashboard data: {e}")
            return False
    
    def _generate_performance_data(self) -> Dict[str, Any]:
        """Generate comprehensive performance data for dashboard"""
        try:
            # Get tracking info
            tracking_info = self.tracker.get_tracking_info()
            
            # Get snapshots for analysis
            snapshots = self.tracker._load_snapshots()
            
            # Generate data for different time periods
            periods = ["7d", "30d", "90d", "1y", "all"]
            period_data = {}
            
            for period in periods:
                period_summary = self.tracker.get_performance_summary(period)
                if "error" not in period_summary:
                    # Add calculated metrics
                    period_snapshots = self.tracker._filter_snapshots_by_period(snapshots, period)
                    if len(period_snapshots) >= 2:
                        # Calculate additional metrics
                        total_return_data = self.calculator.calculate_total_return(period_snapshots, period)
                        risk_metrics = self.calculator.calculate_risk_metrics(period_snapshots)
                        
                        period_data[period] = {
                            **period_summary,
                            "total_return_data": total_return_data if "error" not in total_return_data else None,
                            "risk_metrics": risk_metrics if "error" not in risk_metrics else None
                        }
                    else:
                        period_data[period] = period_summary
                else:
                    period_data[period] = {"error": period_summary["error"]}
            
            # Generate chart data
            chart_data = self._generate_chart_data(snapshots)
            
            # Generate performance metrics summary
            metrics_summary = self._generate_metrics_summary(snapshots)
            
            # Generate performance overview
            overview = self._generate_performance_overview(snapshots)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "tracking_info": tracking_info,
                "period_data": period_data,
                "chart_data": chart_data,
                "metrics_summary": metrics_summary,
                "overview": overview,
                "snapshots_count": len(snapshots)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance data: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _generate_chart_data(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate chart data for dashboard visualization"""
        try:
            if len(snapshots) < 2:
                return {"error": "Insufficient data for charts"}
            
            # Sort snapshots by timestamp
            sorted_snapshots = sorted(snapshots, key=lambda x: x["timestamp"])
            
            # Generate portfolio value chart data
            portfolio_chart = {
                "labels": [s["timestamp"] for s in sorted_snapshots],
                "datasets": [{
                    "label": "Portfolio Value (EUR)",
                    "data": [s["total_value_eur"] for s in sorted_snapshots],
                    "borderColor": "#008cba",
                    "backgroundColor": "rgba(0, 140, 186, 0.1)",
                    "fill": True,
                    "tension": 0.4
                }]
            }
            
            # Generate returns chart data (daily returns)
            returns_data = []
            returns_labels = []
            
            for i in range(1, len(sorted_snapshots)):
                prev_value = sorted_snapshots[i-1]["total_value_eur"]
                curr_value = sorted_snapshots[i]["total_value_eur"]
                
                if prev_value > 0:
                    daily_return = ((curr_value - prev_value) / prev_value) * 100
                    returns_data.append(daily_return)
                    returns_labels.append(sorted_snapshots[i]["timestamp"])
            
            returns_chart = {
                "labels": returns_labels,
                "datasets": [{
                    "label": "Daily Returns (%)",
                    "data": returns_data,
                    "borderColor": "#28a745",
                    "backgroundColor": "rgba(40, 167, 69, 0.1)",
                    "fill": False,
                    "tension": 0.2
                }]
            }
            
            # Generate drawdown chart data
            drawdown_data = []
            peak = sorted_snapshots[0]["total_value_eur"]
            
            for snapshot in sorted_snapshots:
                value = snapshot["total_value_eur"]
                if value > peak:
                    peak = value
                
                drawdown = ((peak - value) / peak) * 100 if peak > 0 else 0
                drawdown_data.append(-drawdown)  # Negative for visual representation
            
            drawdown_chart = {
                "labels": [s["timestamp"] for s in sorted_snapshots],
                "datasets": [{
                    "label": "Drawdown (%)",
                    "data": drawdown_data,
                    "borderColor": "#dc3545",
                    "backgroundColor": "rgba(220, 53, 69, 0.1)",
                    "fill": True,
                    "tension": 0.4
                }]
            }
            
            return {
                "portfolio_value": portfolio_chart,
                "daily_returns": returns_chart,
                "drawdown": drawdown_chart
            }
            
        except Exception as e:
            logger.error(f"Error generating chart data: {e}")
            return {"error": str(e)}
    
    def _generate_metrics_summary(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate key performance metrics summary"""
        try:
            if len(snapshots) < 2:
                return {"error": "Insufficient data for metrics"}
            
            # Calculate comprehensive metrics
            total_return_data = self.calculator.calculate_total_return(snapshots)
            risk_metrics = self.calculator.calculate_risk_metrics(snapshots)
            
            # Get current vs initial values
            sorted_snapshots = sorted(snapshots, key=lambda x: x["timestamp"])
            initial_value = sorted_snapshots[0]["total_value_eur"]
            current_value = sorted_snapshots[-1]["total_value_eur"]
            
            # Calculate additional metrics
            days_tracked = len(snapshots)
            
            return {
                "current_value": current_value,
                "initial_value": initial_value,
                "absolute_change": current_value - initial_value,
                "total_return": total_return_data.get("percentage_return", 0) if "error" not in total_return_data else 0,
                "annualized_return": total_return_data.get("annualized_return", 0) if "error" not in total_return_data else 0,
                "volatility": risk_metrics.get("volatility_annualized", 0) if "error" not in risk_metrics else 0,
                "sharpe_ratio": risk_metrics.get("sharpe_ratio", 0) if "error" not in risk_metrics else 0,
                "max_drawdown": risk_metrics.get("max_drawdown", 0) if "error" not in risk_metrics else 0,
                "sortino_ratio": risk_metrics.get("sortino_ratio", 0) if "error" not in risk_metrics else 0,
                "days_tracked": days_tracked,
                "tracking_start": sorted_snapshots[0]["timestamp"],
                "last_update": sorted_snapshots[-1]["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {"error": str(e)}
    
    def _generate_performance_overview(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate performance overview for dashboard cards"""
        try:
            if len(snapshots) < 2:
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 2 snapshots for performance analysis"
                }
            
            # Get latest performance summary
            latest_summary = self.tracker.get_performance_summary("30d")
            
            if "error" in latest_summary:
                return {
                    "status": "error",
                    "message": latest_summary["error"]
                }
            
            # Determine performance status
            total_return = latest_summary.get("total_return_percent", 0)
            
            if total_return > 5:
                status = "excellent"
                status_color = "success"
            elif total_return > 0:
                status = "good"
                status_color = "success"
            elif total_return > -5:
                status = "neutral"
                status_color = "warning"
            else:
                status = "poor"
                status_color = "danger"
            
            return {
                "status": status,
                "status_color": status_color,
                "total_return": total_return,
                "current_value": latest_summary.get("current_value", 0),
                "initial_value": latest_summary.get("initial_value", 0),
                "period": "30d",
                "snapshots_count": latest_summary.get("snapshots_count", 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance overview: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_performance_data_for_period(self, period: str = "30d") -> Dict[str, Any]:
        """
        Get performance data for specific period
        
        Args:
            period: Time period ("7d", "30d", "90d", "1y", "all")
            
        Returns:
            Dict containing performance data for the period
        """
        try:
            if not self.tracker.is_tracking_enabled():
                return {"error": "Performance tracking not enabled"}
            
            # Get performance summary
            summary = self.tracker.get_performance_summary(period)
            
            if "error" in summary:
                return summary
            
            # Get snapshots for the period
            snapshots = self.tracker._load_snapshots()
            period_snapshots = self.tracker._filter_snapshots_by_period(snapshots, period)
            
            if len(period_snapshots) >= 2:
                # Calculate additional metrics
                total_return_data = self.calculator.calculate_total_return(period_snapshots, period)
                risk_metrics = self.calculator.calculate_risk_metrics(period_snapshots)
                
                return {
                    **summary,
                    "total_return_data": total_return_data if "error" not in total_return_data else None,
                    "risk_metrics": risk_metrics if "error" not in risk_metrics else None,
                    "snapshots_used": len(period_snapshots)
                }
            else:
                return summary
                
        except Exception as e:
            logger.error(f"Error getting performance data for period {period}: {e}")
            return {"error": str(e)}
    
    def is_data_available(self) -> bool:
        """Check if performance data is available for dashboard"""
        try:
            return (self.tracker.is_tracking_enabled() and 
                   self.tracker.get_snapshots_count() >= 2)
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return False
