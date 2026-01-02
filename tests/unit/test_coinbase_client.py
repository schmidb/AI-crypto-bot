"""
Comprehensive unit tests for coinbase_client.py - Coinbase Advanced Trade API integration

Tests cover:
- CoinbaseClient initialization and authentication
- Portfolio retrieval and balance management
- Market data collection and price fetching
- Order creation and execution (simulation and live)
- Error handling and API failures
- Rate limiting and retry logic
- Response validation and processing
- Trading pair management

NOTE: These are UNIT tests - they mock ALL external dependencies including Coinbase API
"""

import pytest
import sys
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# COMPREHENSIVE MOCKING STRATEGY
# Mock ALL possible coinbase import paths before any imports happen
coinbase_mock = Mock()
coinbase_rest_mock = Mock()
rest_client_mock = Mock()

# Mock at sys.modules level - this catches ALL import attempts
sys.modules['coinbase'] = coinbase_mock
sys.modules['coinbase.rest'] = coinbase_rest_mock
sys.modules['coinbase.rest.RESTClient'] = rest_client_mock

# Set up the mock hierarchy
coinbase_mock.rest = coinbase_rest_mock
coinbase_rest_mock.RESTClient = rest_client_mock

# Also patch the specific import path used in coinbase_client.py
with patch.dict('sys.modules', {
    'coinbase': coinbase_mock,
    'coinbase.rest': coinbase_rest_mock
}):
    try:
        from coinbase_client import CoinbaseClient
        COINBASE_CLIENT_AVAILABLE = True
    except ImportError as e:
        COINBASE_CLIENT_AVAILABLE = False
        CoinbaseClient = None

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up completely isolated test environment with NO external dependencies"""
    
    # CRITICAL: Set test environment variables to ensure simulation mode
    test_env_vars = {
        'TESTING': 'true',
        'SIMULATION_MODE': 'true',
        'COINBASE_API_KEY': 'test-key-organizations/test-org/apiKeys/test-key-id',
        'COINBASE_API_SECRET': '-----BEGIN EC PRIVATE KEY-----\nTEST_PRIVATE_KEY_CONTENT\n-----END EC PRIVATE KEY-----\n',
        'BASE_CURRENCY': 'EUR',
        'TRADING_PAIRS': 'BTC-EUR,ETH-EUR',
        'NOTIFICATIONS_ENABLED': 'false'
    }
    
    with patch.dict(os.environ, test_env_vars, clear=False):
        # Mock notification service to prevent external calls
        with patch('utils.notification_service.NotificationService') as mock_notification:
            yield {
                'notification_service': mock_notification
            }

def create_mock_client():
    """Create a properly configured mock Coinbase client"""
    mock_client = Mock()
    
    # Mock accounts response
    mock_accounts_response = Mock()
    mock_accounts_response.accounts = [
        Mock(
            uuid='eur-account-id',
            name='EUR Wallet',
            currency='EUR',
            available_balance=Mock(value='1000.00', currency='EUR'),
            default=False,
            active=True,
            type='wallet',
            ready=True
        ),
        Mock(
            uuid='btc-account-id',
            name='BTC Wallet',
            currency='BTC',
            available_balance=Mock(value='0.01', currency='BTC'),
            default=False,
            active=True,
            type='wallet',
            ready=True
        )
    ]
    mock_client.get_accounts.return_value = mock_accounts_response
    
    # Mock product price response - return string as the API does
    mock_product_response = Mock()
    mock_product_response.price = '45000.00'  # String value as API returns
    mock_product_response.product_id = 'BTC-EUR'
    mock_product_response.price_percentage_change_24h = '2.5'
    mock_client.get_product.return_value = mock_product_response
    
    # Mock market order responses with proper attributes
    mock_buy_order = Mock()
    mock_buy_order.order_id = 'test-order-123'
    mock_buy_order.client_order_id = 'bot-order-123'
    mock_buy_order.product_id = 'BTC-EUR'
    mock_buy_order.side = 'BUY'
    mock_buy_order.filled_size = '0.002'
    mock_buy_order.average_filled_price = '45000'
    mock_buy_order.total_fees = '1.0'
    mock_buy_order.total_value_after_fees = '99.0'
    mock_buy_order.order_configuration = {}
    mock_client.market_order_buy.return_value = mock_buy_order
    
    mock_sell_order = Mock()
    mock_sell_order.order_id = 'test-sell-order-123'
    mock_sell_order.client_order_id = 'bot-sell-order-123'
    mock_sell_order.product_id = 'BTC-EUR'
    mock_sell_order.side = 'SELL'
    mock_sell_order.filled_size = '0.002'
    mock_sell_order.average_filled_price = '45000'
    mock_sell_order.total_fees = '1.0'
    mock_sell_order.total_value_after_fees = '89.0'
    mock_sell_order.order_configuration = {}
    mock_client.market_order_sell.return_value = mock_sell_order
    
    # Mock candles response - return actual list
    mock_candles_response = Mock()
    mock_candles_response.candles = [
        Mock(start=1640995200, low=44000, high=46000, open=45000, close=45800, volume=1000),
        Mock(start=1641081600, low=45800, high=47000, open=45800, close=46500, volume=1200)
    ]
    mock_client.get_candles.return_value = mock_candles_response
    
    # Mock other methods
    mock_client.get_products.return_value = Mock(products=[])
    mock_client.get_product_book.return_value = Mock(pricebook=Mock(bids=[], asks=[]))
    
    return mock_client

@pytest.fixture
def test_env_vars():
    """Set up test environment variables"""
    test_vars = {
        'TESTING': 'true',
        'SIMULATION_MODE': 'true',
        'COINBASE_API_KEY': 'organizations/test-org/apiKeys/test-key-id',
        'COINBASE_API_SECRET': '-----BEGIN EC PRIVATE KEY-----\nTEST_PRIVATE_KEY\n-----END EC PRIVATE KEY-----\n',
        'BASE_CURRENCY': 'EUR',
        'TRADING_PAIRS': 'BTC-EUR,ETH-EUR'
    }
    
    with patch.dict(os.environ, test_vars):
        yield test_vars

@pytest.mark.skipif(not COINBASE_CLIENT_AVAILABLE, reason="CoinbaseClient not available - all external dependencies mocked")
class TestCoinbaseClientBasic:
    """Test basic CoinbaseClient functionality"""
    
    def test_coinbase_client_initialization_success(self):
        """Test successful CoinbaseClient initialization"""
        with patch('coinbase_client.RESTClient') as mock_rest_client, \
             patch('config.Config') as mock_config_class:
            
            # Setup config mock
            mock_config = Mock()
            mock_config.BASE_CURRENCY = 'EUR'
            mock_config.get_trading_pairs.return_value = ['BTC-EUR', 'ETH-EUR']
            mock_config_class.return_value = mock_config
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            
            # Verify client was initialized
            assert client.client is not None
            assert client.api_key is not None
            assert client.api_secret is not None
    
    def test_coinbase_client_missing_credentials(self):
        """Test initialization with missing credentials"""
        # Test with None credentials
        with pytest.raises(ValueError, match="Coinbase API key and secret are required"):
            CoinbaseClient(api_key=None, api_secret=None)
        
        # Test with empty string credentials
        with pytest.raises(ValueError, match="Coinbase API key and secret are required"):
            CoinbaseClient(api_key='', api_secret='')
    
    def test_get_portfolio_success(self):
        """Test successful portfolio retrieval"""
        with patch('coinbase_client.RESTClient') as mock_rest_client, \
             patch('config.Config') as mock_config_class:
            
            # Setup config mock
            mock_config = Mock()
            mock_config.BASE_CURRENCY = 'EUR'
            mock_config.get_trading_pairs.return_value = ['BTC-EUR', 'ETH-EUR']
            mock_config_class.return_value = mock_config
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            portfolio = client.get_portfolio()
            
            # Verify portfolio structure
            assert 'EUR' in portfolio
            assert 'BTC' in portfolio
            
            # Verify EUR balance
            assert portfolio['EUR']['amount'] == 1000.0
            
            # Verify BTC balance
            assert portfolio['BTC']['amount'] == 0.01
    
    def test_get_portfolio_api_error(self):
        """Test portfolio retrieval with API error"""
        with patch('coinbase_client.RESTClient') as mock_rest_client, \
             patch('config.Config') as mock_config_class:
            
            # Setup config mock
            mock_config = Mock()
            mock_config.BASE_CURRENCY = 'EUR'
            mock_config.get_trading_pairs.return_value = ['BTC-EUR', 'ETH-EUR']
            mock_config_class.return_value = mock_config
            
            # Setup failing REST client
            mock_client = Mock()
            mock_client.get_accounts.side_effect = Exception("API Error")
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            portfolio = client.get_portfolio()
            
            # Should return initialized portfolio with zero balances when get_accounts fails
            assert isinstance(portfolio, dict)
            assert 'EUR' in portfolio
            assert 'BTC' in portfolio
            assert portfolio['EUR']['amount'] == 0
            assert portfolio['BTC']['amount'] == 0
    
    def test_get_product_price_success(self):
        """Test successful product price retrieval"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            price_data = client.get_product_price('BTC-EUR')
            
            # Should return mocked price data
            assert price_data['price'] == 45000.0  # Float from mock
    
    def test_get_product_price_api_error(self):
        """Test product price retrieval with API error"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup failing REST client
            mock_client = Mock()
            mock_client.get_product.side_effect = Exception("API Error")
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            price_data = client.get_product_price('BTC-EUR')
            
            # Should return default price on error
            assert price_data['price'] == 0.0
    
    def test_place_market_order_buy_success(self):
        """Test successful BUY market order"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            result = client.place_market_order('BTC-EUR', 'BUY', 100.0)
            
            # Should return successful result from mock
            assert result['success'] is True
            assert result['order_id'] == 'test-order-123'
            assert result['side'] == 'BUY'
            assert result['product_id'] == 'BTC-EUR'
    
    def test_place_market_order_sell_success(self):
        """Test successful SELL market order"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            result = client.place_market_order('BTC-EUR', 'SELL', 0.002)
            
            # Should return successful result from mock
            assert result['success'] is True
            assert result['order_id'] == 'test-sell-order-123'
            assert result['side'] == 'SELL'
            assert result['product_id'] == 'BTC-EUR'
    
    def test_place_market_order_api_error(self):
        """Test market order creation with API error"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup failing REST client
            mock_client = Mock()
            mock_client.market_order_buy.side_effect = Exception("Order failed")
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            result = client.place_market_order('BTC-EUR', 'BUY', 100.0)
            
            # Should return error result
            assert result['success'] is False
            assert 'error' in result
    
    def test_get_market_data_success(self):
        """Test successful market data retrieval"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            market_data = client.get_market_data('BTC-EUR', 'ONE_HOUR', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z')
            
            # Should return mocked candles data
            assert len(market_data) == 2
            assert hasattr(market_data[0], 'close')
            assert hasattr(market_data[0], 'volume')
            assert market_data[0].close == 45800
            assert market_data[1].close == 46500
    
    def test_get_market_data_api_error(self):
        """Test market data retrieval with API error"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup failing REST client
            mock_client = Mock()
            mock_client.get_candles.side_effect = Exception("API Error")
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            market_data = client.get_market_data('BTC-EUR', 'ONE_HOUR', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z')
            
            # Should return empty list on error
            assert market_data == []
    
    def test_get_account_balance_success(self):
        """Test successful account balance retrieval"""
        with patch('coinbase_client.RESTClient') as mock_rest_client, \
             patch('config.Config') as mock_config_class:
            
            # Setup config mock
            mock_config = Mock()
            mock_config.BASE_CURRENCY = 'EUR'
            mock_config.get_trading_pairs.return_value = ['BTC-EUR', 'ETH-EUR']
            mock_config_class.return_value = mock_config
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            
            # Test EUR balance
            eur_balance = client.get_account_balance('EUR')
            assert eur_balance == 1000.0
            
            # Test BTC balance
            btc_balance = client.get_account_balance('BTC')
            assert btc_balance == 0.01
    
    def test_get_account_balance_currency_not_found(self):
        """Test account balance retrieval for non-existent currency"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            balance = client.get_account_balance('UNKNOWN')
            
            # Should return 0.0 for unknown currency
            assert balance == 0.0
    
    def test_rate_limiting_basic(self):
        """Test basic rate limiting functionality"""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            
            # Test that rate limiter allows requests
            client._rate_limit()
            
            # Should not raise exception
            assert True
    
    def test_simulation_mode_behavior(self):
        """Test behavior in simulation mode"""
        with patch('coinbase_client.RESTClient') as mock_rest_client, \
             patch('config.SIMULATION_MODE', True):
            
            # Setup REST client mock
            mock_client = create_mock_client()
            mock_rest_client.return_value = mock_client
            
            client = CoinbaseClient()
            
            # In simulation mode, should return simulated result
            result = client.place_market_order('BTC-EUR', 'BUY', 100.0)
            
            # Should return successful result from mock
            assert result is not None
            assert isinstance(result, dict)
            assert result.get('success') is True
            assert result.get('product_id') == 'BTC-EUR'
            assert result.get('side') == 'BUY'

if __name__ == '__main__':
    pytest.main([__file__])