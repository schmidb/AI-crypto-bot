"""
Client for interacting with Coinbase Advanced Trade API using the official coinbase-advanced-py package
"""

import logging
import time
from typing import Dict, List, Optional, Any
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
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum 100ms between requests
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Coinbase API key and secret are required")
            
        try:
            self.client = RESTClient(api_key=api_key, api_secret=api_secret)
            logger.info("Coinbase Advanced Trade client initialized")
        except Exception as e:
            logger.error(f"Error initializing Coinbase client: {e}")
            # Don't raise - allow graceful degradation
            self.client = None
    
    def _rate_limit(self):
        """Implement basic rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _handle_api_error(self, error, operation: str):
        """Handle common API errors"""
        error_str = str(error).lower()
        
        if 'rate limit' in error_str:
            logger.warning(f"Rate limit hit during {operation}, waiting 60 seconds...")
            time.sleep(60)  # Wait 1 minute for rate limit reset
            return "rate_limit"
        elif 'connection' in error_str or 'timeout' in error_str:
            logger.warning(f"Connection issue during {operation}: {error}")
            return "connection_error"
        elif 'unauthorized' in error_str or 'authentication' in error_str:
            logger.error(f"Authentication error during {operation}: {error}")
            return "auth_error"
        else:
            logger.error(f"Unknown error during {operation}: {error}")
            return "unknown_error"
    
    def get_accounts(self) -> List[Dict]:
        """Get list of accounts/wallets"""
        if not self.client:
            logger.error("Coinbase client not initialized")
            return []
            
        try:
            self._rate_limit()
            response = self.client.get_accounts()
            accounts = []
            
            # Handle response object instead of dict
            if hasattr(response, 'accounts'):
                raw_accounts = response.accounts
            elif hasattr(response, '__dict__'):
                raw_accounts = getattr(response, 'accounts', [])
            else:
                raw_accounts = response.get("accounts", []) if hasattr(response, 'get') else []
            
            # Convert account objects to dictionaries
            for account in raw_accounts:
                if hasattr(account, '__dict__'):
                    # Convert object to dict
                    available_balance = getattr(account, 'available_balance', {})
                    
                    # Handle available_balance as either dict or object
                    if isinstance(available_balance, dict):
                        balance_value = available_balance.get('value', '0')
                        balance_currency = available_balance.get('currency', '')
                    else:
                        balance_value = getattr(available_balance, 'value', '0') if available_balance else '0'
                        balance_currency = getattr(available_balance, 'currency', '') if available_balance else ''
                    
                    account_dict = {
                        'uuid': getattr(account, 'uuid', ''),
                        'name': getattr(account, 'name', ''),
                        'currency': getattr(account, 'currency', ''),
                        'available_balance': {
                            'value': balance_value,
                            'currency': balance_currency
                        },
                        'default': getattr(account, 'default', False),
                        'active': getattr(account, 'active', True),
                        'type': getattr(account, 'type', ''),
                        'ready': getattr(account, 'ready', True)
                    }
                    accounts.append(account_dict)
                else:
                    # Already a dict
                    accounts.append(account)
            
            return accounts
        except Exception as e:
            error_type = self._handle_api_error(e, "get_accounts")
            if error_type == "rate_limit":
                logger.info("Waiting for rate limit reset...")
                return []  # Return empty for now, will retry later
            return []
    
    def get_account_balance(self, currency: str) -> float:
        """Get balance for a specific currency"""
        try:
            accounts = self.get_accounts()
            for account in accounts:
                # Handle both dict and object formats
                if hasattr(account, 'get'):
                    # Dict format
                    if account.get("currency") == currency:
                        return float(account.get("available_balance", {}).get("value", 0))
                else:
                    # Object format
                    if getattr(account, 'currency', None) == currency:
                        available_balance = getattr(account, 'available_balance', None)
                        if available_balance:
                            if hasattr(available_balance, 'value'):
                                return float(available_balance.value)
                            elif hasattr(available_balance, 'get'):
                                return float(available_balance.get('value', 0))
            return 0.0
        except Exception as e:
            logger.error(f"Error getting account balance for {currency}: {e}")
            return 0.0
    
    def get_product_price(self, product_id: str) -> Dict:
        """Get current price for a product (e.g., 'BTC-USD')"""
        try:
            response = self.client.get_product(product_id=product_id)
            # Handle response object instead of dict
            if hasattr(response, 'price'):
                price = response.price
            elif hasattr(response, '__dict__'):
                price = getattr(response, 'price', "0")
            else:
                price = response.get("price", "0") if hasattr(response, 'get') else "0"
            
            # Ensure price is converted to float for consistent type handling
            try:
                price_float = float(price)
                return {"price": price_float}
            except (ValueError, TypeError):
                logger.warning(f"Could not convert price '{price}' to float for {product_id}")
                return {"price": 0.0}
                
        except Exception as e:
            logger.error(f"Error getting product price for {product_id}: {e}")
            return {"price": 0.0}
    
    def _get_precision_limits(self) -> Dict[str, int]:
        """Get precision limits for different trading pairs"""
        return {
            'BTC-EUR': 8, 'BTC-USD': 8,
            'ETH-EUR': 6, 'ETH-USD': 6,
            'SOL-EUR': 3, 'SOL-USD': 3,  # SOL requires only 3 decimal places
            'ADA-EUR': 6, 'ADA-USD': 6,
            'DOT-EUR': 6, 'DOT-USD': 6,
            'LINK-EUR': 6, 'LINK-USD': 6
        }
    
    def _round_to_precision(self, amount: float, precision: int) -> float:
        """Round amount to specified decimal precision using ROUND_DOWN"""
        if amount == 0:
            return 0.0
        
        from decimal import Decimal, ROUND_DOWN
        
        # Convert to Decimal for precise rounding
        decimal_amount = Decimal(str(amount))
        
        # Create the precision string (e.g., '0.000001' for 6 decimal places)
        precision_str = '0.' + '0' * (precision - 1) + '1'
        precision_decimal = Decimal(precision_str)
        
        # Round down to avoid exceeding available balance
        rounded = decimal_amount.quantize(precision_decimal, rounding=ROUND_DOWN)
        
        return float(rounded)

    def place_market_order(self, product_id: str, side: str, size: float, confidence: float = 0) -> Dict:
        """
        Place a market order with proper precision handling and notifications
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            side: 'BUY' or 'SELL'
            size: Amount to buy/sell
            confidence: AI confidence level for the trade (0-100)
            
        Returns:
            Order details
        """
        try:
            client_order_id = f"bot-order-{int(time.time())}"
            
            # Get precision limits
            precision_limits = self._get_precision_limits()
            
            if side.upper() == "BUY":
                # For buy orders, specify quote size (fiat amount) - round to 2 decimal places
                rounded_size = round(size, 2)
                response = self.client.market_order_buy(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    quote_size=str(rounded_size)
                )
            else:
                # For sell orders, specify base size (crypto amount) with proper precision
                precision = precision_limits.get(product_id, 8)  # Default to 8 decimals
                rounded_size = self._round_to_precision(size, precision)
                
                # Ensure we have a valid amount to sell
                if rounded_size <= 0:
                    return {
                        "success": False, 
                        "error": f"Rounded sell amount is too small: {rounded_size} (original: {size})"
                    }
                
                logger.info(f"SELL order: {product_id} - Original: {size:.12f}, Rounded: {rounded_size:.12f} ({precision} decimals)")
                
                response = self.client.market_order_sell(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(rounded_size)
                )
            
            # Handle response object instead of dict
            if hasattr(response, '__dict__'):
                # Convert response object to dict for consistent handling
                response_dict = {
                    'success': True,
                    'order_id': getattr(response, 'order_id', None),
                    'client_order_id': getattr(response, 'client_order_id', None),
                    'product_id': getattr(response, 'product_id', product_id),
                    'side': getattr(response, 'side', side),
                    'order_configuration': getattr(response, 'order_configuration', {}),
                    'filled_size': getattr(response, 'filled_size', '0'),
                    'average_filled_price': getattr(response, 'average_filled_price', '0'),
                    'total_fees': getattr(response, 'total_fees', '0'),
                    'total_value_after_fees': getattr(response, 'total_value_after_fees', '0')
                }
                
                # If order was successful, send notification
                if response:
                    self._send_trade_notification(response_dict, side, product_id, size, confidence)
                    
                return response_dict
            else:
                # Handle dict response
                if response and not response.get('error'):
                    self._send_trade_notification(response, side, product_id, size, confidence)
                    
                return response
        except Exception as e:
            logger.error(f"Error placing market order for {product_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_trade_notification(self, order_response: Dict, side: str, product_id: str, size: float, confidence: float):
        """
        Send push notification for executed trade
        
        Args:
            order_response: Response from Coinbase API
            side: 'BUY' or 'SELL'
            product_id: Trading pair
            size: Trade size
            confidence: AI confidence level
        """
        try:
            # Import here to avoid circular imports
            from utils.notification_service import NotificationService
            
            notification_service = NotificationService()
            
            # Debug: Log the actual API response structure
            logger.info(f"DEBUG: Order response type: {type(order_response)}")
            if isinstance(order_response, dict):
                logger.info(f"DEBUG: Order response keys: {list(order_response.keys())}")
                logger.info(f"DEBUG: Order response content: {order_response}")
            else:
                logger.info(f"DEBUG: Order response attributes: {dir(order_response)}")
                logger.info(f"DEBUG: Order response content: {order_response}")
            
            # Extract fee information from order response
            total_fees = 0.0
            total_value_after_fees = 0.0
            filled_size = 0.0
            average_filled_price = 0.0
            
            # Handle both dict and object responses with comprehensive field checking
            if isinstance(order_response, dict):
                # Check various possible fee field names
                total_fees = float(order_response.get('total_fees', 0)) or \
                           float(order_response.get('fees', 0)) or \
                           float(order_response.get('fee', 0)) or \
                           float(order_response.get('commission', 0))
                
                total_value_after_fees = float(order_response.get('total_value_after_fees', 0)) or \
                                       float(order_response.get('net_proceeds', 0)) or \
                                       float(order_response.get('settled_total', 0))
                
                filled_size = float(order_response.get('filled_size', 0)) or \
                            float(order_response.get('executed_size', 0)) or \
                            float(order_response.get('size', 0))
                
                average_filled_price = float(order_response.get('average_filled_price', 0)) or \
                                     float(order_response.get('executed_price', 0)) or \
                                     float(order_response.get('price', 0))
                
                # Check for fills array (common in Coinbase Advanced Trade)
                if 'fills' in order_response and order_response['fills']:
                    fills = order_response['fills']
                    if isinstance(fills, list) and len(fills) > 0:
                        # Calculate from fills
                        total_fill_fees = 0.0
                        total_fill_size = 0.0
                        total_fill_value = 0.0
                        
                        for fill in fills:
                            if isinstance(fill, dict):
                                fill_fee = float(fill.get('commission', 0)) or float(fill.get('fee', 0))
                                fill_size = float(fill.get('size', 0))
                                fill_price = float(fill.get('price', 0))
                                
                                total_fill_fees += fill_fee
                                total_fill_size += fill_size
                                total_fill_value += fill_size * fill_price
                        
                        if total_fill_fees > 0:
                            total_fees = total_fill_fees
                        if total_fill_size > 0:
                            filled_size = total_fill_size
                            average_filled_price = total_fill_value / total_fill_size if total_fill_size > 0 else 0
                
            else:
                # Handle object responses
                total_fees = float(getattr(order_response, 'total_fees', 0)) or \
                           float(getattr(order_response, 'fees', 0)) or \
                           float(getattr(order_response, 'fee', 0)) or \
                           float(getattr(order_response, 'commission', 0))
                
                total_value_after_fees = float(getattr(order_response, 'total_value_after_fees', 0)) or \
                                       float(getattr(order_response, 'net_proceeds', 0)) or \
                                       float(getattr(order_response, 'settled_total', 0))
                
                filled_size = float(getattr(order_response, 'filled_size', 0)) or \
                            float(getattr(order_response, 'executed_size', 0)) or \
                            float(getattr(order_response, 'size', 0))
                
                average_filled_price = float(getattr(order_response, 'average_filled_price', 0)) or \
                                     float(getattr(order_response, 'executed_price', 0)) or \
                                     float(getattr(order_response, 'price', 0))
            
            # Get current price for fallback if needed
            if average_filled_price == 0.0:
                price_data = self.get_product_price(product_id)
                current_price = float(price_data.get('price', 0.0)) if price_data else 0.0
            else:
                current_price = average_filled_price
            
            # Calculate trade details with actual execution data
            if side.upper() == "BUY":
                # For BUY orders: we know the EUR amount spent and crypto received
                total_value = float(size)  # Original EUR amount requested
                crypto_amount = filled_size if filled_size > 0 else (total_value / current_price if current_price > 0 else 0.0)
                actual_eur_spent = total_value_after_fees if total_value_after_fees > 0 else total_value
            else:
                # For SELL orders: we know the crypto amount sold
                crypto_amount = filled_size if filled_size > 0 else float(size)
                total_value = total_value_after_fees if total_value_after_fees > 0 else (crypto_amount * current_price if current_price > 0 else 0.0)
                actual_eur_spent = total_value  # For sells, this is EUR received
            
            # If no fees were extracted from API response, calculate estimated fees
            if total_fees == 0.0 and total_value > 0:
                # Coinbase Advanced Trade fee structure (approximate)
                # Taker fee is typically 0.6% for retail, but can vary
                # This is a fallback calculation
                estimated_fee_rate = 0.006  # 0.6%
                total_fees = total_value * estimated_fee_rate
                logger.info(f"No fee information in API response, using estimated fee: €{total_fees:.4f} ({estimated_fee_rate*100:.1f}%)")
                
                # Adjust actual amounts based on estimated fees
                if side.upper() == "BUY":
                    # For BUY: fees reduce the crypto amount received
                    actual_eur_spent = total_value
                    crypto_amount = (total_value - total_fees) / current_price if current_price > 0 else crypto_amount
                else:
                    # For SELL: fees reduce the EUR amount received
                    actual_eur_spent = total_value - total_fees
            
            # Log extracted fee information for debugging
            logger.info(f"DEBUG: Extracted fee information:")
            logger.info(f"  total_fees: €{total_fees:.4f}")
            logger.info(f"  total_value_after_fees: €{total_value_after_fees:.4f}")
            logger.info(f"  filled_size: {filled_size:.8f}")
            logger.info(f"  average_filled_price: €{average_filled_price:.2f}")
            
            # Prepare enhanced trade data for notification
            trade_data = {
                'action': side.upper(),
                'product_id': product_id,
                'amount': crypto_amount,
                'price': current_price,
                'total_value': total_value,
                'confidence': float(confidence),
                'order_id': (getattr(order_response, 'order_id', None) if hasattr(order_response, 'order_id') 
                           else order_response.get('order_id', 'unknown') if isinstance(order_response, dict) 
                           else 'unknown'),
                'timestamp': datetime.now().isoformat(),
                # Enhanced fee information
                'total_fees': total_fees,
                'total_value_after_fees': total_value_after_fees,
                'filled_size': filled_size,
                'average_filled_price': average_filled_price,
                'actual_eur_spent': actual_eur_spent,
                'fee_percentage': (total_fees / total_value * 100) if total_value > 0 else 0
            }
            
            # Log detailed trade information including fees
            logger.info(f"Trade executed - {side} {product_id}:")
            logger.info(f"  Crypto amount: {crypto_amount:.8f}")
            logger.info(f"  Average price: €{current_price:.2f}")
            logger.info(f"  Total value: €{total_value:.2f}")
            logger.info(f"  Fees: €{total_fees:.4f}")
            logger.info(f"  Net value after fees: €{actual_eur_spent:.2f}")
            if total_fees > 0:
                fee_percentage = (total_fees / total_value) * 100 if total_value > 0 else 0
                logger.info(f"  Fee percentage: {fee_percentage:.3f}%")
            else:
                logger.warning(f"  No fee information available - this may indicate an API response parsing issue")
            
            # Send notification
            notification_service.send_trade_notification(trade_data)
            
            # Return enhanced result with fee information
            return {
                "success": True,
                "message": f"{side.upper()} order executed: {crypto_amount:.8f} {product_id.split('-')[0]} for €{total_value:.2f}",
                "executed_amount": crypto_amount,
                "executed_price": current_price,
                "fees": total_fees,
                "fee_percentage": (total_fees / total_value * 100) if total_value > 0 else 0,
                "total_value": total_value,
                "actual_eur_spent": actual_eur_spent,
                "order_id": trade_data['order_id'],
                "filled_size": filled_size,
                "average_filled_price": average_filled_price
            }
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
            # Don't fail the trade if notification fails
    
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
            
            # Handle response object instead of dict
            if hasattr(response, 'candles'):
                return response.candles
            elif hasattr(response, '__dict__'):
                return getattr(response, 'candles', [])
            else:
                return response.get("candles", []) if hasattr(response, 'get') else []
                
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
            
            # Handle response object instead of dict
            if hasattr(response, '__dict__'):
                # Extract relevant stats from response object
                return {
                    "volume": getattr(response, "volume_24h", "0"),
                    "volume_30day": getattr(response, "volume_30d", "0"),
                    "high": getattr(response, "price_high_24h", "0"),
                    "low": getattr(response, "price_low_24h", "0")
                }
            else:
                # Fallback to dict access
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
            
            # Handle response object
            if hasattr(response, 'pricebook'):
                pricebook = response.pricebook
                bids = getattr(pricebook, 'bids', [])
                asks = getattr(pricebook, 'asks', [])
                
                # Convert bid/ask objects to lists
                formatted_bids = []
                formatted_asks = []
                
                for bid in bids:
                    if hasattr(bid, 'price') and hasattr(bid, 'size'):
                        formatted_bids.append([bid.price, bid.size])
                    elif isinstance(bid, dict):
                        formatted_bids.append([bid.get("price", "0"), bid.get("size", "0")])
                
                for ask in asks:
                    if hasattr(ask, 'price') and hasattr(ask, 'size'):
                        formatted_asks.append([ask.price, ask.size])
                    elif isinstance(ask, dict):
                        formatted_asks.append([ask.get("price", "0"), ask.get("size", "0")])
                
                return {
                    "bids": formatted_bids,
                    "asks": formatted_asks
                }
            elif hasattr(response, '__dict__'):
                # Try to extract from response object
                bids = getattr(response, 'bids', [])
                asks = getattr(response, 'asks', [])
                
                formatted_bids = []
                formatted_asks = []
                
                for bid in bids:
                    if hasattr(bid, 'price') and hasattr(bid, 'size'):
                        formatted_bids.append([bid.price, bid.size])
                    elif hasattr(bid, 'get'):
                        formatted_bids.append([bid.get("price", "0"), bid.get("size", "0")])
                    else:
                        formatted_bids.append([getattr(bid, 'price', '0'), getattr(bid, 'size', '0')])
                
                for ask in asks:
                    if hasattr(ask, 'price') and hasattr(ask, 'size'):
                        formatted_asks.append([ask.price, ask.size])
                    elif hasattr(ask, 'get'):
                        formatted_asks.append([ask.get("price", "0"), ask.get("size", "0")])
                    else:
                        formatted_asks.append([getattr(ask, 'price', '0'), getattr(ask, 'size', '0')])
                
                return {
                    "bids": formatted_bids,
                    "asks": formatted_asks
                }
            else:
                # Fallback to dict access
                return {
                    "bids": [[bid.get("price"), bid.get("size")] for bid in response.get("bids", [])],
                    "asks": [[ask.get("price"), ask.get("size")] for ask in response.get("asks", [])]
                }
        except Exception as e:
            logger.error(f"Error getting order book for {product_id}: {e}")
            # Get current price as fallback
            price_data = self.get_product_price(product_id)
            price = price_data.get("price", 0.0)  # Already a float from get_product_price
            
            # Return estimated values
            return {
                "bids": [[str(price * 0.999), "1.0"]],
                "asks": [[str(price * 1.001), "1.0"]]
            }
    
    def get_price_changes(self, product_id: str) -> Dict[str, float]:
        """
        Get price changes for different time periods (1h, 4h, 24h, 5d)
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Dict with price changes as percentages
        """
        try:
            current_price = self.get_product_price(product_id).get('price', 0.0)
            if not current_price:
                return {"1h": 0.0, "4h": 0.0, "24h": 0.0, "5d": 0.0}
            
            # current_price is already a float from get_product_price
            now = datetime.utcnow()
            changes = {}
            
            # Define time periods
            periods = {
                "1h": timedelta(hours=1),
                "4h": timedelta(hours=4), 
                "24h": timedelta(hours=24),
                "5d": timedelta(days=5)
            }
            
            for period_name, period_delta in periods.items():
                try:
                    # Calculate start time
                    start_time = now - period_delta
                    
                    # Get historical data
                    # Use appropriate granularity based on time period
                    if period_name in ["1h", "4h"]:
                        granularity = "ONE_HOUR"
                    elif period_name == "24h":
                        granularity = "ONE_HOUR"
                    else:  # 5d
                        granularity = "ONE_DAY"
                    
                    historical_data = self.get_market_data(
                        product_id=product_id,
                        granularity=granularity,
                        start_time=start_time.isoformat() + 'Z',
                        end_time=now.isoformat() + 'Z'
                    )
                    
                    if historical_data and len(historical_data) > 0:
                        # Get the earliest candle (closest to our target time)
                        # Candles are typically returned in reverse chronological order
                        historical_candle = historical_data[-1] if isinstance(historical_data[-1], dict) else historical_data[-1].__dict__
                        
                        # Extract the opening price from the historical candle
                        if isinstance(historical_candle, dict):
                            historical_price = float(historical_candle.get('low', historical_candle.get('open', current_price)))
                        else:
                            historical_price = float(getattr(historical_candle, 'low', getattr(historical_candle, 'open', current_price)))
                        
                        # Calculate percentage change
                        if historical_price > 0:
                            change_percent = ((current_price - historical_price) / historical_price) * 100
                            changes[period_name] = round(change_percent, 2)
                        else:
                            changes[period_name] = 0.0
                    else:
                        changes[period_name] = 0.0
                        
                except Exception as e:
                    logger.warning(f"Error calculating {period_name} change for {product_id}: {e}")
                    changes[period_name] = 0.0
            
            return changes
            
        except Exception as e:
            logger.error(f"Error getting price changes for {product_id}: {e}")
            return {"1h": 0.0, "4h": 0.0, "24h": 0.0, "5d": 0.0}

    def get_portfolio(self) -> Dict[str, Any]:
        """Get complete portfolio data from Coinbase"""
        try:
            # Get trading pairs from environment
            from config import Config
            config = Config()
            trading_pairs = config.get_trading_pairs()
            base_currency = config.BASE_CURRENCY  # Use configured base currency (EUR)
            
            # Extract unique crypto currencies from trading pairs
            crypto_currencies = set()
            for pair in trading_pairs:
                if f'-{base_currency}' in pair:
                    crypto = pair.replace(f'-{base_currency}', '')
                    crypto_currencies.add(crypto)
            
            # Always include base currency and stable coins
            crypto_currencies.add(base_currency)
            crypto_currencies.add('USDC')  # Include USDC for portfolio tracking
            crypto_currencies.add('USD')   # Include USD for portfolio tracking
            
            # Get all accounts/wallets
            accounts = self.get_accounts()
            
            # Initialize portfolio structure dynamically
            portfolio = {
                "trades_executed": 0,
                f"portfolio_value_{base_currency.lower()}": 0,
                f"initial_value_{base_currency.lower()}": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            # Initialize each currency in the portfolio
            for currency in crypto_currencies:
                if currency == base_currency:
                    portfolio[currency] = {"amount": 0, "initial_amount": 0}
                else:
                    portfolio[currency] = {"amount": 0, "initial_amount": 0, f"last_price_{base_currency.lower()}": 0}
            
            # Fill in actual balances from Coinbase
            for account in accounts:
                # Handle both dict and object formats
                if hasattr(account, 'get'):
                    # Dict format
                    currency = account.get("currency")
                    if currency in crypto_currencies:
                        balance = float(account.get("available_balance", {}).get("value", 0))
                        portfolio[currency]["amount"] = balance
                        portfolio[currency]["initial_amount"] = balance  # Set initial amount to current balance
                else:
                    # Object format
                    currency = getattr(account, 'currency', None)
                    if currency in crypto_currencies:
                        available_balance = getattr(account, 'available_balance', None)
                        if available_balance:
                            if hasattr(available_balance, 'value'):
                                balance = float(available_balance.value)
                            elif hasattr(available_balance, 'get'):
                                balance = float(available_balance.get('value', 0))
                            else:
                                balance = 0.0
                            portfolio[currency]["amount"] = balance
                            portfolio[currency]["initial_amount"] = balance  # Set initial amount to current balance
            
            # Get current prices for all crypto currencies
            total_value = 0
            for currency in crypto_currencies:
                if currency != base_currency:
                    # Skip USD pricing if base currency is EUR (USD-EUR doesn't exist)
                    if currency == 'USD' and base_currency == 'EUR':
                        # Use approximate USD to EUR conversion (could be improved with real FX rate)
                        portfolio[currency][f"last_price_{base_currency.lower()}"] = 0.85  # Approximate USD/EUR rate
                        currency_value = portfolio[currency]["amount"] * 0.85
                        total_value += currency_value
                        logger.info(f"Retrieved {currency}: amount={portfolio[currency]['amount']}, price={base_currency}0.85 (estimated)")
                        continue
                    
                    try:
                        price_data = self.get_product_price(f"{currency}-{base_currency}")
                        price = price_data.get("price", 0.0)  # Already a float from get_product_price
                        portfolio[currency][f"last_price_{base_currency.lower()}"] = price
                        
                        # Calculate value
                        currency_value = portfolio[currency]["amount"] * price
                        total_value += currency_value
                        
                        logger.info(f"Retrieved {currency}: amount={portfolio[currency]['amount']}, price={base_currency}{price}")
                    except Exception as e:
                        logger.warning(f"Could not get price for {currency}-{base_currency}: {e}")
                        portfolio[currency][f"last_price_{base_currency.lower()}"] = 0
                else:
                    # Add base currency value
                    total_value += portfolio[base_currency]["amount"]
            
            # Update total portfolio value
            portfolio[f"portfolio_value_{base_currency.lower()}"] = total_value
            portfolio[f"initial_value_{base_currency.lower()}"] = total_value  # Set initial value to current value
            
            # Log portfolio summary
            currency_summary = []
            for currency in sorted(crypto_currencies):
                amount = portfolio[currency]["amount"]
                if amount > 0:
                    currency_summary.append(f"{currency}={amount}")
            
            logger.info(f"Retrieved portfolio from Coinbase: {', '.join(currency_summary)}")
            return portfolio
            
        except Exception as e:
            logger.error(f"Error getting portfolio from Coinbase: {e}")
            return {}
