#!/usr/bin/env python3
"""
Unit tests for the data collector
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector import DataCollector

class TestDataCollector(unittest.TestCase):
    """Test cases for DataCollector class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock Coinbase client
        self.mock_coinbase = MagicMock()
        
        # Create the data collector with the mock client
        self.data_collector = DataCollector(self.mock_coinbase)
    
    def test_initialization(self):
        """Test data collector initialization"""
        self.assertEqual(self.data_collector.client, self.mock_coinbase)
    
    def test_get_historical_data(self):
        """Test getting historical data"""
        # Mock the Coinbase client response
        candles_data = [
            {"start": 1672531200, "low": 45000, "high": 46000, "open": 45500, "close": 45800, "volume": 100},
            {"start": 1672617600, "low": 45800, "high": 47000, "open": 45800, "close": 46500, "volume": 120}
        ]
        self.mock_coinbase.get_product_candles.return_value = candles_data
        
        # Call the method
        result = self.data_collector.get_historical_data(
            product_id="BTC-USD",
            granularity="ONE_DAY",
            days_back=7
        )
        
        # Verify the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('start', result.columns)
        self.assertIn('low', result.columns)
        self.assertIn('high', result.columns)
        self.assertIn('open', result.columns)
        self.assertIn('close', result.columns)
        self.assertIn('volume', result.columns)
        
        # Verify the client was called correctly
        self.mock_coinbase.get_product_candles.assert_called_once()
    
    def test_get_historical_data_empty_response(self):
        """Test getting historical data with empty response"""
        # Mock the Coinbase client to return empty data
        self.mock_coinbase.get_product_candles.return_value = []
        
        # Call the method
        result = self.data_collector.get_historical_data(
            product_id="BTC-USD",
            granularity="ONE_DAY",
            days_back=7
        )
        
        # Verify the result is an empty DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)
    
    def test_get_historical_data_error(self):
        """Test getting historical data when an error occurs"""
        # Mock the Coinbase client to raise an exception
        self.mock_coinbase.get_product_candles.side_effect = Exception("API error")
        
        # Call the method
        result = self.data_collector.get_historical_data(
            product_id="BTC-USD",
            granularity="ONE_DAY",
            days_back=7
        )
        
        # Verify the result is an empty DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)
    
    def test_get_market_data(self):
        """Test getting current market data"""
        # Mock the Coinbase client responses
        self.mock_coinbase.get_product_price.return_value = {"price": "50000.00"}
        
        # Mock the get_historical_data method
        with patch.object(self.data_collector, 'get_historical_data') as mock_get_historical:
            # Create a mock DataFrame with some data
            df = pd.DataFrame({
                'close': [49000, 49500, 50000],
                'volume': [100, 110, 120]
            })
            mock_get_historical.return_value = df
            
            # Call the method
            result = self.data_collector.get_market_data("BTC-USD")
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertEqual(result["product_id"], "BTC-USD")
        self.assertEqual(result["price"], 50000.0)
    
    def test_calculate_technical_indicators(self):
        """Test calculating technical indicators"""
        # Create a test DataFrame with enough data for calculations
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        df = pd.DataFrame({
            'start': dates,
            'close': [45000 + i * 100 for i in range(30)],
            'volume': [1000 for _ in range(30)]
        })
        
        # Call the method
        indicators = self.data_collector.calculate_technical_indicators(df)
        
        # Verify the result
        self.assertIsInstance(indicators, dict)
        self.assertIn("rsi", indicators)
        self.assertIn("macd_line", indicators)
        self.assertIn("macd_signal", indicators)
        self.assertIn("macd_histogram", indicators)
        self.assertIn("bollinger_middle", indicators)
        self.assertIn("bollinger_upper", indicators)
        self.assertIn("bollinger_lower", indicators)
        self.assertIn("market_trend", indicators)
        
        # Verify RSI is within expected range
        self.assertTrue(0 <= indicators["rsi"] <= 100)
        
        # Verify Bollinger Bands relationship
        self.assertTrue(indicators["bollinger_lower"] < indicators["bollinger_middle"] < indicators["bollinger_upper"])

if __name__ == '__main__':
    unittest.main()
