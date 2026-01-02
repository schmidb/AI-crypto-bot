"""
Unit tests for NotificationService - Critical alert system
"""

import pytest
import os
from unittest.mock import patch, MagicMock, Mock
import requests

from utils.notification_service import NotificationService


class TestNotificationServiceInitialization:
    """Test NotificationService initialization."""
    
    def test_notification_service_initialization_disabled(self):
        """Test initialization when notifications are disabled."""
        with patch('utils.notification_service.config') as mock_config:
            mock_config.NOTIFICATIONS_ENABLED = False
            mock_config.PUSHOVER_TOKEN = None
            mock_config.PUSHOVER_USER = None
            
            service = NotificationService()
            
            assert service.notifications_enabled is False
            assert service.pushover_token is None
            assert service.pushover_user is None
    
    def test_notification_service_initialization_enabled(self):
        """Test initialization when notifications are enabled."""
        with patch('utils.notification_service.config') as mock_config:
            mock_config.NOTIFICATIONS_ENABLED = True
            mock_config.PUSHOVER_TOKEN = 'test-token'
            mock_config.PUSHOVER_USER = 'test-user'
            
            service = NotificationService()
            
            assert service.notifications_enabled is True
            assert service.pushover_token == 'test-token'
            assert service.pushover_user == 'test-user'
    
    def test_notification_service_missing_credentials(self):
        """Test initialization with missing credentials."""
        with patch('utils.notification_service.config') as mock_config:
            mock_config.NOTIFICATIONS_ENABLED = True
            mock_config.PUSHOVER_TOKEN = None
            mock_config.PUSHOVER_USER = None
            
            service = NotificationService()
            
            # Should be disabled due to missing credentials
            assert service.notifications_enabled is False
            assert service.pushover_token is None
            assert service.pushover_user is None


class TestStatusNotifications:
    """Test status notification functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config_patcher = patch('utils.notification_service.config')
        mock_config = self.mock_config_patcher.start()
        mock_config.NOTIFICATIONS_ENABLED = True
        mock_config.PUSHOVER_TOKEN = 'test-token'
        mock_config.PUSHOVER_USER = 'test-user'
        
        self.service = NotificationService()
    
    def teardown_method(self):
        """Clean up patches."""
        self.mock_config_patcher.stop()
    
    @patch('requests.post')
    def test_send_status_notification_success(self, mock_post):
        """Test successful status notification."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 1}
        mock_post.return_value = mock_response
        
        result = self.service.send_status_notification("Test status message")
        
        assert result is True
        mock_post.assert_called_once()
        
        # Check API call parameters
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.pushover.net/1/messages.json"
        assert 'token' in call_args[1]['data']
        assert 'user' in call_args[1]['data']
        assert call_args[1]['data']['message'] == "Test status message\n\n⏰ Time: " + call_args[1]['data']['message'].split("⏰ Time: ")[1]
    
    @patch('requests.post')
    def test_send_status_notification_failure(self, mock_post):
        """Test failed status notification."""
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'errors': ['Invalid token']}
        mock_post.return_value = mock_response
        
        result = self.service.send_status_notification("Test message")
        
        assert result is False
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_status_notification_network_error(self, mock_post):
        """Test status notification with network error."""
        # Mock network error
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        result = self.service.send_status_notification("Test message")
        
        assert result is False
        mock_post.assert_called_once()
    
    def test_send_status_notification_disabled(self):
        """Test status notification when service is disabled."""
        with patch('utils.notification_service.config') as mock_config:
            mock_config.NOTIFICATIONS_ENABLED = False
            mock_config.PUSHOVER_TOKEN = None
            mock_config.PUSHOVER_USER = None
            
            disabled_service = NotificationService()
            result = disabled_service.send_status_notification("Test message")
            
            assert result is False


class TestTradingNotifications:
    """Test trading-specific notifications."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config_patcher = patch('utils.notification_service.config')
        mock_config = self.mock_config_patcher.start()
        mock_config.NOTIFICATIONS_ENABLED = True
        mock_config.PUSHOVER_TOKEN = 'test-token'
        mock_config.PUSHOVER_USER = 'test-user'
        
        self.service = NotificationService()
    
    def teardown_method(self):
        """Clean up patches."""
        self.mock_config_patcher.stop()
    
    @patch('requests.post')
    def test_send_trade_notification_buy(self, mock_post):
        """Test BUY trading notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 1}
        mock_post.return_value = mock_response
        
        trade_data = {
            'action': 'BUY',
            'product_id': 'BTC-EUR',
            'amount': 0.001,
            'price': 45000.0,
            'total_value': 45.0,
            'confidence': 75.5
        }
        
        result = self.service.send_trade_notification(trade_data)
        
        assert result is True
        
        # Check message content
        call_args = mock_post.call_args
        message = call_args[1]['data']['message']
        assert "BUY" in message
        assert "BTC-EUR" in message
        assert "0.001" in message
        assert "45000" in message
        assert "75.5" in message
    
    @patch('requests.post')
    def test_send_trade_notification_sell(self, mock_post):
        """Test SELL trading notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 1}
        mock_post.return_value = mock_response
        
        trade_data = {
            'action': 'SELL',
            'product_id': 'ETH-EUR',
            'amount': 0.1,
            'price': 2800.0,
            'total_value': 280.0,
            'confidence': 68.2
        }
        
        result = self.service.send_trade_notification(trade_data)
        
        assert result is True
        
        call_args = mock_post.call_args
        message = call_args[1]['data']['message']
        assert "SELL" in message
        assert "ETH-EUR" in message


class TestErrorNotifications:
    """Test error notification functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config_patcher = patch('utils.notification_service.config')
        mock_config = self.mock_config_patcher.start()
        mock_config.NOTIFICATIONS_ENABLED = True
        mock_config.PUSHOVER_TOKEN = 'test-token'
        mock_config.PUSHOVER_USER = 'test-user'
        
        self.service = NotificationService()
    
    def teardown_method(self):
        """Clean up patches."""
        self.mock_config_patcher.stop()
    
    @patch('requests.post')
    def test_send_error_notification(self, mock_post):
        """Test error notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 1}
        mock_post.return_value = mock_response
        
        result = self.service.send_error_notification(
            "API connection failed",
            "Coinbase API returned 500 error"
        )
        
        assert result is True
        
        # Check that error notifications have high priority
        call_args = mock_post.call_args
        priority = call_args[1]['data'].get('priority', 0)
        assert priority >= 1  # Should be high priority
        
        # Check message content
        message = call_args[1]['data']['message']
        assert "API connection failed" in message
        assert "Coinbase API returned 500 error" in message


class TestTestNotification:
    """Test the test notification functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config_patcher = patch('utils.notification_service.config')
        mock_config = self.mock_config_patcher.start()
        mock_config.NOTIFICATIONS_ENABLED = True
        mock_config.PUSHOVER_TOKEN = 'test-token'
        mock_config.PUSHOVER_USER = 'test-user'
        
        self.service = NotificationService()
    
    def teardown_method(self):
        """Clean up patches."""
        self.mock_config_patcher.stop()
    
    @patch('requests.post')
    def test_test_notification_success(self, mock_post):
        """Test successful test notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 1}
        mock_post.return_value = mock_response
        
        result = self.service.test_notification()
        
        assert result is True
        mock_post.assert_called_once()
        
        # Check message content
        call_args = mock_post.call_args
        message = call_args[1]['data']['message']
        assert "test notification" in message.lower()
        assert "verify" in message.lower()
    
    def test_test_notification_disabled(self):
        """Test test notification when service is disabled."""
        with patch('utils.notification_service.config') as mock_config:
            mock_config.NOTIFICATIONS_ENABLED = False
            mock_config.PUSHOVER_TOKEN = None
            mock_config.PUSHOVER_USER = None
            
            disabled_service = NotificationService()
            result = disabled_service.test_notification()
            
            assert result is False


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_missing_credentials_handling(self):
        """Test handling when credentials are missing."""
        with patch('utils.notification_service.config') as mock_config:
            mock_config.NOTIFICATIONS_ENABLED = True
            mock_config.PUSHOVER_TOKEN = None
            mock_config.PUSHOVER_USER = None
            
            service = NotificationService()
            
            # Should return False when credentials are missing
            result = service.send_status_notification("Test")
            assert result is False
    
    def test_empty_message_handling(self):
        """Test handling of empty messages."""
        with patch('utils.notification_service.config') as mock_config:
            mock_config.NOTIFICATIONS_ENABLED = True
            mock_config.PUSHOVER_TOKEN = 'test-token'
            mock_config.PUSHOVER_USER = 'test-user'
            
            service = NotificationService()
            
            # Should handle empty message gracefully
            result = service.send_status_notification("")
            assert result is False  # Should reject empty messages
    
    def test_none_message_handling(self):
        """Test handling of None messages."""
        with patch('utils.notification_service.config') as mock_config:
            mock_config.NOTIFICATIONS_ENABLED = True
            mock_config.PUSHOVER_TOKEN = 'test-token'
            mock_config.PUSHOVER_USER = 'test-user'
            
            service = NotificationService()
            
            # Should handle None message gracefully
            result = service.send_status_notification(None)
            assert result is False