"""
Unit tests for TradeLogger - Critical trading component
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

from utils.trading.trade_logger import TradeLogger


class TestTradeLoggerInitialization:
    """Test TradeLogger initialization."""
    
    def test_trade_logger_initialization_default(self):
        """Test TradeLogger initializes with default log file."""
        with patch('os.makedirs'):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = mock_open.return_value
                trade_logger = TradeLogger()
                
                assert trade_logger.log_file == "data/trades/trade_history.json"
                # TradeLogger uses module-level logger, not instance attribute
    
    def test_trade_logger_initialization_custom_file(self):
        """Test TradeLogger initializes with custom log file."""
        custom_file = "custom/path/trades.json"
        
        with patch('os.makedirs'):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = mock_open.return_value
                trade_logger = TradeLogger(custom_file)
                
                assert trade_logger.log_file == custom_file


class TestTradeLogging:
    """Test trade logging functionality."""
    
    def setup_method(self):
        """Set up test fixtures with temporary file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        with patch('os.makedirs'):
            self.trade_logger = TradeLogger(self.temp_file.name)
    
    def teardown_method(self):
        """Clean up temporary file."""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_log_trade_basic(self):
        """Test basic trade logging."""
        decision_result = {
            'action': 'BUY',
            'confidence': 75.5,
            'reasoning': 'Strong uptrend detected'
        }
        
        trade_result = {
            'trade_executed': True,
            'execution_price': 45000.0,
            'crypto_amount': 0.001,
            'trade_amount_base': 45.0,
            'execution_status': 'executed',
            'action': 'BUY',  # TradeLogger uses action from result, not decision
            'status': 'executed'
        }
        
        # Log the trade
        self.trade_logger.log_trade('BTC-EUR', decision_result, trade_result)
        
        # Verify trade was logged
        trades = self.trade_logger.get_recent_trades(1)
        assert len(trades) == 1
        
        logged_trade = trades[0]
        assert logged_trade['product_id'] == 'BTC-EUR'
        assert logged_trade['action'] == 'BUY'
        assert logged_trade['confidence'] == 75.5
        assert logged_trade['price'] == 45000.0
        assert logged_trade['status'] == 'executed'
    
    def test_log_trade_hold_decision(self):
        """Test logging HOLD decisions."""
        decision_result = {
            'action': 'HOLD',
            'confidence': 45.0,
            'reasoning': 'Unclear market direction'
        }
        
        trade_result = {
            'trade_executed': False,
            'execution_price': 45000.0,
            'execution_status': 'skipped_hold',
            'action': 'HOLD',  # TradeLogger uses action from result
            'status': 'hold'
        }
        
        self.trade_logger.log_trade('BTC-EUR', decision_result, trade_result)
        
        trades = self.trade_logger.get_recent_trades(1)
        assert len(trades) == 1
        assert trades[0]['action'] == 'HOLD'
        assert trades[0]['status'] == 'hold'
    
    def test_log_trade_failed_execution(self):
        """Test logging failed trade executions."""
        decision_result = {
            'action': 'BUY',
            'confidence': 80.0,
            'reasoning': 'Strong buy signal'
        }
        
        trade_result = {
            'trade_executed': False,
            'execution_price': 45000.0,
            'execution_status': 'insufficient_base',
            'execution_message': 'Insufficient EUR balance',
            'action': 'BUY',  # TradeLogger uses action from result
            'status': 'attempted'
        }
        
        self.trade_logger.log_trade('BTC-EUR', decision_result, trade_result)
        
        trades = self.trade_logger.get_recent_trades(1)
        assert len(trades) == 1
        assert trades[0]['action'] == 'BUY'
        assert trades[0]['status'] == 'attempted'
        assert 'insufficient' in trades[0]['execution_message'].lower()


class TestTradeRetrieval:
    """Test trade retrieval functionality."""
    
    def setup_method(self):
        """Set up test fixtures with sample trades."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        with patch('os.makedirs'):
            self.trade_logger = TradeLogger(self.temp_file.name)
        
        # Add sample trades
        for i in range(5):
            decision = {
                'action': 'BUY' if i % 2 == 0 else 'SELL',
                'confidence': 70.0 + i,
                'reasoning': f'Test trade {i}'
            }
            
            result = {
                'trade_executed': True,
                'execution_price': 45000.0 + i * 100,
                'crypto_amount': 0.001,
                'trade_amount_base': 45.0 + i,
                'execution_status': 'executed'
            }
            
            self.trade_logger.log_trade(f'BTC-EUR', decision, result)
    
    def teardown_method(self):
        """Clean up temporary file."""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_get_recent_trades_limit(self):
        """Test getting recent trades with limit."""
        # Get last 3 trades
        recent_trades = self.trade_logger.get_recent_trades(3)
        
        assert len(recent_trades) == 3
        
        # Should be in reverse chronological order (newest first)
        assert recent_trades[0]['confidence'] == 74.0  # Last trade
        assert recent_trades[1]['confidence'] == 73.0  # Second to last
        assert recent_trades[2]['confidence'] == 72.0  # Third to last
    
    def test_get_recent_trades_all(self):
        """Test getting all recent trades."""
        all_trades = self.trade_logger.get_recent_trades(100)  # More than available
        
        assert len(all_trades) == 5  # Should return all 5 trades
    
    def test_get_recent_trades_empty_file(self):
        """Test getting trades from empty file."""
        # Create new logger with empty file
        empty_temp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        empty_temp.close()
        
        try:
            with patch('os.makedirs'):
                empty_logger = TradeLogger(empty_temp.name)
            
            trades = empty_logger.get_recent_trades(10)
            assert trades == []
            
        finally:
            os.unlink(empty_temp.name)


class TestTradeFiltering:
    """Test trade filtering functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        with patch('os.makedirs'):
            self.trade_logger = TradeLogger(self.temp_file.name)
    
    def teardown_method(self):
        """Clean up temporary file."""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_filter_by_product_id(self):
        """Test filtering trades by product ID."""
        # Add trades for different products
        products = ['BTC-EUR', 'ETH-EUR', 'BTC-EUR', 'SOL-EUR']
        
        for i, product in enumerate(products):
            decision = {'action': 'BUY', 'confidence': 70.0, 'reasoning': 'Test'}
            result = {
                'trade_executed': True, 
                'execution_price': 1000.0, 
                'execution_status': 'executed',
                'action': 'BUY',
                'status': 'executed'
            }
            self.trade_logger.log_trade(product, decision, result)
        
        # Filter for BTC-EUR trades (method doesn't accept limit parameter)
        btc_trades = self.trade_logger.get_trades_by_product('BTC-EUR')
        
        assert len(btc_trades) == 2
        for trade in btc_trades:
            assert trade['product_id'] == 'BTC-EUR'
    
    def test_filter_by_action(self):
        """Test filtering trades by action (manual filtering since method doesn't exist)."""
        # Add mixed trades
        actions = ['BUY', 'SELL', 'HOLD', 'BUY']
        
        for action in actions:
            decision = {'action': action, 'confidence': 70.0, 'reasoning': 'Test'}
            result = {
                'trade_executed': action != 'HOLD', 
                'execution_price': 1000.0, 
                'execution_status': 'executed',
                'action': action,
                'status': 'executed' if action != 'HOLD' else 'hold'
            }
            self.trade_logger.log_trade('BTC-EUR', decision, result)
        
        # Get all trades and filter manually (since get_trades_by_action doesn't exist)
        all_trades = self.trade_logger.get_recent_trades(10)
        buy_trades = [trade for trade in all_trades if trade['action'] == 'BUY']
        
        assert len(buy_trades) == 2
        for trade in buy_trades:
            assert trade['action'] == 'BUY'


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_log_file_path(self):
        """Test handling of invalid log file path."""
        invalid_path = "/invalid/path/that/does/not/exist/trades.json"
        
        # Should handle gracefully with os.makedirs patch
        with patch('os.makedirs', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                TradeLogger(invalid_path)
    
    def test_corrupted_log_file(self):
        """Test handling of corrupted log file."""
        # Create corrupted JSON file
        corrupted_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        corrupted_file.write("invalid json content {")
        corrupted_file.close()
        
        try:
            with patch('os.makedirs'):
                trade_logger = TradeLogger(corrupted_file.name)
            
            # Should handle corrupted file gracefully
            trades = trade_logger.get_recent_trades(10)
            assert trades == []  # Should return empty list
            
        finally:
            os.unlink(corrupted_file.name)
    
    def test_missing_trade_data(self):
        """Test handling of missing trade data."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        
        try:
            with patch('os.makedirs'):
                trade_logger = TradeLogger(temp_file.name)
            
            # Log trade with missing data
            incomplete_decision = {'action': 'BUY'}  # Missing confidence, reasoning
            incomplete_result = {
                'trade_executed': True,
                'action': 'BUY'  # TradeLogger needs action in result
            }  # Missing price, amounts
            
            # Should handle gracefully without crashing
            trade_logger.log_trade('BTC-EUR', incomplete_decision, incomplete_result)
            
            trades = trade_logger.get_recent_trades(1)
            assert len(trades) == 1
            assert trades[0]['action'] == 'BUY'
            
        finally:
            os.unlink(temp_file.name)


class TestPerformanceMetrics:
    """Test performance-related functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        with patch('os.makedirs'):
            self.trade_logger = TradeLogger(self.temp_file.name)
    
    def teardown_method(self):
        """Clean up temporary file."""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_trade_statistics(self):
        """Test calculation of trade statistics (manual calculation since method doesn't exist)."""
        # Add sample trades with different outcomes
        trades_data = [
            ('BUY', True, 100.0),   # Successful buy
            ('SELL', True, 150.0),  # Successful sell
            ('BUY', False, 0.0),    # Failed buy
            ('HOLD', False, 0.0),   # Hold decision
        ]
        
        for action, executed, amount in trades_data:
            decision = {'action': action, 'confidence': 70.0, 'reasoning': 'Test'}
            result = {
                'trade_executed': executed,
                'execution_price': 45000.0,
                'trade_amount_base': amount,
                'execution_status': 'executed' if executed else 'failed',
                'action': action,
                'status': 'executed' if executed else ('hold' if action == 'HOLD' else 'failed')
            }
            self.trade_logger.log_trade('BTC-EUR', decision, result)
        
        # Calculate statistics manually (since get_trade_statistics doesn't exist)
        all_trades = self.trade_logger.get_recent_trades(10)
        
        stats = {
            'total_trades': len(all_trades),
            'successful_trades': len([t for t in all_trades if t.get('status') == 'executed']),
            'failed_trades': len([t for t in all_trades if t.get('status') in ['failed', 'hold']])
        }
        
        assert isinstance(stats, dict)
        assert 'total_trades' in stats
        assert 'successful_trades' in stats
        assert 'failed_trades' in stats
        assert stats['total_trades'] == 4
        assert stats['successful_trades'] == 2  # 2 executed trades
        assert stats['failed_trades'] == 2     # 1 failed + 1 hold