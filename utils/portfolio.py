import os
import json
import logging
import datetime
import copy
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class Portfolio:
    """
    Portfolio class for managing cryptocurrency portfolio data.
    Handles validation, persistence, and calculations related to portfolio holdings.
    """
    
    def __init__(self, portfolio_file: str = "data/portfolio.json", 
                 initial_btc: float = 0.0, initial_eth: float = 0.0, initial_usd: float = 0.0):
        """
        Initialize the portfolio.
        
        Args:
            portfolio_file: Path to the portfolio JSON file
            initial_btc: Initial BTC amount if no portfolio exists
            initial_eth: Initial ETH amount if no portfolio exists
            initial_usd: Initial USD amount if no portfolio exists
        """
        self.portfolio_file = portfolio_file
        self.initial_btc = initial_btc
        self.initial_eth = initial_eth
        self.initial_usd = initial_usd
        self.data = self._load_portfolio()
        
    def _load_portfolio(self) -> Dict[str, Any]:
        """
        Load portfolio from file or initialize with default values.
        
        Returns:
            Dictionary containing portfolio data
        """
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    portfolio_data = json.load(f)
                    
                # Validate the loaded data
                portfolio_data = self._validate_portfolio_structure(portfolio_data)
                logger.info(f"Portfolio loaded from {self.portfolio_file}")
                return portfolio_data
            except Exception as e:
                logger.error(f"Error loading portfolio from {self.portfolio_file}: {e}")
        
        # Create a new portfolio with default values
        logger.info("Creating new portfolio with default values")
        return self._create_default_portfolio()
    
    def _create_default_portfolio(self) -> Dict[str, Any]:
        """
        Create a default portfolio structure with initial values.
        
        Returns:
            Dictionary containing default portfolio data
        """
        portfolio = {
            "BTC": {
                "amount": self.initial_btc,
                "initial_amount": self.initial_btc,
                "last_price_usd": 0.0
            },
            "ETH": {
                "amount": self.initial_eth,
                "initial_amount": self.initial_eth,
                "last_price_usd": 0.0
            },
            "USD": {
                "amount": self.initial_usd,
                "initial_amount": self.initial_usd
            },
            "trades_executed": 0,
            "portfolio_value_usd": 0.0,
            "initial_value_usd": 0.0,
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        # Save the new portfolio
        self.data = portfolio
        self.save()
        
        return portfolio
        
    def _validate_portfolio_structure(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fix portfolio structure if needed.
        
        Args:
            portfolio: Portfolio data to validate
            
        Returns:
            Validated portfolio data with all required fields
        """
        # Make a copy to avoid modifying the input
        validated = copy.deepcopy(portfolio)
        
        # Ensure top-level keys exist
        required_top_keys = [
            "BTC", "ETH", "USD", "trades_executed", 
            "portfolio_value_usd", "initial_value_usd", "last_updated"
        ]
        
        for key in required_top_keys:
            if key not in validated:
                if key in ["BTC", "ETH"]:
                    validated[key] = {
                        "amount": 0.0,
                        "initial_amount": 0.0,
                        "last_price_usd": 0.0
                    }
                elif key == "USD":
                    validated[key] = {
                        "amount": 0.0,
                        "initial_amount": 0.0
                    }
                elif key in ["portfolio_value_usd", "initial_value_usd", "trades_executed"]:
                    validated[key] = 0.0
                elif key == "last_updated":
                    validated[key] = datetime.datetime.now().isoformat()
        
        # Ensure asset keys exist
        for asset in ["BTC", "ETH", "USD"]:
            if not isinstance(validated[asset], dict):
                if asset in ["BTC", "ETH"]:
                    validated[asset] = {
                        "amount": 0.0,
                        "initial_amount": 0.0,
                        "last_price_usd": 0.0
                    }
                else:  # USD
                    validated[asset] = {
                        "amount": 0.0,
                        "initial_amount": 0.0
                    }
            else:
                # Ensure asset dict has required keys
                required_asset_keys = ["amount", "initial_amount"]
                if asset in ["BTC", "ETH"]:
                    required_asset_keys.append("last_price_usd")
                    
                for key in required_asset_keys:
                    if key not in validated[asset]:
                        validated[asset][key] = 0.0
        
        return validated
    
    def save(self) -> None:
        """Save portfolio data to file"""
        try:
            # Update last updated timestamp
            self.data["last_updated"] = datetime.datetime.now().isoformat()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
            
            with open(self.portfolio_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
                
            logger.info(f"Portfolio saved to {self.portfolio_file}")
        except Exception as e:
            logger.error(f"Error saving portfolio to {self.portfolio_file}: {e}")
    
    def update_prices(self, btc_price: float, eth_price: float) -> None:
        """
        Update asset prices and recalculate portfolio value.
        
        Args:
            btc_price: Current BTC price in USD
            eth_price: Current ETH price in USD
        """
        # Update prices
        self.data["BTC"]["last_price_usd"] = btc_price
        self.data["ETH"]["last_price_usd"] = eth_price
        
        # Recalculate portfolio value
        self._calculate_portfolio_value()
        
        # Save changes
        self.save()
        
    def _calculate_portfolio_value(self) -> float:
        """
        Calculate total portfolio value based on current prices.
        
        Returns:
            Total portfolio value in USD
        """
        btc_value = self.data["BTC"]["amount"] * self.data["BTC"]["last_price_usd"]
        eth_value = self.data["ETH"]["amount"] * self.data["ETH"]["last_price_usd"]
        usd_value = self.data["USD"]["amount"]
        
        total_value = btc_value + eth_value + usd_value
        self.data["portfolio_value_usd"] = total_value
        
        # Calculate initial value if not set
        if self.data["initial_value_usd"] == 0.0:
            initial_btc_value = self.data["BTC"]["initial_amount"] * self.data["BTC"]["last_price_usd"]
            initial_eth_value = self.data["ETH"]["initial_amount"] * self.data["ETH"]["last_price_usd"]
            initial_usd_value = self.data["USD"]["initial_amount"]
            initial_value = initial_btc_value + initial_eth_value + initial_usd_value
            self.data["initial_value_usd"] = initial_value
        
        return total_value
        
    def get_asset_allocation(self) -> Dict[str, float]:
        """
        Calculate current asset allocation percentages.
        
        Returns:
            Dictionary with asset allocation percentages
        """
        total_value = self.data["portfolio_value_usd"]
        if total_value <= 0:
            return {"BTC": 0.0, "ETH": 0.0, "USD": 0.0}
            
        btc_value = self.data["BTC"]["amount"] * self.data["BTC"]["last_price_usd"]
        eth_value = self.data["ETH"]["amount"] * self.data["ETH"]["last_price_usd"]
        usd_value = self.data["USD"]["amount"]
        
        return {
            "BTC": (btc_value / total_value) * 100,
            "ETH": (eth_value / total_value) * 100,
            "USD": (usd_value / total_value) * 100
        }
    
    def get_total_return(self) -> float:
        """
        Calculate total portfolio return percentage.
        
        Returns:
            Total return percentage
        """
        initial_value = self.data["initial_value_usd"]
        current_value = self.data["portfolio_value_usd"]
        
        if initial_value <= 0:
            return 0.0
            
        return ((current_value - initial_value) / initial_value) * 100
    
    def execute_trade(self, asset: str, action: str, amount: float, price: float) -> Dict[str, Any]:
        """
        Execute a trade and update portfolio.
        
        Args:
            asset: Asset symbol (BTC, ETH)
            action: Trade action (buy, sell)
            amount: Amount of asset to trade
            price: Price per unit in USD
            
        Returns:
            Dictionary with trade details
        """
        if asset not in ["BTC", "ETH"]:
            raise ValueError(f"Unsupported asset: {asset}")
            
        if action not in ["buy", "sell"]:
            raise ValueError(f"Unsupported action: {action}")
        
        # Calculate USD value
        usd_value = amount * price
        
        # Execute trade
        if action == "buy":
            # Check if enough USD is available
            if self.data["USD"]["amount"] < usd_value:
                return {
                    "success": False,
                    "message": f"Insufficient USD balance: {self.data['USD']['amount']} < {usd_value}"
                }
                
            # Update balances
            self.data["USD"]["amount"] -= usd_value
            self.data[asset]["amount"] += amount
            
        else:  # sell
            # Check if enough asset is available
            if self.data[asset]["amount"] < amount:
                return {
                    "success": False,
                    "message": f"Insufficient {asset} balance: {self.data[asset]['amount']} < {amount}"
                }
                
            # Update balances
            self.data[asset]["amount"] -= amount
            self.data["USD"]["amount"] += usd_value
        
        # Increment trades counter
        self.data["trades_executed"] += 1
        
        # Recalculate portfolio value
        self._calculate_portfolio_value()
        
        # Save changes
        self.save()
        
        return {
            "success": True,
            "action": action,
            "asset": asset,
            "amount": amount,
            "price": price,
            "usd_value": usd_value,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def update_from_exchange(self, exchange_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update portfolio with data from exchange.
        
        Args:
            exchange_data: Portfolio data from exchange
            
        Returns:
            Dictionary with update status
        """
        try:
            # Validate exchange data
            if not isinstance(exchange_data, dict):
                return {
                    "success": False,
                    "message": f"Invalid exchange data type: {type(exchange_data)}"
                }
                
            # Extract asset amounts
            btc_amount = exchange_data.get("BTC", {}).get("amount", self.data["BTC"]["amount"])
            eth_amount = exchange_data.get("ETH", {}).get("amount", self.data["ETH"]["amount"])
            usd_amount = exchange_data.get("USD", {}).get("amount", self.data["USD"]["amount"])
            
            # Update portfolio with new amounts
            self.data["BTC"]["amount"] = btc_amount
            self.data["ETH"]["amount"] = eth_amount
            self.data["USD"]["amount"] = usd_amount
            
            # Preserve price data if not provided
            if "last_price_usd" in exchange_data.get("BTC", {}):
                self.data["BTC"]["last_price_usd"] = exchange_data["BTC"]["last_price_usd"]
                
            if "last_price_usd" in exchange_data.get("ETH", {}):
                self.data["ETH"]["last_price_usd"] = exchange_data["ETH"]["last_price_usd"]
            
            # Recalculate portfolio value
            self._calculate_portfolio_value()
            
            # Save changes
            self.save()
            
            return {
                "success": True,
                "message": "Portfolio updated from exchange data",
                "btc_amount": btc_amount,
                "eth_amount": eth_amount,
                "usd_amount": usd_amount,
                "portfolio_value_usd": self.data["portfolio_value_usd"]
            }
            
        except Exception as e:
            logger.error(f"Error updating portfolio from exchange: {e}")
            return {
                "success": False,
                "message": f"Error updating portfolio: {str(e)}"
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get portfolio data as dictionary.
        
        Returns:
            Dictionary with portfolio data
        """
        return self.data
    
    def get_asset_value(self, asset: str) -> float:
        """
        Get current value of an asset in USD.
        
        Args:
            asset: Asset symbol (BTC, ETH, USD)
            
        Returns:
            Asset value in USD
        """
        if asset not in ["BTC", "ETH", "USD"]:
            raise ValueError(f"Unsupported asset: {asset}")
            
        if asset == "USD":
            return self.data["USD"]["amount"]
            
        return self.data[asset]["amount"] * self.data[asset]["last_price_usd"]
    
    def get_asset_amount(self, asset: str) -> float:
        """
        Get amount of an asset.
        
        Args:
            asset: Asset symbol (BTC, ETH, USD)
            
        Returns:
            Asset amount
        """
        if asset not in ["BTC", "ETH", "USD"]:
            raise ValueError(f"Unsupported asset: {asset}")
            
        return self.data[asset]["amount"]
    
    def get_asset_price(self, asset: str) -> float:
        """
        Get current price of an asset.
        
        Args:
            asset: Asset symbol (BTC, ETH)
            
        Returns:
            Asset price in USD
        """
        if asset not in ["BTC", "ETH"]:
            raise ValueError(f"Unsupported asset: {asset}")
            
        return self.data[asset]["last_price_usd"]
    
    def calculate_rebalance_actions(self, target_allocation: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Calculate actions needed to rebalance portfolio to target allocation.
        
        Args:
            target_allocation: Dictionary with target allocation percentages
            
        Returns:
            List of actions to take for rebalancing
        """
        # Validate target allocation
        if not all(asset in target_allocation for asset in ["BTC", "ETH", "USD"]):
            raise ValueError("Target allocation must include BTC, ETH, and USD")
            
        if abs(sum(target_allocation.values()) - 100) > 0.01:
            raise ValueError("Target allocation percentages must sum to 100")
        
        # Get current allocation
        current_allocation = self.get_asset_allocation()
        
        # Calculate differences
        differences = {
            asset: target_allocation[asset] - current_allocation[asset]
            for asset in ["BTC", "ETH", "USD"]
        }
        
        # Calculate portfolio value
        portfolio_value = self.data["portfolio_value_usd"]
        
        # Calculate actions
        actions = []
        
        # First handle assets that need to be reduced (sold)
        for asset in ["BTC", "ETH"]:
            if differences[asset] < -1.0:  # Only rebalance if difference is significant
                # Calculate amount to sell
                current_value = self.get_asset_value(asset)
                target_value = (target_allocation[asset] / 100) * portfolio_value
                value_to_sell = current_value - target_value
                
                # Calculate asset amount
                price = self.get_asset_price(asset)
                amount_to_sell = value_to_sell / price
                
                actions.append({
                    "action": "sell",
                    "asset": asset,
                    "amount": amount_to_sell,
                    "usd_value": value_to_sell,
                    "reason": "rebalance"
                })
        
        # Then handle assets that need to be increased (bought)
        usd_available = self.get_asset_amount("USD")
        
        for asset in ["BTC", "ETH"]:
            if differences[asset] > 1.0:  # Only rebalance if difference is significant
                # Calculate amount to buy
                current_value = self.get_asset_value(asset)
                target_value = (target_allocation[asset] / 100) * portfolio_value
                value_to_buy = target_value - current_value
                
                # Check if enough USD is available
                if value_to_buy > usd_available:
                    value_to_buy = usd_available
                    
                if value_to_buy <= 0:
                    continue
                    
                # Calculate asset amount
                price = self.get_asset_price(asset)
                amount_to_buy = value_to_buy / price
                
                actions.append({
                    "action": "buy",
                    "asset": asset,
                    "amount": amount_to_buy,
                    "usd_value": value_to_buy,
                    "reason": "rebalance"
                })
                
                # Update available USD
                usd_available -= value_to_buy
        
        return actions
