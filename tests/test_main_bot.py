#!/usr/bin/env python3
"""
Unit tests for the main trading bot orchestration
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the config module before importing main
sys.modules['config'] = MagicMock()
sys.modules['config'].TRADING_PAIRS = ['BTC-USD', 'ETH-USD', 'SOL-USD']
sys.modules['config'].DECISION_INTERVAL_MINUTES = 60
sys.modules['config'].WEBSERVER_SYNC_ENABLED = False
sys.modules['config'].SIMULATION_MODE = True
sys.modules['config'].RISK_LEVEL = 'medium'
sys.modules['config'].Config = MagicMock()

from main import TradingBot

class TestTradingBot(unittest.TestCase):
    """Test cases for TradingBot main orchestration"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock all external dependencies
        self.patcher_coinbase = patch('main.CoinbaseClient')
        self.patcher_llm = patch('main.LLMAnalyzer')
        self.patcher_data_collector = patch('main.DataCollector')
        self.patcher_trading_strategy = patch('main.TradingStrategy')
        self.patcher_dashboard = patch('main.DashboardUpdater')
        self.patcher_webserver = patch('main.WebServerSync')
        self.patcher_tax_report = patch('main.TaxReportGenerator')
        self.patcher_strategy_evaluator = patch('main.StrategyEvaluator')
        self.patcher_logger = patch('main.get_supervisor_logger')
        
        # Start all patches
        self.mock_coinbase = self.patcher_coinbase.start()
        self.mock_llm = self.patcher_llm.start()
        self.mock_data_collector = self.patcher_data_collector.start()
        self.mock_trading_strategy = self.patcher_trading_strategy.start()
        self.mock_dashboard = self.patcher_dashboard.start()
        self.mock_webserver = self.patcher_webserver.start()
        self.mock_tax_report = self.patcher_tax_report.start()
        self.mock_strategy_evaluator = self.patcher_strategy_evaluator.start()
        self.mock_logger = self.patcher_logger.start()
        
        # Configure mock returns
        self.mock_logger.return_value = MagicMock()
        
    def tearDown(self):
        """Clean up after tests"""
        # Stop all patches
        self.patcher_coinbase.stop()
        self.patcher_llm.stop()
        self.patcher_data_collector.stop()
        self.patcher_trading_strategy.stop()
        self.patcher_dashboard.stop()
        self.patcher_webserver.stop()
        self.patcher_tax_report.stop()
        self.patcher_strategy_evaluator.stop()
        self.patcher_logger.stop()
    
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_bot_initialization(self, mock_file, mock_json_dump, mock_makedirs):
        """Test that the bot initializes correctly"""
        bot = TradingBot()
        
        # Verify all components are initialized
        self.mock_coinbase.assert_called_once()
        self.mock_llm.assert_called_once()
        self.mock_data_collector.assert_called_once()
        self.mock_trading_strategy.assert_called_once()
        self.mock_dashboard.assert_called_once()
        self.mock_webserver.assert_called_once()
        self.mock_tax_report.assert_called_once()
        self.mock_strategy_evaluator.assert_called_once()
        
        # Verify directories are created
        mock_makedirs.assert_called()
        
        # Verify startup data is recorded
        mock_json_dump.assert_called()
    
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_record_startup_time(self, mock_file, mock_json_dump, mock_makedirs):
        """Test startup time recording"""
        bot = TradingBot()
        
        # Verify startup data structure
        call_args = mock_json_dump.call_args[0][0]  # First argument to json.dump
        
        self.assertIn('startup_time', call_args)
        self.assertIn('trading_pairs', call_args)
        self.assertIn('decision_interval_minutes', call_args)
        self.assertIn('simulation_mode', call_args)
        self.assertIn('risk_level', call_args)
        self.assertIn('status', call_args)
        self.assertEqual(call_args['status'], 'online')
    
    @patch('main.os.makedirs')
    @patch('main.json.load')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_record_shutdown_time(self, mock_file, mock_json_dump, mock_json_load, mock_makedirs):
        """Test shutdown time recording"""
        # Mock existing startup data
        mock_json_load.return_value = {
            'startup_time': '2024-01-01T00:00:00',
            'status': 'online'
        }
        
        bot = TradingBot()
        bot.record_shutdown_time()
        
        # Verify shutdown data is recorded
        self.assertTrue(mock_json_dump.called)
        call_args = mock_json_dump.call_args[0][0]
        
        self.assertEqual(call_args['status'], 'offline')
        self.assertIn('shutdown_time', call_args)
        self.assertIn('last_seen', call_args)
    
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_run_trading_cycle(self, mock_file, mock_json_dump, mock_makedirs):
        """Test a complete trading cycle"""
        # Configure mocks for trading cycle
        self.mock_data_collector.return_value.collect_market_data.return_value = {
            'BTC-USD': {'price': 50000, 'volume': 1000},
            'ETH-USD': {'price': 3000, 'volume': 500},
            'SOL-USD': {'price': 100, 'volume': 200}
        }
        
        self.mock_llm.return_value.analyze_market_and_decide.return_value = {
            'action': 'buy',
            'asset': 'BTC-USD',
            'confidence': 75,
            'reasoning': 'Test reasoning'
        }
        
        self.mock_trading_strategy.return_value.execute_trade.return_value = {
            'success': True,
            'trade_id': 'test_123'
        }
        
        bot = TradingBot()
        result = bot.run_trading_cycle()
        
        # Verify trading cycle components are called
        self.mock_data_collector.return_value.collect_market_data.assert_called_once()
        self.mock_llm.return_value.analyze_market_and_decide.assert_called_once()
        self.mock_trading_strategy.return_value.execute_trade.assert_called_once()
        self.mock_dashboard.return_value.update_dashboard.assert_called()
        
        self.assertTrue(result)
    
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_trading_cycle_with_hold_decision(self, mock_file, mock_json_dump, mock_makedirs):
        """Test trading cycle with hold decision"""
        # Configure mocks for hold decision
        self.mock_data_collector.return_value.collect_market_data.return_value = {
            'BTC-USD': {'price': 50000, 'volume': 1000}
        }
        
        self.mock_llm.return_value.analyze_market_and_decide.return_value = {
            'action': 'hold',
            'confidence': 60,
            'reasoning': 'Market uncertainty'
        }
        
        bot = TradingBot()
        result = bot.run_trading_cycle()
        
        # Verify no trade is executed for hold decision
        self.mock_trading_strategy.return_value.execute_trade.assert_not_called()
        self.assertTrue(result)
    
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_trading_cycle_error_handling(self, mock_file, mock_json_dump, mock_makedirs):
        """Test error handling in trading cycle"""
        # Configure mock to raise exception
        self.mock_data_collector.return_value.collect_market_data.side_effect = Exception("API Error")
        
        bot = TradingBot()
        result = bot.run_trading_cycle()
        
        # Verify error is handled gracefully
        self.assertFalse(result)
    
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_sync_to_webserver(self, mock_file, mock_json_dump, mock_makedirs):
        """Test web server sync functionality"""
        bot = TradingBot()
        bot.sync_to_webserver()
        
        # Verify webserver sync is called
        self.mock_webserver.return_value.sync_to_webserver.assert_called_once()
    
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_generate_tax_report(self, mock_file, mock_json_dump, mock_makedirs):
        """Test tax report generation"""
        self.mock_tax_report.return_value.generate_report.return_value = True
        
        bot = TradingBot()
        result = bot.generate_tax_report()
        
        # Verify tax report generation is called
        self.mock_tax_report.return_value.generate_report.assert_called_once()
        self.assertTrue(result)
    
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_generate_strategy_report(self, mock_file, mock_json_dump, mock_makedirs):
        """Test strategy performance report generation"""
        self.mock_strategy_evaluator.return_value.generate_performance_report.return_value = True
        
        bot = TradingBot()
        result = bot.generate_strategy_report()
        
        # Verify strategy report generation is called
        self.mock_strategy_evaluator.return_value.generate_performance_report.assert_called_once()
        self.assertTrue(result)

class TestTradingBotIntegration(unittest.TestCase):
    """Integration tests for TradingBot with minimal mocking"""
    
    @patch('main.CoinbaseClient')
    @patch('main.LLMAnalyzer')
    @patch('main.DataCollector')
    @patch('main.TradingStrategy')
    @patch('main.DashboardUpdater')
    @patch('main.WebServerSync')
    @patch('main.TaxReportGenerator')
    @patch('main.StrategyEvaluator')
    @patch('main.get_supervisor_logger')
    @patch('main.os.makedirs')
    @patch('main.json.dump')
    @patch('main.open', new_callable=mock_open)
    def test_full_trading_cycle_integration(self, mock_file, mock_json_dump, mock_makedirs,
                                          mock_logger, mock_strategy_evaluator, mock_tax_report,
                                          mock_webserver, mock_dashboard, mock_trading_strategy,
                                          mock_data_collector, mock_llm, mock_coinbase):
        """Test full integration of trading cycle components"""
        
        # Configure realistic mock responses
        mock_logger.return_value = MagicMock()
        
        # Market data response
        mock_data_collector.return_value.collect_market_data.return_value = {
            'BTC-USD': {
                'price': 45000.50,
                'volume': 1500.25,
                'change_24h': 2.5,
                'rsi': 65,
                'macd': 150,
                'bollinger_upper': 46000,
                'bollinger_lower': 44000
            },
            'ETH-USD': {
                'price': 2800.75,
                'volume': 800.50,
                'change_24h': -1.2,
                'rsi': 45,
                'macd': -50,
                'bollinger_upper': 2900,
                'bollinger_lower': 2700
            }
        }
        
        # LLM analysis response
        mock_llm.return_value.analyze_market_and_decide.return_value = {
            'action': 'buy',
            'asset': 'ETH-USD',
            'confidence': 72,
            'reasoning': 'RSI indicates oversold condition with positive momentum building',
            'amount': 0.5,
            'risk_assessment': 'medium'
        }
        
        # Trading strategy response
        mock_trading_strategy.return_value.execute_trade.return_value = {
            'success': True,
            'trade_id': 'eth_buy_20240611_001',
            'amount': 0.5,
            'price': 2800.75,
            'fees': 5.60,
            'timestamp': datetime.now().isoformat()
        }
        
        # Portfolio state
        mock_trading_strategy.return_value.get_portfolio_summary.return_value = {
            'total_value_usd': 15000.00,
            'btc_amount': 0.15,
            'eth_amount': 2.5,
            'sol_amount': 50.0,
            'usd_amount': 1000.00,
            'total_return_percent': 8.5
        }
        
        # Initialize and run trading cycle
        bot = TradingBot()
        result = bot.run_trading_cycle()
        
        # Verify the complete flow
        self.assertTrue(result)
        
        # Verify data collection
        mock_data_collector.return_value.collect_market_data.assert_called_once()
        
        # Verify LLM analysis
        mock_llm.return_value.analyze_market_and_decide.assert_called_once()
        
        # Verify trade execution
        mock_trading_strategy.return_value.execute_trade.assert_called_once()
        
        # Verify dashboard update
        mock_dashboard.return_value.update_dashboard.assert_called()
        
        # Verify portfolio summary is retrieved
        mock_trading_strategy.return_value.get_portfolio_summary.assert_called()

if __name__ == '__main__':
    unittest.main()
