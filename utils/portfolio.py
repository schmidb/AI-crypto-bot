import os
import json
import logging
import datetime
import copy
from typing import Dict, Any, Optional, List, Union
from coinbase_client import CoinbaseClient

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
            initial_btc: Initial BTC amount if no portfolio exists and API fetch fails
            initial_eth: Initial ETH amount if no portfolio exists and API fetch fails
            initial_usd: Initial USD amount if no portfolio exists and API fetch fails
        """
        self.portfolio_file = portfolio_file
        self.initial_btc = initial_btc
        self.initial_eth = initial_eth
        self.initial_usd = initial_usd
        self.data = self._load_portfolio()
        
    def _load_portfolio(self) -> Dict[str, Any]:
        """
        Load portfolio from file or initialize with data from Coinbase.
        If Coinbase data fetch fails, use default values.
        
        Returns:
            Dictionary containing portfolio data
        """
        # First try to load from file
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
        
        # If file doesn't exist or loading failed, try to fetch from Coinbase
        try:
            logger.info("Attempting to fetch portfolio data from Coinbase")
            client = CoinbaseClient()
            coinbase_portfolio = client.get_portfolio()
            
            if coinbase_portfolio and isinstance(coinbase_portfolio, dict):
                # Validate and enhance the portfolio data
                portfolio_data = self._validate_portfolio_structure(coinbase_portfolio)
                logger.info("Portfolio initialized with data from Coinbase")
                self.data = portfolio_data
                self.save()
                return portfolio_data
        except Exception as e:
            logger.error(f"Error fetching portfolio from Coinbase: {e}")
        
        # If both file loading and Coinbase fetch failed, create a new portfolio
        logger.info("Creating new portfolio with default values")
        return self._create_default_portfolio()
    
    def _get_supported_currencies(self) -> set:
        """
        Get supported currencies from trading pairs configuration.
        
        Returns:
            Set of supported currency symbols
        """
        try:
            # Import config to get trading pairs
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from config import Config
            
            config = Config()
            trading_pairs = config.get_trading_pairs()
            
            # Extract unique crypto currencies from trading pairs
            crypto_currencies = set()
            for pair in trading_pairs:
                if '-USD' in pair:
                    crypto = pair.replace('-USD', '')
                    crypto_currencies.add(crypto)
            
            # Always include USD
            crypto_currencies.add('USD')
            
            return crypto_currencies
            
        except Exception as e:
            logger.warning(f"Could not get trading pairs from config, using defaults: {e}")
            # Fallback to default currencies
            return {'BTC', 'ETH', 'USD'}

    def _create_default_portfolio(self) -> Dict[str, Any]:
        """
        Create a default portfolio structure with initial values.
        
        Returns:
            Dictionary containing default portfolio data
        """
        # Get trading pairs from environment
        crypto_currencies = self._get_supported_currencies()
        
        portfolio = {
            "trades_executed": 0,
            "portfolio_value_usd": 0.0,
            "initial_value_usd": 0.0,
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        # Initialize each currency in the portfolio
        for currency in crypto_currencies:
            if currency == 'USD':
                portfolio[currency] = {
                    "amount": self.initial_usd,
                    "initial_amount": self.initial_usd
                }
            elif currency == 'BTC':
                portfolio[currency] = {
                    "amount": self.initial_btc,
                    "initial_amount": self.initial_btc,
                    "last_price_usd": 0.0
                }
            elif currency == 'ETH':
                portfolio[currency] = {
                    "amount": self.initial_eth,
                    "initial_amount": self.initial_eth,
                    "last_price_usd": 0.0
                }
            else:
                # Default to 0 for other currencies
                portfolio[currency] = {
                    "amount": 0.0,
                    "initial_amount": 0.0,
                    "last_price_usd": 0.0
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
        
        # Get supported currencies
        crypto_currencies = self._get_supported_currencies()
        
        # Ensure top-level keys exist
        required_top_keys = [
            "trades_executed", "portfolio_value_usd", "initial_value_usd", "last_updated"
        ]
        
        for key in required_top_keys:
            if key not in validated:
                if key in ["portfolio_value_usd", "initial_value_usd", "trades_executed"]:
                    validated[key] = 0.0
                elif key == "last_updated":
                    validated[key] = datetime.datetime.now().isoformat()
        
        # Ensure all currency keys exist
        for currency in crypto_currencies:
            if currency not in validated:
                if currency == 'USD':
                    validated[currency] = {
                        "amount": 0.0,
                        "initial_amount": 0.0
                    }
                else:
                    validated[currency] = {
                        "amount": 0.0,
                        "initial_amount": 0.0,
                        "last_price_usd": 0.0
                    }
            else:
                # Ensure currency dict has required keys
                if not isinstance(validated[currency], dict):
                    if currency == 'USD':
                        validated[currency] = {
                            "amount": 0.0,
                            "initial_amount": 0.0
                        }
                    else:
                        validated[currency] = {
                            "amount": 0.0,
                            "initial_amount": 0.0,
                            "last_price_usd": 0.0
                        }
                else:
                    # Ensure currency dict has required keys
                    required_asset_keys = ["amount", "initial_amount"]
                    if currency != 'USD':
                        required_asset_keys.append("last_price_usd")
                        
                    for key in required_asset_keys:
                        if key not in validated[currency]:
                            validated[currency][key] = 0.0
        
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
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        Update asset prices and recalculate portfolio value.
        
        Args:
            prices: Dictionary of asset prices (e.g., {"BTC": 50000, "ETH": 3000, "SOL": 100})
        """
        # Update prices for all provided assets
        for asset, price in prices.items():
            if asset in self.data and asset != 'USD':
                self.data[asset]["last_price_usd"] = price
        
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
        total_value = 0.0
        initial_value = 0.0
        
        # Calculate value for all assets
        for asset, data in self.data.items():
            if isinstance(data, dict) and "amount" in data:
                if asset == 'USD':
                    # USD value is direct
                    asset_value = data["amount"]
                    initial_asset_value = data["initial_amount"]
                else:
                    # Crypto value = amount * price
                    price = data.get("last_price_usd", 0.0)
                    asset_value = data["amount"] * price
                    initial_asset_value = data["initial_amount"] * price
                
                total_value += asset_value
                initial_value += initial_asset_value
        
        self.data["portfolio_value_usd"] = total_value
        
        # Calculate initial value if not set or if it's zero
        if self.data.get("initial_value_usd", 0.0) == 0.0:
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
            # Return zero allocation for all assets
            allocation = {}
            for asset, data in self.data.items():
                if isinstance(data, dict) and "amount" in data:
                    allocation[asset] = 0.0
            return allocation
            
        allocation = {}
        
        # Calculate allocation for all assets
        for asset, data in self.data.items():
            if isinstance(data, dict) and "amount" in data:
                if asset == 'USD':
                    asset_value = data["amount"]
                else:
                    price = data.get("last_price_usd", 0.0)
                    asset_value = data["amount"] * price
                
                allocation[asset] = (asset_value / total_value) * 100
        
        return allocation
    
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
    
    def execute_trade(self, asset: str, action: str, amount: float, price: float, log_trade: bool = True) -> Dict[str, Any]:
        """
        Execute a trade and update portfolio.
        
        Args:
            asset: Asset symbol (BTC, ETH, SOL, etc.)
            action: Trade action (buy, sell)
            amount: Amount of asset to trade
            price: Price per unit in USD
            
        Returns:
            Dictionary with trade details
        """
        # Check if asset is supported
        if asset not in self.data or asset == 'USD':
            return {
                "success": False,
                "message": f"Unsupported asset for trading: {asset}"
            }
            
        if action not in ["buy", "sell"]:
            return {
                "success": False,
                "message": f"Unsupported action: {action}"
            }
        
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
        
        # Log the trade to trade history (only if requested)
        if log_trade:
            self._log_trade_to_history(asset, action, amount, price, usd_value)
        
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
            
            updated_assets = []
            
            # Update all assets present in exchange data
            for asset, asset_data in exchange_data.items():
                if isinstance(asset_data, dict) and "amount" in asset_data:
                    # Ensure asset exists in portfolio
                    if asset not in self.data:
                        if asset == 'USD':
                            self.data[asset] = {"amount": 0.0, "initial_amount": 0.0}
                        else:
                            self.data[asset] = {"amount": 0.0, "initial_amount": 0.0, "last_price_usd": 0.0}
                    
                    # Update amount
                    old_amount = self.data[asset]["amount"]
                    new_amount = asset_data.get("amount", old_amount)
                    self.data[asset]["amount"] = new_amount
                    
                    # Update price if provided
                    if asset != 'USD' and "last_price_usd" in asset_data:
                        self.data[asset]["last_price_usd"] = asset_data["last_price_usd"]
                    
                    updated_assets.append(f"{asset}: {old_amount} -> {new_amount}")
            
            # Recalculate portfolio value
            self._calculate_portfolio_value()
            
            # Save changes
            self.save()
            
            return {
                "success": True,
                "message": f"Portfolio updated from exchange data: {', '.join(updated_assets)}",
                "portfolio_value_usd": self.data["portfolio_value_usd"],
                "updated_assets": len(updated_assets)
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
            asset: Asset symbol (BTC, ETH, SOL, USD, etc.)
            
        Returns:
            Asset value in USD
        """
        if asset not in self.data:
            return 0.0
            
        if asset == "USD":
            return self.data["USD"]["amount"]
            
        amount = self.data[asset].get("amount", 0.0)
        price = self.data[asset].get("last_price_usd", 0.0)
        return amount * price
    
    def get_asset_amount(self, asset: str) -> float:
        """
        Get amount of an asset.
        
        Args:
            asset: Asset symbol (BTC, ETH, SOL, USD, etc.)
            
        Returns:
            Asset amount
        """
        if asset not in self.data:
            return 0.0
            
        return self.data[asset].get("amount", 0.0)
    
    def get_asset_price(self, asset: str) -> float:
        """
        Get current price of an asset.
        
        Args:
            asset: Asset symbol (BTC, ETH, SOL, etc.)
            
        Returns:
            Asset price in USD
        """
        if asset not in self.data or asset == "USD":
            return 0.0 if asset != "USD" else 1.0
            
        return self.data[asset].get("last_price_usd", 0.0)
    
    def calculate_rebalance_actions(self, target_allocation: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Calculate actions needed to rebalance portfolio to target allocation.
        
        Args:
            target_allocation: Dictionary with target allocation percentages
            
        Returns:
            List of actions to take for rebalancing
        """
        # Get all assets in portfolio
        portfolio_assets = set()
        for asset, data in self.data.items():
            if isinstance(data, dict) and "amount" in data:
                portfolio_assets.add(asset)
        
        # Validate target allocation
        target_assets = set(target_allocation.keys())
        if not target_assets.issubset(portfolio_assets):
            missing_assets = target_assets - portfolio_assets
            raise ValueError(f"Target allocation includes unsupported assets: {missing_assets}")
            
        if abs(sum(target_allocation.values()) - 100) > 0.01:
            raise ValueError("Target allocation percentages must sum to 100")
        
        # Get current allocation
        current_allocation = self.get_asset_allocation()
        
        # Calculate differences
        differences = {}
        for asset in target_assets:
            current_pct = current_allocation.get(asset, 0.0)
            differences[asset] = target_allocation[asset] - current_pct
        
        # Calculate portfolio value
        portfolio_value = self.data["portfolio_value_usd"]
        
        # Calculate actions
        actions = []
        
        # First handle assets that need to be reduced (sold)
        crypto_assets = [asset for asset in target_assets if asset != 'USD']
        
        for asset in crypto_assets:
            if differences[asset] < -1.0:  # Only rebalance if difference is significant
                # Calculate amount to sell
                current_value = self.get_asset_value(asset)
                target_value = (target_allocation[asset] / 100) * portfolio_value
                value_to_sell = current_value - target_value
                
                # Calculate asset amount
                price = self.get_asset_price(asset)
                if price > 0:
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
        
        for asset in crypto_assets:
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
                if price > 0:
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
    
    def _log_trade_to_history(self, asset: str, action: str, amount: float, price: float, usd_value: float) -> None:
        """
        Log a trade to the trade history file.
        
        Args:
            asset: Asset symbol (BTC, ETH)
            action: Trade action (buy, sell)
            amount: Amount of asset traded
            price: Price per unit in USD
            usd_value: Total USD value of the trade
        """
        try:
            # Import here to avoid circular imports
            from utils.trade_logger import TradeLogger
            
            # Create trade logger instance
            trade_logger = TradeLogger()
            
            # Create decision and result dictionaries in the format expected by TradeLogger
            product_id = f"{asset}-USD"
            
            decision = {
                "action": action,
                "confidence": 100,  # Portfolio trades are executed with full confidence
                "reason": f"Portfolio trade: {action} {amount:.8f} {asset} at ${price:.2f}"
            }
            
            result = {
                "status": "success",
                "action": action,
                "product_id": product_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "confidence": 100,
                "reason": decision["reason"],
                "current_price": price,
                "price": price,
                "crypto_amount": amount,
                "trade_amount_usd": usd_value,
                "price_changes": {}
            }
            
            # Log the trade
            trade_logger.log_trade(product_id, decision, result)
            logger.info(f"Logged {action} trade: {amount:.8f} {asset} for ${usd_value:.2f}")
            
        except Exception as e:
            logger.error(f"Error logging trade to history: {e}")
            # Don't fail the trade execution if logging fails
