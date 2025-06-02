import logging
import json
import os
import datetime
import shutil
import subprocess
from typing import Dict, List, Any, Union
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Updates the web dashboard with latest trading data and portfolio information"""
    
    def __init__(self, dashboard_dir="dashboard"):
        """Initialize the dashboard updater"""
        self.dashboard_dir = dashboard_dir
        os.makedirs(f"{dashboard_dir}/data", exist_ok=True)
        os.makedirs(f"{dashboard_dir}/images", exist_ok=True)
        
        # Ensure dashboard template files exist
        self._ensure_dashboard_files_exist()
    
    def update_dashboard(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Update the dashboard with latest trading and portfolio data"""
        try:
            logger.info(f"Starting dashboard update")
            self._update_trading_data(trading_data)
            logger.info(f"Trading data updated to {self.dashboard_dir}/data/trading_data.json")
            self._update_portfolio_data(portfolio)
            logger.info(f"Portfolio data updated to {self.dashboard_dir}/data/portfolio_data.json")
            self._update_config_data()
            logger.info(f"Config data updated to {self.dashboard_dir}/data/config.json")
            self._update_latest_decisions(trading_data)
            logger.info(f"Latest decisions updated to {self.dashboard_dir}/data/latest_decisions.json")
            self._generate_charts(trading_data, portfolio)
            logger.info(f"Charts generated in {self.dashboard_dir}/images/")
            self._update_timestamp()
            logger.info(f"Timestamp updated to {self.dashboard_dir}/data/last_updated.txt")
            self._sync_to_webserver()  # Sync files to web server
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def _ensure_dashboard_files_exist(self) -> None:
        """Ensure all necessary dashboard files exist"""
        # Check if index.html exists
        index_path = os.path.join(self.dashboard_dir, "index.html")
        if not os.path.exists(index_path):
            # Copy from template
            template_path = os.path.join("dashboard_templates", "index.html")
            if os.path.exists(template_path):
                shutil.copy(template_path, index_path)
                logger.info(f"Created dashboard index file from template: {index_path}")
            else:
                logger.warning(f"Dashboard template not found: {template_path}")
        
        # Check if analysis.html exists
        analysis_path = os.path.join(self.dashboard_dir, "analysis.html")
        if not os.path.exists(analysis_path):
            # Copy from template
            template_path = os.path.join("dashboard_templates", "analysis.html")
            if os.path.exists(template_path):
                shutil.copy(template_path, analysis_path)
                logger.info(f"Created dashboard analysis file from template: {analysis_path}")
            else:
                logger.warning(f"Dashboard analysis template not found: {template_path}")
            
    def _update_config_data(self) -> None:
        """Update configuration data for the dashboard"""
        try:
            from config import (
                TRADING_PAIRS, DECISION_INTERVAL_MINUTES, RISK_LEVEL,
                LLM_MODEL, PORTFOLIO_REBALANCE, MAX_TRADE_PERCENTAGE,
                SIMULATION_MODE, TARGET_ALLOCATION
            )
            
            # Create config data for dashboard
            config_data = {
                "trading_pairs": TRADING_PAIRS,
                "decision_interval_minutes": DECISION_INTERVAL_MINUTES,
                "risk_level": RISK_LEVEL,
                "llm_model": LLM_MODEL,
                "portfolio_rebalance": PORTFOLIO_REBALANCE,
                "max_trade_percentage": MAX_TRADE_PERCENTAGE,
                "simulation_mode": SIMULATION_MODE,
                "target_allocation": TARGET_ALLOCATION  # Use the TARGET_ALLOCATION dictionary from config
            }
            
            # Save config data to file
            with open(os.path.join(self.dashboard_dir, "data/config.json"), 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating config data: {e}")
            
    def _update_trading_data(self, data: Dict[str, Any]) -> None:
        """Update trading data for the dashboard"""
        try:
            # Save trading data to file
            with open(os.path.join(self.dashboard_dir, "data/trading_data.json"), 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error updating trading data: {e}")
    
    def _update_portfolio_data(self, portfolio: Dict[str, Any]) -> None:
        """Update portfolio data for the dashboard"""
        try:
            # Get target allocation from config
            from config import TARGET_ALLOCATION
            
            # Create portfolio data with current and target allocations
            portfolio_data = {
                "value_usd": portfolio.get("portfolio_value_usd", 0),
                "initial_value_usd": portfolio.get("initial_value_usd", 0),
                "return_pct": round(((portfolio.get("portfolio_value_usd", 0) - portfolio.get("initial_value_usd", 0)) / 
                                    portfolio.get("initial_value_usd", 1)) * 100, 2) if portfolio.get("initial_value_usd", 0) > 0 else 0,
                "holdings": {},
                "allocations": {},
                "target_allocations": TARGET_ALLOCATION  # Add target allocations from config
            }
            
            # Add holdings and calculate current allocations
            total_value = portfolio.get("portfolio_value_usd", 0)
            
            if total_value > 0:
                for asset in ["BTC", "ETH", "USD"]:
                    if asset in portfolio:
                        asset_data = portfolio[asset]
                        amount = asset_data.get("amount", 0)
                        
                        # Calculate USD value
                        if asset == "USD":
                            value_usd = amount
                        else:
                            price = asset_data.get("last_price_usd", 0)
                            value_usd = amount * price
                        
                        # Add to holdings
                        portfolio_data["holdings"][asset] = {
                            "amount": amount,
                            "value_usd": value_usd,
                            "price_usd": asset_data.get("last_price_usd", 0) if asset != "USD" else 1
                        }
                        
                        # Calculate allocation percentage
                        portfolio_data["allocations"][asset] = round((value_usd / total_value) * 100, 2)
            
            # Save portfolio data to file
            with open(os.path.join(self.dashboard_dir, "data/portfolio_data.json"), 'w') as f:
                json.dump(portfolio_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}")
    
    def _update_latest_decisions(self, trading_data: Dict[str, Any]) -> None:
        """Update latest trading decisions for the dashboard"""
        try:
            # Extract latest decisions from trading data
            latest_decisions = {}
            
            for product_id, data in trading_data.get("decisions", {}).items():
                latest_decisions[product_id] = {
                    "timestamp": data.get("timestamp", ""),
                    "action": data.get("action", ""),
                    "confidence": data.get("confidence", 0),
                    "reason": data.get("reason", "")
                }
            
            # Save latest decisions to file
            with open(os.path.join(self.dashboard_dir, "data/latest_decisions.json"), 'w') as f:
                json.dump(latest_decisions, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating latest decisions: {e}")
    
    def _generate_charts(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Generate charts for the dashboard"""
        try:
            # Create charts directory if it doesn't exist
            charts_dir = os.path.join(self.dashboard_dir, "images")
            os.makedirs(charts_dir, exist_ok=True)
            
            # Generate portfolio allocation chart
            self._generate_allocation_chart(portfolio, charts_dir)
            
            # Generate price charts for each trading pair
            for product_id in trading_data.get("prices", {}):
                self._generate_price_chart(product_id, trading_data["prices"][product_id], charts_dir)
                
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def _generate_allocation_chart(self, portfolio: Dict[str, Any], charts_dir: str) -> None:
        """Generate portfolio allocation chart"""
        try:
            # Get target allocation from config
            from config import TARGET_ALLOCATION
            
            # Calculate current allocations
            current_allocations = {}
            total_value = portfolio.get("portfolio_value_usd", 0)
            
            if total_value > 0:
                for asset in ["BTC", "ETH", "USD"]:
                    if asset in portfolio:
                        asset_data = portfolio[asset]
                        amount = asset_data.get("amount", 0)
                        
                        # Calculate USD value
                        if asset == "USD":
                            value_usd = amount
                        else:
                            price = asset_data.get("last_price_usd", 0)
                            value_usd = amount * price
                        
                        # Calculate allocation percentage
                        current_allocations[asset] = round((value_usd / total_value) * 100, 2)
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # Current allocation pie chart
            labels = list(current_allocations.keys())
            sizes = list(current_allocations.values())
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')
            ax1.set_title('Current Allocation')
            
            # Target allocation pie chart
            target_labels = list(TARGET_ALLOCATION.keys())
            target_sizes = [TARGET_ALLOCATION[asset] for asset in target_labels]
            ax2.pie(target_sizes, labels=target_labels, autopct='%1.1f%%', startangle=90)
            ax2.axis('equal')
            ax2.set_title('Target Allocation')
            
            # Save chart
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "allocation_chart.png"))
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating allocation chart: {e}")
    
    def _generate_price_chart(self, product_id: str, price_data: List[Dict[str, Any]], charts_dir: str) -> None:
        """Generate price chart for a trading pair"""
        try:
            # Extract timestamps and prices
            timestamps = [item.get("timestamp", "") for item in price_data]
            prices = [item.get("price", 0) for item in price_data]
            
            # Create figure
            plt.figure(figsize=(10, 6))
            plt.plot(timestamps, prices)
            plt.title(f"{product_id} Price")
            plt.xlabel("Time")
            plt.ylabel("Price (USD)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart
            plt.savefig(os.path.join(charts_dir, f"{product_id.replace('-', '_')}_price_chart.png"))
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating price chart for {product_id}: {e}")
    
    def _update_timestamp(self) -> None:
        """Update last updated timestamp"""
        try:
            # Use UTC time for consistency
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            with open(os.path.join(self.dashboard_dir, "data/last_updated.txt"), 'w') as f:
                f.write(timestamp)
                
        except Exception as e:
            logger.error(f"Error updating timestamp: {e}")
    
    def _sync_to_webserver(self) -> None:
        """Sync dashboard files to web server"""
        try:
            # Check if DASHBOARD_SYNC_COMMAND environment variable is set
            sync_command = os.environ.get("DASHBOARD_SYNC_COMMAND")
            
            if sync_command:
                # Execute sync command
                result = subprocess.run(sync_command, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Dashboard synced to web server: {result.stdout}")
                else:
                    logger.error(f"Error syncing dashboard to web server: {result.stderr}")
                    
        except Exception as e:
            logger.error(f"Error syncing dashboard to web server: {e}")
