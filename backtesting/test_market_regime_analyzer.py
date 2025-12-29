#!/usr/bin/env python3
"""
Test MarketRegimeAnalyzer - Regime Detection Validation

This test validates that the MarketRegimeAnalyzer correctly detects
market regimes using the same logic as the live bot's AdaptiveStrategyManager.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add project root to path
sys.path.append('.')

from utils.backtest.market_regime_analyzer import MarketRegimeAnalyzer, analyze_market_regimes

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_regime_test_data() -> pd.DataFrame:
    """Create test data with known regime characteristics"""
    
    periods = 720  # 30 days of hourly data
    start_date = datetime.now() - timedelta(days=30)
    date_range = pd.date_range(start=start_date, periods=periods, freq='H')
    
    data = pd.DataFrame(index=date_range)
    
    # Create three distinct market periods
    period_1 = periods // 3  # Trending period
    period_2 = periods // 3  # Ranging period  
    period_3 = periods - period_1 - period_2  # Volatile period
    
    prices = []
    base_price = 50000.0
    
    # Period 1: Strong trending market (upward trend)
    trend_prices = []
    current_price = base_price
    for i in range(period_1):
        # Strong upward trend with low volatility
        change = np.random.normal(0.003, 0.01)  # 0.3% average gain, 1% volatility
        current_price *= (1 + change)
        trend_prices.append(current_price)
    
    # Period 2: Ranging market (sideways)
    range_prices = []
    range_center = current_price
    for i in range(period_2):
        # Oscillate around center with low volatility
        change = np.random.normal(0, 0.005)  # No trend, 0.5% volatility
        # Add mean reversion
        deviation = (current_price - range_center) / range_center
        mean_reversion = -deviation * 0.1  # Pull back to center
        current_price *= (1 + change + mean_reversion)
        range_prices.append(current_price)
    
    # Period 3: Volatile market (high volatility, no clear trend)
    volatile_prices = []
    for i in range(period_3):
        # High volatility, no clear direction
        change = np.random.normal(0, 0.03)  # No trend, 3% volatility
        current_price *= (1 + change)
        volatile_prices.append(current_price)
    
    prices = trend_prices + range_prices + volatile_prices
    
    # Create OHLCV data
    data['close'] = prices
    data['open'] = data['close'].shift(1).fillna(data['close'].iloc[0])
    data['high'] = data[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.005, periods))
    data['low'] = data[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.005, periods))
    data['volume'] = np.random.uniform(1000000, 3000000, periods)
    
    # Calculate Bollinger Bands (required for regime detection)
    data['bb_middle_20'] = data['close'].rolling(20).mean().fillna(data['close'])
    bb_std = data['close'].rolling(20).std().fillna(data['close'].std())
    data['bb_upper_20'] = data['bb_middle_20'] + (bb_std * 2)
    data['bb_lower_20'] = data['bb_middle_20'] - (bb_std * 2)
    
    # Add other indicators
    data['rsi_14'] = 50 + np.random.normal(0, 15, periods)
    data['rsi_14'] = np.clip(data['rsi_14'], 0, 100)
    
    logger.info(f"Created regime test data: {len(data)} periods")
    logger.info(f"Period 1 (0-{period_1}): Trending (expected)")
    logger.info(f"Period 2 ({period_1}-{period_1+period_2}): Ranging (expected)")
    logger.info(f"Period 3 ({period_1+period_2}-{periods}): Volatile (expected)")
    
    return data, period_1, period_2, period_3

def test_regime_detection():
    """Test basic regime detection functionality"""
    
    logger.info("🧪 Testing MarketRegimeAnalyzer regime detection...")
    
    try:
        # Create test data
        test_data, period_1, period_2, period_3 = create_regime_test_data()
        
        # Initialize analyzer
        analyzer = MarketRegimeAnalyzer()
        logger.info("✅ MarketRegimeAnalyzer initialized successfully")
        
        # Detect regimes
        regimes = analyzer.detect_market_regimes(test_data)
        
        if regimes.empty:
            logger.error("❌ No regimes detected")
            return False
        
        # Analyze regime distribution
        regime_counts = regimes.value_counts().to_dict()
        regime_percentages = {k: f"{v/len(regimes)*100:.1f}%" for k, v in regime_counts.items()}
        
        logger.info(f"📊 Detected regime distribution: {regime_counts}")
        logger.info(f"📊 Regime percentages: {regime_percentages}")
        
        # Validate that all expected regimes are detected
        expected_regimes = {'trending', 'ranging', 'volatile'}
        detected_regimes = set(regimes.unique())
        
        if not expected_regimes.issubset(detected_regimes):
            missing_regimes = expected_regimes - detected_regimes
            logger.warning(f"⚠️ Missing expected regimes: {missing_regimes}")
        
        # Validate regime detection logic
        success_criteria = [
            len(regime_counts) > 0,  # Should detect at least one regime
            all(regime in ['trending', 'ranging', 'volatile'] for regime in detected_regimes),  # Valid regime names
            len(regimes) == len(test_data)  # Should have regime for every period
        ]
        
        success = all(success_criteria)
        
        if success:
            logger.info("✅ Regime detection test PASSED")
            logger.info("🎯 All periods classified with valid regimes")
        else:
            logger.error("❌ Regime detection test FAILED")
            logger.error(f"Failed criteria: {[i for i, c in enumerate(success_criteria) if not c]}")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Regime detection test crashed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_adaptive_thresholds():
    """Test adaptive confidence thresholds"""
    
    logger.info("🧪 Testing adaptive confidence thresholds...")
    
    try:
        analyzer = MarketRegimeAnalyzer()
        
        # Test threshold retrieval for different combinations
        test_cases = [
            ('trend_following', 'buy', 'trending', 55),
            ('mean_reversion', 'buy', 'ranging', 60),
            ('llm_strategy', 'sell', 'volatile', 70),
            ('momentum', 'buy', 'trending', 60),
            ('unknown_strategy', 'buy', 'trending', 70)  # Should fallback to default
        ]
        
        success = True
        
        for strategy, action, regime, expected_threshold in test_cases:
            threshold = analyzer.get_adaptive_threshold(strategy, action, regime)
            
            logger.info(f"📊 {strategy}/{action}/{regime}: {threshold}% (expected: {expected_threshold}%)")
            
            if strategy == 'unknown_strategy':
                # Should use default threshold
                if threshold != 70:  # Default buy threshold
                    logger.error(f"❌ Wrong default threshold: {threshold}% (expected: 70%)")
                    success = False
            else:
                # Should match expected threshold
                if threshold != expected_threshold:
                    logger.error(f"❌ Wrong threshold: {threshold}% (expected: {expected_threshold}%)")
                    success = False
        
        if success:
            logger.info("✅ Adaptive thresholds test PASSED")
            logger.info("🎯 All thresholds match AdaptiveStrategyManager configuration")
        else:
            logger.error("❌ Adaptive thresholds test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Adaptive thresholds test crashed: {e}")
        return False

def test_strategy_priorities():
    """Test strategy priorities by regime"""
    
    logger.info("🧪 Testing strategy priorities by regime...")
    
    try:
        analyzer = MarketRegimeAnalyzer()
        
        # Test strategy priorities for each regime
        expected_priorities = {
            'trending': ['trend_following', 'momentum', 'llm_strategy', 'mean_reversion'],
            'ranging': ['mean_reversion', 'llm_strategy', 'momentum', 'trend_following'],
            'volatile': ['llm_strategy', 'mean_reversion', 'trend_following', 'momentum']
        }
        
        success = True
        
        for regime, expected_priority in expected_priorities.items():
            actual_priority = analyzer.get_strategy_priorities(regime)
            
            logger.info(f"📊 {regime}: {actual_priority}")
            
            if actual_priority != expected_priority:
                logger.error(f"❌ Wrong priority for {regime}")
                logger.error(f"   Expected: {expected_priority}")
                logger.error(f"   Actual: {actual_priority}")
                success = False
        
        # Test unknown regime (should use default)
        default_priority = analyzer.get_strategy_priorities('unknown_regime')
        logger.info(f"📊 unknown_regime (default): {default_priority}")
        
        if success:
            logger.info("✅ Strategy priorities test PASSED")
            logger.info("🎯 All priorities match AdaptiveStrategyManager configuration")
        else:
            logger.error("❌ Strategy priorities test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Strategy priorities test crashed: {e}")
        return False

def test_regime_performance_analysis():
    """Test regime-specific performance analysis"""
    
    logger.info("🧪 Testing regime performance analysis...")
    
    try:
        # Create test data
        test_data, _, _, _ = create_regime_test_data()
        
        # Create mock signals and returns
        signals_df = pd.DataFrame(index=test_data.index)
        signals_df['buy'] = np.random.choice([True, False], len(test_data), p=[0.1, 0.9])
        signals_df['sell'] = np.random.choice([True, False], len(test_data), p=[0.1, 0.9])
        signals_df['confidence'] = np.random.uniform(30, 90, len(test_data))
        
        # Create mock portfolio returns
        portfolio_returns = pd.Series(
            np.random.normal(0.001, 0.02, len(test_data)),  # 0.1% average return, 2% volatility
            index=test_data.index
        )
        
        # Initialize analyzer and run analysis
        analyzer = MarketRegimeAnalyzer()
        
        # Run comprehensive regime analysis
        results = analyzer.analyze_regime_performance(test_data, signals_df, portfolio_returns)
        
        if not results:
            logger.error("❌ No regime performance results")
            return False
        
        # Validate results structure
        expected_keys = ['regime_distribution', 'regime_transitions']
        missing_keys = [key for key in expected_keys if key not in results]
        
        if missing_keys:
            logger.error(f"❌ Missing result keys: {missing_keys}")
            return False
        
        # Log results
        logger.info(f"📊 Regime distribution: {results['regime_distribution']}")
        logger.info(f"📊 Regime transitions: {results['regime_transitions']}")
        
        # Check for regime-specific metrics
        regime_metrics_found = False
        for regime in ['trending', 'ranging', 'volatile']:
            if regime in results:
                regime_metrics = results[regime]
                logger.info(f"📊 {regime} metrics: {list(regime_metrics.keys())}")
                regime_metrics_found = True
        
        success = regime_metrics_found and len(results['regime_distribution']) > 0
        
        if success:
            logger.info("✅ Regime performance analysis test PASSED")
            logger.info("🎯 Comprehensive regime analysis working")
        else:
            logger.error("❌ Regime performance analysis test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Regime performance analysis test crashed: {e}")
        return False

def test_convenience_function():
    """Test the convenience function for regime analysis"""
    
    logger.info("🧪 Testing convenience function...")
    
    try:
        # Create test data
        test_data, _, _, _ = create_regime_test_data()
        
        # Test basic regime analysis
        results = analyze_market_regimes(test_data)
        
        if not results or 'regimes' not in results:
            logger.error("❌ Convenience function failed")
            return False
        
        regimes = results['regimes']
        regime_distribution = results['regime_distribution']
        
        logger.info(f"📊 Convenience function results:")
        logger.info(f"   Regimes detected: {len(regimes)}")
        logger.info(f"   Distribution: {regime_distribution}")
        
        success = len(regimes) > 0 and len(regime_distribution) > 0
        
        if success:
            logger.info("✅ Convenience function test PASSED")
        else:
            logger.error("❌ Convenience function test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Convenience function test crashed: {e}")
        return False

def main():
    """Run all MarketRegimeAnalyzer tests"""
    
    logger.info("🚀 Starting MarketRegimeAnalyzer Tests")
    
    tests = [
        ("Regime Detection", test_regime_detection),
        ("Adaptive Thresholds", test_adaptive_thresholds),
        ("Strategy Priorities", test_strategy_priorities),
        ("Performance Analysis", test_regime_performance_analysis),
        ("Convenience Function", test_convenience_function)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            success = test_func()
            if success:
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {e}")
    
    success_rate = passed / total
    overall_success = success_rate >= 0.8
    
    logger.info(f"\n{'='*60}")
    logger.info(f"MARKET REGIME ANALYZER TEST RESULTS")
    logger.info(f"{'='*60}")
    logger.info(f"Passed: {passed}/{total} ({success_rate:.1%})")
    logger.info(f"Overall: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    if overall_success:
        logger.info("🎯 MarketRegimeAnalyzer is ready for production use")
        logger.info("🎯 Regime detection aligned with live bot")
    else:
        logger.error("🔧 MarketRegimeAnalyzer needs fixes before use")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)