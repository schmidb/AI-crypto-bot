import pandas as pd
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List
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
            granularity: Time interval (ONE_MINUTE, FIVE_MINUTE, etc.)
            days_back: Number of days of historical data to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        # Format times as ISO 8601
        start_time_iso = start_time.isoformat() + "Z"
        end_time_iso = end_time.isoformat() + "Z"
        
        try:
            # Get candles from Coinbase
            candles = self.client.get_market_data(
                product_id=product_id,
                granularity=granularity,
                start_time=start_time_iso,
                end_time=end_time_iso
            )
            
            # Convert to DataFrame
            if not candles:
                logger.warning(f"No candles returned for {product_id}")
                return pd.DataFrame()
                
            df = pd.DataFrame(candles)
            
            # Rename columns to standard OHLCV format
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Convert price columns to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            logger.info(f"Retrieved {len(df)} candles for {product_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {product_id}: {e}")
            return pd.DataFrame()
    
    def get_current_market_data(self, product_ids: List[str]) -> Dict[str, Dict]:
        """
        Get current market data for multiple trading pairs
        
        Args:
            product_ids: List of trading pairs (e.g., ['BTC-USD', 'ETH-USD'])
            
        Returns:
            Dictionary mapping product_id to current market data
        """
        result = {}
        
        for product_id in product_ids:
            try:
                ticker_data = self.client.get_product_price(product_id)
                result[product_id] = {
                    'price': float(ticker_data.get('price', 0)),
                    'timestamp': datetime.utcnow(),
                    'volume_24h': float(ticker_data.get('volume', 0)),
                    'price_change_24h': float(ticker_data.get('price_change_24h', 0)),
                    'price_change_percentage_24h': float(ticker_data.get('price_change_percentage_24h', 0))
                }
                logger.info(f"Retrieved current market data for {product_id}")
                
            except Exception as e:
                logger.error(f"Error fetching current market data for {product_id}: {e}")
                result[product_id] = None
                
        return result
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators on OHLCV data
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added technical indicators
        """
        if df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        result = df.copy()
        
        # Simple Moving Averages
        result['sma_20'] = result['close'].rolling(window=20).mean()
        result['sma_50'] = result['close'].rolling(window=50).mean()
        result['sma_200'] = result['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        result['ema_12'] = result['close'].ewm(span=12, adjust=False).mean()
        result['ema_26'] = result['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        result['macd'] = result['ema_12'] - result['ema_26']
        result['macd_signal'] = result['macd'].ewm(span=9, adjust=False).mean()
        result['macd_hist'] = result['macd'] - result['macd_signal']
        
        # Relative Strength Index (RSI)
        delta = result['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        result['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        result['bb_middle'] = result['close'].rolling(window=20).mean()
        result['bb_std'] = result['close'].rolling(window=20).std()
        result['bb_upper'] = result['bb_middle'] + 2 * result['bb_std']
        result['bb_lower'] = result['bb_middle'] - 2 * result['bb_std']
        
        # Average True Range (ATR)
        high_low = result['high'] - result['low']
        high_close = (result['high'] - result['close'].shift()).abs()
        low_close = (result['low'] - result['close'].shift()).abs()
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        result['atr'] = true_range.rolling(window=14).mean()
        
        logger.info("Calculated technical indicators")
        return result
