import pandas as pd
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from coinbase_client import CoinbaseClient
import os
from google.cloud import storage
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path

logger = logging.getLogger(__name__)

class DataCollector:
    """Collects and processes market data from Coinbase"""
    
    def __init__(self, coinbase_client: CoinbaseClient, gcs_bucket_name: Optional[str] = None):
        """Initialize the data collector with a Coinbase client"""
        self.client = coinbase_client
        # Use the existing GOOGLE_CLOUD_PROJECT from .env, fallback to GCP_PROJECT_ID, then default
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'ai-crypto-bot')
        self.gcs_bucket_name = gcs_bucket_name or f"{project_id}-backtest-data"
        self.gcs_client = None
        self.local_cache_dir = Path("./data/cache")
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize GCS client if credentials are available
        try:
            self.gcs_client = storage.Client()
            logger.info(f"GCS client initialized for bucket: {self.gcs_bucket_name}")
        except Exception as e:
            logger.warning(f"GCS client initialization failed: {e}. Backtesting features will be limited.")
        
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
            
            # Format timestamps - remove timezone info before adding 'Z'
            start_str = start_time.replace(tzinfo=None).isoformat() + "Z"
            end_str = end_time.replace(tzinfo=None).isoformat() + "Z"
            
            # Use the wrapper method that properly handles the response
            candles = self.client.get_market_data(
                product_id=product_id,
                granularity=granularity,
                start_time=start_str,
                end_time=end_str
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
    
    def calculate_indicators(self, historical_data: pd.DataFrame, trading_style: str = "day_trading") -> Dict[str, Any]:
        """
        Calculate technical indicators from historical data optimized for trading style
        
        Args:
            historical_data: DataFrame with OHLCV data
            trading_style: Trading style (day_trading, swing_trading, long_term)
            
        Returns:
            Dictionary with calculated indicators
        """
        """
        Calculate technical indicators from historical data optimized for trading style
        
        Args:
            historical_data: DataFrame with OHLCV data
            trading_style: Trading style (day_trading, swing_trading, long_term)
            
        Returns:
            Dictionary with calculated indicators
        """
        if historical_data.empty:
            return {}
        
        try:
            indicators = {}
            
            # Determine optimal periods based on trading style
            if trading_style == "day_trading":
                # Day trading: Use shorter periods for faster signals
                rsi_period = 14
                bb_period = 4  # 4-hour Bollinger Bands for day trading
                sma_short = 10  # 10-hour SMA
                sma_long = 20   # 20-hour SMA
                macd_fast, macd_slow, macd_signal = 8, 17, 9  # Faster MACD for day trading
            elif trading_style == "swing_trading":
                # Swing trading: Medium periods
                rsi_period = 14
                bb_period = 20
                sma_short = 20
                sma_long = 50
                macd_fast, macd_slow, macd_signal = 12, 26, 9
            else:  # long_term
                # Long-term: Longer periods for smoother signals
                rsi_period = 21
                bb_period = 50
                sma_short = 50
                sma_long = 200
                macd_fast, macd_slow, macd_signal = 12, 26, 9
            
            # Simple Moving Averages (optimized for trading style)
            if len(historical_data) >= sma_short:
                indicators['sma_short'] = historical_data['close'].rolling(window=sma_short).mean().iloc[-1]
            if len(historical_data) >= sma_long:
                indicators['sma_long'] = historical_data['close'].rolling(window=sma_long).mean().iloc[-1]
            
            # Legacy SMA values for backward compatibility
            if len(historical_data) >= 20:
                indicators['sma_20'] = historical_data['close'].rolling(window=20).mean().iloc[-1]
            if len(historical_data) >= 50:
                indicators['sma_50'] = historical_data['close'].rolling(window=50).mean().iloc[-1]
            
            # RSI (Relative Strength Index) - optimized period
            if len(historical_data) >= rsi_period + 1:
                delta = historical_data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                rs = gain / loss
                indicators['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD (optimized for trading style)
            if len(historical_data) >= macd_slow:
                exp1 = historical_data['close'].ewm(span=macd_fast).mean()
                exp2 = historical_data['close'].ewm(span=macd_slow).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=macd_signal).mean()
                indicators['macd'] = macd.iloc[-1]
                indicators['macd_signal'] = signal.iloc[-1]
                indicators['macd_histogram'] = (macd - signal).iloc[-1]
            
            # Bollinger Bands (optimized for trading style - KEY CHANGE FOR DAY TRADING)
            if len(historical_data) >= bb_period:
                if trading_style == "day_trading":
                    # For day trading: Use 4-period BB on hourly data = 4-hour timeframe
                    logger.info(f"Using {bb_period}-period Bollinger Bands for day trading (4-hour timeframe)")
                
                sma_bb = historical_data['close'].rolling(window=bb_period).mean()
                std_bb = historical_data['close'].rolling(window=bb_period).std()
                indicators['bb_upper'] = (sma_bb + (std_bb * 2)).iloc[-1]
                indicators['bb_lower'] = (sma_bb - (std_bb * 2)).iloc[-1]
                indicators['bb_middle'] = sma_bb.iloc[-1]
                
                # Add Bollinger Band width for volatility assessment
                indicators['bb_width'] = ((indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle']) * 100
                
                # Add Bollinger Band position (where price is relative to bands)
                current_price = historical_data['close'].iloc[-1]
                bb_position = (current_price - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])
                indicators['bb_position'] = bb_position  # 0 = at lower band, 1 = at upper band, 0.5 = at middle
            
            # Additional day trading specific indicators
            if trading_style == "day_trading":
                # Stochastic RSI for better overbought/oversold signals in day trading
                if 'rsi' in indicators and len(historical_data) >= 14:
                    rsi_series = 100 - (100 / (1 + (delta.where(delta > 0, 0)).rolling(window=14).mean() / 
                                                (-delta.where(delta < 0, 0)).rolling(window=14).mean()))
                    rsi_min = rsi_series.rolling(window=14).min()
                    rsi_max = rsi_series.rolling(window=14).max()
                    stoch_rsi = ((rsi_series - rsi_min) / (rsi_max - rsi_min)) * 100
                    indicators['stoch_rsi'] = stoch_rsi.iloc[-1] if not stoch_rsi.empty else 50
                
                # Volume-weighted average price (VWAP) approximation
                if 'volume' in historical_data.columns and len(historical_data) >= 20:
                    typical_price = (historical_data['high'] + historical_data['low'] + historical_data['close']) / 3
                    vwap = (typical_price * historical_data['volume']).rolling(window=20).sum() / historical_data['volume'].rolling(window=20).sum()
                    indicators['vwap'] = vwap.iloc[-1]
            
            # Current price
            indicators['current_price'] = historical_data['close'].iloc[-1]
            
            # Add metadata about the indicators
            indicators['_metadata'] = {
                'trading_style': trading_style,
                'bb_period': bb_period,
                'rsi_period': rsi_period,
                'data_points': len(historical_data),
                'timeframe': '1H',
                'bb_timeframe_hours': bb_period  # This shows the effective timeframe for BB
            }
            
            logger.info(f"Calculated indicators for {trading_style}: BB period={bb_period}h, RSI period={rsi_period}, data points={len(historical_data)}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    # ===== BACKTESTING INFRASTRUCTURE METHODS =====
    
    def fetch_bulk_historical_data(self, product_id: str, start_date: datetime, end_date: datetime, 
                                 granularity: str = 'ONE_MINUTE') -> pd.DataFrame:
        """
        Fetch bulk historical data from Coinbase API with rate limiting and error handling
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            start_date: Start date for historical data
            end_date: End date for historical data
            granularity: Time interval (ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, SIX_HOUR, ONE_DAY)
            
        Returns:
            DataFrame with historical OHLCV data
        """
        try:
            logger.info(f"Fetching bulk historical data for {product_id} from {start_date} to {end_date}")
            
            # Calculate chunk size based on granularity to respect API limits
            granularity_minutes = {
                'ONE_MINUTE': 1,
                'FIVE_MINUTE': 5,
                'FIFTEEN_MINUTE': 15,
                'ONE_HOUR': 60,
                'SIX_HOUR': 360,
                'ONE_DAY': 1440
            }
            
            chunk_minutes = granularity_minutes.get(granularity, 60)
            # Coinbase API limit: 300 candles per request
            chunk_hours = min(300 * chunk_minutes / 60, 24 * 7)  # Max 1 week chunks
            
            all_data = []
            current_start = start_date
            
            while current_start < end_date:
                current_end = min(current_start + timedelta(hours=chunk_hours), end_date)
                
                try:
                    # Rate limiting: 10 requests per second
                    time.sleep(0.1)
                    
                    # Format timestamps - remove timezone info before adding 'Z'
                    start_str = current_start.replace(tzinfo=None).isoformat() + "Z"
                    end_str = current_end.replace(tzinfo=None).isoformat() + "Z"
                    
                    # Fetch data directly using the API for specific date range
                    candles = self.client.get_market_data(
                        product_id=product_id,
                        granularity=granularity,
                        start_time=start_str,
                        end_time=end_str
                    )
                    
                    if candles:
                        chunk_df = self._process_candles_to_dataframe(candles)
                        if not chunk_df.empty:
                            all_data.append(chunk_df)
                            logger.info(f"Fetched {len(chunk_df)} candles for {current_start.date()} to {current_end.date()}")
                    
                except Exception as e:
                    logger.error(f"Error fetching chunk {current_start} to {current_end}: {e}")
                    # Continue with next chunk on error
                
                current_start = current_end
            
            if not all_data:
                logger.warning(f"No data retrieved for {product_id}")
                return pd.DataFrame()
            
            # Combine all chunks
            combined_df = pd.concat(all_data, ignore_index=False)
            combined_df = combined_df.sort_index().drop_duplicates()
            
            # Validate data continuity
            self.validate_data_continuity(combined_df)
            
            logger.info(f"Successfully fetched {len(combined_df)} total candles for {product_id}")
            return combined_df
            
        except Exception as e:
            logger.error(f"Error in fetch_bulk_historical_data: {e}")
            return pd.DataFrame()
    
    def _process_candles_to_dataframe(self, candles: List) -> pd.DataFrame:
        """Convert candle objects to DataFrame (extracted from get_historical_data)"""
        data = []
        for candle in candles:
            try:
                if hasattr(candle, '__dict__'):
                    timestamp = None
                    if hasattr(candle, 'start'):
                        timestamp = int(candle.start)
                    elif hasattr(candle, 'time'):
                        timestamp = int(candle.time)
                    elif hasattr(candle, 'timestamp'):
                        timestamp = int(candle.timestamp)
                    else:
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
                    row = {
                        'time': int(candle.get('start', candle.get('time', candle.get('timestamp', 0)))),
                        'low': float(candle.get('low', 0)),
                        'high': float(candle.get('high', 0)),
                        'open': float(candle.get('open', 0)),
                        'close': float(candle.get('close', 0)),
                        'volume': float(candle.get('volume', 0))
                    }
                
                if row['time'] > 0:
                    data.append(row)
                    
            except Exception as e:
                logger.warning(f"Error processing candle: {e}")
                continue
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.sort_values('time')
        df.set_index('time', inplace=True)
        
        return df
    
    def upload_to_gcs(self, data: pd.DataFrame, bucket_path: str) -> bool:
        """
        Upload DataFrame to Google Cloud Storage as Parquet
        
        Args:
            data: DataFrame to upload
            bucket_path: GCS path (e.g., 'historical/BTC-USD/ONE_MINUTE/2024/12/data.parquet')
            
        Returns:
            True if successful, False otherwise
        """
        if not self.gcs_client:
            logger.error("GCS client not initialized")
            return False
            
        try:
            bucket = self.gcs_client.bucket(self.gcs_bucket_name)
            blob = bucket.blob(bucket_path)
            
            # Convert DataFrame to Parquet bytes
            table = pa.Table.from_pandas(data)
            parquet_buffer = pa.BufferOutputStream()
            pq.write_table(table, parquet_buffer, compression='gzip')
            
            # Upload to GCS
            blob.upload_from_string(parquet_buffer.getvalue().to_pybytes(), content_type='application/octet-stream')
            
            logger.info(f"Successfully uploaded {len(data)} rows to gs://{self.gcs_bucket_name}/{bucket_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            return False
    
    def download_from_gcs(self, bucket_path: str, use_cache: bool = True) -> pd.DataFrame:
        """
        Download DataFrame from Google Cloud Storage
        
        Args:
            bucket_path: GCS path to download from
            use_cache: Whether to use local cache
            
        Returns:
            DataFrame with historical data
        """
        # Check local cache first
        if use_cache:
            cache_file = self.local_cache_dir / bucket_path.replace('/', '_')
            if cache_file.exists():
                cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if cache_age < timedelta(days=7):  # 7-day cache TTL
                    try:
                        df = pd.read_parquet(cache_file)
                        logger.info(f"Loaded {len(df)} rows from local cache: {cache_file}")
                        return df
                    except Exception as e:
                        logger.warning(f"Error reading cache file: {e}")
        
        if not self.gcs_client:
            logger.error("GCS client not initialized")
            return pd.DataFrame()
            
        try:
            bucket = self.gcs_client.bucket(self.gcs_bucket_name)
            blob = bucket.blob(bucket_path)
            
            if not blob.exists():
                logger.warning(f"File not found in GCS: gs://{self.gcs_bucket_name}/{bucket_path}")
                return pd.DataFrame()
            
            # Download and convert to DataFrame
            parquet_data = blob.download_as_bytes()
            df = pd.read_parquet(pa.BufferReader(parquet_data))
            
            # Cache locally if enabled
            if use_cache:
                cache_file = self.local_cache_dir / bucket_path.replace('/', '_')
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(cache_file, compression='gzip')
            
            logger.info(f"Downloaded {len(df)} rows from gs://{self.gcs_bucket_name}/{bucket_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error downloading from GCS: {e}")
            return pd.DataFrame()
    
    def validate_data_continuity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data quality and continuity
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        if df.empty:
            return {"valid": False, "error": "Empty DataFrame"}
        
        try:
            validation_results = {
                "valid": True,
                "total_rows": len(df),
                "date_range": {
                    "start": df.index.min().isoformat(),
                    "end": df.index.max().isoformat()
                },
                "issues": []
            }
            
            # Check for missing timestamps (gaps)
            time_diff = df.index.to_series().diff()
            expected_freq = time_diff.mode()[0] if not time_diff.empty else pd.Timedelta(minutes=1)
            gaps = time_diff[time_diff > expected_freq * 1.5]
            
            if len(gaps) > 0:
                validation_results["issues"].append(f"Found {len(gaps)} time gaps")
                validation_results["gaps"] = len(gaps)
            
            # Validate OHLCV data consistency
            invalid_ohlc = df[(df['open'] > df['high']) | (df['low'] > df['close']) | 
                             (df['high'] < df['low']) | (df['volume'] < 0)]
            
            if len(invalid_ohlc) > 0:
                validation_results["issues"].append(f"Found {len(invalid_ohlc)} invalid OHLCV rows")
                validation_results["invalid_ohlcv"] = len(invalid_ohlc)
            
            # Check for suspicious price movements (>20% in single candle)
            price_changes = ((df['close'] - df['open']) / df['open']).abs()
            suspicious = price_changes[price_changes > 0.20]
            
            if len(suspicious) > 0:
                validation_results["issues"].append(f"Found {len(suspicious)} suspicious price movements (>20%)")
                validation_results["suspicious_moves"] = len(suspicious)
            
            # Calculate data quality score
            total_issues = len(gaps) + len(invalid_ohlc) + len(suspicious)
            quality_score = max(0, 100 - (total_issues / len(df) * 100))
            validation_results["quality_score"] = round(quality_score, 2)
            
            if quality_score < 99.5:
                validation_results["valid"] = False
                validation_results["error"] = f"Data quality score {quality_score}% below threshold (99.5%)"
            
            logger.info(f"Data validation complete: {validation_results['quality_score']}% quality score")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in data validation: {e}")
            return {"valid": False, "error": str(e)}
    
    def sync_historical_data(self, product_ids: List[str] = None, granularity: str = 'ONE_MINUTE', 
                           months_back: int = 12) -> Dict[str, Any]:
        """
        Incremental sync of historical data to GCS
        
        Args:
            product_ids: List of trading pairs to sync (default: ['BTC-USD', 'ETH-USD'])
            granularity: Time interval for data
            months_back: Number of months of historical data to maintain
            
        Returns:
            Dictionary with sync results
        """
        if product_ids is None:
            product_ids = ['BTC-USD', 'ETH-USD']
        
        sync_results = {
            "success": True,
            "products_synced": [],
            "errors": [],
            "total_rows_synced": 0
        }
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)
            
            for product_id in product_ids:
                try:
                    logger.info(f"Syncing historical data for {product_id}")
                    
                    # Fetch bulk historical data
                    df = self.fetch_bulk_historical_data(
                        product_id=product_id,
                        start_date=start_date,
                        end_date=end_date,
                        granularity=granularity
                    )
                    
                    if df.empty:
                        sync_results["errors"].append(f"No data retrieved for {product_id}")
                        continue
                    
                    # Group by month and upload to GCS
                    for year_month, month_data in df.groupby(df.index.to_period('M')):
                        year, month = year_month.year, year_month.month
                        bucket_path = f"historical/{product_id}/{granularity}/{year}/{month:02d}/data.parquet"
                        
                        success = self.upload_to_gcs(month_data, bucket_path)
                        if success:
                            sync_results["total_rows_synced"] += len(month_data)
                        else:
                            sync_results["errors"].append(f"Failed to upload {bucket_path}")
                    
                    sync_results["products_synced"].append(product_id)
                    logger.info(f"Successfully synced {len(df)} rows for {product_id}")
                    
                except Exception as e:
                    error_msg = f"Error syncing {product_id}: {e}"
                    logger.error(error_msg)
                    sync_results["errors"].append(error_msg)
            
            if sync_results["errors"]:
                sync_results["success"] = False
            
            logger.info(f"Sync complete: {sync_results['total_rows_synced']} total rows synced")
            return sync_results
            
        except Exception as e:
            logger.error(f"Error in sync_historical_data: {e}")
            return {"success": False, "error": str(e)}
