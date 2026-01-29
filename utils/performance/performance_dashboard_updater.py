"""
Performance Dashboard Updater

Integrates performance tracking data with the dashboard system.
Updates performance data files for dashboard consumption.
"""

import json
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.performance.performance_tracker import PerformanceTracker
from utils.performance.performance_calculator import PerformanceCalculator
from utils.performance.performance_manager import PerformanceManager

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
        self.manager = PerformanceManager()
        
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
            
            # Phase 3: Add advanced performance management features
            advanced_features = self._generate_advanced_features(period_data)
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tracking_info": tracking_info,
                "period_data": period_data,
                "chart_data": chart_data,
                "metrics_summary": metrics_summary,
                "overview": overview,
                "advanced_features": advanced_features,
                "snapshots_count": len(snapshots)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance data: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
            portfolio_values = []
            for s in sorted_snapshots:
                value_raw = s["total_value_eur"]
                if isinstance(value_raw, dict):
                    value = float(value_raw.get("amount", 0))
                else:
                    value = float(value_raw) if value_raw else 0
                portfolio_values.append(value)
            
            portfolio_chart = {
                "labels": [s["timestamp"] for s in sorted_snapshots],
                "datasets": [{
                    "label": "Portfolio Value (EUR)",
                    "data": portfolio_values,
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
                prev_value_raw = sorted_snapshots[i-1]["total_value_eur"]
                curr_value_raw = sorted_snapshots[i]["total_value_eur"]
                
                # Handle both dict and float formats
                if isinstance(prev_value_raw, dict):
                    prev_value = float(prev_value_raw.get("amount", 0))
                else:
                    prev_value = float(prev_value_raw) if prev_value_raw else 0
                    
                if isinstance(curr_value_raw, dict):
                    curr_value = float(curr_value_raw.get("amount", 0))
                else:
                    curr_value = float(curr_value_raw) if curr_value_raw else 0
                
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
            peak_raw = sorted_snapshots[0]["total_value_eur"]
            if isinstance(peak_raw, dict):
                peak = float(peak_raw.get("amount", 0))
            else:
                peak = float(peak_raw) if peak_raw else 0
            
            for snapshot in sorted_snapshots:
                value_raw = snapshot["total_value_eur"]
                if isinstance(value_raw, dict):
                    value = float(value_raw.get("amount", 0))
                else:
                    value = float(value_raw) if value_raw else 0
                    
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
            
            initial_value_raw = sorted_snapshots[0]["total_value_eur"]
            current_value_raw = sorted_snapshots[-1]["total_value_eur"]
            
            # Handle both dict and float formats
            if isinstance(initial_value_raw, dict):
                initial_value = float(initial_value_raw.get("amount", 0))
            else:
                initial_value = float(initial_value_raw) if initial_value_raw else 0
                
            if isinstance(current_value_raw, dict):
                current_value = float(current_value_raw.get("amount", 0))
            else:
                current_value = float(current_value_raw) if current_value_raw else 0
            
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
    
    def _generate_advanced_features(self, period_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Phase 3 advanced performance management features
        
        Args:
            period_data: Performance data for different periods
            
        Returns:
            Dict with advanced features data
        """
        try:
            advanced_features = {}
            
            # Get performance periods
            periods_info = self.manager.get_performance_periods()
            advanced_features["performance_periods"] = periods_info
            
            # Check performance goals if we have current metrics
            # Try different periods to find one with data
            current_metrics = None
            for period in ["30d", "all", "7d", "1d"]:
                period_metrics = period_data.get(period, {})
                if period_metrics and "error" not in period_metrics and len(period_metrics) > 0:
                    # Map the available metrics to goal metric names
                    mapped_metrics = {}
                    
                    # Map total return
                    if "total_return_percent" in period_metrics:
                        mapped_metrics["total_return"] = period_metrics["total_return_percent"]
                    
                    # Map monthly return (estimate from total return and period)
                    if "total_return_percent" in period_metrics and period == "30d":
                        mapped_metrics["monthly_return"] = period_metrics["total_return_percent"]
                    elif "total_return_percent" in period_metrics:
                        # Rough monthly estimate for other periods
                        days = 30 if period == "30d" else 365 if period == "1y" else 90 if period == "90d" else 7
                        monthly_factor = 30 / days
                        mapped_metrics["monthly_return"] = period_metrics["total_return_percent"] * monthly_factor
                    
                    # Map risk metrics if available
                    risk_metrics = period_metrics.get("risk_metrics", {})
                    if "sharpe_ratio" in risk_metrics:
                        mapped_metrics["sharpe_ratio"] = risk_metrics["sharpe_ratio"]
                    if "max_drawdown" in risk_metrics:
                        # Convert to negative value to match goal expectation
                        mapped_metrics["max_drawdown"] = -abs(risk_metrics["max_drawdown"])
                    
                    # TODO: Add win_rate from trading data if available
                    
                    current_metrics = mapped_metrics
                    logger.info(f"Using {period} period data for performance goals checking with {len(mapped_metrics)} metrics")
                    break
            
            if current_metrics and len(current_metrics) > 0:
                goals_status = self.manager.check_performance_goals(current_metrics)
                advanced_features["goals_status"] = goals_status
            else:
                advanced_features["goals_status"] = {
                    "status": "no_data",
                    "message": "Insufficient data for goal checking"
                }
            
            # Compare to benchmarks
            if current_metrics and "error" not in current_metrics:
                benchmark_comparison = self.manager.compare_to_benchmarks(current_metrics)
                advanced_features["benchmark_comparison"] = benchmark_comparison
            else:
                advanced_features["benchmark_comparison"] = {
                    "status": "no_data",
                    "message": "Insufficient data for benchmark comparison"
                }
            
            # Generate performance insights
            if period_data:
                insights = []
                for period, data in period_data.items():
                    if "error" not in data:
                        period_insights = self.manager._generate_performance_insights(
                            {"periods": {period: data}}, period
                        )
                        insights.extend([f"[{period.upper()}] {insight}" for insight in period_insights])
                
                advanced_features["insights"] = insights[:10]  # Limit to top 10 insights
            else:
                advanced_features["insights"] = ["No performance insights available"]
            
            # Performance grades for each period
            performance_grades = {}
            for period, data in period_data.items():
                if "error" not in data:
                    grade = self.manager._calculate_performance_grade(data)
                    performance_grades[period] = grade
            
            advanced_features["performance_grades"] = performance_grades
            
            # Quick stats summary
            advanced_features["quick_stats"] = self._generate_quick_stats(period_data)
            
            return advanced_features
            
        except Exception as e:
            logger.error(f"Error generating advanced features: {e}")
            return {
                "error": str(e),
                "performance_periods": {"periods": [], "active_period": None},
                "goals_status": {"status": "error", "message": str(e)},
                "benchmark_comparison": {"status": "error", "message": str(e)},
                "insights": ["Error generating insights"],
                "performance_grades": {},
                "quick_stats": {}
            }
    
    def _generate_quick_stats(self, period_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quick statistics summary"""
        try:
            quick_stats = {}
            
            # Best performing period
            best_return = -float('inf')
            best_period = None
            
            # Worst performing period
            worst_return = float('inf')
            worst_period = None
            
            # Average metrics
            total_returns = []
            sharpe_ratios = []
            max_drawdowns = []
            
            for period, data in period_data.items():
                if "error" not in data:
                    total_return = data.get("total_return", 0)
                    
                    if total_return > best_return:
                        best_return = total_return
                        best_period = period
                    
                    if total_return < worst_return:
                        worst_return = total_return
                        worst_period = period
                    
                    total_returns.append(total_return)
                    
                    if "sharpe_ratio" in data:
                        sharpe_ratios.append(data["sharpe_ratio"])
                    
                    if "max_drawdown" in data:
                        max_drawdowns.append(data["max_drawdown"])
            
            if total_returns:
                quick_stats["best_period"] = {
                    "period": best_period,
                    "return": best_return
                }
                
                quick_stats["worst_period"] = {
                    "period": worst_period,
                    "return": worst_return
                }
                
                quick_stats["average_return"] = sum(total_returns) / len(total_returns)
                
                if sharpe_ratios:
                    quick_stats["average_sharpe"] = sum(sharpe_ratios) / len(sharpe_ratios)
                
                if max_drawdowns:
                    quick_stats["average_drawdown"] = sum(max_drawdowns) / len(max_drawdowns)
                    quick_stats["max_drawdown_overall"] = max(max_drawdowns)
            
            return quick_stats
            
        except Exception as e:
            logger.error(f"Error generating quick stats: {e}")
            return {}
    
    def is_data_available(self) -> bool:
        """Check if performance data is available for dashboard"""
        try:
            return (self.tracker.is_tracking_enabled() and 
                   self.tracker.get_snapshots_count() >= 2)
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return False
