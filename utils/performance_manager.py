"""
Performance Manager - Advanced performance tracking management

This module provides advanced management capabilities for performance tracking
including reset functionality, performance periods, and data export/import.
"""

import json
import os
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import uuid

from utils.performance_tracker import PerformanceTracker
from utils.performance_calculator import PerformanceCalculator

logger = logging.getLogger(__name__)


class PerformanceManager:
    """
    Advanced performance tracking management
    
    Provides functionality for:
    - Performance tracking resets with confirmation
    - Performance periods management (quarterly, yearly, custom)
    - Data export/import capabilities
    - Performance goals and benchmarks
    - Advanced analytics and reporting
    """
    
    def __init__(self, performance_path: str = "data/performance/"):
        """
        Initialize the performance manager
        
        Args:
            performance_path: Path to performance data directory
        """
        self.performance_path = Path(performance_path)
        self.tracker = PerformanceTracker(performance_path)
        self.calculator = PerformanceCalculator()
        
        # Performance periods file
        self.periods_file = self.performance_path / "performance_periods.json"
        self.goals_file = self.performance_path / "performance_goals.json"
        self.benchmarks_file = self.performance_path / "performance_benchmarks.json"
        
        # Ensure files exist
        self._ensure_files_exist()
        
        logger.info(f"Performance manager initialized: {performance_path}")
    
    def _ensure_files_exist(self) -> None:
        """Ensure all required files exist with default content"""
        try:
            # Performance periods file
            if not self.periods_file.exists():
                default_periods = {
                    "periods": [],
                    "active_period": None,
                    "created_date": datetime.utcnow().isoformat()
                }
                with open(self.periods_file, 'w') as f:
                    json.dump(default_periods, f, indent=2)
            
            # Performance goals file
            if not self.goals_file.exists():
                default_goals = {
                    "goals": [],
                    "active_goals": [],
                    "created_date": datetime.utcnow().isoformat()
                }
                with open(self.goals_file, 'w') as f:
                    json.dump(default_goals, f, indent=2)
            
            # Performance benchmarks file
            if not self.benchmarks_file.exists():
                default_benchmarks = {
                    "benchmarks": {
                        "btc_eur": {"name": "Bitcoin (BTC-EUR)", "enabled": True},
                        "eth_eur": {"name": "Ethereum (ETH-EUR)", "enabled": True},
                        "market_average": {"name": "Crypto Market Average", "enabled": False}
                    },
                    "created_date": datetime.utcnow().isoformat()
                }
                with open(self.benchmarks_file, 'w') as f:
                    json.dump(default_benchmarks, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Error ensuring performance manager files exist: {e}")
    
    # ===== PERFORMANCE RESET MANAGEMENT =====
    
    def reset_performance_with_confirmation(self, confirmation_code: str = None) -> Dict[str, Any]:
        """
        Reset performance tracking with confirmation code
        
        Args:
            confirmation_code: Required confirmation code for reset
            
        Returns:
            Dict with reset status and information
        """
        try:
            # Generate confirmation code if not provided
            if confirmation_code is None:
                reset_code = str(uuid.uuid4())[:8].upper()
                return {
                    "status": "confirmation_required",
                    "confirmation_code": reset_code,
                    "message": f"To reset performance tracking, call this method with confirmation_code='{reset_code}'",
                    "warning": "This will permanently delete all performance history!"
                }
            
            # Perform reset
            reset_result = self.tracker.reset_performance()
            
            # Create reset record
            reset_record = {
                "reset_date": datetime.utcnow().isoformat(),
                "confirmation_code": confirmation_code,
                "previous_data_backed_up": reset_result.get("backup_created", False),
                "backup_file": reset_result.get("backup_file")
            }
            
            # Save reset record
            reset_history_file = self.performance_path / "reset_history.json"
            reset_history = []
            if reset_history_file.exists():
                with open(reset_history_file, 'r') as f:
                    reset_history = json.load(f)
            
            reset_history.append(reset_record)
            with open(reset_history_file, 'w') as f:
                json.dump(reset_history, f, indent=2)
            
            logger.info(f"Performance tracking reset completed with confirmation: {confirmation_code}")
            
            return {
                "status": "success",
                "message": "Performance tracking has been reset",
                "reset_date": reset_record["reset_date"],
                "backup_created": reset_result.get("backup_created", False)
            }
            
        except Exception as e:
            logger.error(f"Error resetting performance tracking: {e}")
            return {
                "status": "error",
                "message": f"Failed to reset performance tracking: {str(e)}"
            }
    
    # ===== PERFORMANCE PERIODS MANAGEMENT =====
    
    def create_performance_period(self, name: str, description: str = "", 
                                 start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Create a new performance tracking period
        
        Args:
            name: Name of the performance period
            description: Optional description
            start_date: Period start date (defaults to now)
            end_date: Period end date (optional)
            
        Returns:
            Dict with period creation status
        """
        try:
            if start_date is None:
                start_date = datetime.utcnow()
            
            period_id = str(uuid.uuid4())
            period = {
                "id": period_id,
                "name": name,
                "description": description,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat() if end_date else None,
                "created_date": datetime.utcnow().isoformat(),
                "status": "active" if end_date is None else "planned"
            }
            
            # Load existing periods
            with open(self.periods_file, 'r') as f:
                periods_data = json.load(f)
            
            periods_data["periods"].append(period)
            
            # Set as active period if it's the first one or explicitly active
            if not periods_data["active_period"] or end_date is None:
                periods_data["active_period"] = period_id
            
            # Save updated periods
            with open(self.periods_file, 'w') as f:
                json.dump(periods_data, f, indent=2)
            
            logger.info(f"Created performance period: {name} ({period_id})")
            
            return {
                "status": "success",
                "period_id": period_id,
                "message": f"Performance period '{name}' created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating performance period: {e}")
            return {
                "status": "error",
                "message": f"Failed to create performance period: {str(e)}"
            }
    
    def get_performance_periods(self) -> Dict[str, Any]:
        """Get all performance periods"""
        try:
            with open(self.periods_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error getting performance periods: {e}")
            return {"periods": [], "active_period": None}
    
    def set_active_period(self, period_id: str) -> Dict[str, Any]:
        """Set the active performance period"""
        try:
            with open(self.periods_file, 'r') as f:
                periods_data = json.load(f)
            
            # Verify period exists
            period_exists = any(p["id"] == period_id for p in periods_data["periods"])
            if not period_exists:
                return {
                    "status": "error",
                    "message": f"Period {period_id} not found"
                }
            
            periods_data["active_period"] = period_id
            
            with open(self.periods_file, 'w') as f:
                json.dump(periods_data, f, indent=2)
            
            return {
                "status": "success",
                "message": f"Active period set to {period_id}"
            }
            
        except Exception as e:
            logger.error(f"Error setting active period: {e}")
            return {
                "status": "error",
                "message": f"Failed to set active period: {str(e)}"
            }
    
    # ===== PERFORMANCE GOALS MANAGEMENT =====
    
    def set_performance_goal(self, goal_type: str, target_value: float, 
                           timeframe: str, description: str = "") -> Dict[str, Any]:
        """
        Set a performance goal
        
        Args:
            goal_type: Type of goal (return, sharpe_ratio, max_drawdown, etc.)
            target_value: Target value for the goal
            timeframe: Timeframe for the goal (daily, weekly, monthly, yearly)
            description: Optional description
            
        Returns:
            Dict with goal creation status
        """
        try:
            goal_id = str(uuid.uuid4())
            goal = {
                "id": goal_id,
                "type": goal_type,
                "target_value": target_value,
                "timeframe": timeframe,
                "description": description,
                "created_date": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            # Load existing goals
            with open(self.goals_file, 'r') as f:
                goals_data = json.load(f)
            
            goals_data["goals"].append(goal)
            goals_data["active_goals"].append(goal_id)
            
            # Save updated goals
            with open(self.goals_file, 'w') as f:
                json.dump(goals_data, f, indent=2)
            
            logger.info(f"Created performance goal: {goal_type} = {target_value} ({timeframe})")
            
            return {
                "status": "success",
                "goal_id": goal_id,
                "message": f"Performance goal created: {goal_type} = {target_value} ({timeframe})"
            }
            
        except Exception as e:
            logger.error(f"Error setting performance goal: {e}")
            return {
                "status": "error",
                "message": f"Failed to set performance goal: {str(e)}"
            }
    
    def check_performance_goals(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check current performance against goals
        
        Args:
            current_metrics: Current performance metrics
            
        Returns:
            Dict with goal achievement status
        """
        try:
            with open(self.goals_file, 'r') as f:
                goals_data = json.load(f)
            
            goal_results = []
            
            for goal in goals_data["goals"]:
                if goal["id"] not in goals_data["active_goals"]:
                    continue
                
                goal_type = goal["type"]
                target_value = goal["target_value"]
                current_value = current_metrics.get(goal_type)
                
                if current_value is not None:
                    achieved = self._check_goal_achievement(goal_type, current_value, target_value)
                    progress = self._calculate_goal_progress(goal_type, current_value, target_value)
                    
                    goal_results.append({
                        "goal_id": goal["id"],
                        "type": goal_type,
                        "target": target_value,
                        "current": current_value,
                        "achieved": achieved,
                        "progress": progress,
                        "timeframe": goal["timeframe"]
                    })
            
            return {
                "status": "success",
                "goals_checked": len(goal_results),
                "goals_achieved": sum(1 for g in goal_results if g["achieved"]),
                "goal_results": goal_results
            }
            
        except Exception as e:
            logger.error(f"Error checking performance goals: {e}")
            return {
                "status": "error",
                "message": f"Failed to check performance goals: {str(e)}"
            }
    
    def _check_goal_achievement(self, goal_type: str, current_value: float, target_value: float) -> bool:
        """Check if a goal has been achieved"""
        if goal_type in ["total_return", "annualized_return", "sharpe_ratio"]:
            return current_value >= target_value
        elif goal_type in ["max_drawdown", "volatility"]:
            return current_value <= target_value
        else:
            return current_value >= target_value
    
    def _calculate_goal_progress(self, goal_type: str, current_value: float, target_value: float) -> float:
        """Calculate progress towards a goal (0-100%)"""
        if target_value == 0:
            return 100.0 if current_value >= 0 else 0.0
        
        if goal_type in ["max_drawdown", "volatility"]:
            # For goals where lower is better
            if current_value <= target_value:
                return 100.0
            else:
                return max(0.0, 100.0 - ((current_value - target_value) / target_value * 100))
        else:
            # For goals where higher is better
            return min(100.0, max(0.0, (current_value / target_value) * 100))
    
    # ===== BENCHMARK COMPARISON =====
    
    def add_benchmark(self, benchmark_id: str, name: str, enabled: bool = True) -> Dict[str, Any]:
        """Add a new benchmark for comparison"""
        try:
            with open(self.benchmarks_file, 'r') as f:
                benchmarks_data = json.load(f)
            
            benchmarks_data["benchmarks"][benchmark_id] = {
                "name": name,
                "enabled": enabled,
                "added_date": datetime.utcnow().isoformat()
            }
            
            with open(self.benchmarks_file, 'w') as f:
                json.dump(benchmarks_data, f, indent=2)
            
            return {
                "status": "success",
                "message": f"Benchmark '{name}' added successfully"
            }
            
        except Exception as e:
            logger.error(f"Error adding benchmark: {e}")
            return {
                "status": "error",
                "message": f"Failed to add benchmark: {str(e)}"
            }
    
    def compare_to_benchmarks(self, portfolio_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare portfolio performance to benchmarks
        
        Args:
            portfolio_metrics: Current portfolio performance metrics
            
        Returns:
            Dict with benchmark comparison results
        """
        try:
            with open(self.benchmarks_file, 'r') as f:
                benchmarks_data = json.load(f)
            
            comparisons = []
            
            for benchmark_id, benchmark_info in benchmarks_data["benchmarks"].items():
                if not benchmark_info["enabled"]:
                    continue
                
                # For now, we'll create placeholder benchmark data
                # In a real implementation, you'd fetch actual benchmark performance
                benchmark_return = self._get_benchmark_performance(benchmark_id)
                
                portfolio_return = portfolio_metrics.get("total_return", 0.0)
                outperformance = portfolio_return - benchmark_return
                
                comparisons.append({
                    "benchmark_id": benchmark_id,
                    "benchmark_name": benchmark_info["name"],
                    "benchmark_return": benchmark_return,
                    "portfolio_return": portfolio_return,
                    "outperformance": outperformance,
                    "outperforming": outperformance > 0
                })
            
            return {
                "status": "success",
                "comparisons": comparisons,
                "benchmarks_compared": len(comparisons)
            }
            
        except Exception as e:
            logger.error(f"Error comparing to benchmarks: {e}")
            return {
                "status": "error",
                "message": f"Failed to compare to benchmarks: {str(e)}"
            }
    
    def _get_benchmark_performance(self, benchmark_id: str) -> float:
        """
        Get benchmark performance (placeholder implementation)
        
        In a real implementation, this would fetch actual benchmark data
        from external APIs or stored historical data.
        """
        # Placeholder benchmark returns
        benchmark_returns = {
            "btc_eur": 15.5,  # 15.5% return
            "eth_eur": 12.3,  # 12.3% return
            "market_average": 8.7  # 8.7% return
        }
        
        return benchmark_returns.get(benchmark_id, 0.0)
    
    # ===== DATA EXPORT/IMPORT =====
    
    def export_performance_data(self, format_type: str = "json", 
                               include_snapshots: bool = True,
                               include_metrics: bool = True) -> Dict[str, Any]:
        """
        Export performance data to various formats
        
        Args:
            format_type: Export format (json, csv)
            include_snapshots: Include portfolio snapshots
            include_metrics: Include calculated metrics
            
        Returns:
            Dict with export status and file path
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            export_dir = self.performance_path / "exports"
            export_dir.mkdir(exist_ok=True)
            
            if format_type.lower() == "json":
                return self._export_json(export_dir, timestamp, include_snapshots, include_metrics)
            elif format_type.lower() == "csv":
                return self._export_csv(export_dir, timestamp, include_snapshots, include_metrics)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported export format: {format_type}"
                }
                
        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")
            return {
                "status": "error",
                "message": f"Failed to export performance data: {str(e)}"
            }
    
    def _export_json(self, export_dir: Path, timestamp: str, 
                    include_snapshots: bool, include_metrics: bool) -> Dict[str, Any]:
        """Export performance data as JSON"""
        export_file = export_dir / f"performance_export_{timestamp}.json"
        
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "export_timestamp": timestamp,
            "include_snapshots": include_snapshots,
            "include_metrics": include_metrics
        }
        
        if include_snapshots:
            snapshots = self.tracker.get_portfolio_snapshots()
            export_data["portfolio_snapshots"] = snapshots
        
        if include_metrics:
            metrics = self.tracker.get_performance_metrics()
            export_data["performance_metrics"] = metrics
        
        # Include periods, goals, and benchmarks
        export_data["performance_periods"] = self.get_performance_periods()
        
        with open(self.goals_file, 'r') as f:
            export_data["performance_goals"] = json.load(f)
        
        with open(self.benchmarks_file, 'r') as f:
            export_data["performance_benchmarks"] = json.load(f)
        
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return {
            "status": "success",
            "export_file": str(export_file),
            "format": "json",
            "message": f"Performance data exported to {export_file.name}"
        }
    
    def _export_csv(self, export_dir: Path, timestamp: str, 
                   include_snapshots: bool, include_metrics: bool) -> Dict[str, Any]:
        """Export performance data as CSV"""
        exported_files = []
        
        if include_snapshots:
            # Export portfolio snapshots
            snapshots_file = export_dir / f"portfolio_snapshots_{timestamp}.csv"
            snapshots = self.tracker.get_portfolio_snapshots()
            
            if snapshots.get("snapshots"):
                with open(snapshots_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    first_snapshot = snapshots["snapshots"][0]
                    header = ["timestamp", "total_value"] + list(first_snapshot.get("holdings", {}).keys())
                    writer.writerow(header)
                    
                    # Write data
                    for snapshot in snapshots["snapshots"]:
                        row = [
                            snapshot["timestamp"],
                            snapshot["total_value"]
                        ]
                        holdings = snapshot.get("holdings", {})
                        for asset in header[2:]:  # Skip timestamp and total_value
                            row.append(holdings.get(asset, 0))
                        writer.writerow(row)
                
                exported_files.append(snapshots_file.name)
        
        if include_metrics:
            # Export performance metrics
            metrics_file = export_dir / f"performance_metrics_{timestamp}.csv"
            metrics = self.tracker.get_performance_metrics()
            
            if metrics.get("periods"):
                with open(metrics_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    writer.writerow([
                        "period", "total_return", "annualized_return", "sharpe_ratio",
                        "max_drawdown", "volatility", "sortino_ratio"
                    ])
                    
                    # Write data
                    for period, data in metrics["periods"].items():
                        writer.writerow([
                            period,
                            data.get("total_return", 0),
                            data.get("annualized_return", 0),
                            data.get("sharpe_ratio", 0),
                            data.get("max_drawdown", 0),
                            data.get("volatility", 0),
                            data.get("sortino_ratio", 0)
                        ])
                
                exported_files.append(metrics_file.name)
        
        return {
            "status": "success",
            "exported_files": exported_files,
            "format": "csv",
            "message": f"Performance data exported to {len(exported_files)} CSV files"
        }
    
    # ===== ADVANCED ANALYTICS =====
    
    def generate_performance_report(self, period: str = "all") -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Args:
            period: Time period for report (7d, 30d, 90d, 1y, all)
            
        Returns:
            Dict with comprehensive performance report
        """
        try:
            # Get current metrics
            current_metrics = self.tracker.get_performance_metrics()
            
            # Get portfolio snapshots
            snapshots = self.tracker.get_portfolio_snapshots()
            
            # Check goals
            goals_status = self.check_performance_goals(current_metrics.get("periods", {}).get(period, {}))
            
            # Compare to benchmarks
            benchmark_comparison = self.compare_to_benchmarks(current_metrics.get("periods", {}).get(period, {}))
            
            # Generate insights
            insights = self._generate_performance_insights(current_metrics, period)
            
            report = {
                "report_date": datetime.utcnow().isoformat(),
                "period": period,
                "performance_metrics": current_metrics,
                "goals_status": goals_status,
                "benchmark_comparison": benchmark_comparison,
                "insights": insights,
                "summary": self._generate_performance_summary(current_metrics, period)
            }
            
            # Save report
            reports_dir = self.performance_path / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"performance_report_{period}_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Generated performance report for period {period}")
            
            return {
                "status": "success",
                "report": report,
                "report_file": str(report_file),
                "message": f"Performance report generated for {period} period"
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate performance report: {str(e)}"
            }
    
    def _generate_performance_insights(self, metrics: Dict[str, Any], period: str) -> List[str]:
        """Generate performance insights based on metrics"""
        insights = []
        
        period_data = metrics.get("periods", {}).get(period, {})
        
        if not period_data:
            return ["Insufficient data for performance insights"]
        
        # Return insights
        total_return = period_data.get("total_return", 0)
        if total_return > 10:
            insights.append(f"Strong performance with {total_return:.1f}% total return")
        elif total_return > 0:
            insights.append(f"Positive performance with {total_return:.1f}% total return")
        else:
            insights.append(f"Negative performance with {total_return:.1f}% total return")
        
        # Sharpe ratio insights
        sharpe_ratio = period_data.get("sharpe_ratio", 0)
        if sharpe_ratio > 1.5:
            insights.append("Excellent risk-adjusted returns (Sharpe ratio > 1.5)")
        elif sharpe_ratio > 1.0:
            insights.append("Good risk-adjusted returns (Sharpe ratio > 1.0)")
        elif sharpe_ratio > 0:
            insights.append("Positive risk-adjusted returns")
        else:
            insights.append("Poor risk-adjusted returns")
        
        # Drawdown insights
        max_drawdown = period_data.get("max_drawdown", 0)
        if max_drawdown < 5:
            insights.append("Low maximum drawdown indicates good risk management")
        elif max_drawdown < 15:
            insights.append("Moderate maximum drawdown")
        else:
            insights.append("High maximum drawdown suggests elevated risk")
        
        # Volatility insights
        volatility = period_data.get("volatility", 0)
        if volatility < 10:
            insights.append("Low volatility indicates stable performance")
        elif volatility < 25:
            insights.append("Moderate volatility")
        else:
            insights.append("High volatility indicates significant price swings")
        
        return insights
    
    def _generate_performance_summary(self, metrics: Dict[str, Any], period: str) -> Dict[str, Any]:
        """Generate performance summary"""
        period_data = metrics.get("periods", {}).get(period, {})
        
        return {
            "period": period,
            "total_return": period_data.get("total_return", 0),
            "annualized_return": period_data.get("annualized_return", 0),
            "sharpe_ratio": period_data.get("sharpe_ratio", 0),
            "max_drawdown": period_data.get("max_drawdown", 0),
            "volatility": period_data.get("volatility", 0),
            "performance_grade": self._calculate_performance_grade(period_data)
        }
    
    def _calculate_performance_grade(self, period_data: Dict[str, Any]) -> str:
        """Calculate overall performance grade (A-F)"""
        if not period_data:
            return "N/A"
        
        score = 0
        
        # Total return score (40% weight)
        total_return = period_data.get("total_return", 0)
        if total_return >= 20:
            score += 40
        elif total_return >= 10:
            score += 30
        elif total_return >= 5:
            score += 20
        elif total_return >= 0:
            score += 10
        
        # Sharpe ratio score (30% weight)
        sharpe_ratio = period_data.get("sharpe_ratio", 0)
        if sharpe_ratio >= 2.0:
            score += 30
        elif sharpe_ratio >= 1.5:
            score += 25
        elif sharpe_ratio >= 1.0:
            score += 20
        elif sharpe_ratio >= 0.5:
            score += 15
        elif sharpe_ratio >= 0:
            score += 10
        
        # Max drawdown score (20% weight)
        max_drawdown = period_data.get("max_drawdown", 100)
        if max_drawdown <= 5:
            score += 20
        elif max_drawdown <= 10:
            score += 15
        elif max_drawdown <= 20:
            score += 10
        elif max_drawdown <= 30:
            score += 5
        
        # Volatility score (10% weight)
        volatility = period_data.get("volatility", 100)
        if volatility <= 10:
            score += 10
        elif volatility <= 20:
            score += 8
        elif volatility <= 30:
            score += 6
        elif volatility <= 40:
            score += 4
        
        # Convert score to grade
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        elif score >= 45:
            return "D+"
        elif score >= 40:
            return "D"
        else:
            return "F"
