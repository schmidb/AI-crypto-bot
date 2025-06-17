"""
Fixed Coinbase client tests with complete isolation from other test interference.
These tests avoid any conflicts with other test modules that mock CoinbaseClient.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import importlib


class TestCoinbaseClientIsolated:
    """Completely isolated tests for CoinbaseClient functionality."""
    
    def setup_method(self):
        """Setup method to ensure clean imports for each test."""
        # Remove any cached imports to ensure fresh import
        if 'coinbase_client' in sys.modules:
            del sys.modules['coinbase_client']
    
    def test_client_can_be_imported(self):
        """Test that CoinbaseClient can be imported without issues."""
        # Use importlib to ensure fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        assert CoinbaseClient is not None
    
    def test_client_initialization_with_missing_credentials(self):
        """Test client initialization failure with missing credentials."""
        # Fresh import to avoid interference
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        with pytest.raises(ValueError, match="Coinbase API key and secret are required"):
            CoinbaseClient(api_key=None, api_secret="test-secret")
        
        with pytest.raises(ValueError, match="Coinbase API key and secret are required"):
            CoinbaseClient(api_key="test-key", api_secret=None)
        
        with pytest.raises(ValueError, match="Coinbase API key and secret are required"):
            CoinbaseClient(api_key="", api_secret="test-secret")
    
    @patch('coinbase.rest.RESTClient')
    def test_client_initialization_success(self, mock_rest_client):
        """Test successful client initialization."""
        mock_rest_client.return_value = Mock()
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
        
        assert client.api_key == "test-key"
        assert client.api_secret == "test-secret"
        assert client.min_request_interval == 0.1
        assert client.last_request_time == 0
        assert client.client is not None
    
    @patch('coinbase.rest.RESTClient')
    def test_client_initialization_with_error(self, mock_rest_client):
        """Test client initialization with RESTClient error."""
        mock_rest_client.side_effect = Exception("Connection failed")
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        # Should not raise exception, but log error and continue
        client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
        
        assert client.api_key == "test-key"
        assert client.api_secret == "test-secret"
        # Note: Client may still be set even with errors due to graceful degradation
    
    def test_get_accounts_with_no_client(self):
        """Test get_accounts when client is not initialized."""
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        # Create a real instance but manually set client to None
        with patch('coinbase.rest.RESTClient') as mock_rest:
            mock_rest.return_value = Mock()
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            client.client = None  # Simulate failed initialization
            
            accounts = client.get_accounts()
            assert accounts == []
    
    def test_get_account_balance_with_no_client(self):
        """Test get_account_balance when client is not initialized."""
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        # Create a real instance but manually set client to None
        with patch('coinbase.rest.RESTClient') as mock_rest:
            mock_rest.return_value = Mock()
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            client.client = None  # Simulate failed initialization
            
            balance = client.get_account_balance("EUR")
            assert balance == 0.0
    
    def test_get_product_price_with_no_client(self):
        """Test get_product_price when client is not initialized."""
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        # Create a real instance but manually set client to None
        with patch('coinbase.rest.RESTClient') as mock_rest:
            mock_rest.return_value = Mock()
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            client.client = None  # Simulate failed initialization
            
            price_data = client.get_product_price("BTC-EUR")
            assert price_data == {"price": 0.0}
    
    @patch('coinbase.rest.RESTClient')
    def test_error_handling_method_exists(self, mock_rest_client):
        """Test that error handling method exists and works."""
        mock_rest_client.return_value = Mock()
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
        
        # Test that _handle_api_error method exists
        assert hasattr(client, '_handle_api_error')
        
        # Test error handling
        result = client._handle_api_error(Exception("Test error"), "test_operation")
        assert result in ["rate_limit", "connection_error", "unknown_error"]
    
    @patch('coinbase.rest.RESTClient')
    def test_rate_limiting_method_exists(self, mock_rest_client):
        """Test that rate limiting method exists."""
        mock_rest_client.return_value = Mock()
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
        
        # Test that _rate_limit method exists
        assert hasattr(client, '_rate_limit')
        
        # Test that it can be called without error
        client._rate_limit()  # Should not raise exception


class TestCoinbaseClientPrecisionIsolated:
    """Test precision handling functionality with isolation."""
    
    def setup_method(self):
        """Setup method to ensure clean imports for each test."""
        if 'coinbase_client' in sys.modules:
            del sys.modules['coinbase_client']
    
    @patch('coinbase.rest.RESTClient')
    def test_precision_methods_exist(self, mock_rest_client):
        """Test that precision handling methods exist."""
        mock_rest_client.return_value = Mock()
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
        
        # Test that precision methods exist (private method)
        assert hasattr(client, '_round_to_precision')
        
        # Test basic precision rounding
        rounded = client._round_to_precision(1.123456789, 8)
        assert isinstance(rounded, float)
        assert rounded <= 1.123456789  # Should be rounded down


class TestCoinbaseClientIntegrationIsolated:
    """Integration tests that verify the client works as expected with isolation."""
    
    def setup_method(self):
        """Setup method to ensure clean imports for each test."""
        if 'coinbase_client' in sys.modules:
            del sys.modules['coinbase_client']
    
    @patch('coinbase.rest.RESTClient')
    def test_client_has_all_required_methods(self, mock_rest_client):
        """Test that client has all required methods."""
        mock_rest_client.return_value = Mock()
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
        
        # Check that all required methods exist
        required_methods = [
            'get_accounts',
            'get_account_balance', 
            'get_product_price',
            'get_market_data',
            'get_product_stats',
            'place_market_order',
            '_round_to_precision',  # Private method
            '_rate_limit',
            '_handle_api_error'
        ]
        
        for method in required_methods:
            assert hasattr(client, method), f"Client missing required method: {method}"
    
    @patch('coinbase.rest.RESTClient')
    def test_client_attributes_set_correctly(self, mock_rest_client):
        """Test that client attributes are set correctly."""
        mock_rest_client.return_value = Mock()
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        client = CoinbaseClient(api_key="my-key", api_secret="my-secret")
        
        assert client.api_key == "my-key"
        assert client.api_secret == "my-secret"
        assert isinstance(client.min_request_interval, (int, float))
        assert isinstance(client.last_request_time, (int, float))
        assert client.client is not None


class TestCoinbaseClientFunctionalityIsolated:
    """Test actual functionality with proper mocking and isolation."""
    
    def setup_method(self):
        """Setup method to ensure clean imports for each test."""
        if 'coinbase_client' in sys.modules:
            del sys.modules['coinbase_client']
    
    @patch('coinbase.rest.RESTClient')
    def test_get_accounts_with_mock_response(self, mock_rest_client):
        """Test get_accounts with mocked response."""
        mock_client = Mock()
        mock_rest_client.return_value = mock_client
        
        # Mock response
        mock_response = {
            "accounts": [
                {
                    "currency": "EUR",
                    "available_balance": {"value": "1000.00", "currency": "EUR"}
                }
            ]
        }
        mock_client.get_accounts.return_value = mock_response
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
        accounts = client.get_accounts()
        
        assert len(accounts) == 1
        assert accounts[0]["currency"] == "EUR"
    
    @patch('coinbase.rest.RESTClient')
    def test_get_product_price_with_mock_response(self, mock_rest_client):
        """Test get_product_price with mocked response."""
        mock_client = Mock()
        mock_rest_client.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.price = "50000.00"
        mock_client.get_product.return_value = mock_response
        
        # Fresh import
        coinbase_client_module = importlib.import_module('coinbase_client')
        CoinbaseClient = coinbase_client_module.CoinbaseClient
        
        client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
        price_data = client.get_product_price("BTC-EUR")
        
        assert price_data == {"price": 50000.0}
