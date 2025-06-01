import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StrategyEvaluator:
    """Evaluates trading strategy performance"""
    
    def __init__(self, report_file="reports/strategy_performance.json"):
        """Initialize the strategy evaluator"""
        self.report_file = report_file
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    def evaluate(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate trading strategy performance
        
        Args:
            portfolio: Current portfolio state
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            # Calculate performance metrics
            metrics = self._calculate_metrics(portfolio)
            
            # Save performance report
            self._save_report(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating strategy: {e}")
            return {}
    
    def _calculate_metrics(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate performance metrics from portfolio data
        
        Args:
            portfolio: Current portfolio state
            
        Returns:
            Dictionary with performance metrics
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "portfolio_value_usd": portfolio.get("portfolio_value_usd", 0),
            "initial_value_usd": portfolio.get("initial_value_usd", 0),
            "trades_executed": portfolio.get("trades_executed", 0)
        }
        
        # Calculate total return
        if metrics["initial_value_usd"] > 0:
            metrics["total_return_pct"] = round(
                ((metrics["portfolio_value_usd"] - metrics["initial_value_usd"]) / metrics["initial_value_usd"]) * 100,
                2
            )
        else:
            metrics["total_return_pct"] = 0
        
        # Calculate asset allocations
        metrics["allocations"] = {}
        total_value = metrics["portfolio_value_usd"]
        
        if total_value > 0:
            for asset in ["BTC", "ETH", "USD"]:
                if asset in portfolio:
                    asset_value = portfolio[asset]["amount"]
                    if asset != "USD":
                        asset_value *= portfolio[asset]["last_price_usd"]
                    
                    metrics["allocations"][asset] = round((asset_value / total_value) * 100, 2)
        
        return metrics
    
    def _save_report(self, metrics: Dict[str, Any]) -> None:
        """
        Save performance metrics to report file
        
        Args:
            metrics: Performance metrics
        """
        try:
            # Load existing reports
            reports = []
            if os.path.exists(self.report_file):
                with open(self.report_file, 'r') as f:
                    try:
                        reports = json.load(f)
                    except json.JSONDecodeError:
                        reports = []
            
            # Add new report
            reports.append(metrics)
            
            # Save updated reports
            with open(self.report_file, 'w') as f:
                json.dump(reports, f, indent=2)
                
            logger.info(f"Strategy performance report saved: Total return {metrics.get('total_return_pct', 0)}%")
            
        except Exception as e:
            logger.error(f"Error saving performance report: {e}")
    
    def get_performance_history(self) -> Dict[str, Any]:
        """
        Get historical performance data
        
        Returns:
            Dictionary with performance history
        """
        try:
            if os.path.exists(self.report_file):
                with open(self.report_file, 'r') as f:
                    reports = json.load(f)
                
                # Extract time series data
                timestamps = []
                portfolio_values = []
                returns = []
                
                for report in reports:
                    timestamps.append(report.get("timestamp", ""))
                    portfolio_values.append(report.get("portfolio_value_usd", 0))
                    returns.append(report.get("total_return_pct", 0))
                
                return {
                    "timestamps": timestamps,
                    "portfolio_values": portfolio_values,
                    "returns": returns,
                    "latest": reports[-1] if reports else {}
                }
            
            return {"timestamps": [], "portfolio_values": [], "returns": [], "latest": {}}
            
        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            return {"timestamps": [], "portfolio_values": [], "returns": [], "latest": {}}
