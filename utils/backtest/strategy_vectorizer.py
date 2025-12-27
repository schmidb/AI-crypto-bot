"""
Strategy Vectorizer - Convert Live Strategies to Vectorized Backtest Versions

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
    Adapter that converts live strategies to vectorized versions for backtesting
    
    Key Features:
    - Zero impact on live bot operation
    - Maintains exact signal compatibility
    - Efficient batch processing for backtesting
    - Supports all existing strategies
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
        
        logger.info("Vectorized Strategy Adapter initialized")
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
                    # Prepare market data for this timestamp
                    market_data = self._prepare_market_data(row, product_id, i, data_with_indicators)
                    
                    # Prepare technical indicators for this timestamp
                    technical_indicators = self._prepare_technical_indicators(row)
                    
                    # Get signal from live strategy
                    signal = strategy.analyze(market_data, technical_indicators, {})
                    
                    # Convert to vectorized format
                    signals_df.loc[timestamp, 'buy'] = (signal.action == 'BUY')
                    signals_df.loc[timestamp, 'sell'] = (signal.action == 'SELL')
                    signals_df.loc[timestamp, 'confidence'] = signal.confidence
                    signals_df.loc[timestamp, 'reasoning'] = signal.reasoning
                    signals_df.loc[timestamp, 'position_size_multiplier'] = signal.position_size_multiplier
                    
                except Exception as e:
                    logger.warning(f"Error processing row {i} for {strategy_name}: {e}")
                    continue
            
            # Add metadata
            signals_df['strategy'] = strategy_name
            signals_df['product_id'] = product_id
            
            logger.info(f"Generated {signals_df['buy'].sum()} buy signals and {signals_df['sell'].sum()} sell signals")
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
                    
                    # Store results
                    signals_df.loc[timestamp, 'buy'] = (signal.action == 'BUY')
                    signals_df.loc[timestamp, 'sell'] = (signal.action == 'SELL')
                    signals_df.loc[timestamp, 'confidence'] = signal.confidence
                    signals_df.loc[timestamp, 'reasoning'] = signal.reasoning
                    signals_df.loc[timestamp, 'position_size_multiplier'] = signal.position_size_multiplier
                    signals_df.loc[timestamp, 'market_regime'] = market_regime
                    signals_df.loc[timestamp, 'primary_strategy'] = primary_strategy
                    
                except Exception as e:
                    logger.warning(f"Error processing adaptive strategy row {i}: {e}")
                    continue
            
            # Add metadata
            signals_df['strategy'] = 'adaptive'
            signals_df['product_id'] = product_id
            
            logger.info(f"Adaptive strategy: {signals_df['buy'].sum()} buys, {signals_df['sell'].sum()} sells")
            logger.info(f"Market regimes: {signals_df['market_regime'].value_counts().to_dict()}")
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Error vectorizing adaptive strategy: {e}")
            return self._empty_signals_dataframe(data_with_indicators.index)
    
    def _prepare_market_data(self, row: pd.Series, product_id: str, 
                           index: int, full_data: pd.DataFrame) -> Dict:
        """Prepare market data dictionary from DataFrame row"""
        
        # Calculate price changes if we have enough history
        price_changes = {}
        current_price = row.get('close', 0)
        
        if index >= 24:  # 24 hours of hourly data
            price_1h_ago = full_data.iloc[index-1]['close'] if index >= 1 else current_price
            price_24h_ago = full_data.iloc[index-24]['close']
            
            price_changes['1h'] = ((current_price - price_1h_ago) / price_1h_ago * 100) if price_1h_ago > 0 else 0
            price_changes['24h'] = ((current_price - price_24h_ago) / price_24h_ago * 100) if price_24h_ago > 0 else 0
        
        if index >= 120:  # 5 days of hourly data
            price_5d_ago = full_data.iloc[index-120]['close']
            price_changes['5d'] = ((current_price - price_5d_ago) / price_5d_ago * 100) if price_5d_ago > 0 else 0
        
        # Volume data
        current_volume = row.get('volume', 0)
        avg_volume = full_data['volume'].rolling(window=min(24, index+1)).mean().iloc[index] if index >= 0 else current_volume
        
        volume_data = {
            'current': current_volume,
            'average': avg_volume
        }
        
        return {
            'product_id': product_id,
            'price': current_price,
            'price_changes': price_changes,
            'volume': volume_data
        }
    
    def _prepare_technical_indicators(self, row: pd.Series) -> Dict:
        """Prepare technical indicators dictionary from DataFrame row"""
        
        indicators = {}
        
        # Basic OHLCV
        indicators['current_price'] = row.get('close', 0)
        
        # RSI
        if 'rsi_14' in row:
            indicators['rsi'] = row['rsi_14']
        
        # MACD
        if all(col in row for col in ['macd', 'macd_signal', 'macd_histogram']):
            indicators['macd'] = row['macd']
            indicators['macd_signal'] = row['macd_signal']
            indicators['macd_histogram'] = row['macd_histogram']
        
        # Bollinger Bands
        if all(col in row for col in ['bb_upper_20', 'bb_lower_20', 'bb_middle_20']):
            indicators['bb_upper'] = row['bb_upper_20']
            indicators['bb_lower'] = row['bb_lower_20']
            indicators['bb_middle'] = row['bb_middle_20']
        
        # Moving Averages
        if 'sma_20' in row:
            indicators['sma_20'] = row['sma_20']
        if 'sma_50' in row:
            indicators['sma_50'] = row['sma_50']
        
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