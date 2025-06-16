"""
Unit tests for Coinbase Advanced Trade API client.

This module tests the CoinbaseClient class and all API interaction functionality
to ensure proper communication with Coinbase Advanced Trade API.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from coinbase_client import CoinbaseClient


class TestCoinbaseClientInitialization:
    """Test CoinbaseClient initialization and basic setup."""
    
    def test_client_initialization_with_valid_credentials(self):
        """Test successful client initialization with valid API credentials."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            assert client.api_key == "test-key"
            assert client.api_secret == "test-secret"
            assert client.min_request_interval == 0.1
            assert client.last_request_time == 0
            assert client.client is not None
            mock_rest_client.assert_called_once_with(api_key="test-key", api_secret="test-secret")
    
    def test_client_initialization_with_missing_credentials(self):
        """Test client initialization failure with missing credentials."""
        with pytest.raises(ValueError, match="Coinbase API key and secret are required"):
            CoinbaseClient(api_key=None, api_secret="test-secret")
        
        with pytest.raises(ValueError, match="Coinbase API key and secret are required"):
            CoinbaseClient(api_key="test-key", api_secret=None)
        
        with pytest.raises(ValueError, match="Coinbase API key and secret are required"):
            CoinbaseClient(api_key="", api_secret="test-secret")
    
    def test_client_initialization_with_rest_client_error(self):
        """Test graceful handling of RESTClient initialization errors."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.side_effect = Exception("Connection failed")
            
            # Should not raise exception, but log error and set client to None
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            assert client.api_key == "test-key"
            assert client.api_secret == "test-secret"
            assert client.client is None
    
    def test_client_initialization_with_default_credentials(self):
        """Test client initialization with default credentials from config."""
        # Skip this test as it depends on actual config values
        pytest.skip("Skipping test that depends on actual config values")
    
    def test_rate_limit_enforcement(self):
        """Test that rate limiting enforces minimum interval between requests."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Mock time.sleep to verify it's called
            with patch('time.sleep') as mock_sleep:
                with patch('time.time') as mock_time:
                    # First call - no rate limiting needed
                    mock_time.return_value = 1000.0
                    client._rate_limit()
                    assert client.last_request_time == 1000.0
                    mock_sleep.assert_not_called()
                    
                    # Second call too soon - should trigger rate limiting
                    mock_time.return_value = 1000.05  # 50ms later
                    client._rate_limit()
                    # Check that sleep was called with approximately 0.05
                    mock_sleep.assert_called_once()
                    sleep_arg = mock_sleep.call_args[0][0]
                    assert abs(sleep_arg - 0.05) < 0.001  # Allow small floating point errors
    
    def test_rate_limit_no_sleep_when_interval_sufficient(self):
        """Test that rate limiting doesn't sleep when sufficient time has passed."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch('time.sleep') as mock_sleep:
                with patch('time.time') as mock_time:
                    # First call
                    mock_time.return_value = 1000.0
                    client._rate_limit()
                    
                    # Second call after sufficient time
                    mock_time.return_value = 1000.2  # 200ms later
                    client._rate_limit()
                    mock_sleep.assert_not_called()


class TestErrorHandling:
    """Test API error handling functionality."""
    
    def test_handle_rate_limit_error(self):
        """Test handling of rate limit errors."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch('time.sleep') as mock_sleep:
                error = Exception("Rate limit exceeded")
                result = client._handle_api_error(error, "test_operation")
                
                assert result == "rate_limit"
                mock_sleep.assert_called_once_with(60)
    
    def test_handle_connection_error(self):
        """Test handling of connection errors."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            connection_errors = [
                Exception("Connection timeout"),
                Exception("Connection failed"),
                Exception("Request timeout")
            ]
            
            for error in connection_errors:
                result = client._handle_api_error(error, "test_operation")
                assert result == "connection_error"
    
    def test_handle_authentication_error(self):
        """Test handling of authentication errors."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Test the first error that should work
            error = Exception("unauthorized access")
            result = client._handle_api_error(error, "test_operation")
            assert result == "auth_error"
            
            # Test authentication error
            error = Exception("authentication failed")
            result = client._handle_api_error(error, "test_operation")
            assert result == "auth_error"
    
    def test_handle_unknown_error(self):
        """Test handling of unknown errors."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            error = Exception("Some unknown error")
            result = client._handle_api_error(error, "test_operation")
            
            assert result == "unknown_error"


class TestAccountOperations:
    """Test account-related API operations."""
    
    def test_get_accounts_success_with_dict_response(self):
        """Test successful account retrieval with dictionary response format."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock response as dictionary
            mock_response = {
                "accounts": [
                    {
                        "uuid": "account-1",
                        "name": "BTC Wallet",
                        "currency": "BTC",
                        "available_balance": {"value": "0.01", "currency": "BTC"},
                        "default": False,
                        "active": True,
                        "type": "WALLET",
                        "ready": True
                    },
                    {
                        "uuid": "account-2",
                        "name": "EUR Wallet",
                        "currency": "EUR",
                        "available_balance": {"value": "1000.00", "currency": "EUR"},
                        "default": True,
                        "active": True,
                        "type": "FIAT",
                        "ready": True
                    }
                ]
            }
            mock_client.get_accounts.return_value = mock_response
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            accounts = client.get_accounts()
            
            assert len(accounts) == 2
            assert accounts[0]["currency"] == "BTC"
            assert accounts[0]["available_balance"]["value"] == "0.01"
            assert accounts[1]["currency"] == "EUR"
            assert accounts[1]["available_balance"]["value"] == "1000.00"
    
    def test_get_accounts_success_with_object_response(self):
        """Test successful account retrieval with object response format."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock response as object with attributes
            mock_account = Mock()
            mock_account.uuid = "account-1"
            mock_account.name = "BTC Wallet"
            mock_account.currency = "BTC"
            mock_account.available_balance = Mock()
            mock_account.available_balance.value = "0.01"
            mock_account.available_balance.currency = "BTC"
            mock_account.default = False
            mock_account.active = True
            mock_account.type = "WALLET"
            mock_account.ready = True
            
            mock_response = Mock()
            mock_response.accounts = [mock_account]
            mock_client.get_accounts.return_value = mock_response
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            accounts = client.get_accounts()
            
            assert len(accounts) == 1
            assert accounts[0]["currency"] == "BTC"
            assert accounts[0]["available_balance"]["value"] == "0.01"
            assert accounts[0]["uuid"] == "account-1"
    
    def test_get_accounts_with_client_not_initialized(self):
        """Test get_accounts when client is not initialized."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.side_effect = Exception("Init failed")
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            accounts = client.get_accounts()
            
            assert accounts == []
    
    def test_get_accounts_with_api_error(self):
        """Test get_accounts with API error."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            mock_client.get_accounts.side_effect = Exception("API Error")
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch.object(client, '_handle_api_error', return_value="connection_error"):
                accounts = client.get_accounts()
                assert accounts == []
    
    def test_get_account_balance_success(self):
        """Test successful account balance retrieval."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Mock get_accounts to return test data
            mock_accounts = [
                {
                    "currency": "BTC",
                    "available_balance": {"value": "0.01", "currency": "BTC"}
                },
                {
                    "currency": "EUR",
                    "available_balance": {"value": "1000.00", "currency": "EUR"}
                }
            ]
            
            with patch.object(client, 'get_accounts', return_value=mock_accounts):
                btc_balance = client.get_account_balance("BTC")
                eur_balance = client.get_account_balance("EUR")
                unknown_balance = client.get_account_balance("ETH")
                
                assert btc_balance == 0.01
                assert eur_balance == 1000.00
                assert unknown_balance == 0.0
    
    def test_get_account_balance_with_object_format(self):
        """Test account balance retrieval with object format accounts."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Mock account as object (not dict)
            mock_account = Mock()
            mock_account.currency = "BTC"
            mock_account.available_balance = Mock()
            mock_account.available_balance.value = "0.05"
            # Make sure it doesn't have 'get' method to trigger object path
            del mock_account.get
            
            with patch.object(client, 'get_accounts', return_value=[mock_account]):
                balance = client.get_account_balance("BTC")
                assert balance == 0.05
    
    def test_get_account_balance_with_error(self):
        """Test account balance retrieval with error."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch.object(client, 'get_accounts', side_effect=Exception("Error")):
                balance = client.get_account_balance("BTC")
                assert balance == 0.0


class TestMarketDataOperations:
    """Test market data retrieval operations."""
    
    def test_get_product_price_success(self):
        """Test successful product price retrieval."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock response with price attribute
            mock_response = Mock()
            mock_response.price = "50000.00"
            mock_client.get_product.return_value = mock_response
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            price_data = client.get_product_price("BTC-EUR")
            
            assert price_data == {"price": 50000.0}
            mock_client.get_product.assert_called_once_with(product_id="BTC-EUR")
    
    def test_get_product_price_with_dict_response(self):
        """Test product price retrieval with dictionary response."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock response as dictionary
            mock_response = {"price": "3000.50"}
            mock_client.get_product.return_value = mock_response
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            price_data = client.get_product_price("ETH-EUR")
            
            assert price_data == {"price": 3000.5}
    
    def test_get_product_price_with_error(self):
        """Test product price retrieval with API error."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            mock_client.get_product.side_effect = Exception("API Error")
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            price_data = client.get_product_price("BTC-EUR")
            
            assert price_data == {"price": 0.0}
    
    def test_get_market_data_success(self):
        """Test successful market data retrieval."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock candles response
            mock_candles = [
                {"timestamp": 1640995200, "low": "49000", "high": "51000", "open": "50000", "close": "50500", "volume": "100"},
                {"timestamp": 1640998800, "low": "50000", "high": "52000", "open": "50500", "close": "51500", "volume": "150"}
            ]
            mock_response = Mock()
            mock_response.candles = mock_candles
            mock_client.get_candles.return_value = mock_response
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            start_time = "2022-01-01T00:00:00Z"
            end_time = "2022-01-01T01:00:00Z"
            candles = client.get_market_data("BTC-EUR", "ONE_HOUR", start_time, end_time)
            
            assert len(candles) == 2
            assert candles[0]["close"] == "50500"
            assert candles[1]["close"] == "51500"
    
    def test_get_market_data_with_timestamp_conversion(self):
        """Test market data retrieval with timestamp conversion."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            mock_client.get_candles.return_value = Mock(candles=[])
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Test with ISO string timestamps
            start_time = "2022-01-01T00:00:00+00:00"
            end_time = "2022-01-01T01:00:00+00:00"
            client.get_market_data("BTC-EUR", "ONE_HOUR", start_time, end_time)
            
            # Verify that get_candles was called with integer timestamps
            call_args = mock_client.get_candles.call_args
            assert isinstance(call_args.kwargs['start'], int)
            assert isinstance(call_args.kwargs['end'], int)
    
    def test_get_market_data_with_error(self):
        """Test market data retrieval with API error."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            mock_client.get_candles.side_effect = Exception("API Error")
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            candles = client.get_market_data("BTC-EUR", "ONE_HOUR", "2022-01-01T00:00:00Z", "2022-01-01T01:00:00Z")
            
            assert candles == []
    
    def test_get_product_stats_success(self):
        """Test successful product statistics retrieval."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock response with stats attributes
            mock_response = Mock()
            mock_response.volume_24h = "1000.5"
            mock_response.volume_30d = "30000.0"
            mock_response.price_high_24h = "52000.0"
            mock_response.price_low_24h = "48000.0"
            mock_client.get_product.return_value = mock_response
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            stats = client.get_product_stats("BTC-EUR")
            
            expected_stats = {
                "volume": "1000.5",
                "volume_30day": "30000.0",
                "high": "52000.0",
                "low": "48000.0"
            }
            assert stats == expected_stats
    
    def test_get_product_stats_with_error(self):
        """Test product statistics retrieval with error."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            mock_client.get_product.side_effect = Exception("API Error")
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            stats = client.get_product_stats("BTC-EUR")
            
            expected_stats = {
                "volume": "0",
                "volume_30day": "0",
                "high": "0",
                "low": "0"
            }
            assert stats == expected_stats


class TestPrecisionHandling:
    """Test precision handling for different trading pairs."""
    
    def test_get_precision_limits(self):
        """Test precision limits for different trading pairs."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            precision_limits = client._get_precision_limits()
            
            # Test known precision limits
            assert precision_limits['BTC-EUR'] == 8
            assert precision_limits['BTC-USD'] == 8
            assert precision_limits['ETH-EUR'] == 6
            assert precision_limits['ETH-USD'] == 6
            assert precision_limits['SOL-EUR'] == 3
            assert precision_limits['SOL-USD'] == 3
    
    def test_round_to_precision_basic(self):
        """Test basic precision rounding functionality."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Test rounding with different precisions
            assert client._round_to_precision(1.123456789, 6) == 1.123456
            assert client._round_to_precision(1.123456789, 3) == 1.123
            # For 8 decimals, the result will be rounded down due to floating point precision
            result = client._round_to_precision(1.123456789, 8)
            assert abs(result - 1.12345678) < 0.00000001  # Allow for floating point precision
            assert client._round_to_precision(0.0, 6) == 0.0
    
    def test_round_to_precision_round_down(self):
        """Test that precision rounding always rounds down."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Test that it rounds down, not up
            assert client._round_to_precision(1.999999, 3) == 1.999
            assert client._round_to_precision(0.009999, 3) == 0.009
            assert client._round_to_precision(1.123999, 6) == 1.123999


class TestTradingOperations:
    """Test trading operations and order placement."""
    
    def test_place_market_buy_order_success(self):
        """Test successful market buy order placement."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock successful order response
            mock_response = {
                "order_id": "test-order-123",
                "status": "FILLED",
                "filled_size": "0.001",
                "filled_value": "50.00"
            }
            mock_client.market_order_buy.return_value = mock_response
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Mock notification sending
            with patch.object(client, '_send_trade_notification') as mock_notify:
                result = client.place_market_order("BTC-EUR", "BUY", 100.0, 75.0)
                
                assert result == mock_response
                mock_client.market_order_buy.assert_called_once()
                call_args = mock_client.market_order_buy.call_args
                assert call_args.kwargs['product_id'] == "BTC-EUR"
                assert call_args.kwargs['quote_size'] == "100.0"
                mock_notify.assert_called_once()
    
    def test_place_market_sell_order_success(self):
        """Test successful market sell order placement."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock successful order response
            mock_response = {
                "order_id": "test-order-124",
                "status": "FILLED",
                "filled_size": "0.001",
                "filled_value": "50.00"
            }
            mock_client.market_order_sell.return_value = mock_response
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch.object(client, '_send_trade_notification') as mock_notify:
                result = client.place_market_order("BTC-EUR", "SELL", 0.001, 80.0)
                
                assert result == mock_response
                mock_client.market_order_sell.assert_called_once()
                call_args = mock_client.market_order_sell.call_args
                assert call_args.kwargs['product_id'] == "BTC-EUR"
                assert call_args.kwargs['base_size'] == "0.001"
                mock_notify.assert_called_once()
    
    def test_place_market_sell_order_with_precision_rounding(self):
        """Test sell order with precision rounding."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            mock_client.market_order_sell.return_value = {"order_id": "test"}
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch.object(client, '_send_trade_notification'):
                # Test SOL with 3 decimal precision
                client.place_market_order("SOL-EUR", "SELL", 1.123456, 75.0)
                
                call_args = mock_client.market_order_sell.call_args
                assert call_args.kwargs['base_size'] == "1.123"  # Rounded to 3 decimals
    
    def test_place_market_sell_order_too_small_amount(self):
        """Test sell order rejection when rounded amount is too small."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Very small amount that rounds to 0
            result = client.place_market_order("BTC-EUR", "SELL", 0.000000001, 75.0)
            
            assert result["success"] is False
            assert "too small" in result["error"]
    
    def test_place_market_order_with_api_error(self):
        """Test order placement with API error."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            mock_client.market_order_buy.side_effect = Exception("Insufficient funds")
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            result = client.place_market_order("BTC-EUR", "BUY", 100.0, 75.0)
            
            assert result["success"] is False
            assert "Insufficient funds" in result["error"]
    
    def test_send_trade_notification_success(self):
        """Test successful trade notification sending (no crash)."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Mock the get_product_price to return a valid numeric price
            with patch.object(client, 'get_product_price', return_value={"price": 50000.0}):
                order_response = {"order_id": "test-order-123"}
                
                # This should not raise an exception (even if notification fails)
                try:
                    client._send_trade_notification(order_response, "BUY", "BTC-EUR", 100.0, 75.0)
                    # If we get here, the method completed without crashing
                    assert True
                except Exception as e:
                    # If there's an exception, it should be caught and logged, not raised
                    pytest.fail(f"_send_trade_notification should not raise exceptions: {e}")
    
    def test_send_trade_notification_with_error(self):
        """Test trade notification with error (should not fail trade)."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Mock the import to raise an exception
            with patch('coinbase_client.NotificationService', create=True, side_effect=Exception("Import failed")):
                # Should not raise exception
                order_response = {"order_id": "test-order-123"}
                client._send_trade_notification(order_response, "BUY", "BTC-EUR", 100.0, 75.0)


class TestCompatibilityMethods:
    """Test backward compatibility methods."""
    
    def test_get_product_candles_compatibility(self):
        """Test backward compatibility method for getting candles."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch.object(client, 'get_market_data', return_value=[{"test": "data"}]) as mock_get_market_data:
                result = client.get_product_candles("BTC-EUR", "2022-01-01T00:00:00Z", "2022-01-01T01:00:00Z", "ONE_HOUR")
                
                assert result == [{"test": "data"}]
                mock_get_market_data.assert_called_once_with("BTC-EUR", "ONE_HOUR", "2022-01-01T00:00:00Z", "2022-01-01T01:00:00Z")
    
    def test_get_product_ticker_compatibility(self):
        """Test backward compatibility method for getting ticker."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_rest_client.return_value = Mock()
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch.object(client, 'get_product_price', return_value={"price": "50000.0"}) as mock_get_price:
                result = client.get_product_ticker("BTC-EUR")
                
                assert result == {"price": "50000.0"}
                mock_get_price.assert_called_once_with("BTC-EUR")


class TestIntegrationScenarios:
    """Integration tests for complete client workflows."""
    
    def test_complete_trading_workflow(self):
        """Test complete trading workflow from account check to order placement."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock all required API responses
            mock_client.get_accounts.return_value = Mock(accounts=[
                Mock(currency="EUR", available_balance=Mock(value="1000.0"))
            ])
            mock_client.get_product.return_value = Mock(price="50000.0")
            mock_client.market_order_buy.return_value = {"order_id": "test-order", "status": "FILLED"}
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            # Complete workflow
            with patch.object(client, '_send_trade_notification'):
                # 1. Check account balance
                eur_balance = client.get_account_balance("EUR")
                assert eur_balance == 1000.0
                
                # 2. Get current price
                price_data = client.get_product_price("BTC-EUR")
                assert price_data["price"] == 50000.0
                
                # 3. Place order
                order_result = client.place_market_order("BTC-EUR", "BUY", 100.0, 75.0)
                assert order_result["order_id"] == "test-order"
    
    def test_error_recovery_workflow(self):
        """Test error recovery in trading workflow."""
        with patch('coinbase_client.RESTClient') as mock_rest_client:
            mock_client = Mock()
            mock_rest_client.return_value = mock_client
            
            # Mock API errors
            mock_client.get_accounts.side_effect = Exception("Rate limit exceeded")
            
            client = CoinbaseClient(api_key="test-key", api_secret="test-secret")
            
            with patch.object(client, '_handle_api_error', return_value="rate_limit"):
                accounts = client.get_accounts()
                assert accounts == []  # Should return empty list, not crash
