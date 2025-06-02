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
            
    def _update_config_data(self) -> None:
        """Update configuration data for the dashboard"""
        try:
            from config import (
                TRADING_PAIRS, DECISION_INTERVAL_MINUTES, RISK_LEVEL,
                LLM_MODEL, PORTFOLIO_REBALANCE, MAX_TRADE_PERCENTAGE,
<<<<<<< HEAD
                SIMULATION_MODE, TARGET_ALLOCATION
            )
            
            # Create config data for dashboard
            config_data = {
                "trading_pairs": TRADING_PAIRS,
=======
                SIMULATION_MODE
            )
            
            # Calculate next decision time based on current time and interval
            import datetime
            now = datetime.datetime.now()
            minutes_to_add = DECISION_INTERVAL_MINUTES - (now.minute % DECISION_INTERVAL_MINUTES)
            if minutes_to_add == DECISION_INTERVAL_MINUTES:
                minutes_to_add = 0
            next_decision = now + datetime.timedelta(minutes=minutes_to_add)
            next_decision = next_decision.replace(second=0, microsecond=0)
            next_decision_time = next_decision.strftime("%Y-%m-%d %H:%M:%S")
            
            config_data = {
                "trading_pairs": ",".join(TRADING_PAIRS),
>>>>>>> parent of cf67caf (adding trading performance analyses report)
                "decision_interval_minutes": DECISION_INTERVAL_MINUTES,
                "risk_level": RISK_LEVEL,
                "llm_model": LLM_MODEL,
                "portfolio_rebalance": PORTFOLIO_REBALANCE,
                "max_trade_percentage": MAX_TRADE_PERCENTAGE,
                "simulation_mode": SIMULATION_MODE,
<<<<<<< HEAD
                "target_allocation": TARGET_ALLOCATION  # Use the TARGET_ALLOCATION dictionary from config
            }
            
            # Save config data to file
            with open(os.path.join(self.dashboard_dir, "data/config.json"), 'w') as f:
=======
                "next_decision_time": next_decision_time
            }
            
            with open(f"{self.dashboard_dir}/data/config.json", "w") as f:
>>>>>>> parent of cf67caf (adding trading performance analyses report)
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating config data: {e}")
            
<<<<<<< HEAD
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
=======
    def _update_latest_decisions(self, trading_data: Dict[str, Any]) -> None:
        """Update latest trading decisions for the dashboard"""
        try:
            # Extract recent decisions from trading data
            latest_decisions = []
            
            # Check if trading_data has recent_trades
            if "recent_trades" in trading_data and trading_data["recent_trades"]:
                # Get the most recent trade for each product
                product_decisions = {}
                for trade in trading_data["recent_trades"]:
                    product_id = trade.get("product_id")
                    if product_id and (product_id not in product_decisions or 
                                      trade.get("timestamp", "") > product_decisions[product_id].get("timestamp", "")):
                        # Ensure the trade has a price field
                        if "price" in trade and trade["price"] > 0:
                            # Make sure current_price is also set for dashboard display
                            if "current_price" not in trade or trade["current_price"] == 0:
                                trade["current_price"] = trade["price"]
                        product_decisions[product_id] = trade
                
                # Convert to list
                latest_decisions = list(product_decisions.values())
                logger.info(f"Extracted {len(latest_decisions)} decisions from recent trades")
                
                # Debug log to check prices
                for decision in latest_decisions:
                    logger.info(f"Decision for {decision.get('product_id')}: price={decision.get('price')}, current_price={decision.get('current_price')}")
            
            # If we have trading results directly
            elif "trading_results" in trading_data:
                for product_id, result in trading_data["trading_results"].items():
                    if isinstance(result, dict):
                        decision = {
                            "product_id": product_id,
                            "action": result.get("action", "hold"),
                            "confidence": result.get("confidence", 0),
                            "reason": result.get("reason", "No reason provided"),
                            "timestamp": result.get("timestamp", datetime.datetime.now().isoformat()),
                            "price": result.get("price", 0),
                            "current_price": result.get("current_price", result.get("price", 0))
                        }
                        latest_decisions.append(decision)
                logger.info(f"Extracted {len(latest_decisions)} decisions from trading results")
            
            # Try to load existing decisions first
            existing_decisions = []
            try:
                existing_decisions_file = f"{self.dashboard_dir}/data/latest_decisions.json"
                if os.path.exists(existing_decisions_file):
                    with open(existing_decisions_file, 'r') as f:
                        existing_decisions = json.load(f)
                    logger.info(f"Loaded {len(existing_decisions)} existing decisions from file")
            except Exception as e:
                logger.warning(f"Error loading existing decisions: {e}")
            
            # If we have no new decisions but have existing ones, use those
            if not latest_decisions and existing_decisions:
                latest_decisions = existing_decisions
                logger.info("Using existing decisions as no new decisions are available")
            
            # Add market data to decisions if available
            if "market_data" in trading_data:
                for decision in latest_decisions:
                    product_id = decision.get("product_id")
                    if product_id in trading_data["market_data"]:
                        market_data = trading_data["market_data"][product_id]
                        market_price = market_data.get("price", 0)
                        
                        # Always update current_price with the latest market price if available
                        if market_price > 0:
                            decision["current_price"] = market_price
                            logger.info(f"Updated current_price for {product_id} to {market_price}")
                            
                            # If price is missing or zero, set it to the market price too
                            if "price" not in decision or decision["price"] == 0:
                                decision["price"] = market_price
                                logger.info(f"Updated price for {product_id} to {market_price}")
                        
                        # Add price changes if available
                        if "price_changes" in market_data:
                            decision["price_changes"] = market_data["price_changes"]
            
            # Create a map of product_id to decision for quick lookup
            decision_map = {d.get("product_id"): d for d in latest_decisions if d.get("product_id")}
            
            # Add any existing decisions that aren't in the latest decisions
            for existing in existing_decisions:
                product_id = existing.get("product_id")
                if product_id and product_id not in decision_map:
                    latest_decisions.append(existing)
            
            # Ensure all decisions have both price and current_price fields
            for decision in latest_decisions:
                if "price" in decision and decision["price"] > 0:
                    if "current_price" not in decision or decision["current_price"] == 0:
                        decision["current_price"] = decision["price"]
                elif "current_price" in decision and decision["current_price"] > 0:
                    if "price" not in decision or decision["price"] == 0:
                        decision["price"] = decision["current_price"]
            
            # Create the directory if it doesn't exist
            os.makedirs(f"{self.dashboard_dir}/data", exist_ok=True)
            
            # Save to file
            with open(f"{self.dashboard_dir}/data/latest_decisions.json", "w") as f:
                json.dump(latest_decisions, f, indent=2, default=str)
            
            logger.info(f"Saved {len(latest_decisions)} decisions to latest_decisions.json")
>>>>>>> parent of cf67caf (adding trading performance analyses report)
                
        except Exception as e:
            logger.error(f"Error updating latest decisions: {e}")
    
<<<<<<< HEAD
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
=======
    def _sync_to_webserver(self):
        """Copy dashboard files to web server directory"""
        try:
            web_dashboard_dir = "/var/www/html/crypto-bot"
            
            # Check if web directory exists
            if not os.path.exists(web_dashboard_dir):
                logger.info(f"Web dashboard directory {web_dashboard_dir} not found, skipping sync")
                return
                
            # Create target directories if they don't exist
            try:
                import shutil
                os.makedirs(f"{web_dashboard_dir}/data", exist_ok=True)
                os.makedirs(f"{web_dashboard_dir}/images", exist_ok=True)
                
                # Copy data files
                data_files = os.listdir(f"{self.dashboard_dir}/data")
                for file in data_files:
                    shutil.copy2(f"{self.dashboard_dir}/data/{file}", f"{web_dashboard_dir}/data/")
                
                # Copy image files
                if os.path.exists(f"{self.dashboard_dir}/images"):
                    image_files = os.listdir(f"{self.dashboard_dir}/images")
                    for file in image_files:
                        shutil.copy2(f"{self.dashboard_dir}/images/{file}", f"{web_dashboard_dir}/images/")
                
                # Copy HTML files if they exist in dashboard_templates
                templates_dir = "dashboard_templates"
                if os.path.exists(templates_dir):
                    html_files = [f for f in os.listdir(templates_dir) if f.endswith(".html")]
                    for file in html_files:
                        shutil.copy2(f"{templates_dir}/{file}", web_dashboard_dir)
                
                logger.info(f"Dashboard files synced to web server directory: {web_dashboard_dir}")
            except PermissionError as e:
                logger.error(f"Permission error during sync: {e}. Make sure your user has write permissions to {web_dashboard_dir}")
            except Exception as e:
                logger.error(f"Error during sync: {e}")
        except Exception as e:
            logger.error(f"Error syncing dashboard files to web server: {e}")
    
    def _update_trading_data(self, trading_data: Dict[str, Any]) -> None:
        """Update trading data JSON file"""
        with open(f"{self.dashboard_dir}/data/trading_data.json", "w") as f:
            json.dump(trading_data, f, indent=2)
    
    def _update_portfolio_data(self, portfolio: Dict[str, Any]) -> None:
        """Update portfolio data JSON file"""
        try:
            # Validate portfolio data
            if not portfolio or not isinstance(portfolio, dict):
                logger.warning(f"Invalid portfolio data: {type(portfolio)}")
                return
                
            # Make a deep copy of the portfolio to avoid modifying the original
            import copy
            portfolio_copy = copy.deepcopy(portfolio)
                
            # Ensure required keys exist
            required_keys = ["portfolio_value_usd", "initial_value_usd", "BTC", "ETH", "USD"]
            for key in required_keys:
                if key not in portfolio_copy:
                    logger.warning(f"Missing required key in portfolio data: {key}")
                    portfolio_copy[key] = 0 if key.endswith("_usd") else {"amount": 0, "last_price_usd": 0}
            
            # Calculate additional portfolio metrics
            # Calculate allocation percentages
            total_value = float(portfolio_copy["portfolio_value_usd"])
            if total_value > 0:
                for asset in ["BTC", "ETH", "USD"]:
                    if asset in portfolio_copy and isinstance(portfolio_copy[asset], dict):
                        # Ensure asset dict has required keys
                        if "amount" not in portfolio_copy[asset]:
                            portfolio_copy[asset]["amount"] = 0
                        if asset != "USD" and "last_price_usd" not in portfolio_copy[asset]:
                            portfolio_copy[asset]["last_price_usd"] = 0
                            
                        # Calculate asset value
                        asset_amount = float(portfolio_copy[asset]["amount"])
                        asset_value = asset_amount
                        if asset != "USD":
                            asset_price = float(portfolio_copy[asset]["last_price_usd"])
                            asset_value = asset_amount * asset_price
                            
                        portfolio_copy[asset]["value_usd"] = asset_value
                        portfolio_copy[asset]["allocation"] = round((asset_value / total_value) * 100, 2)
                
                # Calculate target allocations and deviations
                from config import TARGET_ALLOCATION
                target_allocations = TARGET_ALLOCATION
                for asset in [asset for asset in target_allocations.keys() if asset in ["BTC", "ETH", "USD"]]:
                    if asset in portfolio_copy and isinstance(portfolio_copy[asset], dict):
                        if "allocation" not in portfolio_copy[asset]:
                            portfolio_copy[asset]["allocation"] = 0
                            
                        current_allocation = portfolio_copy[asset]["allocation"]
                        target = target_allocations[asset]
                        deviation = current_allocation - target
                        portfolio_copy[asset]["deviation"] = round(deviation, 2)
                        
                        # Determine rebalance status
                        if abs(deviation) > 5:
                            if deviation > 0:
                                portfolio_copy[asset]["rebalance_status"] = "Overweight"
                            else:
                                portfolio_copy[asset]["rebalance_status"] = "Underweight"
                        else:
                            portfolio_copy[asset]["rebalance_status"] = "Balanced"
                
                # Calculate total return
                initial_value = float(portfolio_copy["initial_value_usd"])
                if initial_value > 0:
                    portfolio_copy["total_return"] = round(
                        ((total_value - initial_value) / initial_value) * 100, 
                        2
                    )
                else:
                    portfolio_copy["total_return"] = 0
            
            # Add timestamp to portfolio data
            portfolio_copy["last_updated"] = datetime.datetime.now().isoformat()
            
            # Save updated portfolio data
            with open(f"{self.dashboard_dir}/data/portfolio_data.json", "w") as f:
                json.dump(portfolio_copy, f, indent=2, default=str)
            
            # Log the updated portfolio values for debugging
            logger.info(f"Dashboard portfolio updated - BTC: {portfolio_copy['BTC']['amount']}, ETH: {portfolio_copy['ETH']['amount']}, USD: {portfolio_copy['USD']['amount']}, Total: ${portfolio_copy['portfolio_value_usd']}")
            
            # Append to historical portfolio value for time series
            self._append_portfolio_history(portfolio_copy)
            
        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}")
            # Create a minimal valid portfolio data file to prevent further errors
            minimal_portfolio = {
                "portfolio_value_usd": 0,
                "initial_value_usd": 0,
                "total_return": 0,
                "last_updated": datetime.datetime.now().isoformat(),
                "BTC": {"amount": 0, "last_price_usd": 0, "value_usd": 0, "allocation": 0},
                "ETH": {"amount": 0, "last_price_usd": 0, "value_usd": 0, "allocation": 0},
                "USD": {"amount": 0, "value_usd": 0, "allocation": 0}
            }
            with open(f"{self.dashboard_dir}/data/portfolio_data.json", "w") as f:
                json.dump(minimal_portfolio, f, indent=2, default=str)
    
    def _append_portfolio_history(self, portfolio: Dict[str, Any]) -> None:
        """Append current portfolio value to historical data"""
        try:
            history_file = f"{self.dashboard_dir}/data/portfolio_history.csv"
            
            # Create new history file if it doesn't exist
            if not os.path.exists(history_file):
                os.makedirs(os.path.dirname(history_file), exist_ok=True)
                with open(history_file, "w") as f:
                    f.write("timestamp,portfolio_value_usd,btc_amount,eth_amount,usd_amount,btc_price,eth_price\n")
            
            # Ensure portfolio data is valid
            if not isinstance(portfolio, dict):
                logger.warning(f"Invalid portfolio data type: {type(portfolio)}")
                return
                
            # Extract values with type checking
            timestamp = datetime.datetime.now().isoformat()
            portfolio_value = float(portfolio.get("portfolio_value_usd", 0))
            
            # Extract asset data with validation
            btc_data = portfolio.get("BTC", {})
            eth_data = portfolio.get("ETH", {})
            usd_data = portfolio.get("USD", {})
            
            # Ensure asset data is dictionary type
            if not isinstance(btc_data, dict): btc_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(eth_data, dict): eth_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(usd_data, dict): usd_data = {"amount": 0}
            
            # Extract values with defaults
            btc_amount = float(btc_data.get("amount", 0))
            eth_amount = float(eth_data.get("amount", 0))
            usd_amount = float(usd_data.get("amount", 0))
            btc_price = float(btc_data.get("last_price_usd", 0))
            eth_price = float(eth_data.get("last_price_usd", 0))
            
            # Append current values
            with open(history_file, "a") as f:
                f.write(f"{timestamp},{portfolio_value},{btc_amount},{eth_amount},{usd_amount},{btc_price},{eth_price}\n")
                
        except Exception as e:
            logger.error(f"Error appending portfolio history: {e}")
    
    def _generate_charts(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Generate charts for the dashboard"""
        try:
            # Validate inputs
            if not isinstance(portfolio, dict):
                logger.warning(f"Invalid portfolio data type for chart generation: {type(portfolio)}")
                return
                
            self._generate_portfolio_allocation_chart(portfolio)
            self._generate_portfolio_value_chart()
            self._generate_target_vs_current_allocation(portfolio)
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def _generate_portfolio_allocation_chart(self, portfolio: Dict[str, Any]) -> None:
        """Generate pie chart showing portfolio allocation"""
        try:
            if not portfolio or not isinstance(portfolio, dict):
                logger.warning("Invalid portfolio data for allocation chart")
                return
                
            # Extract data
            labels = []
            sizes = []
            
            for asset in ["BTC", "ETH", "USD"]:
                if asset in portfolio and isinstance(portfolio[asset], dict):
                    asset_data = portfolio[asset]
                    
                    # Calculate asset value
                    if "value_usd" in asset_data:
                        asset_value = float(asset_data["value_usd"])
                    else:
                        asset_amount = float(asset_data.get("amount", 0))
                        if asset != "USD" and "last_price_usd" in asset_data:
                            asset_price = float(asset_data["last_price_usd"])
                            asset_value = asset_amount * asset_price
                        else:
                            asset_value = asset_amount
                    
                    if asset_value > 0:
                        labels.append(asset)
                        sizes.append(asset_value)
            
            # Create pie chart if we have data
            if labels and sizes:
                plt.figure(figsize=(8, 8))
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                plt.axis('equal')
                plt.title('Current Portfolio Allocation')
                
                # Ensure directory exists
                os.makedirs(f"{self.dashboard_dir}/images", exist_ok=True)
                plt.savefig(f"{self.dashboard_dir}/images/portfolio_allocation.png")
                plt.close()
            else:
                logger.warning("No data available for portfolio allocation chart")
                
        except Exception as e:
            logger.error(f"Error generating portfolio allocation chart: {e}")
    
    def _generate_portfolio_value_chart(self) -> None:
        """Generate line chart showing portfolio value over time"""
        try:
            history_file = f"{self.dashboard_dir}/data/portfolio_history.csv"
            
            if not os.path.exists(history_file):
                logger.warning(f"Portfolio history file not found: {history_file}")
                return
                
            # Load historical data
            df = pd.read_csv(history_file)
            if df.empty:
                logger.warning("Portfolio history file is empty")
                return
                
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Create line chart
            plt.figure(figsize=(12, 6))
            plt.plot(df['timestamp'], df['portfolio_value_usd'])
            plt.title('Portfolio Value Over Time')
            plt.xlabel('Date')
            plt.ylabel('Value (USD)')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Ensure directory exists
            os.makedirs(f"{self.dashboard_dir}/images", exist_ok=True)
            plt.savefig(f"{self.dashboard_dir}/images/portfolio_value.png")
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating portfolio value chart: {e}")
    
    def _generate_target_vs_current_allocation(self, portfolio: Dict[str, Any]) -> None:
        """Generate bar chart comparing target vs current allocation"""
        try:
            if not portfolio or not isinstance(portfolio, dict):
                logger.warning("Invalid portfolio data for allocation comparison chart")
                return
                
            # Import target allocation from config
            from config import TARGET_ALLOCATION
            target = TARGET_ALLOCATION
            
            # Current allocation
            current = {}
            for asset in target.keys():
                if asset in portfolio and isinstance(portfolio[asset], dict):
                    # Calculate allocation if not already present
                    if "allocation" not in portfolio[asset]:
                        # Calculate asset value
                        if asset == "USD":
                            asset_value = portfolio[asset].get("amount", 0)
                        else:
                            asset_amount = portfolio[asset].get("amount", 0)
                            asset_price = portfolio[asset].get("last_price_usd", 0)
                            asset_value = asset_amount * asset_price
                            
                        # Calculate allocation percentage
                        total_value = portfolio.get("portfolio_value_usd", 0)
                        if total_value > 0:
                            allocation = (asset_value / total_value) * 100
                        else:
                            allocation = 0
                            
                        current[asset] = allocation
                    else:
                        current[asset] = portfolio[asset].get("allocation", 0)
                        
                    # Ensure it's a number
                    if not isinstance(current[asset], (int, float)):
                        try:
                            current[asset] = float(current[asset])
                        except (ValueError, TypeError):
                            current[asset] = 0
                else:
                    current[asset] = 0
            
            # Log the values for debugging
            logger.info(f"Target allocation: {target}")
            logger.info(f"Current allocation: {current}")
            
            # Create bar chart
            assets = list(target.keys())
            target_values = [target[asset] for asset in assets]
            current_values = [current.get(asset, 0) for asset in assets]
            
            x = range(len(assets))
            width = 0.35
            
            plt.figure(figsize=(10, 6))
            plt.bar(x, target_values, width, label='Target', color='blue')
            plt.bar([i + width for i in x], current_values, width, label='Current', color='orange')
            
            plt.xlabel('Assets')
            plt.ylabel('Allocation (%)')
            plt.title('Target vs Current Asset Allocation')
            plt.xticks([i + width/2 for i in x], assets)
            plt.legend()
            
            # Add value labels on top of bars
            for i, v in enumerate(target_values):
                plt.text(i, v + 1, f"{v}%", ha='center')
                
            for i, v in enumerate(current_values):
                plt.text(i + width, v + 1, f"{v:.1f}%", ha='center')
            
            # Set y-axis to start at 0 and have some headroom
            plt.ylim(0, max(max(target_values), max(current_values) if current_values else 0) * 1.2)
            
            # Ensure directory exists
            os.makedirs(f"{self.dashboard_dir}/images", exist_ok=True)
            plt.savefig(f"{self.dashboard_dir}/images/allocation_comparison.png")
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating allocation comparison chart: {e}")
    
    def _update_timestamp(self) -> None:
        """Update the last updated timestamp"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Ensure directory exists
            os.makedirs(f"{self.dashboard_dir}/data", exist_ok=True)
            with open(f"{self.dashboard_dir}/data/last_updated.txt", "w") as f:
>>>>>>> parent of cf67caf (adding trading performance analyses report)
                f.write(timestamp)
                
        except Exception as e:
            logger.error(f"Error updating timestamp: {e}")
<<<<<<< HEAD
    
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
=======
>>>>>>> parent of cf67caf (adding trading performance analyses report)
