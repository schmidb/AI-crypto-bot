"""
Strategy Vectorizer - Convert Live Strategies to Vectorized Backtest Versions

FIXED VERSION - Resolves pandas boolean logic issues

This module creates vectorized versions of existing strategies for backtesting
without affecting the live bot operation. It maintains signal compatibility
while enabling efficient batch processing of historical data.
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

class VectorizedStrategyAdapter:
    """
    FIXED Adapter that converts live strategies to vectorized versions for backtesting
    
    Key Features:
    - Zero impact on live bot operation
    - Maintains exact signal compatibility
    - Efficient batch processing for backtesting
    - Supports all existing strategies
    - FIXED: Proper pandas Series to scalar conversion
    - FIXED: Safe handling of NaN values
    - FIXED: Robust error handling for boolean logic
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the vectorized strategy adapter"""
        self.config = config or {}
        
        # Initialize live strategies (read-only)
        self.live_strategies = {
            'mean_reversion': MeanReversionStrategy(self.config),
            'momentum': MomentumStrategy(self.config),
            'trend_following': TrendFollowingStrategy(self.config)
        }
        
        # Cache for vectorized results
        self._signal_cache = {}
        
        logger.info("FIXED Vectorized Strategy Adapter initialized")
        logger.info(f"Available strategies: {list(self.live_strategies.keys())}")
    
    def vectorize_strategy(self, strategy_name: str, data_with_indicators: pd.DataFrame, 
                          product_id: str = "BTC-USD") -> pd.DataFrame:
        """
        Convert a live strategy to vectorized signals for entire dataset
        
        Args:
            strategy_name: Name of strategy to vectorize
            data_with_indicators: DataFrame with OHLCV data and indicators
            product_id: Trading pair identifier
            
        Returns:
            DataFrame with buy/sell signals and metadata
        """
        try:
            if strategy_name not in self.live_strategies:
                logger.error(f"Strategy '{strategy_name}' not found")
                return self._empty_signals_dataframe(data_with_indicators.index)
            
            logger.info(f"Vectorizing {strategy_name} strategy for {len(data_with_indicators)} rows")
            
            strategy = self.live_strategies[strategy_name]
            
            # Create signals DataFrame
            signals_df = pd.DataFrame(index=data_with_indicators.index)
            signals_df['buy'] = False
            signals_df['sell'] = False
            signals_df['confidence'] = 50.0
            signals_df['reasoning'] = ""
            signals_df['position_size_multiplier'] = 1.0
            
            # Process each row (vectorized where possible)
            for i, (timestamp, row) in enumerate(data_with_indicators.iterrows()):
                try:
                    # FIXED: Prepare market data for this timestamp
                    market_data = self._prepare_market_data(row, product_id, i, data_with_indicators)
                    
                    # FIXED: Prepare technical indicators for this timestamp
                    technical_indicators = self._prepare_technical_indicators(row)
                    
                    # Get signal from live strategy
                    signal = strategy.analyze(market_data, technical_indicators, {})
                    
                    # Convert to vectorized format with safe conversion
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
            
            # Add metadata
            signals_df['strategy'] = strategy_name
            signals_df['product_id'] = product_id
            
            buy_count = int(signals_df['buy'].sum())
            sell_count = int(signals_df['sell'].sum())
            logger.info(f"Generated {buy_count} buy signals and {sell_count} sell signals")
            return signals_df
            
        except Exception as e:
            logger.error(f"Error vectorizing {strategy_name}: {e}")
            return self._empty_signals_dataframe(data_with_indicators.index)
    
    def vectorize_adaptive_strategy(self, data_with_indicators: pd.DataFrame, 
                                  product_id: str = "BTC-USD") -> pd.DataFrame:
        """
        Vectorize the adaptive strategy manager (hierarchical decision making)
        
        Args:
            data_with_indicators: DataFrame with OHLCV data and indicators
            product_id: Trading pair identifier
            
        Returns:
            DataFrame with adaptive strategy signals
        """
        try:
            logger.info(f"Vectorizing adaptive strategy for {len(data_with_indicators)} rows")
            
            # Initialize adaptive strategy manager (read-only)
            adaptive_manager = AdaptiveStrategyManager(self.config)
            
            # Create signals DataFrame
            signals_df = pd.DataFrame(index=data_with_indicators.index)
            signals_df['buy'] = False
            signals_df['sell'] = False
            signals_df['confidence'] = 50.0
            signals_df['reasoning'] = ""
            signals_df['position_size_multiplier'] = 1.0
            signals_df['market_regime'] = "ranging"
            signals_df['primary_strategy'] = ""
            
            # Process each row
            for i, (timestamp, row) in enumerate(data_with_indicators.iterrows()):
                try:
                    # Prepare data for adaptive manager
                    market_data = self._prepare_market_data(row, product_id, i, data_with_indicators)
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
            
            # Add metadata
            signals_df['strategy'] = 'adaptive'
            signals_df['product_id'] = product_id
            
            buy_count = int(signals_df['buy'].sum())
            sell_count = int(signals_df['sell'].sum())
            logger.info(f"Adaptive strategy: {buy_count} buys, {sell_count} sells")
            logger.info(f"Market regimes: {signals_df['market_regime'].value_counts().to_dict()}")
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Error vectorizing adaptive strategy: {e}")
            return self._empty_signals_dataframe(data_with_indicators.index)
    
    def _prepare_market_data(self, row: pd.Series, product_id: str, 
                           index: int, full_data: pd.DataFrame) -> Dict:
        """FIXED: Prepare market data dictionary from DataFrame row"""
        
        # FIXED: Safe conversion to scalar values
        def safe_float(value, default=0.0):
            """Safely convert pandas value to float"""
            try:
                if pd.isna(value):
                    return default
                if hasattr(value, 'item'):  # pandas scalar
                    return float(value.item())
                return float(value)
            except (ValueError, TypeError, AttributeError):
                return default
        
        # Calculate price changes if we have enough history
        price_changes = {}
        current_price = safe_float(row.get('close', 0))
        
        if current_price > 0:  # Only calculate if we have valid price
            if index >= 24:  # 24 hours of hourly data
                price_1h_ago = safe_float(full_data.iloc[index-1]['close'], current_price)
                price_24h_ago = safe_float(full_data.iloc[index-24]['close'], current_price)
                
                if price_1h_ago > 0:
                    price_changes['1h'] = ((current_price - price_1h_ago) / price_1h_ago * 100)
                if price_24h_ago > 0:
                    price_changes['24h'] = ((current_price - price_24h_ago) / price_24h_ago * 100)
            
            if index >= 120:  # 5 days of hourly data
                price_5d_ago = safe_float(full_data.iloc[index-120]['close'], current_price)
                if price_5d_ago > 0:
                    price_changes['5d'] = ((current_price - price_5d_ago) / price_5d_ago * 100)
        
        # Volume data with safe conversion
        current_volume = safe_float(row.get('volume', 0))
        
        # FIXED: Safe rolling average calculation
        try:
            if index >= 24:
                avg_volume = safe_float(full_data['volume'].iloc[max(0, index-24):index+1].mean(), current_volume)
            else:
                avg_volume = current_volume
        except Exception:
            avg_volume = current_volume
        
        volume_data = {
            'current': current_volume,
            'average': max(avg_volume, 1.0)  # Avoid division by zero
        }
        
        return {
            'product_id': product_id,
            'price': current_price,
            'price_changes': price_changes,
            'volume': volume_data
        }
    
    def _prepare_technical_indicators(self, row: pd.Series) -> Dict:
        """FIXED: Prepare technical indicators dictionary from DataFrame row"""
        
        def safe_float(value, default=0.0):
            """Safely convert pandas value to float"""
            try:
                if pd.isna(value):
                    return default
                if hasattr(value, 'item'):  # pandas scalar
                    return float(value.item())
                return float(value)
            except (ValueError, TypeError, AttributeError):
                return default
        
        indicators = {}
        
        # Basic OHLCV - FIXED with safe conversion
        indicators['current_price'] = safe_float(row.get('close', 0))
        
        # RSI - FIXED with safe conversion
        if 'rsi_14' in row:
            indicators['rsi'] = safe_float(row['rsi_14'], 50.0)
        
        # MACD - FIXED with safe conversion and proper dict structure
        macd_dict = {}
        if 'macd' in row:
            macd_dict['macd'] = safe_float(row['macd'], 0.0)
        if 'macd_signal' in row:
            macd_dict['signal'] = safe_float(row['macd_signal'], 0.0)
        if 'macd_histogram' in row:
            macd_dict['histogram'] = safe_float(row['macd_histogram'], 0.0)
        
        if macd_dict:  # Only add if we have at least one MACD value
            indicators['macd'] = macd_dict
        
        # Bollinger Bands - FIXED with safe conversion
        if all(col in row for col in ['bb_upper_20', 'bb_lower_20', 'bb_middle_20']):
            indicators['bb_upper'] = safe_float(row['bb_upper_20'])
            indicators['bb_lower'] = safe_float(row['bb_lower_20'])
            indicators['bb_middle'] = safe_float(row['bb_middle_20'])
        
        # Moving Averages - FIXED with safe conversion
        if 'sma_20' in row:
            indicators['sma_20'] = safe_float(row['sma_20'])
        if 'sma_50' in row:
            indicators['sma_50'] = safe_float(row['sma_50'])
        
        return indicators
    
    def _extract_primary_strategy(self, reasoning: str) -> str:
        """Extract primary strategy name from reasoning text"""
        
        strategy_keywords = {
            'mean_reversion': ['mean reversion', 'Mean reversion', 'RSI', 'Bollinger'],
            'momentum': ['momentum', 'Momentum', 'breakout'],
            'trend_following': ['trend', 'Trend', 'trending'],
            'llm_strategy': ['LLM', 'llm', 'AI analysis']
        }
        
        for strategy, keywords in strategy_keywords.items():
            if any(keyword in reasoning for keyword in keywords):
                return strategy
        
        return "unknown"
    
    def _empty_signals_dataframe(self, index: pd.Index) -> pd.DataFrame:
        """Create empty signals DataFrame with correct structure"""
        
        signals_df = pd.DataFrame(index=index)
        signals_df['buy'] = False
        signals_df['sell'] = False
        signals_df['confidence'] = 50.0
        signals_df['reasoning'] = "No signals generated"
        signals_df['position_size_multiplier'] = 1.0
        signals_df['strategy'] = "none"
        signals_df['product_id'] = "unknown"
        
        return signals_df
    
    def vectorize_all_strategies(self, data_with_indicators: pd.DataFrame, 
                               product_id: str = "BTC-USD") -> Dict[str, pd.DataFrame]:
        """
        Vectorize all available strategies
        
        Args:
            data_with_indicators: DataFrame with OHLCV data and indicators
            product_id: Trading pair identifier
            
        Returns:
            Dictionary mapping strategy names to signal DataFrames
        """
        try:
            logger.info(f"Vectorizing all strategies for {product_id}")
            
            results = {}
            
            # Vectorize individual strategies
            for strategy_name in self.live_strategies.keys():
                logger.info(f"Processing {strategy_name}...")
                results[strategy_name] = self.vectorize_strategy(
                    strategy_name, data_with_indicators, product_id
                )
            
            # Vectorize adaptive strategy
            logger.info("Processing adaptive strategy...")
            results['adaptive'] = self.vectorize_adaptive_strategy(
                data_with_indicators, product_id
            )
            
            # Summary
            total_signals = sum(len(df[df['buy'] | df['sell']]) for df in results.values())
            logger.info(f"Vectorization complete: {len(results)} strategies, {total_signals} total signals")
            
            return results
            
        except Exception as e:
            logger.error(f"Error vectorizing all strategies: {e}")
            return {}

# Convenience functions for easy integration
def vectorize_strategy_for_backtest(strategy_name: str, data_with_indicators: pd.DataFrame, 
                                  product_id: str = "BTC-USD", config: Dict = None) -> pd.DataFrame:
    """
    Convenience function to vectorize a single strategy
    
    Args:
        strategy_name: Name of strategy ('mean_reversion', 'momentum', 'trend_following', 'adaptive')
        data_with_indicators: DataFrame with OHLCV data and indicators
        product_id: Trading pair identifier
        config: Strategy configuration
        
    Returns:
        DataFrame with buy/sell signals
    """
    adapter = VectorizedStrategyAdapter(config)
    
    if strategy_name == 'adaptive':
        return adapter.vectorize_adaptive_strategy(data_with_indicators, product_id)
    else:
        return adapter.vectorize_strategy(strategy_name, data_with_indicators, product_id)

def vectorize_all_strategies_for_backtest(data_with_indicators: pd.DataFrame, 
                                        product_id: str = "BTC-USD", 
                                        config: Dict = None) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to vectorize all strategies
    
    Args:
        data_with_indicators: DataFrame with OHLCV data and indicators
        product_id: Trading pair identifier
        config: Strategy configuration
        
    Returns:
        Dictionary mapping strategy names to signal DataFrames
    """
    adapter = VectorizedStrategyAdapter(config)
    return adapter.vectorize_all_strategies(data_with_indicators, product_id)