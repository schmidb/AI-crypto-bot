import os
import csv
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class StrategyEvaluator:
    """
    Logs and evaluates trading strategy performance with detailed metrics.
    """
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the strategy evaluator."""
        self.log_dir = log_dir
        self.strategy_log_file = os.path.join(log_dir, "strategy_performance.csv")
        self.detailed_log_dir = os.path.join(log_dir, "detailed_logs")
        
        # Create log directories if they don't exist
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(self.detailed_log_dir, exist_ok=True)
        
        # Initialize log file with headers if it doesn't exist
        self._initialize_strategy_log_file()
        
        logger.info(f"Strategy evaluator initialized. Logs will be saved to {log_dir}")
    
    def _initialize_strategy_log_file(self):
        """Initialize the strategy performance CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.strategy_log_file):
            with open(self.strategy_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'trade_id',
                    'product_id',
                    'side',
                    'price',
                    'size',
                    'value_usd',
                    'fee_usd',
                    'profit_loss_usd',
                    'profit_loss_percent',
                    'holding_period_hours',
                    'market_volatility',
                    'market_volume',
                    'market_trend',
                    'rsi',
                    'macd',
                    'bollinger_width',
                    'llm_confidence',
                    'decision_factors',
                    'risk_level'
                ])
            logger.info(f"Created new strategy performance log file: {self.strategy_log_file}")
    
    def log_trade_decision(self, trade_data: Dict[str, Any], market_data: Dict[str, Any], 
                          indicators: Dict[str, Any], llm_analysis: Dict[str, Any],
                          strategy_params: Dict[str, Any]):
        """
        Log a trade decision with comprehensive performance metrics.
        
        Args:
            trade_data: Basic trade information
            market_data: Market conditions at time of trade
            indicators: Technical indicators at time of trade
            llm_analysis: LLM analysis results
            strategy_params: Strategy parameters used
        """
        try:
            timestamp = trade_data.get('timestamp', datetime.now().isoformat())
            trade_id = trade_data.get('trade_id', '')
            
            # Calculate profit/loss if this is a sell
            profit_loss_usd = 0.0
            profit_loss_percent = 0.0
            holding_period_hours = 0.0
            
            if trade_data.get('side') == 'sell' and trade_data.get('cost_basis_usd'):
                profit_loss_usd = trade_data.get('value_usd', 0.0) - trade_data.get('cost_basis_usd', 0.0)
                if trade_data.get('cost_basis_usd', 0.0) > 0:
                    profit_loss_percent = (profit_loss_usd / trade_data.get('cost_basis_usd', 1.0)) * 100
                
                # Calculate holding period if we have buy_timestamp
                if trade_data.get('buy_timestamp'):
                    buy_time = datetime.fromisoformat(trade_data.get('buy_timestamp'))
                    sell_time = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
                    holding_period_hours = (sell_time - buy_time).total_seconds() / 3600
            
            # Write to CSV
            with open(self.strategy_log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    trade_id,
                    trade_data.get('product_id', ''),
                    trade_data.get('side', ''),
                    trade_data.get('price', 0.0),
                    trade_data.get('size', 0.0),
                    trade_data.get('value_usd', 0.0),
                    trade_data.get('fee_usd', 0.0),
                    profit_loss_usd,
                    profit_loss_percent,
                    holding_period_hours,
                    market_data.get('volatility_24h', 0.0),
                    market_data.get('volume_24h', 0.0),
                    market_data.get('market_trend', 'neutral'),
                    indicators.get('rsi', 0.0),
                    indicators.get('macd', 0.0),
                    indicators.get('bollinger_width', 0.0),
                    llm_analysis.get('confidence', 0.0),
                    str(llm_analysis.get('key_factors', []))[:100],  # Truncate for CSV
                    strategy_params.get('risk_level', 'medium')
                ])
            
            # Save detailed log as JSON
            detailed_log = {
                'trade_data': trade_data,
                'market_data': market_data,
                'indicators': indicators,
                'llm_analysis': llm_analysis,
                'strategy_params': strategy_params,
                'performance_metrics': {
                    'profit_loss_usd': profit_loss_usd,
                    'profit_loss_percent': profit_loss_percent,
                    'holding_period_hours': holding_period_hours
                }
            }
            
            # Save detailed log to JSON file
            detailed_log_file = os.path.join(
                self.detailed_log_dir, 
                f"{trade_data.get('product_id', 'unknown').replace('-', '_')}_{trade_id}_{timestamp.replace(':', '-')}.json"
            )
            
            with open(detailed_log_file, 'w') as f:
                json.dump(detailed_log, f, indent=2, default=str)
            
            logger.info(f"Logged detailed strategy metrics for trade ID: {trade_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging strategy metrics: {e}")
            return False
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate overall strategy performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        try:
            if not os.path.exists(self.strategy_log_file):
                logger.warning(f"Strategy log file not found: {self.strategy_log_file}")
                return {}
            
            df = pd.read_csv(self.strategy_log_file)
            if df.empty:
                return {}
            
            # Filter to only include completed trades (with profit/loss)
            completed_trades = df[df['profit_loss_usd'] != 0]
            
            # Calculate metrics
            metrics = {}
            
            # Basic metrics
            metrics['total_trades'] = len(df)
            metrics['completed_trades'] = len(completed_trades)
            metrics['total_volume_usd'] = df['value_usd'].sum()
            
            if not completed_trades.empty:
                # Win/loss metrics
                winning_trades = completed_trades[completed_trades['profit_loss_usd'] > 0]
                losing_trades = completed_trades[completed_trades['profit_loss_usd'] < 0]
                
                metrics['winning_trades'] = len(winning_trades)
                metrics['losing_trades'] = len(losing_trades)
                
                if len(winning_trades) > 0 and len(losing_trades) > 0:
                    metrics['win_rate'] = len(winning_trades) / len(completed_trades)
                    metrics['avg_win_usd'] = winning_trades['profit_loss_usd'].mean()
                    metrics['avg_loss_usd'] = losing_trades['profit_loss_usd'].mean()
                    metrics['profit_factor'] = abs(winning_trades['profit_loss_usd'].sum() / losing_trades['profit_loss_usd'].sum()) if losing_trades['profit_loss_usd'].sum() != 0 else float('inf')
                
                # Overall performance
                metrics['total_profit_loss_usd'] = completed_trades['profit_loss_usd'].sum()
                metrics['avg_profit_loss_usd'] = completed_trades['profit_loss_usd'].mean()
                metrics['avg_profit_loss_percent'] = completed_trades['profit_loss_percent'].mean()
                
                # Risk metrics
                metrics['max_profit_usd'] = completed_trades['profit_loss_usd'].max()
                metrics['max_loss_usd'] = completed_trades['profit_loss_usd'].min()
                metrics['profit_loss_std_dev'] = completed_trades['profit_loss_usd'].std()
                
                # Time metrics
                metrics['avg_holding_period_hours'] = completed_trades['holding_period_hours'].mean()
                
                # Calculate drawdown (simplified)
                cumulative_returns = completed_trades['profit_loss_usd'].cumsum()
                if not cumulative_returns.empty:
                    running_max = cumulative_returns.cummax()
                    drawdown = (cumulative_returns - running_max)
                    metrics['max_drawdown_usd'] = drawdown.min()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def generate_performance_report(self, output_file: str):
        """
        Generate a detailed performance report in Excel format.
        
        Args:
            output_file: Path to output Excel file
        """
        try:
            # Calculate performance metrics
            metrics = self.calculate_performance_metrics()
            if not metrics:
                logger.warning("No performance metrics available for report")
                return False
            
            # Read the strategy log
            df = pd.read_csv(self.strategy_log_file)
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Create Excel writer
            with pd.ExcelWriter(output_file) as writer:
                # Write summary sheet
                summary_df = pd.DataFrame([metrics])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Write all trades
                df.to_excel(writer, sheet_name='All Trades', index=False)
                
                # Write winning trades
                winning_trades = df[df['profit_loss_usd'] > 0]
                if not winning_trades.empty:
                    winning_trades.to_excel(writer, sheet_name='Winning Trades', index=False)
                
                # Write losing trades
                losing_trades = df[df['profit_loss_usd'] < 0]
                if not losing_trades.empty:
                    losing_trades.to_excel(writer, sheet_name='Losing Trades', index=False)
                
                # Write trades by product
                for product in df['product_id'].unique():
                    product_df = df[df['product_id'] == product]
                    sheet_name = f"{product.replace('-', '_')}_Trades"[:31]  # Excel sheet name length limit
                    product_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Write correlation analysis
                if len(df) > 5:  # Need enough data for correlation
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    correlation = df[numeric_cols].corr()
                    correlation.to_excel(writer, sheet_name='Correlations')
            
            logger.info(f"Performance report generated: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return False
