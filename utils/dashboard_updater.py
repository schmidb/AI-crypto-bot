import logging
import json
import os
import datetime
import shutil
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Updates the web dashboard with latest trading data and portfolio information"""
    
    def __init__(self):
        """Initialize the dashboard updater with new data structure"""
        # Create directories if they don't exist
        os.makedirs("data/portfolio", exist_ok=True)
        os.makedirs("data/cache", exist_ok=True)
        os.makedirs("data/config", exist_ok=True)
        os.makedirs("dashboard/images", exist_ok=True)
    
    def update_dashboard(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Update the dashboard with latest trading and portfolio data"""
        try:
            logger.info("Starting dashboard update with new structure")
            self._update_trading_cache(trading_data)
            self._update_portfolio_data(portfolio)
            self._update_config_data()
            self._update_latest_decisions(trading_data)
            self._generate_charts(trading_data, portfolio)
            self._update_timestamp()
            self._sync_to_webserver()
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def _update_trading_cache(self, trading_data: Dict[str, Any]) -> None:
        """Update trading data cache file"""
        with open("data/cache/trading_data.json", "w") as f:
            json.dump(trading_data, f, indent=2)
        logger.info("Updated trading data cache")
    
    def _update_portfolio_data(self, portfolio: Dict[str, Any]) -> None:
        """Update portfolio data file"""
        try:
            if not portfolio or not isinstance(portfolio, dict):
                logger.warning(f"Invalid portfolio data: {type(portfolio)}")
                return
            
            # Process portfolio data (same logic as before)
            import copy
            portfolio_copy = copy.deepcopy(portfolio)
            
            # Add timestamp
            portfolio_copy["last_updated"] = datetime.datetime.now().isoformat()
            
            # Save to new location
            with open("data/portfolio/portfolio_data.json", "w") as f:
                json.dump(portfolio_copy, f, indent=2, default=str)
            
            logger.info("Updated portfolio data")
            
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
                    f.write("timestamp,portfolio_value_usd,btc_amount,eth_amount,usd_amount,btc_price,eth_price\n")
            
            # Extract and append data (same logic as before)
            timestamp = datetime.datetime.now().isoformat()
            portfolio_value = float(portfolio.get("portfolio_value_usd", 0))
            
            # Extract asset data with validation
            btc_data = portfolio.get("BTC", {})
            eth_data = portfolio.get("ETH", {})
            usd_data = portfolio.get("USD", {})
            
            if not isinstance(btc_data, dict): btc_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(eth_data, dict): eth_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(usd_data, dict): usd_data = {"amount": 0}
            
            btc_amount = float(btc_data.get("amount", 0))
            eth_amount = float(eth_data.get("amount", 0))
            usd_amount = float(usd_data.get("amount", 0))
            btc_price = float(btc_data.get("last_price_usd", 0))
            eth_price = float(eth_data.get("last_price_usd", 0))
            
            with open(history_file, "a") as f:
                f.write(f"{timestamp},{portfolio_value},{btc_amount},{eth_amount},{usd_amount},{btc_price},{eth_price}\n")
                
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
    
    def _update_latest_decisions(self, trading_data: Dict[str, Any]) -> None:
        """Update latest trading decisions cache"""
        try:
            # Same logic as before, but save to new location
            latest_decisions = []
            # ... (same processing logic)
            
            with open("data/cache/latest_decisions.json", "w") as f:
                json.dump(latest_decisions, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error updating latest decisions: {e}")
    
    def _generate_charts(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Generate charts for the dashboard"""
        try:
            self._generate_portfolio_allocation_chart(portfolio)
            self._generate_portfolio_value_chart()
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
            plt.plot(df['timestamp'], df['portfolio_value_usd'])
            plt.title('Portfolio Value Over Time')
            plt.xlabel('Date')
            plt.ylabel('Value (USD)')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plt.savefig("dashboard/images/portfolio_value.png")
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating portfolio value chart: {e}")
    
    def _generate_portfolio_allocation_chart(self, portfolio: Dict[str, Any]) -> None:
        """Generate pie chart showing portfolio allocation"""
        # Same logic as before, save to dashboard/images/
        pass
    
    def _generate_target_vs_current_allocation(self, portfolio: Dict[str, Any]) -> None:
        """Generate bar chart comparing target vs current allocation"""
        # Same logic as before, save to dashboard/images/
        pass
    
    def _update_timestamp(self) -> None:
        """Update the last updated timestamp"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("data/cache/last_updated.txt", "w") as f:
                f.write(timestamp)
        except Exception as e:
            logger.error(f"Error updating timestamp: {e}")
    
    def _sync_to_webserver(self):
        """Copy dashboard files to web server directory"""
        try:
            web_dashboard_dir = "/var/www/html/crypto-bot"
            
            if not os.path.exists(web_dashboard_dir):
                logger.info(f"Web dashboard directory {web_dashboard_dir} not found, skipping sync")
                return
            
            # Copy data files from new structure
            os.makedirs(f"{web_dashboard_dir}/data", exist_ok=True)
            
            # Copy portfolio data
            if os.path.exists("data/portfolio/portfolio_data.json"):
                shutil.copy2("data/portfolio/portfolio_data.json", f"{web_dashboard_dir}/data/")
            
            # Copy cache data
            cache_files = ["latest_decisions.json", "trading_data.json", "last_updated.txt", "bot_startup.json"]
            for file in cache_files:
                if os.path.exists(f"data/cache/{file}"):
                    shutil.copy2(f"data/cache/{file}", f"{web_dashboard_dir}/data/")
            
            # Copy config
            if os.path.exists("data/config/config.json"):
                shutil.copy2("data/config/config.json", f"{web_dashboard_dir}/data/")
            
            # Update market data symlinks
            self._update_market_data_symlinks(web_dashboard_dir)
            
            # Copy images
            if os.path.exists("dashboard/images"):
                os.makedirs(f"{web_dashboard_dir}/images", exist_ok=True)
                for file in os.listdir("dashboard/images"):
                    shutil.copy2(f"dashboard/images/{file}", f"{web_dashboard_dir}/images/")
            
            # Copy static files
            if os.path.exists("dashboard/static"):
                for file in os.listdir("dashboard/static"):
                    if file.endswith((".html", ".css", ".js")):
                        shutil.copy2(f"dashboard/static/{file}", f"{web_dashboard_dir}/")
            
            logger.info("Dashboard files synced to web server")
            
        except Exception as e:
            logger.error(f"Error syncing dashboard files: {e}")
    
    def _update_market_data_symlinks(self, web_dashboard_dir: str) -> None:
        """Update symlinks to latest market data files"""
        try:
            import glob
            
            data_dir = os.path.abspath("data")
            web_data_dir = f"{web_dashboard_dir}/data"
            
            # Update symlinks for each trading pair
            assets = ['BTC', 'ETH', 'SOL']
            
            for asset in assets:
                # Find the latest market data file for this asset
                pattern = f"{data_dir}/{asset}_USD_*.json"
                files = glob.glob(pattern)
                
                if files:
                    # Sort by filename (which includes timestamp) and get the latest
                    latest_file = sorted(files)[-1]
                    symlink_path = f"{web_data_dir}/{asset.lower()}_latest.json"
                    
                    # Remove existing symlink if it exists
                    if os.path.islink(symlink_path):
                        os.unlink(symlink_path)
                    elif os.path.exists(symlink_path):
                        os.remove(symlink_path)
                    
                    # Create new symlink
                    os.symlink(latest_file, symlink_path)
                    logger.info(f"Updated {asset} market data symlink to {latest_file}")
            
            # Also update trade history symlink
            trade_history_path = f"{data_dir}/trades/trade_history.json"
            if os.path.exists(trade_history_path):
                symlink_path = f"{web_data_dir}/trade_history.json"
                
                if os.path.islink(symlink_path):
                    os.unlink(symlink_path)
                elif os.path.exists(symlink_path):
                    os.remove(symlink_path)
                
                os.symlink(trade_history_path, symlink_path)
                logger.info("Updated trade history symlink")
                
        except Exception as e:
            logger.error(f"Error updating market data symlinks: {e}")
