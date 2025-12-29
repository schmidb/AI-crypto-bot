#!/usr/bin/env python3
"""
Test script for the indicator factory
"""

import pandas as pd
import logging
from pathlib import Path
from utils.performance.indicator_factory import IndicatorFactory, calculate_indicators

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_indicator_factory():
    """Test the indicator factory with real historical data"""
    
    try:
        # Load historical data
        data_dir = Path("./data/historical")
        btc_file = data_dir / "BTC-USD_hourly_30d.parquet"
        eth_file = data_dir / "ETH-USD_hourly_30d.parquet"
        
        if not btc_file.exists():
            logger.error(f"BTC data file not found: {btc_file}")
            logger.info("Please run sync_historical_data.py first")
            return False
        
        # Load BTC data
        logger.info("Loading BTC historical data...")
        btc_df = pd.read_parquet(btc_file)
        logger.info(f"Loaded {len(btc_df)} rows of BTC data")
        logger.info(f"Date range: {btc_df.index.min()} to {btc_df.index.max()}")
        
        # Test indicator factory
        logger.info("Testing indicator factory...")
        factory = IndicatorFactory()
        
        # Calculate indicators
        btc_with_indicators = factory.calculate_all_indicators(btc_df, "BTC-USD")
        
        # Get summary
        summary = factory.get_indicator_summary(btc_with_indicators)
        
        logger.info(f"Indicator calculation complete!")
        logger.info(f"Total indicators: {summary['total_indicators']}")
        
        # Display indicator groups
        for group, indicators in summary['indicator_groups'].items():
            if indicators:
                logger.info(f"{group}: {len(indicators)} indicators")
                logger.info(f"  {', '.join(indicators[:5])}{'...' if len(indicators) > 5 else ''}")
        
        # Test some specific indicators
        logger.info("\nSample indicator values (latest):")
        
        # Moving averages
        if 'sma_20' in btc_with_indicators.columns:
            latest_price = btc_with_indicators['close'].iloc[-1]
            latest_sma20 = btc_with_indicators['sma_20'].iloc[-1]
            logger.info(f"  Current Price: ${latest_price:.2f}")
            logger.info(f"  SMA 20: ${latest_sma20:.2f}")
            logger.info(f"  Price vs SMA20: {((latest_price - latest_sma20) / latest_sma20 * 100):+.2f}%")
        
        # RSI
        if 'rsi_14' in btc_with_indicators.columns:
            latest_rsi = btc_with_indicators['rsi_14'].iloc[-1]
            logger.info(f"  RSI 14: {latest_rsi:.2f}")
            
            if latest_rsi > 70:
                logger.info("    → Overbought territory")
            elif latest_rsi < 30:
                logger.info("    → Oversold territory")
            else:
                logger.info("    → Neutral territory")
        
        # MACD
        if 'macd' in btc_with_indicators.columns:
            latest_macd = btc_with_indicators['macd'].iloc[-1]
            latest_signal = btc_with_indicators['macd_signal'].iloc[-1]
            logger.info(f"  MACD: {latest_macd:.2f}")
            logger.info(f"  MACD Signal: {latest_signal:.2f}")
            
            if latest_macd > latest_signal:
                logger.info("    → Bullish crossover")
            else:
                logger.info("    → Bearish crossover")
        
        # Bollinger Bands
        if 'bb_position_20' in btc_with_indicators.columns:
            bb_position = btc_with_indicators['bb_position_20'].iloc[-1]
            logger.info(f"  Bollinger Band Position: {bb_position:.3f}")
            
            if bb_position > 0.8:
                logger.info("    → Near upper band (potential resistance)")
            elif bb_position < 0.2:
                logger.info("    → Near lower band (potential support)")
            else:
                logger.info("    → Middle range")
        
        # Market regime
        if 'market_regime' in btc_with_indicators.columns:
            regime = btc_with_indicators['market_regime'].iloc[-1]
            regime_names = {0: "Ranging", 1: "Trending", 2: "Volatile"}
            logger.info(f"  Market Regime: {regime_names.get(regime, 'Unknown')}")
        
        # Test with ETH data if available
        if eth_file.exists():
            logger.info("\nTesting with ETH data...")
            eth_df = pd.read_parquet(eth_file)
            eth_with_indicators = calculate_indicators(eth_df, "ETH-USD")  # Test convenience function
            
            logger.info(f"ETH indicators calculated: {len(eth_with_indicators.columns) - 5} indicators")
        
        # Performance test
        logger.info("\nPerformance test...")
        import time
        
        start_time = time.time()
        for i in range(5):
            _ = factory.calculate_all_indicators(btc_df, f"BTC-USD-test-{i}")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 5
        logger.info(f"Average calculation time: {avg_time:.3f} seconds")
        logger.info(f"Throughput: {len(btc_df) / avg_time:.0f} rows/second")
        
        logger.info("\nIndicator factory test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in indicator factory test: {e}")
        return False

if __name__ == "__main__":
    success = test_indicator_factory()
    exit(0 if success else 1)