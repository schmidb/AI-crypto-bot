import json
import os
import datetime
from typing import Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

class DashboardUpdater:
    """Updates the web dashboard with latest trading data and portfolio information"""
    
    def __init__(self, dashboard_dir="dashboard"):
        """Initialize the dashboard updater"""
        self.dashboard_dir = dashboard_dir
        os.makedirs(f"{dashboard_dir}/data", exist_ok=True)
        os.makedirs(f"{dashboard_dir}/images", exist_ok=True)
    
    def update_dashboard(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Update the dashboard with latest trading and portfolio data"""
        self._update_trading_data(trading_data)
        self._update_portfolio_data(portfolio)
        self._generate_charts(trading_data, portfolio)
        self._update_timestamp()
    
    def _update_trading_data(self, trading_data: Dict[str, Any]) -> None:
        """Update trading data JSON file"""
        with open(f"{self.dashboard_dir}/data/trading_data.json", "w") as f:
            json.dump(trading_data, f, indent=2)
    
    def _update_portfolio_data(self, portfolio: Dict[str, Any]) -> None:
        """Update portfolio data JSON file"""
        # Calculate additional portfolio metrics
        if portfolio:
            # Calculate allocation percentages
            total_value = portfolio["portfolio_value_usd"]
            if total_value > 0:
                for asset in ["BTC", "ETH", "USD"]:
                    if asset in portfolio:
                        asset_value = portfolio[asset]["amount"]
                        if asset != "USD":
                            asset_value *= portfolio[asset]["last_price_usd"]
                        portfolio[asset]["value_usd"] = asset_value
                        portfolio[asset]["allocation"] = round((asset_value / total_value) * 100, 2)
                
                # Calculate target allocations and deviations
                target_allocations = {"BTC": 40, "ETH": 40, "USD": 20}
                for asset in ["BTC", "ETH", "USD"]:
                    if asset in portfolio:
                        current_allocation = portfolio[asset]["allocation"]
                        target = target_allocations[asset]
                        deviation = current_allocation - target
                        portfolio[asset]["deviation"] = round(deviation, 2)
                        
                        # Determine rebalance status
                        if abs(deviation) > 5:
                            if deviation > 0:
                                portfolio[asset]["rebalance_status"] = "Overweight"
                            else:
                                portfolio[asset]["rebalance_status"] = "Underweight"
                        else:
                            portfolio[asset]["rebalance_status"] = "Balanced"
                
                # Calculate total return
                if portfolio["initial_value_usd"] > 0:
                    portfolio["total_return"] = round(
                        ((total_value - portfolio["initial_value_usd"]) / portfolio["initial_value_usd"]) * 100, 
                        2
                    )
        
        # Save updated portfolio data
        with open(f"{self.dashboard_dir}/data/portfolio_data.json", "w") as f:
            json.dump(portfolio, f, indent=2)
        
        # Append to historical portfolio value for time series
        self._append_portfolio_history(portfolio)
    
    def _append_portfolio_history(self, portfolio: Dict[str, Any]) -> None:
        """Append current portfolio value to historical data"""
        history_file = f"{self.dashboard_dir}/data/portfolio_history.csv"
        
        # Create new history file if it doesn't exist
        if not os.path.exists(history_file):
            with open(history_file, "w") as f:
                f.write("timestamp,portfolio_value_usd,btc_amount,eth_amount,usd_amount,btc_price,eth_price\n")
        
        # Append current values
        with open(history_file, "a") as f:
            timestamp = datetime.datetime.now().isoformat()
            portfolio_value = portfolio.get("portfolio_value_usd", 0)
            btc_amount = portfolio.get("BTC", {}).get("amount", 0)
            eth_amount = portfolio.get("ETH", {}).get("amount", 0)
            usd_amount = portfolio.get("USD", {}).get("amount", 0)
            btc_price = portfolio.get("BTC", {}).get("last_price_usd", 0)
            eth_price = portfolio.get("ETH", {}).get("last_price_usd", 0)
            
            f.write(f"{timestamp},{portfolio_value},{btc_amount},{eth_amount},{usd_amount},{btc_price},{eth_price}\n")
    
    def _generate_charts(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Generate charts for the dashboard"""
        self._generate_portfolio_allocation_chart(portfolio)
        self._generate_portfolio_value_chart()
        self._generate_target_vs_current_allocation(portfolio)
    
    def _generate_portfolio_allocation_chart(self, portfolio: Dict[str, Any]) -> None:
        """Generate pie chart showing portfolio allocation"""
        if not portfolio:
            return
            
        # Extract data
        labels = []
        sizes = []
        
        for asset in ["BTC", "ETH", "USD"]:
            if asset in portfolio:
                asset_value = portfolio[asset]["amount"]
                if asset != "USD":
                    asset_value *= portfolio[asset]["last_price_usd"]
                
                if asset_value > 0:
                    labels.append(asset)
                    sizes.append(asset_value)
        
        # Create pie chart
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title('Current Portfolio Allocation')
        plt.savefig(f"{self.dashboard_dir}/images/portfolio_allocation.png")
        plt.close()
    
    def _generate_portfolio_value_chart(self) -> None:
        """Generate line chart showing portfolio value over time"""
        history_file = f"{self.dashboard_dir}/data/portfolio_history.csv"
        
        if not os.path.exists(history_file):
            return
            
        # Load historical data
        df = pd.read_csv(history_file)
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
        plt.savefig(f"{self.dashboard_dir}/images/portfolio_value.png")
        plt.close()
    
    def _generate_target_vs_current_allocation(self, portfolio: Dict[str, Any]) -> None:
        """Generate bar chart comparing target vs current allocation"""
        if not portfolio:
            return
            
        # Target allocation
        target = {"BTC": 40, "ETH": 40, "USD": 20}
        
        # Current allocation
        current = {}
        for asset in ["BTC", "ETH", "USD"]:
            if asset in portfolio:
                current[asset] = portfolio[asset].get("allocation", 0)
        
        # Create bar chart
        assets = list(target.keys())
        target_values = [target[asset] for asset in assets]
        current_values = [current.get(asset, 0) for asset in assets]
        
        x = range(len(assets))
        width = 0.35
        
        plt.figure(figsize=(10, 6))
        plt.bar(x, target_values, width, label='Target')
        plt.bar([i + width for i in x], current_values, width, label='Current')
        
        plt.xlabel('Assets')
        plt.ylabel('Allocation (%)')
        plt.title('Target vs Current Asset Allocation')
        plt.xticks([i + width/2 for i in x], assets)
        plt.legend()
        plt.savefig(f"{self.dashboard_dir}/images/allocation_comparison.png")
        plt.close()
    
    def _update_timestamp(self) -> None:
        """Update the last updated timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(f"{self.dashboard_dir}/data/last_updated.txt", "w") as f:
            f.write(timestamp)
