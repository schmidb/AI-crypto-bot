#!/usr/bin/env python3
"""
Dashboard updater module for the crypto trading bot
Updates the HTML dashboard with the latest trading information
"""

import os
import json
import logging
from datetime import datetime
import glob
from typing import Dict, List, Any, Optional
import shutil

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Updates the HTML dashboard with the latest trading information"""
    
    def __init__(self, dashboard_dir: str = "/var/www/html/crypto-bot"):
        """Initialize the dashboard updater"""
        self.dashboard_dir = dashboard_dir
        self.data_dir = "data"
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
                
                # Keep only the last 100 results
                historical_data[pair] = historical_data[pair][-100:]
            
            # Save updated historical data
            self._save_historical_data(historical_data)
            
            # Generate performance metrics
            performance = self._calculate_performance(historical_data)
            
            # Update the HTML dashboard
            self._generate_html_dashboard(trading_results, historical_data, performance, bot_status)
            
            logger.info("Dashboard updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return False
    
    def _load_historical_data(self) -> Dict[str, List[Dict]]:
        """
        Load historical trading data from JSON files
        
        Returns:
            Dictionary mapping trading pairs to lists of trading results
        """
        historical_data = {}
        
        # Create data directory in dashboard if it doesn't exist
        dashboard_data_dir = os.path.join(self.dashboard_dir, "data")
        os.makedirs(dashboard_data_dir, exist_ok=True)
        
        # Try to load existing historical data
        history_file = os.path.join(dashboard_data_dir, "historical_data.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    historical_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse historical data file: {history_file}")
        
        # If no historical data was loaded, try to build it from data files
        if not historical_data:
            # Get all JSON files in the data directory
            data_files = glob.glob(os.path.join(self.data_dir, "*.json"))
            
            for file_path in sorted(data_files):
                try:
                    # Extract trading pair from filename
                    filename = os.path.basename(file_path)
                    parts = filename.split('_')
                    if len(parts) < 2:
                        continue
                        
                    pair = parts[0].replace('_', '-')
                    
                    # Load the data
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Add to historical data
                    if pair not in historical_data:
                        historical_data[pair] = []
                    
                    # Add timestamp if not present
                    if "timestamp" not in data:
                        # Try to extract timestamp from filename
                        try:
                            timestamp_str = '_'.join(parts[1:]).split('.')[0]
                            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S").isoformat()
                            data["timestamp"] = timestamp
                        except:
                            data["timestamp"] = datetime.now().isoformat()
                    
                    historical_data[pair].append(data)
                    
                except Exception as e:
                    logger.warning(f"Error processing data file {file_path}: {e}")
        
        # Keep only the last 100 results for each pair
        for pair in historical_data:
            historical_data[pair] = historical_data[pair][-100:]
        
        return historical_data
    
    def _save_historical_data(self, historical_data: Dict[str, List[Dict]]):
        """
        Save historical trading data to a JSON file
        
        Args:
            historical_data: Dictionary mapping trading pairs to lists of trading results
        """
        dashboard_data_dir = os.path.join(self.dashboard_dir, "data")
        os.makedirs(dashboard_data_dir, exist_ok=True)
        
        history_file = os.path.join(dashboard_data_dir, "historical_data.json")
        with open(history_file, 'w') as f:
            json.dump(historical_data, f, indent=2, default=str)
    
    def _calculate_performance(self, historical_data: Dict[str, List[Dict]]) -> Dict:
        """
        Calculate performance metrics from historical data
        
        Args:
            historical_data: Dictionary mapping trading pairs to lists of trading results
            
        Returns:
            Dictionary with performance metrics
        """
        performance = {
            "total_trades": 0,
            "successful_trades": 0,
            "buy_trades": 0,
            "sell_trades": 0,
            "hold_decisions": 0,
            "profit_loss": 0.0,
            "win_rate": 0.0,
            "pairs": {}
        }
        
        for pair, results in historical_data.items():
            pair_performance = {
                "total_trades": 0,
                "successful_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "hold_decisions": 0,
                "profit_loss": 0.0,
                "win_rate": 0.0,
                "last_price": None,
                "last_decision": None,
                "last_confidence": None
            }
            
            for result in results:
                # Count decisions
                decision = result.get('decision', 'UNKNOWN')
                
                if decision == "BUY":
                    pair_performance["buy_trades"] += 1
                    performance["buy_trades"] += 1
                    
                    if result.get('trade_executed', False):
                        pair_performance["total_trades"] += 1
                        performance["total_trades"] += 1
                        
                        # Check if trade was successful
                        if result.get('trade_details', {}).get('success', False):
                            pair_performance["successful_trades"] += 1
                            performance["successful_trades"] += 1
                
                elif decision == "SELL":
                    pair_performance["sell_trades"] += 1
                    performance["sell_trades"] += 1
                    
                    if result.get('trade_executed', False):
                        pair_performance["total_trades"] += 1
                        performance["total_trades"] += 1
                        
                        # Check if trade was successful
                        if result.get('trade_details', {}).get('success', False):
                            pair_performance["successful_trades"] += 1
                            performance["successful_trades"] += 1
                
                elif decision == "HOLD":
                    pair_performance["hold_decisions"] += 1
                    performance["hold_decisions"] += 1
                
                # Track last price and decision
                pair_performance["last_price"] = result.get('current_price')
                pair_performance["last_decision"] = decision
                pair_performance["last_confidence"] = result.get('confidence')
            
            # Calculate win rate
            if pair_performance["total_trades"] > 0:
                pair_performance["win_rate"] = (pair_performance["successful_trades"] / pair_performance["total_trades"]) * 100
            
            performance["pairs"][pair] = pair_performance
        
        # Calculate overall win rate
        if performance["total_trades"] > 0:
            performance["win_rate"] = (performance["successful_trades"] / performance["total_trades"]) * 100
        
        return performance
    
    def _generate_html_dashboard(self, 
                               latest_results: Dict[str, Dict], 
                               historical_data: Dict[str, List[Dict]], 
                               performance: Dict,
                               bot_status: str):
        """
        Generate the HTML dashboard
        
        Args:
            latest_results: Latest trading results
            historical_data: Historical trading data
            performance: Performance metrics
            bot_status: Current status of the bot
        """
        # Load the dashboard template
        dashboard_template = self._load_template("dashboard.html")
        if not dashboard_template:
            logger.error("Could not load dashboard template")
            return
        
        # Generate trading pairs HTML
        pairs_html = ""
        for pair, perf in performance["pairs"].items():
            decision_class = perf["last_decision"].lower() if perf["last_decision"] else "unknown"
            
            pairs_html += f"""
            <div class="pair-card">
                <h3>{pair}</h3>
                <div class="pair-details">
                    <p>Last Price: <strong>${perf["last_price"]}</strong></p>
                    <p>Last Decision: <span class="{decision_class}">{perf["last_decision"]}</span> ({perf["last_confidence"]}% confidence)</p>
                    <p>Buy Trades: {perf["buy_trades"]}</p>
                    <p>Sell Trades: {perf["sell_trades"]}</p>
                    <p>Hold Decisions: {perf["hold_decisions"]}</p>
                </div>
            </div>
            """
        
        # Generate recent trades HTML
        trades_html = "<table><thead><tr><th>Time</th><th>Pair</th><th>Type</th><th>Price</th><th>Amount</th><th>Status</th></tr></thead><tbody>"
        
        # Collect all trades
        all_trades = []
        for pair, results in historical_data.items():
            for result in results:
                if result.get('trade_executed', False):
                    trade_details = result.get('trade_details', {})
                    all_trades.append({
                        'timestamp': result.get('timestamp'),
                        'pair': pair,
                        'type': trade_details.get('order_type', 'UNKNOWN'),
                        'price': result.get('current_price'),
                        'amount': trade_details.get('size'),
                        'currency': trade_details.get('currency'),
                        'status': 'Success' if trade_details.get('success', False) else 'Failed'
                    })
        
        # Sort trades by timestamp (newest first)
        all_trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Take only the 10 most recent trades
        recent_trades = all_trades[:10]
        
        if recent_trades:
            for trade in recent_trades:
                trade_type_class = trade['type'].lower()
                trades_html += f"""
                <tr>
                    <td>{self._format_timestamp(trade['timestamp'])}</td>
                    <td>{trade['pair']}</td>
                    <td class="{trade_type_class}">{trade['type']}</td>
                    <td>${trade['price']}</td>
                    <td>{trade['amount']} {trade['currency']}</td>
                    <td>{trade['status']}</td>
                </tr>
                """
        else:
            trades_html += "<tr><td colspan='6'>No trades executed yet.</td></tr>"
        
        trades_html += "</tbody></table>"
        
        # Generate performance metrics HTML
        performance_html = """
        <div class="performance-metrics">
            <div class="metric-card">
                <h3>Total Trades</h3>
                <div class="metric-value">{}</div>
            </div>
            <div class="metric-card">
                <h3>Success Rate</h3>
                <div class="metric-value">{:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>Buy Trades</h3>
                <div class="metric-value">{}</div>
            </div>
            <div class="metric-card">
                <h3>Sell Trades</h3>
                <div class="metric-value">{}</div>
            </div>
            <div class="metric-card">
                <h3>Hold Decisions</h3>
                <div class="metric-value">{}</div>
            </div>
        </div>
        """.format(
            performance["total_trades"],
            performance["win_rate"],
            performance["buy_trades"],
            performance["sell_trades"],
            performance["hold_decisions"]
        )
        
        # Replace placeholders in the template
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dashboard_html = dashboard_template.replace("{{UPDATE_TIME}}", now)
        dashboard_html = dashboard_html.replace("{{BOT_STATUS}}", bot_status)
        dashboard_html = dashboard_html.replace("{{TRADING_PAIRS}}", pairs_html)
        dashboard_html = dashboard_html.replace("{{RECENT_TRADES}}", trades_html)
        dashboard_html = dashboard_html.replace("{{PERFORMANCE_METRICS}}", performance_html)
        
        # Write the dashboard HTML
        with open(os.path.join(self.dashboard_dir, "index.html"), 'w') as f:
            f.write(dashboard_html)
        
        # Copy CSS file if it exists in the template directory
        css_template = self._load_template("styles.css")
        if css_template:
            with open(os.path.join(self.dashboard_dir, "styles.css"), 'w') as f:
                f.write(css_template)
    
    def _load_template(self, filename: str) -> Optional[str]:
        """
        Load a template file
        
        Args:
            filename: Name of the template file
            
        Returns:
            Template content as string, or None if the file could not be loaded
        """
        # First try to load from the template directory
        template_path = os.path.join(self.template_dir, filename)
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return f.read()
        
        # If that fails, try to load from the dashboard directory
        dashboard_path = os.path.join(self.dashboard_dir, filename)
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r') as f:
                return f.read()
        
        return None
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """
        Format a timestamp string for display
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            Formatted timestamp string
        """
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return timestamp_str
