"""
Performance Calculator - Calculate various performance metrics

This module provides comprehensive performance calculation functionality including
return calculations, risk metrics, and trading performance analysis.
"""

import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from statistics import mean, stdev
import numpy as np

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """
    Calculate various performance metrics from portfolio snapshots and trade history
    
    Provides comprehensive performance analysis including total returns, risk metrics,
    trading performance, and market performance separation.
    """
    
    def __init__(self):
        """Initialize the performance calculator"""
        logger.debug("Performance calculator initialized")
    
    def calculate_total_return(self, snapshots: List[Dict[str, Any]], 
                             period: str = "all") -> Dict[str, Any]:
        """
        Calculate total return for the specified period
        
        Args:
            snapshots: List of portfolio snapshots
            period: Time period for calculation
            
        Returns:
            Dict containing total return metrics
        """
        try:
            if len(snapshots) < 2:
                return {"error": "Insufficient data for return calculation"}
            
            # Sort snapshots by timestamp
            sorted_snapshots = sorted(snapshots, key=lambda x: x["timestamp"])
            
            initial_value_raw = sorted_snapshots[0]["total_value_eur"]
            final_value_raw = sorted_snapshots[-1]["total_value_eur"]
            
            # Handle both dict and float formats for total_value_eur
            if isinstance(initial_value_raw, dict):
                initial_value = float(initial_value_raw.get("amount", 0))
            else:
                initial_value = float(initial_value_raw) if initial_value_raw else 0
                
            if isinstance(final_value_raw, dict):
                final_value = float(final_value_raw.get("amount", 0))
            else:
                final_value = float(final_value_raw) if final_value_raw else 0
            
            if initial_value <= 0:
                return {"error": "Invalid initial portfolio value"}
            
            # Calculate returns
            absolute_return = final_value - initial_value
            percentage_return = (absolute_return / initial_value) * 100
            
            # Calculate time period
            start_date = datetime.fromisoformat(sorted_snapshots[0]["timestamp"])
            end_date = datetime.fromisoformat(sorted_snapshots[-1]["timestamp"])
            
            # Make timezone-aware if naive
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            days_elapsed = (end_date - start_date).days
            
            # Calculate annualized return
            annualized_return = 0.0
            if days_elapsed > 0:
                years_elapsed = days_elapsed / 365.25
                if years_elapsed > 0:
                    annualized_return = (((final_value / initial_value) ** (1 / years_elapsed)) - 1) * 100
            
            result = {
                "period": period,
                "start_date": sorted_snapshots[0]["timestamp"],
                "end_date": sorted_snapshots[-1]["timestamp"],
                "days_elapsed": days_elapsed,
                "initial_value": initial_value,
                "final_value": final_value,
                "absolute_return": absolute_return,
                "percentage_return": percentage_return,
                "annualized_return": annualized_return,
                "snapshots_used": len(sorted_snapshots)
            }
            
            logger.debug(f"Total return calculated: {percentage_return:.2f}% over {days_elapsed} days")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating total return: {e}")
            return {"error": str(e)}
    
    def calculate_trading_performance(self, trade_history: List[Dict[str, Any]],
                                    period_start: Optional[str] = None,
                                    period_end: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate performance from trading activity only
        
        Args:
            trade_history: List of executed trades
            period_start: Start date for calculation (ISO format)
            period_end: End date for calculation (ISO format)
            
        Returns:
            Dict containing trading performance metrics
        """
        try:
            if not trade_history:
                return {"error": "No trade history available"}
            
            # Filter trades by period if specified
            filtered_trades = self._filter_trades_by_period(trade_history, period_start, period_end)
            
            if not filtered_trades:
                return {"error": "No trades in specified period"}
            
            # Calculate trading metrics
            total_trades = len(filtered_trades)
            winning_trades = 0
            losing_trades = 0
            total_profit = 0.0
            total_loss = 0.0
            total_fees = 0.0
            
            for trade in filtered_trades:
                # Calculate trade P&L
                trade_pnl = self._calculate_trade_pnl(trade)
                fees = trade.get("total_fees", 0.0)
                
                total_fees += fees
                
                if trade_pnl > 0:
                    winning_trades += 1
                    total_profit += trade_pnl
                elif trade_pnl < 0:
                    losing_trades += 1
                    total_loss += abs(trade_pnl)
            
            # Calculate performance metrics
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            net_profit = total_profit - total_loss - total_fees
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            average_win = total_profit / winning_trades if winning_trades > 0 else 0
            average_loss = total_loss / losing_trades if losing_trades > 0 else 0
            
            result = {
                "period_start": period_start,
                "period_end": period_end,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "total_profit": total_profit,
                "total_loss": total_loss,
                "total_fees": total_fees,
                "net_profit": net_profit,
                "profit_factor": profit_factor,
                "average_win": average_win,
                "average_loss": average_loss
            }
            
            logger.debug(f"Trading performance calculated: {win_rate:.1f}% win rate, €{net_profit:.2f} net profit")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating trading performance: {e}")
            return {"error": str(e)}
    
    def calculate_market_performance(self, snapshots: List[Dict[str, Any]],
                                   trade_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate portfolio performance from market movements (excluding trading)
        
        Args:
            snapshots: Portfolio snapshots
            trade_history: Trade history for comparison
            
        Returns:
            Dict containing market performance metrics
        """
        try:
            if len(snapshots) < 2:
                return {"error": "Insufficient snapshot data"}
            
            # Calculate total portfolio performance
            total_performance = self.calculate_total_return(snapshots)
            if "error" in total_performance:
                return total_performance
            
            # Calculate trading performance
            trading_performance = self.calculate_trading_performance(trade_history)
            
            # Market performance = Total performance - Trading performance
            total_return = total_performance.get("percentage_return", 0)
            trading_return = 0
            
            if "error" not in trading_performance:
                # Convert trading profit to percentage of initial portfolio value
                initial_value = total_performance.get("initial_value", 1)
                trading_profit = trading_performance.get("net_profit", 0)
                trading_return = (trading_profit / initial_value) * 100 if initial_value > 0 else 0
            
            market_return = total_return - trading_return
            
            result = {
                "total_return": total_return,
                "trading_return": trading_return,
                "market_return": market_return,
                "market_contribution": (market_return / total_return) * 100 if total_return != 0 else 0,
                "trading_contribution": (trading_return / total_return) * 100 if total_return != 0 else 0
            }
            
            logger.debug(f"Market performance: {market_return:.2f}% (vs {trading_return:.2f}% from trading)")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating market performance: {e}")
            return {"error": str(e)}
    
    def calculate_risk_metrics(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate risk metrics including volatility, Sharpe ratio, and max drawdown
        
        Args:
            snapshots: Portfolio snapshots
            
        Returns:
            Dict containing risk metrics
        """
        try:
            if len(snapshots) < 3:
                return {"error": "Insufficient data for risk calculation"}
            
            # Sort snapshots and calculate daily returns
            sorted_snapshots = sorted(snapshots, key=lambda x: x["timestamp"])
            daily_returns = []
            
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
                    daily_return = (curr_value - prev_value) / prev_value
                    daily_returns.append(daily_return)
            
            if len(daily_returns) < 2:
                return {"error": "Insufficient return data"}
            
            # Calculate volatility (standard deviation of returns)
            volatility_daily = stdev(daily_returns) if len(daily_returns) > 1 else 0
            volatility_annualized = volatility_daily * math.sqrt(252)  # 252 trading days per year
            
            # Calculate Sharpe ratio (assuming 0% risk-free rate)
            mean_return = mean(daily_returns)
            sharpe_ratio = (mean_return / volatility_daily) * math.sqrt(252) if volatility_daily > 0 else 0
            
            # Calculate maximum drawdown
            max_drawdown = self._calculate_max_drawdown(sorted_snapshots)
            
            # Calculate downside deviation (for Sortino ratio)
            negative_returns = [r for r in daily_returns if r < 0]
            downside_deviation = stdev(negative_returns) if len(negative_returns) > 1 else 0
            downside_deviation_annualized = downside_deviation * math.sqrt(252)
            
            # Calculate Sortino ratio
            sortino_ratio = (mean_return / downside_deviation) * math.sqrt(252) if downside_deviation > 0 else 0
            
            result = {
                "volatility_daily": volatility_daily,
                "volatility_annualized": volatility_annualized,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "max_drawdown": max_drawdown,
                "downside_deviation": downside_deviation_annualized,
                "return_samples": len(daily_returns)
            }
            
            logger.debug(f"Risk metrics calculated: Sharpe {sharpe_ratio:.2f}, Max DD {max_drawdown:.2f}%")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_max_drawdown(self, snapshots: List[Dict[str, Any]]) -> float:
        """Calculate maximum drawdown from portfolio snapshots"""
        try:
            if len(snapshots) < 2:
                return 0.0
            
            # Handle both dict and float formats for total_value_eur
            values = []
            for s in snapshots:
                value_raw = s["total_value_eur"]
                if isinstance(value_raw, dict):
                    value = float(value_raw.get("amount", 0))
                else:
                    value = float(value_raw) if value_raw else 0
                values.append(value)
            
            peak = values[0]
            max_drawdown = 0.0
            
            for value in values:
                if value > peak:
                    peak = value
                
                drawdown = ((peak - value) / peak) * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def _calculate_trade_pnl(self, trade: Dict[str, Any]) -> float:
        """Calculate profit/loss for a single trade"""
        try:
            action = trade.get("action", "").upper()
            crypto_amount = trade.get("crypto_amount", 0)
            price = trade.get("price", 0)
            
            # For now, return 0 as we need more complex logic to track
            # entry/exit prices for proper P&L calculation
            # This would require tracking position opening/closing
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating trade P&L: {e}")
            return 0.0
    
    def _filter_trades_by_period(self, trades: List[Dict[str, Any]], 
                               start_date: Optional[str], 
                               end_date: Optional[str]) -> List[Dict[str, Any]]:
        """Filter trades by date period"""
        try:
            if not start_date and not end_date:
                return trades
            
            filtered_trades = []
            
            for trade in trades:
                trade_date = trade.get("timestamp")
                if not trade_date:
                    continue
                
                trade_datetime = datetime.fromisoformat(trade_date)
                
                # Check start date
                if start_date:
                    start_datetime = datetime.fromisoformat(start_date)
                    if trade_datetime < start_datetime:
                        continue
                
                # Check end date
                if end_date:
                    end_datetime = datetime.fromisoformat(end_date)
                    if trade_datetime > end_datetime:
                        continue
                
                filtered_trades.append(trade)
            
            return filtered_trades
            
        except Exception as e:
            logger.error(f"Error filtering trades by period: {e}")
            return trades
    
    def calculate_annualized_return(self, snapshots: List[Dict[str, Any]], 
                                  period: str = "all") -> float:
        """
        Calculate annualized return (CAGR)
        
        Args:
            snapshots: Portfolio snapshots
            period: Time period
            
        Returns:
            Annualized return percentage
        """
        try:
            total_return_data = self.calculate_total_return(snapshots, period)
            return total_return_data.get("annualized_return", 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating annualized return: {e}")
            return 0.0
    
    def calculate_win_rate(self, trade_history: List[Dict[str, Any]]) -> float:
        """
        Calculate win rate from trade history
        
        Args:
            trade_history: List of trades
            
        Returns:
            Win rate percentage
        """
        try:
            trading_performance = self.calculate_trading_performance(trade_history)
            return trading_performance.get("win_rate", 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating win rate: {e}")
            return 0.0
