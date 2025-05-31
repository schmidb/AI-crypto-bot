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
            
            # Convert to ISO format
            start_iso = start_time.isoformat() + "Z"
            end_iso = end_time.isoformat() + "Z"
            
            # Get candles from Coinbase
            candles = self.client.get_market_data(
                product_id=product_id,
                start_time=start_iso,
                end_time=end_iso,
                granularity=granularity
            )
            
            if not candles:
                logger.warning(f"No historical data available for {product_id}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            
            # Rename columns
            df.columns = ['start', 'low', 'high', 'open', 'close', 'volume']
            
            # Convert timestamp to datetime - first convert to numeric type, then to datetime
            df['start'] = pd.to_datetime(pd.to_numeric(df['start']), unit='s')
            
            # Sort by time
            df = df.sort_values('start')
            
            logger.info(f"Retrieved {len(df)} candles for {product_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving historical data for {product_id}: {e}")
            return pd.DataFrame()
    
    def get_market_data(self, product_id: str) -> Dict[str, Any]:
        """
        Get current market data for a trading pair
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Dictionary with current market data
        """
        try:
            # Get product ticker (price)
            ticker = self.client.get_product_price(product_id)
            
            # Since we don't have direct methods for stats and order book,
            # we'll use what's available and provide reasonable defaults
            price = float(ticker.get("price", 0))
            
            # Create market data with available information
            market_data = {
                "product_id": product_id,
                "price": price,
                "bid": price * 0.999,  # Estimate bid as slightly below price
                "ask": price * 1.001,  # Estimate ask as slightly above price
                "volume_24h": 0,  # We don't have this data
                "volume_30d": 0,  # We don't have this data
                "high_24h": 0,  # We don't have this data
                "low_24h": 0,  # We don't have this data
                "timestamp": datetime.now().isoformat()
            }
            
            # Calculate additional metrics
            market_data["spread"] = market_data["ask"] - market_data["bid"]
            market_data["spread_percent"] = (market_data["spread"] / market_data["price"]) * 100
            
            # Get historical data for volatility calculation
            historical_data = self.get_historical_data(product_id, "ONE_HOUR", 1)
            if not historical_data.empty:
                # Calculate volatility (standard deviation of returns)
                returns = historical_data["close"].pct_change().dropna()
                market_data["volatility_24h"] = returns.std() * 100  # Convert to percentage
                
                # Determine market trend
                if len(historical_data) >= 24:
                    sma6 = historical_data["close"].tail(6).mean()
                    sma24 = historical_data["close"].tail(24).mean()
                    
                    if sma6 > sma24 and market_data["price"] > sma6:
                        market_data["market_trend"] = "bullish"
                    elif sma6 < sma24 and market_data["price"] < sma6:
                        market_data["market_trend"] = "bearish"
                    else:
                        market_data["market_trend"] = "neutral"
                else:
                    market_data["market_trend"] = "neutral"
            else:
                market_data["volatility_24h"] = 0.0
                market_data["market_trend"] = "neutral"
            
            logger.info(f"Retrieved market data for {product_id}")
            return market_data
            
        except Exception as e:
            logger.error(f"Error retrieving market data for {product_id}: {e}")
            return {}
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators from historical price data"""
        try:
            # Make a copy to avoid modifying the original dataframe
            df = df.copy()
            
            # Calculate RSI (Relative Strength Index)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Calculate MACD (Moving Average Convergence Divergence)
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = macd_histogram.iloc[-1]
            
            # Calculate Bollinger Bands
            sma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            
            upper_band = sma20 + (std20 * 2)
            lower_band = sma20 - (std20 * 2)
            
            current_sma20 = sma20.iloc[-1]
            current_upper_band = upper_band.iloc[-1]
            current_lower_band = lower_band.iloc[-1]
            current_bollinger_width = (current_upper_band - current_lower_band) / current_sma20
            
            # Calculate market volatility
            returns = df['close'].pct_change()
            volatility_24h = returns.tail(24).std() * 100  # Convert to percentage
            
            # Calculate market volume trend
            avg_volume = df['volume'].rolling(window=24).mean()
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume.iloc[-1] if not pd.isna(avg_volume.iloc[-1]) and avg_volume.iloc[-1] > 0 else 1.0
            
            # Determine market trend
            sma50 = df['close'].rolling(window=50).mean()
            sma200 = df['close'].rolling(window=200).mean()
            
            current_price = df['close'].iloc[-1]
            
            if current_price > sma50.iloc[-1] and sma50.iloc[-1] > sma200.iloc[-1]:
                market_trend = "bullish"
            elif current_price < sma50.iloc[-1] and sma50.iloc[-1] < sma200.iloc[-1]:
                market_trend = "bearish"
            else:
                market_trend = "neutral"
            
            # Return all indicators
            return {
                "rsi": current_rsi,
                "macd_line": current_macd,
                "macd_signal": current_signal,
                "macd_histogram": current_histogram,
                "bollinger_middle": current_sma20,
                "bollinger_upper": current_upper_band,
                "bollinger_lower": current_lower_band,
                "bollinger_width": current_bollinger_width,
                "volatility_24h": volatility_24h,
                "volume_ratio": volume_ratio,
                "market_trend": market_trend,
                "sma50": sma50.iloc[-1] if not pd.isna(sma50.iloc[-1]) else None,
                "sma200": sma200.iloc[-1] if not pd.isna(sma200.iloc[-1]) else None,
                "price": current_price,
                "volume_24h": df['volume'].tail(24).sum()
            }
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
