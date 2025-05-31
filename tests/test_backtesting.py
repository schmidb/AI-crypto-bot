#!/usr/bin/env python3
"""
Unit tests for the backtesting module
"""

import unittest
from datetime import datetime, timedelta
import pandas as pd
from backtesting import Backtester, BacktestResult, BacktestTrade
from data_collector import DataCollector
from coinbase_client import CoinbaseClient

class MockDataCollector:
    """Mock data collector for testing"""
    
    def get_historical_data(self, product_id, granularity, days_back):
        """Return mock historical data"""
        # Create a simple DataFrame with test data
        dates = [datetime.now() - timedelta(days=i) for i in range(days_back, 0, -1)]
        data = {
            'start': dates,
            'open': [100 + i for i in range(len(dates))],
            'high': [105 + i for i in range(len(dates))],
            'low': [95 + i for i in range(len(dates))],
            'close': [102 + i for i in range(len(dates))],
            'volume': [1000 for _ in range(len(dates))]
        }
        return pd.DataFrame(data)
    
    def calculate_technical_indicators(self, df):
        """Return mock technical indicators"""
        return {
            'rsi': 50,
            'macd_histogram': 0.5,
            'bollinger_upper': 110,
            'bollinger_lower': 90,
            'market_trend': 'neutral'
        }

class TestBacktesting(unittest.TestCase):
    """Test cases for backtesting module"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_data_collector = MockDataCollector()
        self.backtester = Backtester(self.mock_data_collector)
        
    def test_backtest_result_initialization(self):
        """Test BacktestResult initialization"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        result = BacktestResult('BTC-USD', start_date, end_date, 10000, 'Test Strategy')
        
        self.assertEqual(result.product_id, 'BTC-USD')
        self.assertEqual(result.start_date, start_date)
        self.assertEqual(result.end_date, end_date)
        self.assertEqual(result.initial_balance_usd, 10000)
        self.assertEqual(result.final_balance_usd, 10000)
        self.assertEqual(result.strategy_name, 'Test Strategy')
        self.assertEqual(len(result.trades), 0)
        
    def test_add_trade(self):
        """Test adding a trade to BacktestResult"""
        result = BacktestResult('BTC-USD', datetime.now(), datetime.now(), 10000, 'Test')
        
        trade = BacktestTrade(
            timestamp=datetime.now(),
            product_id='BTC-USD',
            side='buy',
            price=50000,
            size=0.1,
            value_usd=5000
        )
        
        result.add_trade(trade)
        self.assertEqual(len(result.trades), 1)
        self.assertEqual(result.trades[0], trade)
        
    def test_calculate_metrics(self):
        """Test calculating metrics from trades"""
        result = BacktestResult('BTC-USD', datetime.now(), datetime.now(), 10000, 'Test')
        
        # Add a winning trade
        trade1 = BacktestTrade(
            timestamp=datetime.now(),
            product_id='BTC-USD',
            side='sell',
            price=52000,
            size=0.1,
            value_usd=5200,
            profit_loss_usd=200,
            profit_loss_percent=4.0
        )
        
        # Add a losing trade
        trade2 = BacktestTrade(
            timestamp=datetime.now(),
            product_id='BTC-USD',
            side='sell',
            price=48000,
            size=0.1,
            value_usd=4800,
            profit_loss_usd=-200,
            profit_loss_percent=-4.0
        )
        
        result.add_trade(trade1)
        result.add_trade(trade2)
        
        metrics = result.calculate_metrics()
        
        self.assertEqual(metrics['total_trades'], 2)
        self.assertEqual(metrics['winning_trades'], 1)
        self.assertEqual(metrics['losing_trades'], 1)
        self.assertEqual(metrics['win_rate'], 0.5)
        self.assertEqual(metrics['total_profit_loss_usd'], 0)
        
    def test_run_backtest(self):
        """Test running a backtest"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        result = self.backtester.run_backtest(
            product_id='BTC-USD',
            start_date=start_date,
            end_date=end_date,
            initial_balance_usd=10000,
            trade_size_usd=1000
        )
        
        # Basic validation of the result
        self.assertEqual(result.product_id, 'BTC-USD')
        self.assertEqual(result.start_date, start_date)
        self.assertEqual(result.end_date, end_date)
        self.assertEqual(result.initial_balance_usd, 10000)
        
        # There should be some trades
        self.assertGreater(len(result.trades), 0)
        
        # Metrics should be calculated
        self.assertIsNotNone(result.metrics)
        self.assertIn('total_trades', result.metrics)
        self.assertIn('win_rate', result.metrics)
        self.assertIn('total_return_percent', result.metrics)

if __name__ == '__main__':
    unittest.main()
