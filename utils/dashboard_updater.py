import logging
import json
import os
import datetime
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Updates local dashboard data files - web server sync handled separately"""
    
    def __init__(self):
        """Initialize the dashboard updater for local data management only"""
        # Create directories if they don't exist
        os.makedirs("data/portfolio", exist_ok=True)
        os.makedirs("data/cache", exist_ok=True)
        os.makedirs("data/config", exist_ok=True)
        os.makedirs("dashboard/images", exist_ok=True)
    
    def update_dashboard(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Update local dashboard data files only"""
        try:
            logger.info("Updating local dashboard data")
            self._update_trading_cache(trading_data)
            self._update_portfolio_data(portfolio)
            self._update_config_data()
            self._update_detailed_config_data()
            self._update_latest_decisions(trading_data)
            self._generate_charts(trading_data, portfolio)
            self._update_timestamp()
            logger.info("Local dashboard data updated successfully")
        except Exception as e:
            logger.error(f"Error updating local dashboard data: {e}")
    
    def _update_trading_cache(self, trading_data: Dict[str, Any]) -> None:
        """Update trading data cache file"""
        with open("data/cache/trading_data.json", "w") as f:
            json.dump(trading_data, f, indent=2)
        logger.debug("Updated trading data cache")
    
    def _update_portfolio_data(self, portfolio: Dict[str, Any]) -> None:
        """Update portfolio data file"""
        try:
            if not portfolio or not isinstance(portfolio, dict):
                logger.warning(f"Invalid portfolio data: {type(portfolio)}")
                return
            
            # Process portfolio data
            import copy
            portfolio_copy = copy.deepcopy(portfolio)
            
            # Get the most recent timestamp from trades or decisions
            latest_trade_time = self._get_latest_trade_timestamp()
            latest_decision_time = self._get_latest_decision_timestamp()
            latest_time = max(latest_trade_time, latest_decision_time)
            
            # Use the most recent timestamp for last_updated
            portfolio_copy["last_updated"] = latest_time
            
            # Save to portfolio data file (standardized to portfolio.json)
            with open("data/portfolio/portfolio.json", "w") as f:
                json.dump(portfolio_copy, f, indent=2, default=str)
            
            logger.debug("Updated portfolio data")
            
            # Update portfolio history
            self._append_portfolio_history(portfolio_copy)
            
        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}")
    
    def _append_portfolio_history(self, portfolio: Dict[str, Any]) -> None:
        """Append current portfolio value to historical data"""
        try:
            history_file = "data/portfolio/portfolio_history.csv"
            
            # Create new history file if it doesn't exist
            if not os.path.exists(history_file):
                with open(history_file, "w") as f:
                    f.write("timestamp,portfolio_value_usd,btc_amount,eth_amount,sol_amount,usd_amount,btc_price,eth_price,sol_price\n")
            
            # Extract and append data
            timestamp = datetime.datetime.now().isoformat()
            portfolio_value = float(portfolio.get("portfolio_value_usd", 0))
            
            # Extract asset data with validation
            btc_data = portfolio.get("BTC", {})
            eth_data = portfolio.get("ETH", {})
            sol_data = portfolio.get("SOL", {})
            usd_data = portfolio.get("USD", {})
            
            if not isinstance(btc_data, dict): btc_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(eth_data, dict): eth_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(sol_data, dict): sol_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(usd_data, dict): usd_data = {"amount": 0}
            
            btc_amount = float(btc_data.get("amount", 0))
            eth_amount = float(eth_data.get("amount", 0))
            sol_amount = float(sol_data.get("amount", 0))
            usd_amount = float(usd_data.get("amount", 0))
            btc_price = float(btc_data.get("last_price_usd", 0))
            eth_price = float(eth_data.get("last_price_usd", 0))
            sol_price = float(sol_data.get("last_price_usd", 0))
            
            with open(history_file, "a") as f:
                f.write(f"{timestamp},{portfolio_value},{btc_amount},{eth_amount},{sol_amount},{usd_amount},{btc_price},{eth_price},{sol_price}\n")
                
        except Exception as e:
            logger.error(f"Error appending portfolio history: {e}")
    
    def _update_config_data(self) -> None:
        """Update configuration data for the dashboard"""
        try:
            from config import (
                TRADING_PAIRS, DECISION_INTERVAL_MINUTES, RISK_LEVEL,
                LLM_MODEL, PORTFOLIO_REBALANCE, MAX_TRADE_PERCENTAGE,
                SIMULATION_MODE, TARGET_ALLOCATION, DASHBOARD_TRADE_HISTORY_LIMIT
            )
            
            config_data = {
                "trading_pairs": ",".join(TRADING_PAIRS),
                "decision_interval_minutes": DECISION_INTERVAL_MINUTES,
                "risk_level": RISK_LEVEL,
                "llm_model": LLM_MODEL,
                "portfolio_rebalance": PORTFOLIO_REBALANCE,
                "max_trade_percentage": MAX_TRADE_PERCENTAGE,
                "simulation_mode": SIMULATION_MODE,
                "target_allocation": TARGET_ALLOCATION,
                "dashboard_trade_history_limit": DASHBOARD_TRADE_HISTORY_LIMIT
            }
            
            with open("data/config/config.json", "w") as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating config data: {e}")
    
    def _update_detailed_config_data(self) -> None:
        """Update detailed configuration data including all environment variables"""
        try:
            import os
            from config import config
            
            # Get all configuration attributes from the config object
            detailed_config = {}
            
            # API Credentials
            detailed_config['COINBASE_API_KEY'] = getattr(config, 'COINBASE_API_KEY', None)
            detailed_config['COINBASE_API_SECRET'] = '***HIDDEN***' if getattr(config, 'COINBASE_API_SECRET', None) else None
            
            # Google Cloud Settings
            detailed_config['GOOGLE_CLOUD_PROJECT'] = getattr(config, 'GOOGLE_CLOUD_PROJECT', None)
            detailed_config['GOOGLE_APPLICATION_CREDENTIALS'] = getattr(config, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            
            # LLM Configuration
            detailed_config['LLM_PROVIDER'] = getattr(config, 'LLM_PROVIDER', None)
            detailed_config['LLM_MODEL'] = getattr(config, 'LLM_MODEL', None)
            detailed_config['LLM_LOCATION'] = getattr(config, 'LLM_LOCATION', None)
            
            # Trading Parameters
            detailed_config['TRADING_PAIRS'] = ",".join(getattr(config, 'TRADING_PAIRS', []))
            detailed_config['DECISION_INTERVAL_MINUTES'] = getattr(config, 'DECISION_INTERVAL_MINUTES', None)
            detailed_config['RISK_LEVEL'] = getattr(config, 'RISK_LEVEL', None)
            detailed_config['SIMULATION_MODE'] = getattr(config, 'SIMULATION_MODE', None)
            
            # Portfolio Management
            detailed_config['PORTFOLIO_REBALANCE'] = getattr(config, 'PORTFOLIO_REBALANCE', None)
            detailed_config['MAX_TRADE_PERCENTAGE'] = getattr(config, 'MAX_TRADE_PERCENTAGE', None)
            detailed_config['TARGET_CRYPTO_ALLOCATION'] = getattr(config, 'TARGET_CRYPTO_ALLOCATION', None)
            detailed_config['TARGET_USD_ALLOCATION'] = getattr(config, 'TARGET_USD_ALLOCATION', None)
            
            # Enhanced Trading Strategy
            detailed_config['CONFIDENCE_THRESHOLD_BUY'] = getattr(config, 'CONFIDENCE_THRESHOLD_BUY', None)
            detailed_config['CONFIDENCE_THRESHOLD_SELL'] = getattr(config, 'CONFIDENCE_THRESHOLD_SELL', None)
            detailed_config['CONFIDENCE_BOOST_TREND_ALIGNED'] = getattr(config, 'CONFIDENCE_BOOST_TREND_ALIGNED', None)
            detailed_config['CONFIDENCE_PENALTY_COUNTER_TREND'] = getattr(config, 'CONFIDENCE_PENALTY_COUNTER_TREND', None)
            
            # Technical Analysis
            detailed_config['RSI_NEUTRAL_MIN'] = getattr(config, 'RSI_NEUTRAL_MIN', None)
            detailed_config['RSI_NEUTRAL_MAX'] = getattr(config, 'RSI_NEUTRAL_MAX', None)
            detailed_config['MACD_SIGNAL_WEIGHT'] = getattr(config, 'MACD_SIGNAL_WEIGHT', None)
            detailed_config['RSI_SIGNAL_WEIGHT'] = getattr(config, 'RSI_SIGNAL_WEIGHT', None)
            detailed_config['BOLLINGER_SIGNAL_WEIGHT'] = getattr(config, 'BOLLINGER_SIGNAL_WEIGHT', None)
            
            # Risk Management
            detailed_config['RISK_HIGH_POSITION_MULTIPLIER'] = getattr(config, 'RISK_HIGH_POSITION_MULTIPLIER', None)
            detailed_config['RISK_MEDIUM_POSITION_MULTIPLIER'] = getattr(config, 'RISK_MEDIUM_POSITION_MULTIPLIER', None)
            detailed_config['RISK_LOW_POSITION_MULTIPLIER'] = getattr(config, 'RISK_LOW_POSITION_MULTIPLIER', None)
            
            # Trade Limits
            detailed_config['MIN_TRADE_USD'] = getattr(config, 'MIN_TRADE_USD', None)
            detailed_config['MAX_POSITION_SIZE_USD'] = getattr(config, 'MAX_POSITION_SIZE_USD', None)
            
            # Portfolio Rebalancing
            detailed_config['REBALANCE_THRESHOLD_PERCENT'] = getattr(config, 'REBALANCE_THRESHOLD_PERCENT', None)
            detailed_config['REBALANCE_CHECK_INTERVAL_MINUTES'] = getattr(config, 'REBALANCE_CHECK_INTERVAL_MINUTES', None)
            
            # Dashboard & Logging
            detailed_config['DASHBOARD_TRADE_HISTORY_LIMIT'] = getattr(config, 'DASHBOARD_TRADE_HISTORY_LIMIT', None)
            detailed_config['LOG_LEVEL'] = getattr(config, 'LOG_LEVEL', None)
            detailed_config['LOG_FILE'] = getattr(config, 'LOG_FILE', None)
            
            # Web Server Sync
            detailed_config['WEBSERVER_SYNC_ENABLED'] = getattr(config, 'WEBSERVER_SYNC_ENABLED', None)
            detailed_config['WEBSERVER_SYNC_PATH'] = getattr(config, 'WEBSERVER_SYNC_PATH', None)
            
            # Save detailed configuration
            with open("data/config/detailed_config.json", "w") as f:
                json.dump(detailed_config, f, indent=2, default=str)
                
            logger.debug("Updated detailed configuration data")
                
        except Exception as e:
            logger.error(f"Error updating detailed config data: {e}")
    
    def _update_latest_decisions(self, trading_data: Dict[str, Any]) -> None:
        """Update latest trading decisions cache"""
        try:
            latest_decisions = []
            assets = ["BTC", "ETH", "SOL"]
            
            # Get latest decision data for each asset
            for asset in assets:
                try:
                    # Read the latest decision file directly
                    import glob
                    pattern = f"data/{asset}_USD_*.json"
                    files = glob.glob(pattern)
                    
                    if files:
                        # Get the latest file
                        latest_file = sorted(files)[-1]
                        with open(latest_file, "r") as f:
                            decision_data = json.load(f)
                            
                        decision = {
                            "timestamp": decision_data.get("timestamp", ""),
                            "asset": asset,
                            "action": decision_data.get("action", "unknown"),
                            "confidence": decision_data.get("confidence", 0),
                            "reasoning": decision_data.get("reason", decision_data.get("reasoning", "No reasoning provided"))
                        }
                        latest_decisions.append(decision)
                    else:
                        logger.warning(f"No decision files found for {asset}")
                        
                except Exception as e:
                    logger.error(f"Error reading latest decision data for {asset}: {e}")
            
            # Sort by timestamp, newest first
            latest_decisions.sort(key=lambda x: x["timestamp"], reverse=True)
            
            with open("data/cache/latest_decisions.json", "w") as f:
                json.dump(latest_decisions, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error updating latest decisions: {e}")
    
    def _generate_charts(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Generate charts for the dashboard"""
        try:
            self._generate_portfolio_value_chart()
            self._generate_portfolio_allocation_chart(portfolio)
            self._generate_target_vs_current_allocation(portfolio)
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def _generate_portfolio_value_chart(self) -> None:
        """Generate line chart showing portfolio value over time"""
        try:
            history_file = "data/portfolio/portfolio_history.csv"
            
            if not os.path.exists(history_file):
                logger.warning(f"Portfolio history file not found: {history_file}")
                return
                
            df = pd.read_csv(history_file)
            if df.empty:
                return
                
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            plt.figure(figsize=(12, 6))
            plt.plot(df['timestamp'], df['portfolio_value_usd'], linewidth=2, color='#4CAF50')
            plt.title('Portfolio Value Over Time', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Value (USD)', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plt.savefig("dashboard/images/portfolio_value.png", dpi=150, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating portfolio value chart: {e}")
    
    def _generate_portfolio_allocation_chart(self, portfolio: Dict[str, Any]) -> None:
        """Generate pie chart showing portfolio allocation"""
        try:
            if not portfolio:
                return
            
            # Extract asset values
            assets = {}
            for asset in ['BTC', 'ETH', 'SOL', 'USD']:
                if asset in portfolio and isinstance(portfolio[asset], dict):
                    amount = portfolio[asset].get('amount', 0)
                    price = portfolio[asset].get('last_price_usd', 1 if asset == 'USD' else 0)
                    value = amount * price
                    if value > 0:
                        assets[asset] = value
            
            if not assets:
                return
            
            # Create pie chart
            plt.figure(figsize=(10, 8))
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            wedges, texts, autotexts = plt.pie(
                assets.values(), 
                labels=assets.keys(), 
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )
            
            plt.title('Portfolio Allocation', fontsize=16, fontweight='bold')
            plt.axis('equal')
            
            plt.savefig("dashboard/images/portfolio_allocation.png", dpi=150, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating portfolio allocation chart: {e}")
    
    def _generate_target_vs_current_allocation(self, portfolio: Dict[str, Any]) -> None:
        """Generate bar chart comparing target vs current allocation"""
        try:
            from config import TARGET_ALLOCATION
            
            if not portfolio or not TARGET_ALLOCATION:
                return
            
            # Calculate current allocation percentages
            total_value = portfolio.get('portfolio_value_usd', 0)
            if total_value <= 0:
                return
            
            current_allocation = {}
            for asset in TARGET_ALLOCATION.keys():
                if asset in portfolio and isinstance(portfolio[asset], dict):
                    amount = portfolio[asset].get('amount', 0)
                    price = portfolio[asset].get('last_price_usd', 1 if asset == 'USD' else 0)
                    value = amount * price
                    current_allocation[asset] = (value / total_value) * 100
                else:
                    current_allocation[asset] = 0
            
            # Create comparison chart
            assets = list(TARGET_ALLOCATION.keys())
            target_values = [TARGET_ALLOCATION[asset] for asset in assets]
            current_values = [current_allocation.get(asset, 0) for asset in assets]
            
            x = range(len(assets))
            width = 0.35
            
            plt.figure(figsize=(12, 6))
            plt.bar([i - width/2 for i in x], target_values, width, label='Target', color='#4CAF50', alpha=0.7)
            plt.bar([i + width/2 for i in x], current_values, width, label='Current', color='#2196F3', alpha=0.7)
            
            plt.xlabel('Assets', fontsize=12)
            plt.ylabel('Allocation (%)', fontsize=12)
            plt.title('Target vs Current Allocation', fontsize=16, fontweight='bold')
            plt.xticks(x, assets)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            plt.savefig("dashboard/images/allocation_comparison.png", dpi=150, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating allocation comparison chart: {e}")
    
    def _update_timestamp(self) -> None:
        """Update the last updated timestamp using most recent activity"""
        try:
            # Get the most recent timestamp from trades or decisions
            latest_trade_time = self._get_latest_trade_timestamp()
            latest_decision_time = self._get_latest_decision_timestamp()
            latest_time = max(latest_trade_time, latest_decision_time)
            
            # Convert to datetime for formatting
            timestamp = datetime.datetime.fromisoformat(latest_time.replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M:%S")
            
            with open("data/cache/last_updated.txt", "w") as f:
                f.write(timestamp)
        except Exception as e:
            logger.error(f"Error updating timestamp: {e}")
    
    def _get_latest_trade_timestamp(self) -> str:
        """Get the most recent trade timestamp from trade history file"""
        try:
            trade_history_file = "data/trades/trade_history.json"
            if os.path.exists(trade_history_file):
                with open(trade_history_file, "r") as f:
                    trade_history = json.load(f)
                if trade_history and isinstance(trade_history, list):
                    return max([trade.get('timestamp', '2000-01-01T00:00:00') 
                              for trade in trade_history], default='2000-01-01T00:00:00')
        except Exception as e:
            logger.error(f"Error reading trade history: {e}")
        return '2000-01-01T00:00:00'
    
    def _get_latest_decision_timestamp(self) -> str:
        """Get the most recent decision timestamp from latest decisions file"""
        try:
            decisions_file = "data/cache/latest_decisions.json"
            if os.path.exists(decisions_file):
                with open(decisions_file, "r") as f:
                    latest_decisions = json.load(f)
                if latest_decisions and isinstance(latest_decisions, list):
                    return max([decision.get('timestamp', '2000-01-01T00:00:00') 
                              for decision in latest_decisions], default='2000-01-01T00:00:00')
        except Exception as e:
            logger.error(f"Error reading latest decisions: {e}")
        return '2000-01-01T00:00:00'
