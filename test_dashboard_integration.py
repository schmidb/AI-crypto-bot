#!/usr/bin/env python3
"""
Test Dashboard Integration

This script tests the dashboard integration by generating sample data
and running the backtesting dashboard integration.
"""

import logging
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from dashboard_integration import DashboardIntegration
from utils.indicator_factory import calculate_indicators

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_data(days: int = 30) -> pd.DataFrame:
    """Create sample historical data for testing"""
    try:
        logger.info(f"Creating {days} days of sample data")
        
        # Generate sample price data
        start_date = datetime.now() - timedelta(days=days)
        dates = pd.date_range(start=start_date, periods=days*24, freq='H')
        
        # Create realistic price movement
        initial_price = 45000  # Starting BTC price
        returns = np.random.normal(0, 0.02, len(dates))  # 2% hourly volatility
        
        prices = [initial_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # Generate realistic OHLCV from price
            volatility = abs(np.random.normal(0, 0.01))
            
            high = price * (1 + volatility)
            low = price * (1 - volatility)
            open_price = prices[i-1] if i > 0 else price
            close = price
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        logger.info(f"Created sample data: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return pd.DataFrame()

def create_sample_backtest_results():
    """Create sample backtest results for testing"""
    try:
        logger.info("Creating sample backtest results")
        
        # Sample individual strategy results
        individual_results = {
            'momentum': {
                'total_return': 0.95,
                'annual_return': 58.46,
                'sharpe_ratio': 3.489,
                'sortino_ratio': 5.671,
                'max_drawdown': -1.05,
                'total_trades': 2,
                'win_rate': 50.0,
                'profit_factor': 1.25,
                'initial_capital': 10000.0,
                'final_value': 10095.0,
                'buy_signals': 14,
                'sell_signals': 6,
                'signal_count': 20
            },
            'mean_reversion': {
                'total_return': -1.84,
                'annual_return': -45.23,
                'sharpe_ratio': -8.321,
                'sortino_ratio': -12.45,
                'max_drawdown': -2.59,
                'total_trades': 2,
                'win_rate': 0.0,
                'profit_factor': 0.75,
                'initial_capital': 10000.0,
                'final_value': 9816.0,
                'buy_signals': 18,
                'sell_signals': 24,
                'signal_count': 42
            },
            'trend_following': {
                'total_return': -0.52,
                'annual_return': -12.84,
                'sharpe_ratio': -2.529,
                'sortino_ratio': -3.21,
                'max_drawdown': -2.53,
                'total_trades': 4,
                'win_rate': 25.0,
                'profit_factor': 0.89,
                'initial_capital': 10000.0,
                'final_value': 9948.0,
                'buy_signals': 18,
                'sell_signals': 13,
                'signal_count': 31
            },
            'adaptive': {
                'total_return': -3.93,
                'annual_return': -78.45,
                'sharpe_ratio': -20.626,
                'sortino_ratio': -25.34,
                'max_drawdown': -4.81,
                'total_trades': 8,
                'win_rate': 12.5,
                'profit_factor': 0.45,
                'initial_capital': 10000.0,
                'final_value': 9607.0,
                'buy_signals': 23,
                'sell_signals': 23,
                'signal_count': 46
            }
        }
        
        # Sample comparative analysis
        comparative_analysis = {
            'best_strategy': {
                'name': 'momentum',
                'score': 0.856
            },
            'rankings': {
                'total_return': [
                    {'strategy': 'momentum', 'value': 0.95, 'rank': 1},
                    {'strategy': 'trend_following', 'value': -0.52, 'rank': 2},
                    {'strategy': 'mean_reversion', 'value': -1.84, 'rank': 3},
                    {'strategy': 'adaptive', 'value': -3.93, 'rank': 4}
                ]
            },
            'risk_return_profile': [
                {'strategy': 'momentum', 'return': 0.95, 'risk': 1.05, 'sharpe': 3.489, 'trades': 2},
                {'strategy': 'mean_reversion', 'return': -1.84, 'risk': 2.59, 'sharpe': -8.321, 'trades': 2},
                {'strategy': 'trend_following', 'return': -0.52, 'risk': 2.53, 'sharpe': -2.529, 'trades': 4},
                {'strategy': 'adaptive', 'return': -3.93, 'risk': 4.81, 'sharpe': -20.626, 'trades': 8}
            ],
            'summary': {
                'strategies_tested': 4,
                'best_return': 0.95,
                'best_sharpe': 3.489,
                'lowest_drawdown': 1.05,
                'total_trades': 16
            }
        }
        
        # Complete backtest results
        backtest_results = {
            'timestamp': datetime.now().isoformat(),
            'product_id': 'BTC-USD',
            'individual_results': individual_results,
            'comparative_analysis': comparative_analysis,
            'data_period': {
                'start': (datetime.now() - timedelta(days=30)).isoformat(),
                'end': datetime.now().isoformat(),
                'rows': 720  # 30 days * 24 hours
            }
        }
        
        return backtest_results
        
    except Exception as e:
        logger.error(f"Error creating sample backtest results: {e}")
        return {}

def create_sample_optimization_results():
    """Create sample optimization results for testing"""
    try:
        logger.info("Creating sample optimization results")
        
        optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'strategy_name': 'momentum',
            'product_id': 'BTC-USD',
            'optimization_metric': 'sortino_ratio',
            'param_grid': {
                'confidence_threshold': [0.6, 0.7, 0.8],
                'lookback_period': [10, 20, 30],
                'volatility_threshold': [0.02, 0.03, 0.04]
            },
            'best_params': {
                'confidence_threshold': 0.6,
                'lookback_period': 10,
                'volatility_threshold': 0.02
            },
            'best_performance': 5.671,
            'total_combinations': 27,
            'top_results': [
                {
                    'confidence_threshold': 0.6,
                    'lookback_period': 10,
                    'volatility_threshold': 0.02,
                    'sortino_ratio': 5.671,
                    'total_return': 0.95,
                    'sharpe_ratio': 3.489
                },
                {
                    'confidence_threshold': 0.7,
                    'lookback_period': 10,
                    'volatility_threshold': 0.02,
                    'sortino_ratio': 5.234,
                    'total_return': 0.87,
                    'sharpe_ratio': 3.201
                }
            ]
        }
        
        return optimization_results
        
    except Exception as e:
        logger.error(f"Error creating sample optimization results: {e}")
        return {}

def create_sample_walkforward_results():
    """Create sample walk-forward analysis results"""
    try:
        logger.info("Creating sample walk-forward results")
        
        # Generate sample periods
        periods = []
        base_date = datetime.now() - timedelta(days=90)
        
        for i in range(3):  # 3 walk-forward periods
            train_start = base_date + timedelta(days=i*15)
            train_end = train_start + timedelta(days=60)
            test_start = train_end + timedelta(hours=1)
            test_end = test_start + timedelta(days=15)
            
            # Sample performance for each period
            test_return = np.random.normal(0.5, 1.5)  # Random return around 0.5%
            
            periods.append({
                'period_id': i,
                'train_start': train_start.isoformat(),
                'train_end': train_end.isoformat(),
                'test_start': test_start.isoformat(),
                'test_end': test_end.isoformat(),
                'train_days': 60,
                'test_days': 15,
                'best_params': {
                    'confidence_threshold': np.random.choice([0.6, 0.7, 0.8]),
                    'lookback_period': np.random.choice([10, 20, 30]),
                    'volatility_threshold': np.random.choice([0.02, 0.03, 0.04])
                },
                'train_performance': np.random.uniform(3.0, 6.0),
                'test_performance': {
                    'total_return': test_return,
                    'sharpe_ratio': np.random.uniform(-2.0, 4.0),
                    'max_drawdown': -abs(np.random.uniform(0.5, 3.0)),
                    'total_trades': np.random.randint(1, 8),
                    'win_rate': np.random.uniform(20, 80)
                }
            })
        
        walkforward_results = {
            'timestamp': datetime.now().isoformat(),
            'strategy_name': 'momentum',
            'product_id': 'BTC-USD',
            'periods': periods,
            'analysis': {
                'periods_tested': len(periods),
                'avg_test_return': np.mean([p['test_performance']['total_return'] for p in periods]),
                'std_test_return': np.std([p['test_performance']['total_return'] for p in periods]),
                'avg_test_sharpe': np.mean([p['test_performance']['sharpe_ratio'] for p in periods]),
                'std_test_sharpe': np.std([p['test_performance']['sharpe_ratio'] for p in periods]),
                'positive_periods': sum(1 for p in periods if p['test_performance']['total_return'] > 0),
                'negative_periods': sum(1 for p in periods if p['test_performance']['total_return'] < 0),
                'win_rate': sum(1 for p in periods if p['test_performance']['total_return'] > 0) / len(periods) * 100,
                'parameter_stability': 0.67  # 67% parameter stability
            }
        }
        
        return walkforward_results
        
    except Exception as e:
        logger.error(f"Error creating sample walk-forward results: {e}")
        return {}

def test_dashboard_integration():
    """Test the dashboard integration with sample data"""
    try:
        logger.info("Starting dashboard integration test")
        
        # Initialize dashboard integration
        dashboard = DashboardIntegration()
        
        # Create sample data files
        logger.info("Creating sample dashboard data files...")
        
        # Create backtest results
        backtest_results = create_sample_backtest_results()
        dashboard._create_latest_backtest_file(backtest_results, "BTC-USD")
        
        # Create sample data for data summary
        sample_data = create_sample_data(30)
        if not sample_data.empty:
            sample_data_with_indicators = calculate_indicators(sample_data, "BTC-USD")
            dashboard._create_data_summary_file(sample_data_with_indicators, "BTC-USD")
            dashboard._create_strategy_comparison_file(backtest_results)
        
        # Create optimization results
        optimization_results = create_sample_optimization_results()
        output_file = dashboard.dashboard_data_dir / "backtest_results" / "latest_optimization.json"
        with open(output_file, 'w') as f:
            json.dump(optimization_results, f, indent=2, default=str)
        
        # Create walk-forward results
        walkforward_results = create_sample_walkforward_results()
        output_file = dashboard.dashboard_data_dir / "backtest_results" / "latest_walkforward.json"
        with open(output_file, 'w') as f:
            json.dump(walkforward_results, f, indent=2, default=str)
        
        # Create update status
        status = {
            'last_update': datetime.now().isoformat(),
            'status': 'success',
            'product_id': 'BTC-USD',
            'next_update': (datetime.now() + timedelta(hours=1)).isoformat(),
            'test_mode': True
        }
        
        status_file = dashboard.dashboard_data_dir / "backtest_results" / "update_status.json"
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)
        
        logger.info("✅ Dashboard integration test completed successfully")
        
        # Print summary
        print("\n🎉 Dashboard Integration Test Results:")
        print("=" * 50)
        print(f"✅ Sample data files created in: {dashboard.dashboard_data_dir}")
        print("✅ Backtest results: latest_backtest.json")
        print("✅ Data summary: data_summary.json")
        print("✅ Strategy comparison: strategy_comparison.json")
        print("✅ Optimization results: latest_optimization.json")
        print("✅ Walk-forward analysis: latest_walkforward.json")
        print("✅ Update status: update_status.json")
        print("\n📊 Dashboard Access:")
        print("Open: dashboard/static/backtesting.html")
        print("The dashboard will display the sample backtesting data.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in dashboard integration test: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_dashboard_integration()
    exit(0 if success else 1)