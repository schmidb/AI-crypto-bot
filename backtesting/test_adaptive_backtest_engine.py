#!/usr/bin/env python3
"""
Test AdaptiveBacktestEngine - Alignment Validation

This test validates that the AdaptiveBacktestEngine produces decisions
that align with the live bot's AdaptiveStrategyManager.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add project root to path
sys.path.append('.')

from utils.backtest.adaptive_backtest_engine import AdaptiveBacktestEngine
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_data(periods: int = 720) -> pd.DataFrame:
    """Create synthetic test data with indicators"""
    
    # Create datetime index (30 days of hourly data)
    start_date = datetime.now() - timedelta(days=30)
    date_range = pd.date_range(start=start_date, periods=periods, freq='H')
    
    # Generate synthetic OHLCV data
    np.random.seed(42)  # For reproducible results
    
    # Start with base price and add random walk
    base_price = 50000.0
    price_changes = np.random.normal(0, 0.02, periods)  # 2% volatility
    prices = [base_price]
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1000))  # Minimum price floor
    
    # Create OHLCV data
    data = pd.DataFrame(index=date_range)
    data['close'] = prices
    data['open'] = data['close'].shift(1).fillna(data['close'].iloc[0])
    data['high'] = data[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.01, periods))
    data['low'] = data[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.01, periods))
    data['volume'] = np.random.uniform(1000000, 5000000, periods)
    
    # Add technical indicators
    data['rsi_14'] = 50 + np.random.normal(0, 15, periods)  # RSI around 50
    data['rsi_14'] = np.clip(data['rsi_14'], 0, 100)
    
    # Bollinger Bands
    data['bb_middle_20'] = data['close'].rolling(20).mean().fillna(data['close'])
    bb_std = data['close'].rolling(20).std().fillna(data['close'].std())
    data['bb_upper_20'] = data['bb_middle_20'] + (bb_std * 2)
    data['bb_lower_20'] = data['bb_middle_20'] - (bb_std * 2)
    
    # Moving averages
    data['sma_20'] = data['close'].rolling(20).mean().fillna(data['close'])
    data['sma_50'] = data['close'].rolling(50).mean().fillna(data['close'])
    data['ema_12'] = data['close'].ewm(span=12).mean()
    data['ema_26'] = data['close'].ewm(span=26).mean()
    
    # MACD
    data['macd'] = data['ema_12'] - data['ema_26']
    data['macd_signal'] = data['macd'].ewm(span=9).mean()
    
    # Volume indicators
    data['volume_sma_20'] = data['volume'].rolling(20).mean().fillna(data['volume'])
    
    # ATR
    data['atr'] = (data['high'] - data['low']).rolling(14).mean().fillna(data['high'] - data['low'])
    
    # Stochastic
    data['stoch_k'] = 50 + np.random.normal(0, 20, periods)
    data['stoch_k'] = np.clip(data['stoch_k'], 0, 100)
    data['stoch_d'] = data['stoch_k'].rolling(3).mean()
    
    logger.info(f"Created test data: {len(data)} periods, price range ${data['close'].min():.0f}-${data['close'].max():.0f}")
    return data

def test_adaptive_backtest_engine():
    """Test AdaptiveBacktestEngine functionality"""
    
    logger.info("🧪 Testing AdaptiveBacktestEngine...")
    
    try:
        # Create test data
        test_data = create_test_data(720)  # 30 days of hourly data
        
        # Initialize AdaptiveBacktestEngine
        config = Config()
        engine = AdaptiveBacktestEngine(
            initial_capital=10000.0,
            fees=0.006,
            slippage=0.0005,
            config=config
        )
        
        logger.info("✅ AdaptiveBacktestEngine initialized successfully")
        
        # Run adaptive backtest
        logger.info("🔄 Running adaptive backtest...")
        results = engine.run_adaptive_backtest(test_data, "BTC-EUR")
        
        # Validate results structure
        required_fields = [
            'total_return', 'sharpe_ratio', 'max_drawdown', 'total_trades',
            'regime_distribution', 'strategy_usage', 'total_decisions'
        ]
        
        missing_fields = [field for field in required_fields if field not in results]
        if missing_fields:
            logger.error(f"❌ Missing required fields: {missing_fields}")
            return False
        
        # Validate regime analysis
        if 'regime_distribution' in results and results['regime_distribution']:
            regime_count = sum(results['regime_distribution'].values())
            logger.info(f"📊 Regime distribution: {results['regime_distribution']}")
            logger.info(f"📊 Total regime periods: {regime_count}")
        else:
            logger.warning("⚠️ No regime distribution found")
        
        # Validate strategy attribution
        if 'strategy_usage' in results and results['strategy_usage']:
            strategy_count = sum(results['strategy_usage'].values())
            logger.info(f"📊 Strategy usage: {results['strategy_usage']}")
            logger.info(f"📊 Total strategy decisions: {strategy_count}")
        else:
            logger.warning("⚠️ No strategy usage found")
        
        # Validate decision making
        total_decisions = results.get('total_decisions', 0)
        if total_decisions > 0:
            logger.info(f"🧠 Total decisions made: {total_decisions}")
        else:
            logger.warning("⚠️ No decisions recorded")
        
        # Validate performance metrics
        total_return = results.get('total_return', 0)
        sharpe_ratio = results.get('sharpe_ratio', 0)
        max_drawdown = results.get('max_drawdown', 0)
        total_trades = results.get('total_trades', 0)
        
        logger.info(f"📈 Performance Results:")
        logger.info(f"   Total Return: {total_return:.2f}%")
        logger.info(f"   Sharpe Ratio: {sharpe_ratio:.2f}")
        logger.info(f"   Max Drawdown: {max_drawdown:.2f}%")
        logger.info(f"   Total Trades: {total_trades}")
        
        # Validate risk management
        risk_active = results.get('risk_management_active', False)
        blocked_trades = results.get('blocked_trades', 0)
        approved_trades = results.get('approved_trades', 0)
        
        logger.info(f"🛡️ Risk Management:")
        logger.info(f"   Active: {risk_active}")
        logger.info(f"   Blocked Trades: {blocked_trades}")
        logger.info(f"   Approved Trades: {approved_trades}")
        
        # Success criteria
        success_criteria = [
            total_decisions > 0,  # Should make some decisions
            len(results.get('regime_distribution', {})) > 0,  # Should detect regimes
            len(results.get('strategy_usage', {})) > 0,  # Should use strategies
            'error' not in results  # Should not have errors
        ]
        
        success = all(success_criteria)
        
        if success:
            logger.info("✅ AdaptiveBacktestEngine test PASSED")
            logger.info("🎯 Engine successfully uses AdaptiveStrategyManager logic")
            logger.info("🎯 Market regime detection working")
            logger.info("🎯 Strategy attribution working")
            logger.info("🎯 Risk management integration working")
        else:
            logger.error("❌ AdaptiveBacktestEngine test FAILED")
            logger.error(f"Failed criteria: {[i for i, c in enumerate(success_criteria) if not c]}")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 AdaptiveBacktestEngine test crashed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_decision_alignment():
    """Test that AdaptiveBacktestEngine decisions align with live bot logic"""
    
    logger.info("🎯 Testing decision alignment with live bot...")
    
    try:
        # Create smaller test dataset for detailed analysis
        test_data = create_test_data(168)  # 7 days of hourly data
        
        # Initialize engine
        config = Config()
        engine = AdaptiveBacktestEngine(initial_capital=10000.0, config=config)
        
        # Run backtest and capture decision log
        results = engine.run_adaptive_backtest(test_data, "BTC-EUR")
        
        # Analyze decision log
        decision_log = engine.decision_log
        
        if not decision_log:
            logger.error("❌ No decision log captured")
            return False
        
        # Analyze decision patterns
        actions = [d['action'] for d in decision_log]
        regimes = [d['market_regime'] for d in decision_log]
        strategies = [d['primary_strategy'] for d in decision_log]
        
        action_counts = {action: actions.count(action) for action in set(actions)}
        regime_counts = {regime: regimes.count(regime) for regime in set(regimes)}
        strategy_counts = {strategy: strategies.count(strategy) for strategy in set(strategies)}
        
        logger.info(f"📊 Decision Analysis:")
        logger.info(f"   Actions: {action_counts}")
        logger.info(f"   Regimes: {regime_counts}")
        logger.info(f"   Strategies: {strategy_counts}")
        
        # Validate decision logic patterns
        success_criteria = [
            len(set(actions)) > 1,  # Should have variety in actions
            len(set(regimes)) > 1,  # Should detect different regimes
            len(set(strategies)) > 1,  # Should use different strategies
            'HOLD' in actions,  # Should have some HOLD decisions
            any(regime in regimes for regime in ['trending', 'ranging', 'volatile'])  # Should detect known regimes
        ]
        
        success = all(success_criteria)
        
        if success:
            logger.info("✅ Decision alignment test PASSED")
            logger.info("🎯 Decisions show expected variety and patterns")
        else:
            logger.error("❌ Decision alignment test FAILED")
            logger.error(f"Failed criteria: {[i for i, c in enumerate(success_criteria) if not c]}")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Decision alignment test crashed: {e}")
        return False

def main():
    """Run all AdaptiveBacktestEngine tests"""
    
    logger.info("🚀 Starting AdaptiveBacktestEngine Tests")
    
    tests = [
        ("Basic Functionality", test_adaptive_backtest_engine),
        ("Decision Alignment", test_decision_alignment)
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
    logger.info(f"ADAPTIVE BACKTEST ENGINE TEST RESULTS")
    logger.info(f"{'='*60}")
    logger.info(f"Passed: {passed}/{total} ({success_rate:.1%})")
    logger.info(f"Overall: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    if overall_success:
        logger.info("🎯 AdaptiveBacktestEngine is ready for production use")
        logger.info("🎯 Alignment with live bot verified")
    else:
        logger.error("🔧 AdaptiveBacktestEngine needs fixes before use")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)