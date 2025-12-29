"""
Enhanced Strategy Vectorizer - With Market Filters and Optimized Thresholds

IMPROVEMENTS:
1. Added "avoid_declining_periods" market filter
2. Lowered confidence thresholds to 30% for all strategies
3. Enhanced market regime detection
4. Better signal quality filtering
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Callable
import logging
from pathlib import Path

# Import existing strategies (read-only, no modification)
import sys
sys.path.append('.')
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum import MomentumStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.adaptive_strategy_manager import AdaptiveStrategyManager

logger = logging.getLogger(__name__)

class EnhancedVectorizedStrategyAdapter:
    """
    Enhanced Adapter with Market Filters and Optimized Parameters
    
    Key Improvements:
    - Market regime filtering to avoid bad trading conditions
    - Lowered confidence thresholds (30% instead of 50%+)
    - Avoid declining periods filter
    - Better signal quality control
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the enhanced vectorized strategy adapter"""
        self.config = config or {}
        
        # OPTIMIZATION 1: Lower confidence thresholds to 30%
        self.optimized_thresholds = {
            'mean_reversion': {'buy': 30, 'sell': 30},
            'momentum': {'buy': 30, 'sell': 30},
            'trend_following': {'buy': 30, 'sell': 30},
            'adaptive': {'buy': 30, 'sell': 30}
        }
        
        # Initialize live strategies (read-only)
        self.live_strategies = {
            'mean_reversion': MeanReversionStrategy(self.config),
            'momentum': MomentumStrategy(self.config),
            'trend_following': TrendFollowingStrategy(self.config)
        }
        
        # Cache for vectorized results
        self._signal_cache = {}
        
        logger.info("Enhanced Vectorized Strategy Adapter initialized")
        logger.info(f"Available strategies: {list(self.live_strategies.keys())}")
        logger.info(f"Optimized thresholds: {self.optimized_thresholds}")
    
    def _calculate_market_filter(self, data: pd.DataFrame) -> pd.Series:
        """
        OPTIMIZATION 2: Calculate market filter to avoid declining periods
        
        Returns boolean Series where True = good trading conditions
        """
        try:
            # Calculate 24-hour rolling price change
            price_changes = data['close'].pct_change()
            rolling_24h_change = price_changes.rolling(24, min_periods=12).mean()
            
            # Avoid periods with declining trends (24h average change < -0.1%)
            avoid_declining = rolling_24h_change > -0.001
            
            # Additional filters
            volatility = price_changes.rolling(24, min_periods=12).std()
            high_vol_threshold = volatility.quantile(0.8)  # Top 20% volatility
            avoid_extreme_volatility = volatility < high_vol_threshold
            
            # Combine filters
            market_filter = avoid_declining & avoid_extreme_volatility
            
            # Fill NaN values with False (conservative approach)
            market_filter = market_filter.fillna(False)
            
            logger.info(f"Market filter: {market_filter.sum()}/{len(market_filter)} periods allowed ({market_filter.mean()*100:.1f}%)")
            
            return market_filter
            
        except Exception as e:
            logger.error(f"Error calculating market filter: {e}")
            # Return all True if filter calculation fails
            return pd.Series(True, index=data.index)
    
    def _apply_confidence_threshold(self, signals_df: pd.DataFrame, strategy_name: str) -> pd.DataFrame:
        """
        Apply optimized confidence thresholds to filter signals
        """
        try:
            thresholds = self.optimized_thresholds.get(strategy_name, {'buy': 50, 'sell': 50})
            
            # Filter buy signals by confidence threshold
            buy_mask = (signals_df['buy'] == True) & (signals_df['confidence'] >= thresholds['buy'])
            signals_df.loc[~buy_mask, 'buy'] = False
            
            # Filter sell signals by confidence threshold
            sell_mask = (signals_df['sell'] == True) & (signals_df['confidence'] >= thresholds['sell'])
            signals_df.loc[~sell_mask, 'sell'] = False
            
            # Update reasoning for filtered signals
            filtered_buy = (signals_df['buy'] == False) & (signals_df['confidence'] < thresholds['buy'])
            filtered_sell = (signals_df['sell'] == False) & (signals_df['confidence'] < thresholds['sell'])
            
            signals_df.loc[filtered_buy, 'reasoning'] += f" [Filtered: confidence {signals_df.loc[filtered_buy, 'confidence']:.1f}% < {thresholds['buy']}%]"
            signals_df.loc[filtered_sell, 'reasoning'] += f" [Filtered: confidence {signals_df.loc[filtered_sell, 'confidence']:.1f}% < {thresholds['sell']}%]"
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Error applying confidence threshold: {e}")
            return signals_df
    
    def vectorize_strategy(self, strategy_name: str, data_with_indicators: pd.DataFrame, 
                          product_id: str = "BTC-USD", apply_market_filter: bool = True) -> pd.DataFrame:
        """
        Convert a live strategy to vectorized signals with enhancements
        
        Args:
            strategy_name: Name of strategy to vectorize
            data_with_indicators: DataFrame with OHLCV data and indicators
            product_id: Trading pair identifier
            apply_market_filter: Whether to apply market regime filtering
            
        Returns:
            DataFrame with enhanced buy/sell signals
        """
        try:
            if strategy_name not in self.live_strategies:
                logger.error(f"Strategy '{strategy_name}' not found")
                return self._empty_signals_dataframe(data_with_indicators.index)
            
            logger.info(f"Vectorizing {strategy_name} strategy for {len(data_with_indicators)} rows")
            
            strategy = self.live_strategies[strategy_name]
            
            # CRITICAL FIX: Remove duplicate columns
            data_clean = data_with_indicators.loc[:, ~data_with_indicators.columns.duplicated()]
            logger.info(f"Cleaned data: {len(data_clean.columns)} columns (removed duplicates)")
            
            # Calculate market filter
            market_filter = self._calculate_market_filter(data_clean) if apply_market_filter else pd.Series(True, index=data_clean.index)
            
            # Create signals DataFrame
            signals_df = pd.DataFrame(index=data_clean.index)
            signals_df['buy'] = False
            signals_df['sell'] = False
            signals_df['confidence'] = 50.0
            signals_df['reasoning'] = ""
            signals_df['position_size_multiplier'] = 1.0
            signals_df['market_filter_passed'] = market_filter
            
            # Process each row
            for i, (timestamp, row) in enumerate(data_clean.iterrows()):
                try:
                    # Prepare market data for this timestamp
                    market_data = self._prepare_market_data(row, product_id, i, data_clean)
                    
                    # Prepare technical indicators for this timestamp
                    technical_indicators = self._prepare_technical_indicators(row)
                    
                    # Get signal from live strategy
                    signal = strategy.analyze(market_data, technical_indicators, {})
                    
                    # Store raw signal first
                    signals_df.loc[timestamp, 'buy'] = (signal.action == 'BUY')
                    signals_df.loc[timestamp, 'sell'] = (signal.action == 'SELL')
                    signals_df.loc[timestamp, 'confidence'] = float(signal.confidence)
                    signals_df.loc[timestamp, 'reasoning'] = str(signal.reasoning)
                    signals_df.loc[timestamp, 'position_size_multiplier'] = float(signal.position_size_multiplier)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {i} for {strategy_name}: {e}")
                    # Set safe default values for this row
                    signals_df.loc[timestamp, 'buy'] = False
                    signals_df.loc[timestamp, 'sell'] = False
                    signals_df.loc[timestamp, 'confidence'] = 50.0
                    signals_df.loc[timestamp, 'reasoning'] = f"Error: {str(e)}"
                    signals_df.loc[timestamp, 'position_size_multiplier'] = 1.0
                    continue
            
            # Apply confidence thresholds
            signals_df = self._apply_confidence_threshold(signals_df, strategy_name)
            
            # Apply market filter
            if apply_market_filter:
                # Filter out signals during bad market conditions
                bad_market_mask = ~market_filter
                signals_df.loc[bad_market_mask, 'buy'] = False
                signals_df.loc[bad_market_mask, 'sell'] = False
                signals_df.loc[bad_market_mask, 'reasoning'] += " [Filtered: bad market conditions]"
            
            # Add metadata
            signals_df['strategy'] = strategy_name
            signals_df['product_id'] = product_id
            
            buy_count = int(signals_df['buy'].sum())
            sell_count = int(signals_df['sell'].sum())
            total_periods = len(signals_df)
            filtered_periods = (~market_filter).sum() if apply_market_filter else 0
            
            logger.info(f"Generated {buy_count} buy signals and {sell_count} sell signals")
            logger.info(f"Market filter removed {filtered_periods}/{total_periods} periods ({filtered_periods/total_periods*100:.1f}%)")
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Error vectorizing {strategy_name}: {e}")
            return self._empty_signals_dataframe(data_with_indicators.index)
    
    def vectorize_adaptive_strategy(self, data_with_indicators: pd.DataFrame, 
                                  product_id: str = "BTC-USD", apply_market_filter: bool = True) -> pd.DataFrame:
        """
        Vectorize the adaptive strategy manager with enhancements
        """
        try:
            logger.info(f"Vectorizing enhanced adaptive strategy for {len(data_with_indicators)} rows")
            
            # Initialize adaptive strategy manager (read-only)
            adaptive_manager = AdaptiveStrategyManager(self.config)
            
            # CRITICAL FIX: Remove duplicate columns
            data_clean = data_with_indicators.loc[:, ~data_with_indicators.columns.duplicated()]
            logger.info(f"Cleaned data: {len(data_clean.columns)} columns (removed duplicates)")
            
            # Calculate market filter
            market_filter = self._calculate_market_filter(data_clean) if apply_market_filter else pd.Series(True, index=data_clean.index)
            
            # Create signals DataFrame
            signals_df = pd.DataFrame(index=data_clean.index)
            signals_df['buy'] = False
            signals_df['sell'] = False
            signals_df['confidence'] = 50.0
            signals_df['reasoning'] = ""
            signals_df['position_size_multiplier'] = 1.0
            signals_df['market_regime'] = "ranging"
            signals_df['primary_strategy'] = ""
            signals_df['market_filter_passed'] = market_filter
            
            # Process each row
            for i, (timestamp, row) in enumerate(data_clean.iterrows()):
                try:
                    # Prepare data for adaptive manager
                    market_data = self._prepare_market_data(row, product_id, i, data_clean)
                    technical_indicators = self._prepare_technical_indicators(row)
                    
                    # Get combined signal from adaptive manager
                    signal = adaptive_manager.get_combined_signal(market_data, technical_indicators, {})
                    
                    # Extract market regime and primary strategy info
                    market_regime = getattr(adaptive_manager, 'current_market_regime', 'ranging')
                    primary_strategy = self._extract_primary_strategy(signal.reasoning)
                    
                    # Store results with safe conversion
                    signals_df.loc[timestamp, 'buy'] = (signal.action == 'BUY')
                    signals_df.loc[timestamp, 'sell'] = (signal.action == 'SELL')
                    signals_df.loc[timestamp, 'confidence'] = float(signal.confidence)
                    signals_df.loc[timestamp, 'reasoning'] = str(signal.reasoning)
                    signals_df.loc[timestamp, 'position_size_multiplier'] = float(signal.position_size_multiplier)
                    signals_df.loc[timestamp, 'market_regime'] = str(market_regime)
                    signals_df.loc[timestamp, 'primary_strategy'] = str(primary_strategy)
                    
                except Exception as e:
                    logger.warning(f"Error processing adaptive strategy row {i}: {e}")
                    # Set safe defaults
                    signals_df.loc[timestamp, 'buy'] = False
                    signals_df.loc[timestamp, 'sell'] = False
                    signals_df.loc[timestamp, 'confidence'] = 50.0
                    signals_df.loc[timestamp, 'reasoning'] = f"Error: {str(e)}"
                    signals_df.loc[timestamp, 'position_size_multiplier'] = 1.0
                    signals_df.loc[timestamp, 'market_regime'] = "ranging"
                    signals_df.loc[timestamp, 'primary_strategy'] = "unknown"
                    continue
            
            # Apply confidence thresholds for adaptive strategy
            signals_df = self._apply_confidence_threshold(signals_df, 'adaptive')
            
            # Apply market filter
            if apply_market_filter:
                bad_market_mask = ~market_filter
                signals_df.loc[bad_market_mask, 'buy'] = False
                signals_df.loc[bad_market_mask, 'sell'] = False
                signals_df.loc[bad_market_mask, 'reasoning'] += " [Filtered: bad market conditions]"
            
            # Add metadata
            signals_df['strategy'] = 'adaptive'
            signals_df['product_id'] = product_id
            
            # Count market regimes
            regime_counts = signals_df['market_regime'].value_counts().to_dict()
            buy_count = int(signals_df['buy'].sum())
            sell_count = int(signals_df['sell'].sum())
            
            logger.info(f"Adaptive strategy: {buy_count} buys, {sell_count} sells")
            logger.info(f"Market regimes: {regime_counts}")
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Error vectorizing adaptive strategy: {e}")
            return self._empty_signals_dataframe(data_with_indicators.index)
    
    def _prepare_market_data(self, row: pd.Series, product_id: str, index: int, full_data: pd.DataFrame) -> Dict:
        """Prepare market data dictionary from row data"""
        try:
            # Calculate price changes for context
            current_price = float(row['close'])
            
            # Get previous prices for change calculations
            if index > 0:
                prev_price = float(full_data.iloc[index-1]['close'])
                change_1h = ((current_price - prev_price) / prev_price) * 100
            else:
                change_1h = 0.0
            
            # Calculate longer-term changes if enough data
            change_24h = 0.0
            change_5d = 0.0
            
            if index >= 24:
                price_24h_ago = float(full_data.iloc[index-24]['close'])
                change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
            
            if index >= 120:  # 5 days * 24 hours
                price_5d_ago = float(full_data.iloc[index-120]['close'])
                change_5d = ((current_price - price_5d_ago) / price_5d_ago) * 100
            
            return {
                'product_id': product_id,
                'price': current_price,
                'volume': float(row['volume']),
                'timestamp': row.name.isoformat() if hasattr(row.name, 'isoformat') else str(row.name),
                'price_changes': {
                    '1h': change_1h,
                    '24h': change_24h,
                    '5d': change_5d
                }
            }
        except Exception as e:
            logger.warning(f"Error preparing market data: {e}")
            return {
                'product_id': product_id,
                'price': 50000.0,  # Safe default
                'volume': 1000000.0,
                'timestamp': str(row.name),
                'price_changes': {'1h': 0.0, '24h': 0.0, '5d': 0.0}
            }
    
    def _prepare_technical_indicators(self, row: pd.Series) -> Dict:
        """Prepare technical indicators dictionary from row data"""
        try:
            indicators = {}
            
            # Map column names to expected indicator names
            column_mapping = {
                'rsi_14': 'rsi',
                'bb_upper_20': 'bb_upper',
                'bb_lower_20': 'bb_lower', 
                'bb_middle_20': 'bb_middle',
                'macd': 'macd',
                'macd_signal': 'macd_signal',
                'sma_20': 'sma_20',
                'sma_50': 'sma_50',
                'ema_12': 'ema_12',
                'ema_26': 'ema_26',
                'volume_sma_20': 'volume_sma',
                'atr': 'atr',
                'stoch_k': 'stoch_k',
                'stoch_d': 'stoch_d'
            }
            
            # Extract available indicators
            for col_name, indicator_name in column_mapping.items():
                if col_name in row.index:
                    try:
                        value = float(row[col_name])
                        if not np.isnan(value):
                            indicators[indicator_name] = value
                    except (ValueError, TypeError):
                        continue
            
            # Add any other numeric columns as indicators
            for col in row.index:
                if col not in ['open', 'high', 'low', 'close', 'volume'] and col not in column_mapping:
                    try:
                        value = float(row[col])
                        if not np.isnan(value):
                            indicators[col] = value
                    except (ValueError, TypeError):
                        continue
            
            return indicators
            
        except Exception as e:
            logger.warning(f"Error preparing technical indicators: {e}")
            return {}
    
    def _extract_primary_strategy(self, reasoning: str) -> str:
        """Extract primary strategy name from reasoning text"""
        try:
            reasoning_lower = reasoning.lower()
            if 'mean_reversion' in reasoning_lower or 'mean reversion' in reasoning_lower:
                return 'mean_reversion'
            elif 'momentum' in reasoning_lower:
                return 'momentum'
            elif 'trend_following' in reasoning_lower or 'trend following' in reasoning_lower:
                return 'trend_following'
            elif 'llm' in reasoning_lower:
                return 'llm_strategy'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def _empty_signals_dataframe(self, index: pd.Index) -> pd.DataFrame:
        """Create empty signals DataFrame with proper structure"""
        signals_df = pd.DataFrame(index=index)
        signals_df['buy'] = False
        signals_df['sell'] = False
        signals_df['confidence'] = 50.0
        signals_df['reasoning'] = "No signals generated"
        signals_df['position_size_multiplier'] = 1.0
        signals_df['strategy'] = 'unknown'
        signals_df['product_id'] = 'unknown'
        signals_df['market_filter_passed'] = True
        return signals_df