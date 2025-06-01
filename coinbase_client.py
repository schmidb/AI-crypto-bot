"""
Client for interacting with Coinbase Advanced Trade API using the official coinbase-advanced-py package
"""

import logging
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from coinbase.rest import RESTClient
from config import COINBASE_API_KEY, COINBASE_API_SECRET

logger = logging.getLogger(__name__)

class CoinbaseClient:
    """Client for interacting with Coinbase Advanced Trade API"""
    
    def __init__(self, api_key: str = COINBASE_API_KEY, api_secret: str = COINBASE_API_SECRET):
        """Initialize the Coinbase client with API credentials"""
        self.api_key = api_key
        self.api_secret = api_secret
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Coinbase API key and secret are required")
            
        try:
            self.client = RESTClient(api_key=api_key, api_secret=api_secret)
            logger.info("Coinbase Advanced Trade client initialized")
        except Exception as e:
            logger.error(f"Error initializing Coinbase client: {e}")
            raise
    
    def get_accounts(self) -> List[Dict]:
        """Get list of accounts/wallets"""
        try:
            response = self.client.get_accounts()
            return response.get("accounts", [])
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return []
    
    def get_account_balance(self, currency: str) -> float:
        """Get balance for a specific currency"""
        try:
            accounts = self.get_accounts()
            for account in accounts:
                if account.get("currency") == currency:
                    return float(account.get("available_balance", {}).get("value", 0))
            return 0.0
        except Exception as e:
            logger.error(f"Error getting account balance for {currency}: {e}")
            return 0.0
    
    def get_product_price(self, product_id: str) -> Dict:
        """Get current price for a product (e.g., 'BTC-USD')"""
        try:
            response = self.client.get_product(product_id=product_id)
            # Extract price from product data
            price = response.get("price", "0")
            return {"price": price}
        except Exception as e:
            logger.error(f"Error getting product price for {product_id}: {e}")
            return {"price": "0"}
    
    def place_market_order(self, product_id: str, side: str, size: float) -> Dict:
        """
        Place a market order
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            side: 'BUY' or 'SELL'
            size: Amount to buy/sell
            
        Returns:
            Order details
        """
        try:
            client_order_id = f"bot-order-{int(time.time())}"
            
            if side.upper() == "BUY":
                # For buy orders, specify quote size (USD amount)
                response = self.client.create_market_order(
                    product_id=product_id,
                    side=side.upper(),
                    quote_size=str(size)
                )
            else:
                # For sell orders, specify base size (crypto amount)
                response = self.client.create_market_order(
                    product_id=product_id,
                    side=side.upper(),
                    base_size=str(size)
                )
                
            return response
        except Exception as e:
            logger.error(f"Error placing market order for {product_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_market_data(self, product_id: str, granularity: str, start_time: str, end_time: str) -> List[Dict]:
        """
        Get historical market data
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            granularity: Time interval (ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, THIRTY_MINUTE, ONE_HOUR, TWO_HOUR, SIX_HOUR, ONE_DAY)
            start_time: ISO 8601 start time
            end_time: ISO 8601 end time
            
        Returns:
            List of candles with OHLCV data
        """
        try:
            # Convert ISO string to unix timestamp (seconds since epoch)
            if isinstance(start_time, str):
                # Remove the 'Z' and convert to datetime
                start_time = start_time.replace('Z', '+00:00')
                start_dt = datetime.fromisoformat(start_time)
                start_timestamp = int(start_dt.timestamp())
            else:
                start_timestamp = int(start_time)
                
            if isinstance(end_time, str):
                # Remove the 'Z' and convert to datetime
                end_time = end_time.replace('Z', '+00:00')
                end_dt = datetime.fromisoformat(end_time)
                end_timestamp = int(end_dt.timestamp())
            else:
                end_timestamp = int(end_time)
                
            response = self.client.get_candles(
                product_id=product_id,
                start=start_timestamp,
                end=end_timestamp,
                granularity=granularity
            )
            
            return response.get("candles", [])
        except Exception as e:
            logger.error(f"Error getting market data for {product_id}: {e}")
            return []
    
    # Compatibility methods for existing code
    def get_product_candles(self, product_id: str, start: str, end: str, granularity: str) -> List[Dict]:
        """Alias for get_market_data for backward compatibility"""
        return self.get_market_data(product_id, granularity, start, end)
    
    def get_product_ticker(self, product_id: str) -> Dict:
        """Alias for get_product_price for backward compatibility"""
        return self.get_product_price(product_id)
    
    def get_product_stats(self, product_id: str) -> Dict:
        """Get 24h stats for a product"""
        try:
            # Get product details which include stats
            response = self.client.get_product(product_id=product_id)
            
            # Extract relevant stats
            return {
                "volume": response.get("volume_24h", "0"),
                "volume_30day": response.get("volume_30d", "0"),
                "high": response.get("price_high_24h", "0"),
                "low": response.get("price_low_24h", "0")
            }
        except Exception as e:
            logger.error(f"Error getting product stats for {product_id}: {e}")
            return {
                "volume": "0",
                "volume_30day": "0",
                "high": "0",
                "low": "0"
            }
    
    def get_product_order_book(self, product_id: str, level: int = 1) -> Dict:
        """Get order book for a product"""
        try:
            response = self.client.get_product_book(product_id=product_id, limit=level)
            
            # Format the response to match expected structure
            return {
                "bids": [[bid.get("price"), bid.get("size")] for bid in response.get("bids", [])],
                "asks": [[ask.get("price"), ask.get("size")] for ask in response.get("asks", [])]
            }
        except Exception as e:
            logger.error(f"Error getting order book for {product_id}: {e}")
            # Get current price as fallback
            price_data = self.get_product_price(product_id)
            price = float(price_data.get("price", 0))
            
            # Return estimated values
            return {
                "bids": [[str(price * 0.999), "1.0"]],
                "asks": [[str(price * 1.001), "1.0"]]
            }
    def get_portfolio(self) -> Dict[str, Any]:
        """Get complete portfolio data from Coinbase"""
        try:
            # Get all accounts/wallets
            accounts = self.get_accounts()
            
            # Initialize portfolio structure
            portfolio = {
                "BTC": {"amount": 0, "initial_amount": 0, "last_price_usd": 0},
                "ETH": {"amount": 0, "initial_amount": 0, "last_price_usd": 0},
                "USD": {"amount": 0, "initial_amount": 0},
                "trades_executed": 0,
                "portfolio_value_usd": 0,
                "initial_value_usd": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            # Fill in actual balances from Coinbase
            for account in accounts:
                currency = account.get("currency")
                if currency in ["BTC", "ETH", "USD"]:
                    balance = float(account.get("available_balance", {}).get("value", 0))
                    portfolio[currency]["amount"] = balance
                    portfolio[currency]["initial_amount"] = balance  # Set initial amount to current balance
            
            # Get current prices for BTC and ETH
            btc_price = float(self.get_product_price("BTC-USD").get("price", 0))
            eth_price = float(self.get_product_price("ETH-USD").get("price", 0))
            
            # Update prices in portfolio
            portfolio["BTC"]["last_price_usd"] = btc_price
            portfolio["ETH"]["last_price_usd"] = eth_price
            
            # Calculate total portfolio value
            btc_value = portfolio["BTC"]["amount"] * btc_price
            eth_value = portfolio["ETH"]["amount"] * eth_price
            usd_value = portfolio["USD"]["amount"]
            
            portfolio["portfolio_value_usd"] = btc_value + eth_value + usd_value
            portfolio["initial_value_usd"] = portfolio["portfolio_value_usd"]  # Set initial value to current value
            
            logger.info(f"Retrieved portfolio from Coinbase: BTC={portfolio['BTC']['amount']}, ETH={portfolio['ETH']['amount']}, USD={portfolio['USD']['amount']}")
            return portfolio
            
        except Exception as e:
            logger.error(f"Error getting portfolio from Coinbase: {e}")
            return {}
