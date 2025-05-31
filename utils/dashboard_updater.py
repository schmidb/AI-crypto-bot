#!/usr/bin/env python3
"""
Dashboard updater module for the crypto trading bot
Updates the HTML dashboard with the latest trading information
"""

import os
import json
import logging
import pandas as pd
import glob
from datetime import datetime
import shutil
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Updates the HTML dashboard with the latest trading information"""
    
    def __init__(self, dashboard_dir: str = "/var/www/html/crypto-bot"):
        """Initialize the dashboard updater"""
        self.dashboard_dir = dashboard_dir
        self.data_dir = "data"
        self.logs_dir = "logs"
        self.reports_dir = "reports"
        self.template_dir = os.path.join(os.path.dirname(__file__), "../dashboard_templates")
        
        # Ensure the dashboard directory exists
        if not os.path.exists(self.dashboard_dir):
            logger.warning(f"Dashboard directory {self.dashboard_dir} does not exist. Dashboard updates will be skipped.")
        else:
            logger.info(f"Dashboard updater initialized with directory: {self.dashboard_dir}")
    
    def update_dashboard(self, trading_results: Dict[str, Dict], bot_status: str = "running"):
        """
        Update the dashboard with the latest trading results
        
        Args:
            trading_results: Dictionary mapping trading pairs to their results
            bot_status: Current status of the bot (running, stopped, error)
        """
        if not os.path.exists(self.dashboard_dir):
            logger.warning("Dashboard directory does not exist. Skipping dashboard update.")
            return False
        
        try:
            # Load historical data
            historical_data = self._load_historical_data()
            
            # Update historical data with new results
            for pair, result in trading_results.items():
                if pair not in historical_data:
                    historical_data[pair] = []
                
                # Add timestamp if not present
                if "timestamp" not in result:
                    result["timestamp"] = datetime.now().isoformat()
                
                historical_data[pair].append(result)
            
            # Save updated historical data
            self._save_historical_data(historical_data)
            
            # Load trade history
            trade_history = self._load_trade_history()
            
            # Load strategy performance data
            strategy_performance = self._load_strategy_performance()
            
            # Generate HTML content
            html_content = self._generate_html_content(
                trading_results=trading_results,
                historical_data=historical_data,
                trade_history=trade_history,
                strategy_performance=strategy_performance,
                bot_status=bot_status
            )
            
            # Write HTML content to dashboard
            dashboard_html_path = os.path.join(self.dashboard_dir, "index.html")
            with open(dashboard_html_path, "w") as f:
                f.write(html_content)
            
            # Copy CSS file
            css_src = os.path.join(self.template_dir, "styles.css")
            css_dest = os.path.join(self.dashboard_dir, "styles.css")
            shutil.copyfile(css_src, css_dest)
            
            # Copy report files
            self._copy_reports_to_dashboard()
            
            logger.info("Dashboard updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return False
    
    def _load_historical_data(self) -> Dict[str, List[Dict]]:
        """Load historical trading data from JSON files"""
        historical_data = {}
        
        try:
            history_file = os.path.join(self.data_dir, "trading_history.json")
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    historical_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
        
        return historical_data
    
    def _save_historical_data(self, historical_data: Dict[str, List[Dict]]):
        """Save historical trading data to JSON file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Save to JSON file
            history_file = os.path.join(self.data_dir, "trading_history.json")
            with open(history_file, "w") as f:
                json.dump(historical_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving historical data: {e}")
    
    def _load_trade_history(self) -> pd.DataFrame:
        """Load trade history from CSV file"""
        try:
            trade_history_file = os.path.join(self.logs_dir, "trade_history.csv")
            if os.path.exists(trade_history_file):
                return pd.read_csv(trade_history_file)
            else:
                logger.warning(f"Trade history file not found: {trade_history_file}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return pd.DataFrame()
    
    def _load_strategy_performance(self) -> Dict[str, Any]:
        """Load strategy performance data"""
        try:
            # Load strategy performance CSV
            performance_file = os.path.join(self.logs_dir, "strategy_performance.csv")
            if os.path.exists(performance_file):
                df = pd.read_csv(performance_file)
                
                # Calculate performance metrics
                metrics = {}
                
                # Basic metrics
                metrics['total_trades'] = len(df)
                
                # Filter to only include completed trades (with profit/loss)
                completed_trades = df[df['profit_loss_usd'] != 0]
                metrics['completed_trades'] = len(completed_trades)
                
                if not completed_trades.empty:
                    # Win/loss metrics
                    winning_trades = completed_trades[completed_trades['profit_loss_usd'] > 0]
                    losing_trades = completed_trades[completed_trades['profit_loss_usd'] < 0]
                    
                    metrics['winning_trades'] = len(winning_trades)
                    metrics['losing_trades'] = len(losing_trades)
                    
                    if len(completed_trades) > 0:
                        metrics['win_rate'] = round((len(winning_trades) / len(completed_trades)) * 100, 2)
                    else:
                        metrics['win_rate'] = 0
                    
                    if len(winning_trades) > 0:
                        metrics['avg_win_usd'] = round(winning_trades['profit_loss_usd'].mean(), 2)
                    else:
                        metrics['avg_win_usd'] = 0
                    
                    if len(losing_trades) > 0:
                        metrics['avg_loss_usd'] = round(losing_trades['profit_loss_usd'].mean(), 2)
                    else:
                        metrics['avg_loss_usd'] = 0
                    
                    if len(losing_trades) > 0 and losing_trades['profit_loss_usd'].sum() != 0:
                        metrics['profit_factor'] = round(abs(winning_trades['profit_loss_usd'].sum() / losing_trades['profit_loss_usd'].sum()), 2)
                    else:
                        metrics['profit_factor'] = float('inf')
                    
                    # Overall performance
                    metrics['total_profit_loss_usd'] = round(completed_trades['profit_loss_usd'].sum(), 2)
                    metrics['avg_profit_loss_usd'] = round(completed_trades['profit_loss_usd'].mean(), 2)
                    metrics['avg_profit_loss_percent'] = round(completed_trades['profit_loss_percent'].mean(), 2)
                    
                    # Risk metrics
                    metrics['max_profit_usd'] = round(completed_trades['profit_loss_usd'].max(), 2)
                    metrics['max_loss_usd'] = round(completed_trades['profit_loss_usd'].min(), 2)
                    
                    # Time metrics
                    metrics['avg_holding_period_hours'] = round(completed_trades['holding_period_hours'].mean(), 2)
                    
                    # Calculate drawdown (simplified)
                    cumulative_returns = completed_trades['profit_loss_usd'].cumsum()
                    if not cumulative_returns.empty:
                        running_max = cumulative_returns.cummax()
                        drawdown = (cumulative_returns - running_max)
                        metrics['max_drawdown_usd'] = round(drawdown.min(), 2)
                    else:
                        metrics['max_drawdown_usd'] = 0
                    
                    # Prepare chart data
                    metrics['chart_data'] = self._prepare_chart_data(df, completed_trades)
                
                return metrics
            else:
                logger.warning(f"Strategy performance file not found: {performance_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading strategy performance: {e}")
            return {}
    
    def _prepare_chart_data(self, df: pd.DataFrame, completed_trades: pd.DataFrame) -> Dict[str, Any]:
        """Prepare chart data for the dashboard"""
        chart_data = {}
        
        try:
            # Trade history chart data
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                
                # Price history
                chart_data['trade_history'] = {
                    'labels': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                    'datasets': [
                        {
                            'label': 'Price',
                            'data': df['price'].tolist(),
                            'borderColor': '#3498db',
                            'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                            'fill': True
                        }
                    ]
                }
            
            # PnL chart data
            if not completed_trades.empty:
                completed_trades['timestamp'] = pd.to_datetime(completed_trades['timestamp'])
                completed_trades = completed_trades.sort_values('timestamp')
                
                # Cumulative PnL
                cumulative_pnl = completed_trades['profit_loss_usd'].cumsum()
                
                chart_data['pnl'] = {
                    'labels': completed_trades['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                    'datasets': [
                        {
                            'label': 'Cumulative P&L (USD)',
                            'data': cumulative_pnl.tolist(),
                            'borderColor': '#2ecc71',
                            'backgroundColor': 'rgba(46, 204, 113, 0.1)',
                            'fill': True
                        }
                    ]
                }
            
            # Market condition chart data
            if not completed_trades.empty and 'market_trend' in completed_trades.columns:
                # Group by market trend
                market_trend_pnl = completed_trades.groupby('market_trend')['profit_loss_usd'].sum()
                
                chart_data['market_condition'] = {
                    'labels': market_trend_pnl.index.tolist(),
                    'datasets': [
                        {
                            'label': 'P&L by Market Trend (USD)',
                            'data': market_trend_pnl.tolist(),
                            'backgroundColor': [
                                'rgba(46, 204, 113, 0.6)',  # bullish - green
                                'rgba(231, 76, 60, 0.6)',   # bearish - red
                                'rgba(52, 152, 219, 0.6)'   # neutral - blue
                            ]
                        }
                    ]
                }
            
            return chart_data
        except Exception as e:
            logger.error(f"Error preparing chart data: {e}")
            return {}
    
    def _generate_html_content(self, trading_results: Dict[str, Dict], 
                              historical_data: Dict[str, List[Dict]],
                              trade_history: pd.DataFrame,
                              strategy_performance: Dict[str, Any],
                              bot_status: str) -> str:
        """Generate HTML content for the dashboard"""
        try:
            # Load HTML template
            template_path = os.path.join(self.template_dir, "dashboard.html")
            with open(template_path, "r") as f:
                html_content = f.read()
            
            # Replace placeholders with actual data
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = html_content.replace("{{UPDATE_TIME}}", update_time)
            html_content = html_content.replace("{{BOT_STATUS}}", bot_status)
            
            # Generate trading pairs HTML
            pairs_html = self._generate_pairs_html(trading_results, historical_data)
            html_content = html_content.replace("{{TRADING_PAIRS}}", pairs_html)
            
            # Generate trade history HTML
            trade_history_html = self._generate_trade_history_html(trade_history)
            html_content = html_content.replace("{{TRADE_HISTORY}}", trade_history_html)
            
            # Generate performance metrics HTML
            performance_metrics = strategy_performance
            
            # Summary metrics
            total_trades = performance_metrics.get('total_trades', 0)
            win_rate = performance_metrics.get('win_rate', 0)
            total_pnl = performance_metrics.get('total_profit_loss_usd', 0)
            
            html_content = html_content.replace("{{TOTAL_TRADES}}", str(total_trades))
            html_content = html_content.replace("{{WIN_RATE}}", str(win_rate))
            html_content = html_content.replace("{{TOTAL_PNL}}", str(total_pnl))
            
            # Last trade time
            last_trade_time = "N/A"
            if not trade_history.empty:
                last_trade_time = pd.to_datetime(trade_history['timestamp'].iloc[-1]).strftime("%Y-%m-%d %H:%M")
            html_content = html_content.replace("{{LAST_TRADE_TIME}}", last_trade_time)
            
            # Performance metrics
            win_loss_ratio = "N/A"
            if performance_metrics.get('losing_trades', 0) > 0:
                win_loss_ratio = round(performance_metrics.get('winning_trades', 0) / performance_metrics.get('losing_trades', 1), 2)
            
            html_content = html_content.replace("{{WIN_LOSS_RATIO}}", str(win_loss_ratio))
            html_content = html_content.replace("{{AVG_WIN}}", str(performance_metrics.get('avg_win_usd', 0)))
            html_content = html_content.replace("{{AVG_LOSS}}", str(performance_metrics.get('avg_loss_usd', 0)))
            html_content = html_content.replace("{{PROFIT_FACTOR}}", str(performance_metrics.get('profit_factor', 0)))
            html_content = html_content.replace("{{MAX_DRAWDOWN}}", str(performance_metrics.get('max_drawdown_usd', 0)))
            html_content = html_content.replace("{{AVG_HOLD_TIME}}", str(performance_metrics.get('avg_holding_period_hours', 0)))
            
            # Chart data
            chart_data = performance_metrics.get('chart_data', {})
            
            # Trade history chart data
            trade_history_chart_data = json.dumps(chart_data.get('trade_history', {'labels': [], 'datasets': []}))
            html_content = html_content.replace("{{TRADE_HISTORY_CHART_DATA}}", trade_history_chart_data)
            
            # PnL chart data
            pnl_chart_data = json.dumps(chart_data.get('pnl', {'labels': [], 'datasets': []}))
            html_content = html_content.replace("{{PNL_CHART_DATA}}", pnl_chart_data)
            
            # Market condition chart data
            market_condition_chart_data = json.dumps(chart_data.get('market_condition', {'labels': [], 'datasets': []}))
            html_content = html_content.replace("{{MARKET_CONDITION_CHART_DATA}}", market_condition_chart_data)
            
            # Generate reports links
            tax_reports_html = self._generate_reports_html("tax_report")
            strategy_reports_html = self._generate_reports_html("strategy_performance")
            
            html_content = html_content.replace("{{TAX_REPORTS}}", tax_reports_html)
            html_content = html_content.replace("{{STRATEGY_REPORTS}}", strategy_reports_html)
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating HTML content: {e}")
            return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"
    
    def _generate_pairs_html(self, trading_results: Dict[str, Dict], historical_data: Dict[str, List[Dict]]) -> str:
        """Generate HTML for trading pairs"""
        pairs_html = ""
        
        for pair, result in trading_results.items():
            # Get current price
            current_price = result.get("price", 0)
            
            # Get previous price from historical data
            previous_price = 0
            if pair in historical_data and len(historical_data[pair]) > 1:
                previous_price = historical_data[pair][-2].get("price", 0)
            
            # Determine price direction
            price_class = ""
            if current_price > previous_price:
                price_class = "price-up"
            elif current_price < previous_price:
                price_class = "price-down"
            
            # Get decision and confidence
            decision = result.get("decision", "HOLD")
            confidence = result.get("confidence", 0)
            
            # Generate HTML for this pair
            pairs_html += f"""
            <div class="pair-card">
                <div class="pair-header">
                    <span class="pair-name">{pair}</span>
                    <span class="pair-price {price_class}">${current_price:.2f}</span>
                </div>
                <div class="pair-details">
                    <div class="pair-detail">
                        <span>Decision:</span>
                        <span>{decision}</span>
                    </div>
                    <div class="pair-detail">
                        <span>Confidence:</span>
                        <span>{confidence}%</span>
                    </div>
                </div>
            </div>
            """
        
        return pairs_html
    
    def _generate_trade_history_html(self, trade_history: pd.DataFrame) -> str:
        """Generate HTML for trade history table"""
        if trade_history.empty:
            return "<tr><td colspan='7'>No trades recorded yet</td></tr>"
        
        # Sort by timestamp (newest first)
        trade_history = trade_history.sort_values('timestamp', ascending=False)
        
        # Take only the most recent 10 trades
        recent_trades = trade_history.head(10)
        
        trade_rows = ""
        for _, trade in recent_trades.iterrows():
            timestamp = pd.to_datetime(trade['timestamp']).strftime("%Y-%m-%d %H:%M")
            side_class = "buy" if trade['side'] == "buy" else "sell"
            
            trade_rows += f"""
            <tr>
                <td>{timestamp}</td>
                <td>{trade['product_id']}</td>
                <td class="{side_class}">{trade['side'].upper()}</td>
                <td>${float(trade['price']):.2f}</td>
                <td>{float(trade['size']):.6f}</td>
                <td>${float(trade['value_usd']):.2f}</td>
                <td>${float(trade['fee_usd']):.2f}</td>
            </tr>
            """
        
        return trade_rows
    
    def _generate_reports_html(self, report_type: str) -> str:
        """Generate HTML for report links"""
        reports_html = ""
        
        # Get all report files
        report_pattern = os.path.join(self.reports_dir, f"{report_type}_*.xlsx")
        report_files = glob.glob(report_pattern)
        
        # Sort by modification time (newest first)
        report_files.sort(key=os.path.getmtime, reverse=True)
        
        # Take only the 5 most recent reports
        recent_reports = report_files[:5]
        
        if not recent_reports:
            return "<li>No reports available</li>"
        
        for report_file in recent_reports:
            filename = os.path.basename(report_file)
            report_url = f"reports/{filename}"
            
            # Extract date from filename
            date_str = filename.split('_')[-1].split('.')[0]
            if len(date_str) == 8:  # YYYYMMDD format
                display_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            else:
                display_date = filename
            
            reports_html += f'<li><a href="{report_url}" target="_blank">{display_date}</a></li>'
        
        return reports_html
    
    def _copy_reports_to_dashboard(self):
        """Copy report files to the dashboard directory"""
        try:
            # Create reports directory in dashboard if it doesn't exist
            dashboard_reports_dir = os.path.join(self.dashboard_dir, "reports")
            os.makedirs(dashboard_reports_dir, exist_ok=True)
            
            # Copy all report files
            report_files = glob.glob(os.path.join(self.reports_dir, "*.xlsx"))
            for report_file in report_files:
                filename = os.path.basename(report_file)
                dest_file = os.path.join(dashboard_reports_dir, filename)
                shutil.copyfile(report_file, dest_file)
            
            logger.info(f"Copied {len(report_files)} report files to dashboard")
        except Exception as e:
            logger.error(f"Error copying reports to dashboard: {e}")
