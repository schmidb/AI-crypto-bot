import time
import hmac
import hashlib
import base64
import json
import requests
from typing import Dict, List, Optional, Union, Any
import logging
from config import COINBASE_API_KEY, COINBASE_API_SECRET

logger = logging.getLogger(__name__)

class CoinbaseClient:
    """Client for interacting with Coinbase Advanced Trade API"""
    
    BASE_URL = "https://api.coinbase.com"
    ADVANCED_TRADE_URL = "https://api.coinbase.com/api/v3/brokerage"
    
    def __init__(self, api_key: str = COINBASE_API_KEY, api_secret: str = COINBASE_API_SECRET):
        """Initialize the Coinbase client with API credentials"""
        self.api_key = api_key
        self.api_secret = api_secret
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Coinbase API key and secret are required")
            
        logger.info("Coinbase client initialized")
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Generate signature for API request authentication"""
        message = timestamp + method + request_path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make an authenticated request to the Coinbase API"""
        url = f"{self.ADVANCED_TRADE_URL}{endpoint}"
        timestamp = str(int(time.time()))
        
        body = ""
        if data:
            body = json.dumps(data)
        
        signature = self._generate_signature(timestamp, method, endpoint, body)
        
        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=body if data else None
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_accounts(self) -> List[Dict]:
        """Get list of accounts/wallets"""
        response = self._request("GET", "/accounts")
        return response.get("accounts", [])
    
    def get_account_balance(self, currency: str) -> float:
        """Get balance for a specific currency"""
        accounts = self.get_accounts()
        for account in accounts:
            if account.get("currency") == currency:
                return float(account.get("available_balance", {}).get("value", 0))
        return 0.0
    
    def get_product_price(self, product_id: str) -> Dict:
        """Get current price for a product (e.g., 'BTC-USD')"""
        response = self._request("GET", f"/products/{product_id}/ticker")
        return response
    
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
        data = {
            "client_order_id": f"bot-order-{int(time.time())}",
            "product_id": product_id,
            "side": side,
            "order_configuration": {
                "market_market_ioc": {
                    "quote_size": str(size) if side == "BUY" else None,
                    "base_size": str(size) if side == "SELL" else None
                }
            }
        }
        
        return self._request("POST", "/orders", data=data)
    
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
        params = {
            "product_id": product_id,
            "granularity": granularity,
            "start": start_time,
            "end": end_time
        }
        
        response = self._request("GET", "/products/candles", params=params)
        return response.get("candles", [])
    def get_product_candles(self, product_id: str, start: str, end: str, granularity: str) -> List[Dict]:
        """
        Get historical candle data (alias for get_market_data for compatibility)
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            start: ISO 8601 start time
            end: ISO 8601 end time
            granularity: Time interval
            
        Returns:
            List of candles with OHLCV data
        """
        return self.get_market_data(product_id, granularity, start, end)
    def get_product_ticker(self, product_id: str) -> Dict:
        """
        Get product ticker (alias for get_product_price for compatibility)
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Ticker information
        """
        return self.get_product_price(product_id)
        
    def get_product_stats(self, product_id: str) -> Dict:
        """
        Get 24h stats for a product
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Stats information with default values
        """
        # This is a placeholder since we don't have a direct equivalent
        # in the current implementation
        return {
            "volume": "0",
            "volume_30day": "0",
            "high": "0",
            "low": "0"
        }
        
    def get_product_order_book(self, product_id: str, level: int = 1) -> Dict:
        """
        Get order book for a product
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            level: Order book level
            
        Returns:
            Order book information with default values
        """
        # This is a placeholder since we don't have a direct equivalent
        # Get the current price as a reference
        ticker = self.get_product_price(product_id)
        price = float(ticker.get("price", 0))
        
        # Create a simple order book with estimated values
        return {
            "bids": [[str(price * 0.999), "1.0"]],
            "asks": [[str(price * 1.001), "1.0"]]
        }
