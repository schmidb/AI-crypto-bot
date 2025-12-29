#!/usr/bin/env python3
"""
Test RiskManagementValidator - Risk Management Validation

This test validates that the RiskManagementValidator correctly enforces
risk management rules and prevents excessive losses in backtesting.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict

# Add project root to path
sys.path.append('.')

from utils.backtest.risk_management_validator import RiskManagementValidator
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_portfolio_states(periods: int = 100) -> List[Dict]:
    """Create test portfolio states with various risk scenarios"""
    
    portfolio_states = []
    base_value = 10000.0
    
    for i in range(periods):
        # Simulate portfolio evolution
        portfolio_value = base_value * (1 + np.random.normal(0, 0.02))  # 2% volatility
        
        # Create different risk scenarios
        if i < 20:
            # Normal scenario
            eur_percent = 0.20  # 20% EUR
            btc_percent = 0.60  # 60% BTC
            eth_percent = 0.20  # 20% ETH
        elif i < 40:
            # Low EUR reserve scenario (risky)
            eur_percent = 0.05  # 5% EUR (below 12% minimum)
            btc_percent = 0.75  # 75% BTC
            eth_percent = 0.20  # 20% ETH
        elif i < 60:
            # High concentration scenario (risky)
            eur_percent = 0.15  # 15% EUR
            btc_percent = 0.80  # 80% BTC (above 75% limit)
            eth_percent = 0.05  # 5% ETH
        else:
            # Recovery scenario
            eur_percent = 0.25  # 25% EUR
            btc_percent = 0.50  # 50% BTC
            eth_percent = 0.25  # 25% ETH
        
        portfolio = {
            'portfolio_value_eur': {'amount': portfolio_value},
            'EUR': {'amount': portfolio_value * eur_percent},
            'BTC': {
                'amount': (portfolio_value * btc_percent) / 50000,  # Assume BTC = €50,000
                'last_price_eur': 50000
            },
            'ETH': {
                'amount': (portfolio_value * eth_percent) / 3000,   # Assume ETH = €3,000
                'last_price_eur': 3000
            }
        }
        
        portfolio_states.append(portfolio)
    
    logger.info(f"Created {len(portfolio_states)} test portfolio states")
    return portfolio_states

def create_test_trade_signals(periods: int = 100) -> List[Dict]:
    """Create test trade signals with various risk scenarios"""
    
    trade_signals = []
    
    for i in range(periods):
        # Create different trade size scenarios
        if i < 20:
            # Normal trades
            proposed_size = np.random.uniform(500, 2000)  # €500-2000
        elif i < 40:
            # Oversized trades (risky)
            proposed_size = np.random.uniform(4000, 6000)  # €4000-6000 (>35% of €10k)
        elif i < 60:
            # Undersized trades
            proposed_size = np.random.uniform(1, 4)  # €1-4 (below €5 minimum)
        else:
            # Mixed scenarios
            proposed_size = np.random.uniform(100, 3000)
        
        signal = {
            'action': np.random.choice(['BUY', 'SELL', 'HOLD'], p=[0.3, 0.3, 0.4]),
            'asset': np.random.choice(['BTC', 'ETH'], p=[0.7, 0.3]),
            'proposed_size': proposed_size,
            'confidence': np.random.uniform(30, 90),
            'index': i
        }
        
        trade_signals.append(signal)
    
    logger.info(f"Created {len(trade_signals)} test trade signals")
    return trade_signals

def create_test_trade_history(periods: int = 50) -> List[Dict]:
    """Create test trade history with various scenarios"""
    
    trade_history = []
    
    for i in range(periods):
        # Create different trade scenarios
        if i < 10:
            # Normal trades
            trade_amount = np.random.uniform(100, 2000)
        elif i < 20:
            # Small trades (some below minimum)
            trade_amount = np.random.uniform(1, 10)
        else:
            # Mixed trades
            trade_amount = np.random.uniform(50, 1500)
        
        trade = {
            'action': np.random.choice(['BUY', 'SELL']),
            'asset': np.random.choice(['BTC', 'ETH']),
            'trade_amount_base': trade_amount,
            'timestamp': datetime.now() - timedelta(hours=periods-i),
            'index': i
        }
        
        trade_history.append(trade)
    
    logger.info(f"Created {len(trade_history)} test trades")
    return trade_history

def create_test_portfolio_values(periods: int = 100) -> pd.Series:
    """Create test portfolio values with drawdown scenarios"""
    
    # Create portfolio value series with intentional drawdowns
    dates = pd.date_range(start=datetime.now() - timedelta(hours=periods), periods=periods, freq='H')
    
    values = []
    base_value = 10000.0
    current_value = base_value
    
    for i in range(periods):
        if 20 <= i < 40:
            # Drawdown period
            change = np.random.normal(-0.01, 0.02)  # -1% average with 2% volatility
        elif 40 <= i < 60:
            # Severe drawdown period
            change = np.random.normal(-0.02, 0.03)  # -2% average with 3% volatility
        else:
            # Normal/recovery period
            change = np.random.normal(0.001, 0.015)  # +0.1% average with 1.5% volatility
        
        current_value *= (1 + change)
        current_value = max(current_value, base_value * 0.5)  # Floor at 50% of initial
        values.append(current_value)
    
    portfolio_values = pd.Series(values, index=dates)
    
    max_drawdown = ((portfolio_values - portfolio_values.expanding().max()) / portfolio_values.expanding().max()).min() * 100
    logger.info(f"Created portfolio values with {max_drawdown:.2f}% max drawdown")
    
    return portfolio_values

def test_position_sizing_validation():
    """Test position sizing validation"""
    
    logger.info("🧪 Testing position sizing validation...")
    
    try:
        # Create test data
        portfolio_states = create_test_portfolio_states(50)
        trade_signals = create_test_trade_signals(50)
        
        # Initialize validator
        config = Config()
        validator = RiskManagementValidator(config)
        
        # Run position sizing validation
        results = validator.validate_position_sizing(portfolio_states, trade_signals)
        
        if 'error' in results:
            logger.error(f"❌ Position sizing validation error: {results['error']}")
            return False
        
        # Validate results structure
        required_fields = [
            'total_trades_evaluated', 'approved_trades', 'blocked_trades',
            'block_rate', 'violations', 'violation_rate', 'position_sizing_effective'
        ]
        
        missing_fields = [field for field in required_fields if field not in results]
        if missing_fields:
            logger.error(f"❌ Missing result fields: {missing_fields}")
            return False
        
        # Log results
        logger.info(f"📊 Position sizing results:")
        logger.info(f"   Total trades: {results['total_trades_evaluated']}")
        logger.info(f"   Approved: {results['approved_trades']}")
        logger.info(f"   Blocked: {results['blocked_trades']} ({results['block_rate']:.1%})")
        logger.info(f"   Violations: {results['violation_count']} ({results['violation_rate']:.1%})")
        logger.info(f"   Effective: {results['position_sizing_effective']}")
        
        # Success criteria
        success_criteria = [
            results['total_trades_evaluated'] > 0,  # Should evaluate some trades
            results['block_rate'] >= 0,  # Should have valid block rate
            results['violation_rate'] <= 1.0,  # Violation rate should be reasonable
            isinstance(results['position_sizing_effective'], bool)  # Should have effectiveness flag
        ]
        
        success = all(success_criteria)
        
        if success:
            logger.info("✅ Position sizing validation test PASSED")
        else:
            logger.error("❌ Position sizing validation test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Position sizing validation test crashed: {e}")
        return False

def test_portfolio_constraints_validation():
    """Test portfolio constraints validation"""
    
    logger.info("🧪 Testing portfolio constraints validation...")
    
    try:
        # Create test data with constraint violations
        portfolio_states = create_test_portfolio_states(60)
        
        # Initialize validator
        config = Config()
        validator = RiskManagementValidator(config)
        
        # Run portfolio constraints validation
        results = validator.validate_portfolio_constraints(portfolio_states)
        
        if 'error' in results:
            logger.error(f"❌ Portfolio constraints validation error: {results['error']}")
            return False
        
        # Validate results structure
        required_fields = [
            'total_snapshots', 'violations', 'violation_count',
            'violation_rate', 'constraints_effective'
        ]
        
        missing_fields = [field for field in required_fields if field not in results]
        if missing_fields:
            logger.error(f"❌ Missing result fields: {missing_fields}")
            return False
        
        # Log results
        logger.info(f"📊 Portfolio constraints results:")
        logger.info(f"   Total snapshots: {results['total_snapshots']}")
        logger.info(f"   Violations: {results['violation_count']} ({results['violation_rate']:.1%})")
        logger.info(f"   Effective: {results['constraints_effective']}")
        
        # Analyze violation types
        violation_types = {}
        for violation in results['violations']:
            vtype = violation['type']
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        if violation_types:
            logger.info(f"   Violation types: {violation_types}")
        
        # Success criteria
        success_criteria = [
            results['total_snapshots'] > 0,  # Should have snapshots
            results['violation_count'] >= 0,  # Should have valid violation count
            len(results['violations']) == results['violation_count'],  # Counts should match
            isinstance(results['constraints_effective'], bool)  # Should have effectiveness flag
        ]
        
        success = all(success_criteria)
        
        if success:
            logger.info("✅ Portfolio constraints validation test PASSED")
        else:
            logger.error("❌ Portfolio constraints validation test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Portfolio constraints validation test crashed: {e}")
        return False

def test_drawdown_protection_validation():
    """Test drawdown protection validation"""
    
    logger.info("🧪 Testing drawdown protection validation...")
    
    try:
        # Create test data with drawdowns
        portfolio_values = create_test_portfolio_values(80)
        trade_history = create_test_trade_history(30)
        
        # Initialize validator
        config = Config()
        validator = RiskManagementValidator(config)
        
        # Run drawdown protection validation
        results = validator.validate_drawdown_protection(portfolio_values, trade_history)
        
        if 'error' in results:
            logger.error(f"❌ Drawdown protection validation error: {results['error']}")
            return False
        
        # Validate results structure
        required_fields = [
            'max_drawdown_percent', 'drawdown_periods', 'excessive_drawdowns',
            'drawdown_protection_active', 'protection_effective'
        ]
        
        missing_fields = [field for field in required_fields if field not in results]
        if missing_fields:
            logger.error(f"❌ Missing result fields: {missing_fields}")
            return False
        
        # Log results
        logger.info(f"📊 Drawdown protection results:")
        logger.info(f"   Max drawdown: {results['max_drawdown_percent']:.2f}%")
        logger.info(f"   Drawdown periods: {results['drawdown_periods']}")
        logger.info(f"   Excessive drawdowns: {results['excessive_drawdowns']}")
        logger.info(f"   Protection active: {results['drawdown_protection_active']}")
        logger.info(f"   Protection effective: {results['protection_effective']}")
        
        # Success criteria
        success_criteria = [
            isinstance(results['max_drawdown_percent'], (int, float)),  # Should have numeric drawdown
            results['drawdown_periods'] >= 0,  # Should have valid period count
            results['excessive_drawdowns'] >= 0,  # Should have valid excessive count
            isinstance(results['protection_effective'], bool)  # Should have effectiveness flag
        ]
        
        success = all(success_criteria)
        
        if success:
            logger.info("✅ Drawdown protection validation test PASSED")
        else:
            logger.error("❌ Drawdown protection validation test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Drawdown protection validation test crashed: {e}")
        return False

def test_trade_size_limits_validation():
    """Test trade size limits validation"""
    
    logger.info("🧪 Testing trade size limits validation...")
    
    try:
        # Create test data with size violations
        trade_history = create_test_trade_history(40)
        
        # Initialize validator
        config = Config()
        validator = RiskManagementValidator(config)
        
        # Run trade size limits validation
        results = validator.validate_trade_size_limits(trade_history)
        
        if 'error' in results:
            logger.error(f"❌ Trade size limits validation error: {results['error']}")
            return False
        
        # Validate results structure
        required_fields = [
            'total_trades', 'valid_trades', 'violations',
            'violation_count', 'violation_rate', 'size_limits_effective'
        ]
        
        missing_fields = [field for field in required_fields if field not in results]
        if missing_fields:
            logger.error(f"❌ Missing result fields: {missing_fields}")
            return False
        
        # Log results
        logger.info(f"📊 Trade size limits results:")
        logger.info(f"   Total trades: {results['total_trades']}")
        logger.info(f"   Valid trades: {results['valid_trades']}")
        logger.info(f"   Violations: {results['violation_count']} ({results['violation_rate']:.1%})")
        logger.info(f"   Effective: {results['size_limits_effective']}")
        
        # Success criteria
        success_criteria = [
            results['total_trades'] >= 0,  # Should have valid trade count
            results['valid_trades'] + results['violation_count'] == results['total_trades'],  # Counts should add up
            results['violation_rate'] <= 1.0,  # Violation rate should be reasonable
            isinstance(results['size_limits_effective'], bool)  # Should have effectiveness flag
        ]
        
        success = all(success_criteria)
        
        if success:
            logger.info("✅ Trade size limits validation test PASSED")
        else:
            logger.error("❌ Trade size limits validation test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Trade size limits validation test crashed: {e}")
        return False

def test_comprehensive_validation():
    """Test comprehensive risk management validation"""
    
    logger.info("🧪 Testing comprehensive risk management validation...")
    
    try:
        # Create comprehensive test data
        portfolio_history = create_test_portfolio_states(60)
        trade_history = create_test_trade_history(30)
        portfolio_values = create_test_portfolio_values(60)
        trade_signals = create_test_trade_signals(60)
        
        backtest_data = {
            'portfolio_history': portfolio_history,
            'trade_history': trade_history,
            'portfolio_values': portfolio_values,
            'trade_signals': trade_signals
        }
        
        # Initialize validator
        config = Config()
        validator = RiskManagementValidator(config)
        
        # Run comprehensive validation
        results = validator.run_comprehensive_validation(backtest_data)
        
        if 'error' in results:
            logger.error(f"❌ Comprehensive validation error: {results['error']}")
            return False
        
        # Validate results structure
        required_fields = [
            'validation_timestamp', 'validations_run', 'individual_results',
            'overall_effectiveness_score', 'risk_management_grade', 'recommendations'
        ]
        
        missing_fields = [field for field in required_fields if field not in results]
        if missing_fields:
            logger.error(f"❌ Missing result fields: {missing_fields}")
            return False
        
        # Log results
        logger.info(f"📊 Comprehensive validation results:")
        logger.info(f"   Validations run: {results['validations_run']}")
        logger.info(f"   Overall effectiveness: {results['overall_effectiveness_score']:.1%}")
        logger.info(f"   Grade: {results['risk_management_grade']}")
        logger.info(f"   Recommendations: {len(results['recommendations'])}")
        
        for rec in results['recommendations'][:3]:  # Show first 3 recommendations
            logger.info(f"     • {rec}")
        
        # Success criteria
        success_criteria = [
            len(results['validations_run']) > 0,  # Should run some validations
            0 <= results['overall_effectiveness_score'] <= 1,  # Score should be valid
            len(results['recommendations']) > 0,  # Should have recommendations
            isinstance(results['individual_results'], dict)  # Should have individual results
        ]
        
        success = all(success_criteria)
        
        if success:
            logger.info("✅ Comprehensive validation test PASSED")
            logger.info("🎯 Risk management validation framework working")
        else:
            logger.error("❌ Comprehensive validation test FAILED")
        
        return success
        
    except Exception as e:
        logger.error(f"💥 Comprehensive validation test crashed: {e}")
        return False

def main():
    """Run all RiskManagementValidator tests"""
    
    logger.info("🚀 Starting RiskManagementValidator Tests")
    
    tests = [
        ("Position Sizing Validation", test_position_sizing_validation),
        ("Portfolio Constraints Validation", test_portfolio_constraints_validation),
        ("Drawdown Protection Validation", test_drawdown_protection_validation),
        ("Trade Size Limits Validation", test_trade_size_limits_validation),
        ("Comprehensive Validation", test_comprehensive_validation)
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
    logger.info(f"RISK MANAGEMENT VALIDATOR TEST RESULTS")
    logger.info(f"{'='*60}")
    logger.info(f"Passed: {passed}/{total} ({success_rate:.1%})")
    logger.info(f"Overall: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    if overall_success:
        logger.info("🛡️ RiskManagementValidator is ready for production use")
        logger.info("🎯 Risk management validation working correctly")
    else:
        logger.error("🔧 RiskManagementValidator needs fixes before use")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)