import pandas as pd
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from coinbase_client import CoinbaseClient

logger = logging.getLogger(__name__)

class DataCollector:
    """Collects and processes market data from Coinbase"""
    
    def __init__(self, coinbase_client: CoinbaseClient):
        """Initialize the data collector with a Coinbase client"""
        self.client = coinbase_client
        logger.info("Data collector initialized")
    
    def get_historical_data(self, product_id: str, granularity: str, days_back: int = 7) -> pd.DataFrame:
        """
        Get historical market data for a trading pair
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            granularity: Time interval (e.g., 'ONE_HOUR', 'ONE_DAY')
            days_back: Number of days of historical data to retrieve
            
        Returns:
            DataFrame with historical market data
        """
        try:
            # Calculate start and end times
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            
            # Convert to unix timestamps (seconds since epoch)
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            # Use the wrapper method that properly handles the response
            candles = self.client.get_market_data(
                product_id=product_id,
                granularity=granularity,
                start_time=start_time.isoformat() + "Z",
                end_time=end_time.isoformat() + "Z"
            )
            
            if not candles:
                logger.warning(f"No historical data available for {product_id}")
                return pd.DataFrame()
            
            # Convert candle objects to list of dictionaries
            data = []
            for candle in candles:
                try:
                    if hasattr(candle, '__dict__'):
                        # Object format - try multiple attribute names
                        timestamp = None
                        if hasattr(candle, 'start'):
                            timestamp = int(candle.start)
                        elif hasattr(candle, 'time'):
                            timestamp = int(candle.time)
                        elif hasattr(candle, 'timestamp'):
                            timestamp = int(candle.timestamp)
                        else:
                            # Skip this candle if no timestamp found
                            logger.warning(f"Candle object missing timestamp attribute: {dir(candle)}")
                            continue
                            
                        row = {
                            'time': timestamp,
                            'low': float(getattr(candle, 'low', 0)),
                            'high': float(getattr(candle, 'high', 0)),
                            'open': float(getattr(candle, 'open', 0)),
                            'close': float(getattr(candle, 'close', 0)),
                            'volume': float(getattr(candle, 'volume', 0))
                        }
                    else:
                        # Dict format (fallback)
                        row = {
                            'time': int(candle.get('start', candle.get('time', candle.get('timestamp', 0)))),
                            'low': float(candle.get('low', 0)),
                            'high': float(candle.get('high', 0)),
                            'open': float(candle.get('open', 0)),
                            'close': float(candle.get('close', 0)),
                            'volume': float(candle.get('volume', 0))
                        }
                    
                    # Only add if we have a valid timestamp
                    if row['time'] > 0:
                        data.append(row)
                        
                except Exception as e:
                    logger.warning(f"Error processing candle data: {e}, candle: {candle}")
                    continue
            
            # Create DataFrame
            if not data:
                logger.warning(f"No valid candle data retrieved for {product_id}")
                # Return empty DataFrame with correct structure
                return pd.DataFrame(columns=['low', 'high', 'open', 'close', 'volume'])
                
            df = pd.DataFrame(data)
            
            # Convert timestamp to datetime
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Sort by time
            df = df.sort_values('time')
            
            # Set time as index
            df.set_index('time', inplace=True)
            
            logger.info(f"Retrieved {len(df)} candles for {product_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data for {product_id}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, product_id: str) -> float:
        """
        Get current price for a product
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Current price as float
        """
        try:
            price_data = self.client.get_product_price(product_id)
            return float(price_data.get("price", 0))
        except Exception as e:
            logger.error(f"Error getting current price for {product_id}: {e}")
            return 0.0

    def get_market_data(self, product_id: str) -> Dict[str, Any]:
        """
        Get current market data for a trading pair including price changes
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Dictionary with current market data and price changes
        """
        try:
            # Get current price
            price_data = self.client.get_product_price(product_id)
            price = float(price_data.get("price", 0))
            
            # Get price changes for different time periods
            price_changes = self.client.get_price_changes(product_id)
            
            return {
                "product_id": product_id,
                "price": price,
                "price_changes": price_changes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting market data for {product_id}: {e}")
            return {
                "product_id": product_id, 
                "price": 0,
                "price_changes": {"1h": 0.0, "4h": 0.0, "24h": 0.0, "5d": 0.0}
            }
    
    def calculate_indicators(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators from historical data
        
        Args:
            historical_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with calculated indicators
        """
        if historical_data.empty:
            return {}
        
        try:
            indicators = {}
            
            # Simple Moving Averages
            indicators['sma_20'] = historical_data['close'].rolling(window=20).mean().iloc[-1]
            indicators['sma_50'] = historical_data['close'].rolling(window=50).mean().iloc[-1]
            
            # RSI (Relative Strength Index)
            delta = historical_data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD
            exp1 = historical_data['close'].ewm(span=12).mean()
            exp2 = historical_data['close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            indicators['macd'] = macd.iloc[-1]
            indicators['macd_signal'] = signal.iloc[-1]
            indicators['macd_histogram'] = (macd - signal).iloc[-1]
            
            # Bollinger Bands
            sma_20 = historical_data['close'].rolling(window=20).mean()
            std_20 = historical_data['close'].rolling(window=20).std()
            indicators['bb_upper'] = (sma_20 + (std_20 * 2)).iloc[-1]
            indicators['bb_lower'] = (sma_20 - (std_20 * 2)).iloc[-1]
            indicators['bb_middle'] = sma_20.iloc[-1]
            
            # Current price
            indicators['current_price'] = historical_data['close'].iloc[-1]
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
