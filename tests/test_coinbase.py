#!/usr/bin/env python3
"""
Unit tests for the Coinbase client
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coinbase_client import CoinbaseClient

class TestCoinbaseClient(unittest.TestCase):
    """Test cases for CoinbaseClient class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock client with test API keys
        with patch.object(CoinbaseClient, '__init__', return_value=None):
            self.client = CoinbaseClient()
            self.client.api_key = "test_api_key"
            self.client.api_secret = "test_api_secret"
            self.client.BASE_URL = "https://api.coinbase.com"
            self.client.ADVANCED_TRADE_URL = "https://api.coinbase.com/api/v3/brokerage"
    
    @patch('coinbase_client.requests.request')
    def test_generate_signature(self, mock_request):
        """Test signature generation for API authentication"""
        timestamp = "1622222222"
        method = "GET"
        request_path = "/products/BTC-USD/ticker"
        body = ""
        
        # Call the method
        signature = self.client._generate_signature(timestamp, method, request_path, body)
        
        # Verify signature is a base64 string
        self.assertIsInstance(signature, str)
        self.assertTrue(len(signature) > 0)
    
    @patch('coinbase_client.requests.request')
    def test_request_method(self, mock_request):
        """Test the _request method"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"price": "50000.00"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Call the method
        with patch.object(self.client, '_generate_signature', return_value="test_signature"):
            result = self.client._request("GET", "/products/BTC-USD/ticker")
        
        # Verify the result
        self.assertEqual(result, {"price": "50000.00"})
        
        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['method'], "GET")
        self.assertTrue(kwargs['url'].endswith("/products/BTC-USD/ticker"))
        self.assertIn("CB-ACCESS-KEY", kwargs['headers'])
        self.assertIn("CB-ACCESS-SIGN", kwargs['headers'])
        self.assertIn("CB-ACCESS-TIMESTAMP", kwargs['headers'])
    
    @patch('coinbase_client.requests.request')
    def test_get_product_price(self, mock_request):
        """Test getting product price"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"price": "50000.00"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Mock the _request method
        with patch.object(self.client, '_request', return_value={"price": "50000.00"}):
            result = self.client.get_product_price("BTC-USD")
        
        # Verify the result
        self.assertEqual(result, {"price": "50000.00"})
    
    @patch('coinbase_client.requests.request')
    def test_get_market_data(self, mock_request):
        """Test getting historical market data"""
        # Setup mock response
        candles_data = [
            {"start": "2023-01-01T00:00:00Z", "low": "45000", "high": "46000", "open": "45500", "close": "45800", "volume": "100"},
            {"start": "2023-01-02T00:00:00Z", "low": "45800", "high": "47000", "open": "45800", "close": "46500", "volume": "120"}
        ]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"candles": candles_data}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Mock the _request method
        with patch.object(self.client, '_request', return_value={"candles": candles_data}):
            result = self.client.get_market_data(
                product_id="BTC-USD",
                granularity="ONE_DAY",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-02T00:00:00Z"
            )
        
        # Verify the result
        self.assertEqual(result, candles_data)
        self.assertEqual(len(result), 2)
    
    @patch('coinbase_client.requests.request')
    def test_place_market_order(self, mock_request):
        """Test placing a market order"""
        # Setup mock response
        order_response = {
            "order_id": "test-order-id",
            "product_id": "BTC-USD",
            "side": "BUY",
            "status": "PENDING"
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = order_response
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Mock the _request method
        with patch.object(self.client, '_request', return_value=order_response):
            result = self.client.place_market_order(
                product_id="BTC-USD",
                side="BUY",
                size=0.1
            )
        
        # Verify the result
        self.assertEqual(result, order_response)
        self.assertEqual(result["product_id"], "BTC-USD")
        self.assertEqual(result["side"], "BUY")

if __name__ == '__main__':
    unittest.main()
