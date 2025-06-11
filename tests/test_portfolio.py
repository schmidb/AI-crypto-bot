#!/usr/bin/env python3
"""
Unit tests for portfolio management functionality
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.portfolio import Portfolio

class TestPortfolio(unittest.TestCase):
    """Test cases for Portfolio class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_portfolio_data = {
            'btc_amount': 0.15,
            'eth_amount': 2.5,
            'sol_amount': 50.0,
            'usd_amount': 1000.0,
            'last_updated': '2024-01-01T12:00:00',
            'total_value_usd': 15000.0,
            'initial_value_usd': 12000.0
        }
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_portfolio_initialization_existing_file(self, mock_file, mock_json_load, mock_makedirs):
        """Test portfolio initialization with existing portfolio file"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        # Verify portfolio data is loaded
        self.assertEqual(portfolio.btc_amount, 0.15)
        self.assertEqual(portfolio.eth_amount, 2.5)
        self.assertEqual(portfolio.sol_amount, 50.0)
        self.assertEqual(portfolio.usd_amount, 1000.0)
        self.assertEqual(portfolio.total_value_usd, 15000.0)
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_portfolio_initialization_new_file(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test portfolio initialization with new portfolio file"""
        mock_json_load.side_effect = FileNotFoundError()
        
        portfolio = Portfolio()
        
        # Verify default values are set
        self.assertEqual(portfolio.btc_amount, 0.0)
        self.assertEqual(portfolio.eth_amount, 0.0)
        self.assertEqual(portfolio.sol_amount, 0.0)
        self.assertEqual(portfolio.usd_amount, 10000.0)  # Default starting amount
        
        # Verify save is called
        mock_json_dump.assert_called_once()
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_update_balance(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test updating individual asset balances"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        # Test BTC balance update
        portfolio.update_balance('BTC', 0.25)
        self.assertEqual(portfolio.btc_amount, 0.25)
        
        # Test ETH balance update
        portfolio.update_balance('ETH', 3.0)
        self.assertEqual(portfolio.eth_amount, 3.0)
        
        # Test SOL balance update
        portfolio.update_balance('SOL', 75.0)
        self.assertEqual(portfolio.sol_amount, 75.0)
        
        # Test USD balance update
        portfolio.update_balance('USD', 2000.0)
        self.assertEqual(portfolio.usd_amount, 2000.0)
        
        # Verify save is called
        self.assertTrue(mock_json_dump.called)
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_execute_buy_trade(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test executing a buy trade"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        # Execute BTC buy trade
        result = portfolio.execute_trade('buy', 'BTC-USD', 0.1, 45000.0, 10.0)
        
        # Verify trade execution
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'buy')
        self.assertEqual(result['asset'], 'BTC-USD')
        self.assertEqual(result['amount'], 0.1)
        self.assertEqual(result['price'], 45000.0)
        self.assertEqual(result['fees'], 10.0)
        
        # Verify portfolio balances updated
        self.assertEqual(portfolio.btc_amount, 0.25)  # 0.15 + 0.1
        self.assertEqual(portfolio.usd_amount, 490.0)  # 1000 - (0.1 * 45000) - 10
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_execute_sell_trade(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test executing a sell trade"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        # Execute ETH sell trade
        result = portfolio.execute_trade('sell', 'ETH-USD', 1.0, 3000.0, 15.0)
        
        # Verify trade execution
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'sell')
        self.assertEqual(result['asset'], 'ETH-USD')
        self.assertEqual(result['amount'], 1.0)
        
        # Verify portfolio balances updated
        self.assertEqual(portfolio.eth_amount, 1.5)  # 2.5 - 1.0
        self.assertEqual(portfolio.usd_amount, 3985.0)  # 1000 + (1.0 * 3000) - 15
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_insufficient_balance_buy(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test buy trade with insufficient USD balance"""
        # Portfolio with low USD balance
        low_usd_portfolio = self.test_portfolio_data.copy()
        low_usd_portfolio['usd_amount'] = 100.0
        mock_json_load.return_value = low_usd_portfolio
        
        portfolio = Portfolio()
        
        # Attempt to buy more than available USD
        result = portfolio.execute_trade('buy', 'BTC-USD', 1.0, 50000.0, 10.0)
        
        # Verify trade fails
        self.assertFalse(result['success'])
        self.assertIn('insufficient', result['error'].lower())
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_insufficient_balance_sell(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test sell trade with insufficient asset balance"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        # Attempt to sell more BTC than available
        result = portfolio.execute_trade('sell', 'BTC-USD', 1.0, 45000.0, 10.0)
        
        # Verify trade fails
        self.assertFalse(result['success'])
        self.assertIn('insufficient', result['error'].lower())
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    def test_get_portfolio_summary(self, mock_json_load, mock_makedirs):
        """Test getting portfolio summary"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        # Mock current prices
        current_prices = {
            'BTC-USD': 46000.0,
            'ETH-USD': 3100.0,
            'SOL-USD': 110.0
        }
        
        summary = portfolio.get_portfolio_summary(current_prices)
        
        # Verify summary structure
        self.assertIn('btc_amount', summary)
        self.assertIn('eth_amount', summary)
        self.assertIn('sol_amount', summary)
        self.assertIn('usd_amount', summary)
        self.assertIn('total_value_usd', summary)
        self.assertIn('btc_value_usd', summary)
        self.assertIn('eth_value_usd', summary)
        self.assertIn('sol_value_usd', summary)
        
        # Verify calculations
        expected_btc_value = 0.15 * 46000.0  # 6900
        expected_eth_value = 2.5 * 3100.0    # 7750
        expected_sol_value = 50.0 * 110.0    # 5500
        expected_total = expected_btc_value + expected_eth_value + expected_sol_value + 1000.0  # 21150
        
        self.assertEqual(summary['btc_value_usd'], expected_btc_value)
        self.assertEqual(summary['eth_value_usd'], expected_eth_value)
        self.assertEqual(summary['sol_value_usd'], expected_sol_value)
        self.assertEqual(summary['total_value_usd'], expected_total)
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    def test_calculate_allocation_percentages(self, mock_json_load, mock_makedirs):
        """Test calculation of asset allocation percentages"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        current_prices = {
            'BTC-USD': 40000.0,  # 0.15 * 40000 = 6000
            'ETH-USD': 2800.0,   # 2.5 * 2800 = 7000
            'SOL-USD': 100.0     # 50.0 * 100 = 5000
        }
        # Total: 6000 + 7000 + 5000 + 1000 = 19000
        
        allocations = portfolio.get_allocation_percentages(current_prices)
        
        # Verify allocation calculations
        self.assertAlmostEqual(allocations['btc_percent'], 31.58, places=2)  # 6000/19000
        self.assertAlmostEqual(allocations['eth_percent'], 36.84, places=2)  # 7000/19000
        self.assertAlmostEqual(allocations['sol_percent'], 26.32, places=2)  # 5000/19000
        self.assertAlmostEqual(allocations['usd_percent'], 5.26, places=2)   # 1000/19000
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_rebalance_portfolio(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test portfolio rebalancing functionality"""
        # Portfolio heavily weighted in BTC
        unbalanced_portfolio = {
            'btc_amount': 0.5,    # High BTC allocation
            'eth_amount': 0.5,    # Low ETH allocation
            'sol_amount': 10.0,   # Low SOL allocation
            'usd_amount': 500.0,  # Low USD allocation
            'last_updated': '2024-01-01T12:00:00',
            'total_value_usd': 25000.0,
            'initial_value_usd': 20000.0
        }
        
        mock_json_load.return_value = unbalanced_portfolio
        
        portfolio = Portfolio()
        
        current_prices = {
            'BTC-USD': 40000.0,
            'ETH-USD': 3000.0,
            'SOL-USD': 120.0
        }
        
        # Target allocation: 40% BTC, 40% ETH, 20% SOL, 0% USD
        target_allocation = {
            'btc_percent': 40.0,
            'eth_percent': 40.0,
            'sol_percent': 20.0,
            'usd_percent': 0.0
        }
        
        rebalance_trades = portfolio.calculate_rebalance_trades(current_prices, target_allocation)
        
        # Verify rebalancing trades are suggested
        self.assertIsInstance(rebalance_trades, list)
        self.assertTrue(len(rebalance_trades) > 0)
        
        # Each trade should have required fields
        for trade in rebalance_trades:
            self.assertIn('action', trade)
            self.assertIn('asset', trade)
            self.assertIn('amount', trade)
            self.assertIn('reason', trade)
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_portfolio_history_tracking(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test portfolio value history tracking"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        current_prices = {
            'BTC-USD': 45000.0,
            'ETH-USD': 3000.0,
            'SOL-USD': 110.0
        }
        
        # Record portfolio value
        portfolio.record_portfolio_value(current_prices)
        
        # Verify history recording
        mock_json_dump.assert_called()
        
        # Check that portfolio value is calculated and stored
        self.assertTrue(hasattr(portfolio, 'total_value_usd'))
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    def test_portfolio_performance_metrics(self, mock_json_load, mock_makedirs):
        """Test portfolio performance calculation"""
        mock_json_load.return_value = self.test_portfolio_data
        
        portfolio = Portfolio()
        
        current_prices = {
            'BTC-USD': 50000.0,  # Price increased
            'ETH-USD': 3200.0,   # Price increased
            'SOL-USD': 130.0     # Price increased
        }
        
        performance = portfolio.calculate_performance(current_prices)
        
        # Verify performance metrics
        self.assertIn('current_value_usd', performance)
        self.assertIn('initial_value_usd', performance)
        self.assertIn('total_return_usd', performance)
        self.assertIn('total_return_percent', performance)
        self.assertIn('daily_return_percent', performance)
        
        # Current value should be higher due to price increases
        self.assertGreater(performance['current_value_usd'], performance['initial_value_usd'])
        self.assertGreater(performance['total_return_percent'], 0)

class TestPortfolioIntegration(unittest.TestCase):
    """Integration tests for portfolio with trading scenarios"""
    
    @patch('utils.portfolio.os.makedirs')
    @patch('utils.portfolio.json.load')
    @patch('utils.portfolio.json.dump')
    @patch('utils.portfolio.open', new_callable=mock_open)
    def test_complete_trading_scenario(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test complete trading scenario with multiple trades"""
        # Start with initial portfolio
        initial_portfolio = {
            'btc_amount': 0.0,
            'eth_amount': 0.0,
            'sol_amount': 0.0,
            'usd_amount': 10000.0,
            'last_updated': '2024-01-01T00:00:00',
            'total_value_usd': 10000.0,
            'initial_value_usd': 10000.0
        }
        
        mock_json_load.return_value = initial_portfolio
        
        portfolio = Portfolio()
        
        # Execute series of trades
        trades = [
            ('buy', 'BTC-USD', 0.1, 45000.0, 10.0),
            ('buy', 'ETH-USD', 1.5, 3000.0, 15.0),
            ('buy', 'SOL-USD', 25.0, 120.0, 8.0),
            ('sell', 'BTC-USD', 0.05, 46000.0, 5.0),
            ('sell', 'ETH-USD', 0.5, 3100.0, 7.0)
        ]
        
        trade_results = []
        for action, asset, amount, price, fees in trades:
            result = portfolio.execute_trade(action, asset, amount, price, fees)
            trade_results.append(result)
        
        # Verify all trades executed successfully
        for result in trade_results:
            self.assertTrue(result['success'])
        
        # Verify final portfolio state
        self.assertEqual(portfolio.btc_amount, 0.05)  # 0.1 - 0.05
        self.assertEqual(portfolio.eth_amount, 1.0)   # 1.5 - 0.5
        self.assertEqual(portfolio.sol_amount, 25.0)
        
        # Calculate expected USD balance
        # Initial: 10000
        # BTC buy: -4500 - 10 = -4510
        # ETH buy: -4500 - 15 = -4515
        # SOL buy: -3000 - 8 = -3008
        # BTC sell: +2300 - 5 = +2295
        # ETH sell: +1550 - 7 = +1543
        # Final: 10000 - 4510 - 4515 - 3008 + 2295 + 1543 = 1805
        expected_usd = 1805.0
        self.assertEqual(portfolio.usd_amount, expected_usd)
        
        # Verify portfolio summary
        current_prices = {
            'BTC-USD': 47000.0,
            'ETH-USD': 3150.0,
            'SOL-USD': 125.0
        }
        
        summary = portfolio.get_portfolio_summary(current_prices)
        
        expected_total_value = (
            0.05 * 47000.0 +    # BTC: 2350
            1.0 * 3150.0 +      # ETH: 3150
            25.0 * 125.0 +      # SOL: 3125
            1805.0              # USD: 1805
        )  # Total: 10430
        
        self.assertEqual(summary['total_value_usd'], expected_total_value)

if __name__ == '__main__':
    unittest.main()
