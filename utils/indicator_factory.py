"""
Vectorized Indicator Factory for Backtesting

This module provides efficient, vectorized calculation of technical indicators
for use in backtesting strategies. All indicators are calculated for entire
historical datasets at once for maximum performance.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class IndicatorFactory:
    """Factory for calculating vectorized technical indicators"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the indicator factory
        
        Args:
            cache_dir: Directory for caching calculated indicators
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./data/cache/indicators")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._indicator_cache = {}
        
    def calculate_all_indicators(self, df: pd.DataFrame, product_id: str = "unknown", 
                               use_cache: bool = True) -> pd.DataFrame:
        """
        Calculate all technical indicators for a dataset
        
        Args:
            df: DataFrame with OHLCV data (indexed by datetime)
            product_id: Product identifier for caching
            use_cache: Whether to use cached results
            
        Returns:
            DataFrame with all indicators added as columns
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to indicator factory")
            return df.copy()
        
        # Check cache first
        cache_key = f"{product_id}_{len(df)}_{df.index.min()}_{df.index.max()}"
        if use_cache and cache_key in self._indicator_cache:
            logger.info(f"Using cached indicators for {product_id}")
            return self._indicator_cache[cache_key].copy()
        
        try:
            logger.info(f"Calculating indicators for {product_id} ({len(df)} rows)")
            
            # Start with original data
            result_df = df.copy()
            
            # Calculate all indicator groups
            result_df = self._add_moving_averages(result_df)
            result_df = self._add_rsi_indicators(result_df)
            result_df = self._add_macd_indicators(result_df)
            result_df = self._add_bollinger_bands(result_df)
            result_df = self._add_volume_indicators(result_df)
            result_df = self._add_volatility_indicators(result_df)
            result_df = self._add_momentum_indicators(result_df)
            result_df = self._add_market_regime_indicators(result_df)
            
            # Cache the result
            if use_cache:
                self._indicator_cache[cache_key] = result_df.copy()
                logger.info(f"Cached indicators for {product_id}")
            
            logger.info(f"Calculated {len(result_df.columns) - len(df.columns)} indicators")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df.copy()
    
    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add various moving averages"""
        try:
            # Simple Moving Averages
            for period in [10, 20, 50, 200]:
                if len(df) >= period:
                    df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            
            # Exponential Moving Averages
            for period in [12, 26, 50]:
                if len(df) >= period:
                    df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            
            # Volume Weighted Moving Average (approximation)
            if len(df) >= 20:
                typical_price = (df['high'] + df['low'] + df['close']) / 3
                vwma = (typical_price * df['volume']).rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
                df['vwma_20'] = vwma
            
            return df
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return df
    
    def _add_rsi_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add RSI and related indicators"""
        try:
            # Standard RSI
            for period in [14, 21]:
                if len(df) >= period + 1:
                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rs = gain / loss
                    df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
            
            # Stochastic RSI
            if 'rsi_14' in df.columns and len(df) >= 14:
                rsi_min = df['rsi_14'].rolling(window=14).min()
                rsi_max = df['rsi_14'].rolling(window=14).max()
                df['stoch_rsi'] = ((df['rsi_14'] - rsi_min) / (rsi_max - rsi_min)) * 100
            
            return df
        except Exception as e:
            logger.error(f"Error calculating RSI indicators: {e}")
            return df
    
    def _add_macd_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD indicators"""
        try:
            # Standard MACD (12, 26, 9)
            if len(df) >= 26:
                ema_12 = df['close'].ewm(span=12).mean()
                ema_26 = df['close'].ewm(span=26).mean()
                df['macd'] = ema_12 - ema_26
                df['macd_signal'] = df['macd'].ewm(span=9).mean()
                df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Fast MACD for day trading (8, 17, 9)
            if len(df) >= 17:
                ema_8 = df['close'].ewm(span=8).mean()
                ema_17 = df['close'].ewm(span=17).mean()
                df['macd_fast'] = ema_8 - ema_17
                df['macd_fast_signal'] = df['macd_fast'].ewm(span=9).mean()
                df['macd_fast_histogram'] = df['macd_fast'] - df['macd_fast_signal']
            
            return df
        except Exception as e:
            logger.error(f"Error calculating MACD indicators: {e}")
            return df
    
    def _add_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Bollinger Bands with multiple periods"""
        try:
            # Standard Bollinger Bands (20 period)
            for period in [20, 4]:  # 20 for swing trading, 4 for day trading
                if len(df) >= period:
                    sma = df['close'].rolling(window=period).mean()
                    std = df['close'].rolling(window=period).std()
                    
                    df[f'bb_upper_{period}'] = sma + (std * 2)
                    df[f'bb_lower_{period}'] = sma - (std * 2)
                    df[f'bb_middle_{period}'] = sma
                    
                    # Bollinger Band width (volatility measure)
                    df[f'bb_width_{period}'] = ((df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / df[f'bb_middle_{period}']) * 100
                    
                    # Bollinger Band position (0 = lower band, 1 = upper band)
                    df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'])
            
            return df
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return df
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based indicators"""
        try:
            # Volume SMA
            for period in [10, 20]:
                if len(df) >= period:
                    df[f'volume_sma_{period}'] = df['volume'].rolling(window=period).mean()
            
            # Volume Rate of Change
            if len(df) >= 10:
                df['volume_roc'] = df['volume'].pct_change(periods=10) * 100
            
            # On Balance Volume (OBV)
            if len(df) >= 2:
                price_change = df['close'].diff()
                obv = np.where(price_change > 0, df['volume'], 
                              np.where(price_change < 0, -df['volume'], 0))
                df['obv'] = pd.Series(obv, index=df.index).cumsum()
            
            # Volume-Price Trend (VPT)
            if len(df) >= 2:
                price_change_pct = df['close'].pct_change()
                df['vpt'] = (price_change_pct * df['volume']).cumsum()
            
            return df
        except Exception as e:
            logger.error(f"Error calculating volume indicators: {e}")
            return df
    
    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""
        try:
            # Average True Range (ATR)
            if len(df) >= 14:
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                
                true_range = np.maximum(high_low, np.maximum(high_close, low_close))
                df['atr'] = pd.Series(true_range, index=df.index).rolling(window=14).mean()
            
            # Historical Volatility (20-day)
            if len(df) >= 20:
                returns = df['close'].pct_change()
                df['volatility_20'] = returns.rolling(window=20).std() * np.sqrt(252) * 100  # Annualized
            
            return df
        except Exception as e:
            logger.error(f"Error calculating volatility indicators: {e}")
            return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        try:
            # Rate of Change (ROC)
            for period in [10, 20]:
                if len(df) >= period:
                    df[f'roc_{period}'] = df['close'].pct_change(periods=period) * 100
            
            # Stochastic Oscillator
            if len(df) >= 14:
                lowest_low = df['low'].rolling(window=14).min()
                highest_high = df['high'].rolling(window=14).max()
                df['stoch_k'] = ((df['close'] - lowest_low) / (highest_high - lowest_low)) * 100
                df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            # Williams %R
            if len(df) >= 14:
                highest_high = df['high'].rolling(window=14).max()
                lowest_low = df['low'].rolling(window=14).min()
                df['williams_r'] = ((highest_high - df['close']) / (highest_high - lowest_low)) * -100
            
            return df
        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {e}")
            return df
    
    def _add_market_regime_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market regime detection indicators"""
        try:
            # Trend detection using linear regression slope
            if len(df) >= 20:
                def calculate_slope(series, window=20):
                    slopes = []
                    for i in range(len(series)):
                        if i < window - 1:
                            slopes.append(np.nan)
                        else:
                            y = series.iloc[i-window+1:i+1].values
                            x = np.arange(len(y))
                            slope = np.polyfit(x, y, 1)[0]
                            slopes.append(slope)
                    return pd.Series(slopes, index=series.index)
                
                df['trend_slope_20'] = calculate_slope(df['close'], 20)
            
            # Volatility regime (using rolling standard deviation)
            if len(df) >= 20:
                returns = df['close'].pct_change()
                df['volatility_regime'] = returns.rolling(window=20).std()
            
            # Market regime classification
            if 'trend_slope_20' in df.columns and 'volatility_regime' in df.columns:
                # Define thresholds (these can be optimized)
                trend_threshold = df['trend_slope_20'].quantile(0.3)  # Bottom 30% = ranging
                vol_threshold = df['volatility_regime'].quantile(0.7)  # Top 30% = volatile
                
                conditions = [
                    (df['trend_slope_20'].abs() <= abs(trend_threshold)) & (df['volatility_regime'] <= vol_threshold),  # Ranging
                    (df['trend_slope_20'].abs() > abs(trend_threshold)) & (df['volatility_regime'] <= vol_threshold),   # Trending
                    df['volatility_regime'] > vol_threshold  # Volatile
                ]
                
                choices = [0, 1, 2]  # 0=Ranging, 1=Trending, 2=Volatile
                df['market_regime'] = np.select(conditions, choices, default=0).astype(np.int8)
            
            return df
        except Exception as e:
            logger.error(f"Error calculating market regime indicators: {e}")
            return df
    
    def get_indicator_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary of available indicators in DataFrame"""
        indicator_columns = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        summary = {
            "total_indicators": len(indicator_columns),
            "indicator_groups": {
                "moving_averages": [col for col in indicator_columns if 'sma_' in col or 'ema_' in col or 'vwma_' in col],
                "rsi_indicators": [col for col in indicator_columns if 'rsi' in col],
                "macd_indicators": [col for col in indicator_columns if 'macd' in col],
                "bollinger_bands": [col for col in indicator_columns if 'bb_' in col],
                "volume_indicators": [col for col in indicator_columns if 'volume_' in col or col in ['obv', 'vpt']],
                "volatility_indicators": [col for col in indicator_columns if col in ['atr', 'volatility_20']],
                "momentum_indicators": [col for col in indicator_columns if col in ['roc_10', 'roc_20', 'stoch_k', 'stoch_d', 'williams_r']],
                "regime_indicators": [col for col in indicator_columns if 'regime' in col or 'trend_slope' in col]
            },
            "data_range": {
                "start": df.index.min().isoformat() if not df.empty else None,
                "end": df.index.max().isoformat() if not df.empty else None,
                "rows": len(df)
            }
        }
        
        return summary
    
    def clear_cache(self):
        """Clear the indicator cache"""
        self._indicator_cache.clear()
        logger.info("Indicator cache cleared")

# Convenience function for quick indicator calculation
def calculate_indicators(df: pd.DataFrame, product_id: str = "unknown") -> pd.DataFrame:
    """
    Quick function to calculate all indicators for a DataFrame
    
    Args:
        df: DataFrame with OHLCV data
        product_id: Product identifier
        
    Returns:
        DataFrame with indicators added
    """
    factory = IndicatorFactory()
    return factory.calculate_all_indicators(df, product_id)