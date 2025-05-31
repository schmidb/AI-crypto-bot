#!/usr/bin/env python3
"""
Unit tests for the trading strategy
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import sys
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_strategy import TradingStrategy
from data_collector import DataCollector

class TestTradingStrategy(unittest.TestCase):
    """Test cases for TradingStrategy class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mock objects
        self.mock_coinbase = MagicMock()
        self.mock_llm_analyzer = MagicMock()
        self.mock_data_collector = MagicMock()
        
        # Configure mocks to return appropriate values
        market_data = {
            "product_id": "BTC-USD",
            "price": 50000.0,
            "market_trend": "bullish",
            "rsi": 30,
            "volatility_24h": 2.5
        }
        self.mock_data_collector.get_market_data.return_value = market_data
        
        # Mock historical data with proper structure
        historical_data = pd.DataFrame({
            'start': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
            'open': [49000, 50000],
            'high': [51000, 52000],
            'low': [48000, 49000],
            'close': [50000, 51000],
            'volume': [100, 120]
        })
        self.mock_data_collector.get_historical_data.return_value = historical_data
        
        # Mock technical indicators
        indicators = {
            "rsi": 30,
            "macd_line": 100,
            "macd_signal": 50,
            "macd_histogram": 50,
            "bollinger_middle": 50000,
            "bollinger_upper": 52000,
            "bollinger_lower": 48000,
            "bollinger_width": 0.08,
            "market_trend": "bullish"
        }
        self.mock_data_collector.calculate_technical_indicators.return_value = indicators
        
        # Mock LLM analyzer to return a decision
        llm_decision = {
            "decision": "BUY",
            "confidence": 85,
            "reasoning": ["RSI is oversold", "Market trend is bullish"]
        }
        self.mock_llm_analyzer.analyze_market.return_value = llm_decision
        
        # Create the strategy with mock dependencies
        self.strategy = TradingStrategy(
            coinbase_client=self.mock_coinbase,
            llm_analyzer=self.mock_llm_analyzer,
            data_collector=self.mock_data_collector
        )
    
    def test_initialization(self):
        """Test strategy initialization"""
        # Update attribute names to match actual implementation
        self.assertEqual(self.strategy.client, self.mock_coinbase)
        self.assertEqual(self.strategy.analyzer, self.mock_llm_analyzer)
        self.assertEqual(self.strategy.data_collector, self.mock_data_collector)
    
    def test_execute_strategy_buy_decision(self):
        """Test executing strategy with a BUY decision"""
        # Configure mock for BUY decision
        llm_decision = {
            "decision": "BUY",
            "confidence": 85,
            "reasoning": ["RSI is oversold", "Market trend is bullish"]
        }
        self.mock_llm_analyzer.analyze_market.return_value = llm_decision
        
        # Mock the _execute_trade method to return a successful result
        with patch.object(self.strategy, '_execute_trade') as mock_execute_trade:
            mock_execute_trade.return_value = {
                "success": True,
                "trade_id": "test-trade-id",
                "side": "buy",
                "size": 0.1,
                "value_usd": 5000
            }
            
            # Execute the strategy
            result = self.strategy.execute_strategy("BTC-USD")
            
            # Verify the result
            self.assertEqual(result["product_id"], "BTC-USD")
            self.assertEqual(result["decision"], "BUY")
            self.assertEqual(result["confidence"], 85)
            self.assertEqual(result["price"], 50000.0)
            self.assertTrue(result["success"])
    
    def test_execute_strategy_sell_decision(self):
        """Test executing strategy with a SELL decision"""
        # Configure mock for SELL decision
        market_data = {
            "product_id": "BTC-USD",
            "price": 50000.0,
            "market_trend": "bearish",
            "rsi": 75,
            "volatility_24h": 3.5
        }
        self.mock_data_collector.get_market_data.return_value = market_data
        
        llm_decision = {
            "decision": "SELL",
            "confidence": 80,
            "reasoning": ["RSI is overbought", "Market trend is bearish"]
        }
        self.mock_llm_analyzer.analyze_market.return_value = llm_decision
        
        # Mock the _execute_trade method to return a successful result
        with patch.object(self.strategy, '_execute_trade') as mock_execute_trade:
            mock_execute_trade.return_value = {
                "success": True,
                "trade_id": "test-trade-id",
                "side": "sell",
                "size": 0.1,
                "value_usd": 5000
            }
            
            # Execute the strategy
            result = self.strategy.execute_strategy("BTC-USD")
            
            # Verify the result
            self.assertEqual(result["product_id"], "BTC-USD")
            self.assertEqual(result["decision"], "SELL")
            self.assertEqual(result["confidence"], 80)
            self.assertEqual(result["price"], 50000.0)
            self.assertTrue(result["success"])
    
    def test_execute_strategy_hold_decision(self):
        """Test executing strategy with a HOLD decision"""
        # Configure mock for HOLD decision
        market_data = {
            "product_id": "BTC-USD",
            "price": 50000.0,
            "market_trend": "neutral",
            "rsi": 50,
            "volatility_24h": 1.5
        }
        self.mock_data_collector.get_market_data.return_value = market_data
        
        llm_decision = {
            "decision": "HOLD",
            "confidence": 60,
            "reasoning": ["RSI is neutral", "Market trend is neutral"]
        }
        self.mock_llm_analyzer.analyze_market.return_value = llm_decision
        
        # Execute the strategy
        result = self.strategy.execute_strategy("BTC-USD")
        
        # Verify the result
        self.assertEqual(result["product_id"], "BTC-USD")
        self.assertEqual(result["decision"], "HOLD")
        self.assertEqual(result["confidence"], 60)
        self.assertEqual(result["price"], 50000.0)
        self.assertTrue(result["success"])
    
    def test_execute_strategy_with_error(self):
        """Test executing strategy when an error occurs"""
        # Mock the data collector to raise an exception
        self.mock_data_collector.get_market_data.side_effect = Exception("API error")
        
        # Execute the strategy
        result = self.strategy.execute_strategy("BTC-USD")
        
        # Verify the result indicates an error
        self.assertEqual(result["product_id"], "BTC-USD")
        self.assertEqual(result["success"], False)
        self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()
