import pandas as pd
import numpy as np
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
            df = pd.DataFrame(candles, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Sort by time
            df = df.sort_values('time')
            
            # Set time as index
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data for {product_id}: {e}")
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
            # Get current price
            price_data = self.client.get_product_price(product_id)
            price = float(price_data.get("price", 0))
            
            # Get 24h stats
            # Note: In a real implementation, you would get 24h stats from the API
            # For now, we'll just return the price
            
            return {
                "product_id": product_id,
                "price": price,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting market data for {product_id}: {e}")
            return {"product_id": product_id, "price": 0}
    
    def calculate_indicators(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators from historical data
        
        Args:
            historical_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with calculated indicators
        """
        try:
            df = historical_data.copy()
            
            # Ensure we have the required columns
            if 'close' not in df.columns:
                logger.error("Historical data missing 'close' column")
                return {}
                
            # Calculate RSI (Relative Strength Index)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Calculate MACD (Moving Average Convergence Divergence)
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_histogram = macd_line - signal_line
            
            # Calculate Bollinger Bands
            sma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            upper_band = sma20 + (std20 * 2)
            lower_band = sma20 - (std20 * 2)
            
            # Get the latest values
            latest_close = df['close'].iloc[-1]
            latest_rsi = rsi.iloc[-1]
            latest_macd = macd_line.iloc[-1]
            latest_signal = signal_line.iloc[-1]
            latest_histogram = macd_histogram.iloc[-1]
            latest_upper_band = upper_band.iloc[-1]
            latest_lower_band = lower_band.iloc[-1]
            latest_sma20 = sma20.iloc[-1]
            
            # Determine if price is overbought/oversold based on RSI
            rsi_signal = "oversold" if latest_rsi < 30 else "overbought" if latest_rsi > 70 else "neutral"
            
            # Determine MACD signal
            macd_signal = "bullish" if latest_macd > latest_signal else "bearish"
            
            # Determine Bollinger Band signal
            if latest_close > latest_upper_band:
                bb_signal = "overbought"
            elif latest_close < latest_lower_band:
                bb_signal = "oversold"
            else:
                bb_signal = "neutral"
            
            # Compile indicators
            indicators = {
                "rsi": {
                    "value": round(latest_rsi, 2),
                    "signal": rsi_signal
                },
                "macd": {
                    "value": round(latest_macd, 6),
                    "signal": round(latest_signal, 6),
                    "histogram": round(latest_histogram, 6),
                    "trend": macd_signal
                },
                "bollinger_bands": {
                    "upper": round(latest_upper_band, 2),
                    "middle": round(latest_sma20, 2),
                    "lower": round(latest_lower_band, 2),
                    "signal": bb_signal
                }
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
            
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
            
            # Ensure price is converted to float
            try:
                price = float(ticker.get("price", "0"))
            except (ValueError, TypeError):
                price = 0.0
            
            # Create market data with available information - ensure all values are float
            market_data = {
                "product_id": product_id,
                "price": price,
                "bid": price * 0.999,  # Estimate bid as slightly below price
                "ask": price * 1.001,  # Estimate ask as slightly above price
                "volume_24h": 0.0,  # We don't have this data
                "volume_30d": 0.0,  # We don't have this data
                "high_24h": 0.0,  # We don't have this data
                "low_24h": 0.0,  # We don't have this data
                "timestamp": datetime.now().isoformat()
            }
            
            # Calculate additional metrics - ensure we're using float values
            market_data["spread"] = float(market_data["ask"]) - float(market_data["bid"])
            
            # Avoid division by zero
            if price > 0:
                market_data["spread_percent"] = (float(market_data["spread"]) / float(market_data["price"])) * 100
            else:
                market_data["spread_percent"] = 0.0
            
            # Get historical data for volatility calculation
            historical_data = self.get_historical_data(product_id, "ONE_HOUR", 1)
            if not historical_data.empty:
                # Ensure close prices are numeric
                historical_data["close"] = pd.to_numeric(historical_data["close"], errors='coerce')
                
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
            
            # Ensure all price columns are numeric
            for col in ['close', 'open', 'high', 'low']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Calculate RSI (Relative Strength Index)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            # Avoid division by zero
            rs = avg_gain / avg_loss.replace(0, float('nan'))
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
            
            # Calculate MACD (Moving Average Convergence Divergence)
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1] if not pd.isna(macd_line.iloc[-1]) else 0.0
            current_signal = signal_line.iloc[-1] if not pd.isna(signal_line.iloc[-1]) else 0.0
            current_histogram = macd_histogram.iloc[-1] if not pd.isna(macd_histogram.iloc[-1]) else 0.0
            
            # Calculate Bollinger Bands
            sma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            
            upper_band = sma20 + (std20 * 2)
            lower_band = sma20 - (std20 * 2)
            
            current_sma20 = sma20.iloc[-1] if not pd.isna(sma20.iloc[-1]) else df['close'].iloc[-1]
            current_upper_band = upper_band.iloc[-1] if not pd.isna(upper_band.iloc[-1]) else df['close'].iloc[-1] * 1.02
            current_lower_band = lower_band.iloc[-1] if not pd.isna(lower_band.iloc[-1]) else df['close'].iloc[-1] * 0.98
            
            # Avoid division by zero
            if current_sma20 > 0:
                current_bollinger_width = (current_upper_band - current_lower_band) / current_sma20
            else:
                current_bollinger_width = 0.04  # Default value
            
            # Calculate market volatility
            returns = df['close'].pct_change()
            volatility_24h = returns.tail(24).std() * 100 if len(returns) >= 24 else 0.0  # Convert to percentage
            
            # Calculate market volume trend
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            avg_volume = df['volume'].rolling(window=24).mean()
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume.iloc[-1] if not pd.isna(avg_volume.iloc[-1]) and avg_volume.iloc[-1] > 0 else 1.0
            
            # Determine market trend
            sma50 = df['close'].rolling(window=50).mean()
            sma200 = df['close'].rolling(window=200).mean()
            
            current_price = df['close'].iloc[-1]
            
            # Handle NaN values in moving averages
            sma50_value = sma50.iloc[-1] if not pd.isna(sma50.iloc[-1]) and len(sma50) > 0 else current_price
            sma200_value = sma200.iloc[-1] if not pd.isna(sma200.iloc[-1]) and len(sma200) > 0 else current_price
            
            if current_price > sma50_value and sma50_value > sma200_value:
                market_trend = "bullish"
            elif current_price < sma50_value and sma50_value < sma200_value:
                market_trend = "bearish"
            else:
                market_trend = "neutral"
            
            # Return all indicators - ensure all values are numeric
            return {
                "rsi": float(current_rsi),
                "macd_line": float(current_macd),
                "macd_signal": float(current_signal),
                "macd_histogram": float(current_histogram),
                "bollinger_middle": float(current_sma20),
                "bollinger_upper": float(current_upper_band),
                "bollinger_lower": float(current_lower_band),
                "bollinger_width": float(current_bollinger_width),
                "volatility_24h": float(volatility_24h),
                "volume_ratio": float(volume_ratio),
                "market_trend": market_trend,
                "sma50": float(sma50_value),
                "sma200": float(sma200_value),
                "price": float(current_price),
                "volume_24h": float(df['volume'].tail(24).sum() if len(df) >= 24 else 0.0)
            }
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
