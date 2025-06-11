#!/usr/bin/env python3
"""
Unit tests for the LLM analyzer
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the config module
sys.modules['config'] = MagicMock()
sys.modules['config'].GOOGLE_PROJECT_ID = 'test-project'
sys.modules['config'].GOOGLE_LOCATION = 'us-central1'
sys.modules['config'].LLM_MODEL = 'text-bison'
sys.modules['config'].SIMULATION_MODE = True

from llm_analyzer import LLMAnalyzer

class TestLLMAnalyzer(unittest.TestCase):
    """Test cases for LLMAnalyzer class"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock Vertex AI
        self.patcher_vertexai = patch('llm_analyzer.vertexai')
        self.patcher_textgen = patch('llm_analyzer.TextGenerationModel')
        self.patcher_logger = patch('llm_analyzer.logger')
        
        self.mock_vertexai = self.patcher_vertexai.start()
        self.mock_textgen = self.patcher_textgen.start()
        self.mock_logger = self.patcher_logger.start()
        
        # Configure mock model
        self.mock_model = MagicMock()
        self.mock_textgen.from_pretrained.return_value = self.mock_model
        
    def tearDown(self):
        """Clean up after tests"""
        self.patcher_vertexai.stop()
        self.patcher_textgen.stop()
        self.patcher_logger.stop()
    
    def test_initialization(self):
        """Test LLM analyzer initialization"""
        analyzer = LLMAnalyzer()
        
        # Verify Vertex AI initialization
        self.mock_vertexai.init.assert_called_once()
        self.mock_textgen.from_pretrained.assert_called_once()
        
        # Verify model is set
        self.assertEqual(analyzer.model, self.mock_model)
    
    def test_analyze_market_and_decide_buy_signal(self):
        """Test market analysis with buy signal"""
        # Mock LLM response for buy signal
        mock_response = MagicMock()
        mock_response.text = """
        Based on the technical analysis:
        
        DECISION: BUY
        ASSET: BTC-USD
        CONFIDENCE: 78
        REASONING: Strong bullish momentum with RSI at 35 indicating oversold conditions. MACD showing positive crossover and price breaking above Bollinger Band middle line. Volume is increasing, confirming the upward movement.
        AMOUNT: 0.25
        RISK_LEVEL: medium
        """
        
        self.mock_model.predict.return_value = mock_response
        
        # Test data
        market_data = {
            'BTC-USD': {
                'price': 45000,
                'volume': 1200,
                'change_24h': 3.5,
                'rsi': 35,
                'macd': 120,
                'bollinger_upper': 46000,
                'bollinger_lower': 43000
            }
        }
        
        portfolio_data = {
            'btc_amount': 0.1,
            'usd_amount': 5000,
            'total_value_usd': 10000
        }
        
        analyzer = LLMAnalyzer()
        result = analyzer.analyze_market_and_decide(market_data, portfolio_data)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result['action'], 'buy')
        self.assertEqual(result['asset'], 'BTC-USD')
        self.assertEqual(result['confidence'], 78)
        self.assertIn('reasoning', result)
        self.assertEqual(result['amount'], 0.25)
        self.assertEqual(result['risk_level'], 'medium')
    
    def test_analyze_market_and_decide_sell_signal(self):
        """Test market analysis with sell signal"""
        # Mock LLM response for sell signal
        mock_response = MagicMock()
        mock_response.text = """
        Market Analysis Results:
        
        DECISION: SELL
        ASSET: ETH-USD
        CONFIDENCE: 82
        REASONING: Overbought conditions with RSI at 75. MACD showing bearish divergence and price approaching resistance at Bollinger upper band. Volume declining suggests weakening momentum.
        AMOUNT: 0.5
        RISK_LEVEL: low
        """
        
        self.mock_model.predict.return_value = mock_response
        
        # Test data
        market_data = {
            'ETH-USD': {
                'price': 3200,
                'volume': 800,
                'change_24h': -2.1,
                'rsi': 75,
                'macd': -80,
                'bollinger_upper': 3250,
                'bollinger_lower': 3000
            }
        }
        
        portfolio_data = {
            'eth_amount': 2.0,
            'usd_amount': 2000,
            'total_value_usd': 12000
        }
        
        analyzer = LLMAnalyzer()
        result = analyzer.analyze_market_and_decide(market_data, portfolio_data)
        
        # Verify result
        self.assertEqual(result['action'], 'sell')
        self.assertEqual(result['asset'], 'ETH-USD')
        self.assertEqual(result['confidence'], 82)
        self.assertEqual(result['amount'], 0.5)
        self.assertEqual(result['risk_level'], 'low')
    
    def test_analyze_market_and_decide_hold_signal(self):
        """Test market analysis with hold signal"""
        # Mock LLM response for hold signal
        mock_response = MagicMock()
        mock_response.text = """
        Technical Analysis Summary:
        
        DECISION: HOLD
        ASSET: SOL-USD
        CONFIDENCE: 65
        REASONING: Mixed signals in the market. RSI at neutral 52, MACD showing sideways movement. Price consolidating within Bollinger Bands. Waiting for clearer directional signals.
        AMOUNT: 0
        RISK_LEVEL: medium
        """
        
        self.mock_model.predict.return_value = mock_response
        
        # Test data
        market_data = {
            'SOL-USD': {
                'price': 120,
                'volume': 600,
                'change_24h': 0.5,
                'rsi': 52,
                'macd': 5,
                'bollinger_upper': 125,
                'bollinger_lower': 115
            }
        }
        
        portfolio_data = {
            'sol_amount': 50,
            'usd_amount': 3000,
            'total_value_usd': 15000
        }
        
        analyzer = LLMAnalyzer()
        result = analyzer.analyze_market_and_decide(market_data, portfolio_data)
        
        # Verify result
        self.assertEqual(result['action'], 'hold')
        self.assertEqual(result['asset'], 'SOL-USD')
        self.assertEqual(result['confidence'], 65)
        self.assertEqual(result['amount'], 0)
    
    def test_parse_llm_response_edge_cases(self):
        """Test parsing of various LLM response formats"""
        analyzer = LLMAnalyzer()
        
        # Test malformed response
        malformed_response = "This is not a proper trading decision format"
        result = analyzer._parse_llm_response(malformed_response)
        
        self.assertEqual(result['action'], 'hold')
        self.assertEqual(result['confidence'], 50)
        self.assertIn('Unable to parse', result['reasoning'])
    
    def test_parse_llm_response_missing_fields(self):
        """Test parsing response with missing required fields"""
        analyzer = LLMAnalyzer()
        
        # Response missing confidence
        incomplete_response = """
        DECISION: BUY
        ASSET: BTC-USD
        REASONING: Good opportunity
        """
        
        result = analyzer._parse_llm_response(incomplete_response)
        
        self.assertEqual(result['action'], 'buy')
        self.assertEqual(result['asset'], 'BTC-USD')
        self.assertEqual(result['confidence'], 50)  # Default value
    
    def test_create_analysis_prompt(self):
        """Test creation of analysis prompt"""
        analyzer = LLMAnalyzer()
        
        market_data = {
            'BTC-USD': {
                'price': 50000,
                'rsi': 60,
                'macd': 100
            }
        }
        
        portfolio_data = {
            'btc_amount': 0.1,
            'total_value_usd': 10000
        }
        
        prompt = analyzer._create_analysis_prompt(market_data, portfolio_data)
        
        # Verify prompt contains key information
        self.assertIn('BTC-USD', prompt)
        self.assertIn('50000', prompt)
        self.assertIn('RSI: 60', prompt)
        self.assertIn('MACD: 100', prompt)
        self.assertIn('Portfolio', prompt)
        self.assertIn('DECISION:', prompt)
        self.assertIn('CONFIDENCE:', prompt)
    
    def test_error_handling_api_failure(self):
        """Test error handling when API fails"""
        # Mock API failure
        self.mock_model.predict.side_effect = Exception("API Error")
        
        analyzer = LLMAnalyzer()
        
        market_data = {'BTC-USD': {'price': 50000}}
        portfolio_data = {'total_value_usd': 10000}
        
        result = analyzer.analyze_market_and_decide(market_data, portfolio_data)
        
        # Should return safe default
        self.assertEqual(result['action'], 'hold')
        self.assertIn('error', result['reasoning'].lower())
    
    def test_confidence_validation(self):
        """Test confidence level validation"""
        analyzer = LLMAnalyzer()
        
        # Test confidence clamping
        test_cases = [
            ("CONFIDENCE: 150", 100),  # Too high
            ("CONFIDENCE: -10", 0),    # Too low
            ("CONFIDENCE: 75", 75),    # Valid
            ("CONFIDENCE: invalid", 50) # Invalid format
        ]
        
        for response_text, expected_confidence in test_cases:
            full_response = f"""
            DECISION: HOLD
            ASSET: BTC-USD
            {response_text}
            REASONING: Test
            """
            
            result = analyzer._parse_llm_response(full_response)
            self.assertEqual(result['confidence'], expected_confidence)
    
    def test_asset_validation(self):
        """Test asset symbol validation"""
        analyzer = LLMAnalyzer()
        
        # Test valid assets
        valid_assets = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        for asset in valid_assets:
            response = f"""
            DECISION: BUY
            ASSET: {asset}
            CONFIDENCE: 70
            REASONING: Test
            """
            
            result = analyzer._parse_llm_response(response)
            self.assertEqual(result['asset'], asset)
        
        # Test invalid asset
        invalid_response = """
        DECISION: BUY
        ASSET: INVALID-USD
        CONFIDENCE: 70
        REASONING: Test
        """
        
        result = analyzer._parse_llm_response(invalid_response)
        self.assertEqual(result['action'], 'hold')  # Should default to hold for invalid asset

class TestLLMAnalyzerIntegration(unittest.TestCase):
    """Integration tests for LLM analyzer with realistic scenarios"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.patcher_vertexai = patch('llm_analyzer.vertexai')
        self.patcher_textgen = patch('llm_analyzer.TextGenerationModel')
        
        self.mock_vertexai = self.patcher_vertexai.start()
        self.mock_textgen = self.patcher_textgen.start()
        
        self.mock_model = MagicMock()
        self.mock_textgen.from_pretrained.return_value = self.mock_model
    
    def tearDown(self):
        """Clean up integration tests"""
        self.patcher_vertexai.stop()
        self.patcher_textgen.stop()
    
    def test_multi_asset_analysis(self):
        """Test analysis with multiple assets"""
        # Mock comprehensive LLM response
        mock_response = MagicMock()
        mock_response.text = """
        Multi-Asset Analysis:
        
        BTC-USD: Strong support at $44,000, RSI oversold at 32
        ETH-USD: Consolidating, RSI neutral at 48  
        SOL-USD: Breaking resistance, RSI at 68
        
        DECISION: BUY
        ASSET: BTC-USD
        CONFIDENCE: 76
        REASONING: Bitcoin showing strongest reversal signals with oversold RSI and volume spike. Best risk/reward opportunity among the three assets.
        AMOUNT: 0.3
        RISK_LEVEL: medium
        """
        
        self.mock_model.predict.return_value = mock_response
        
        # Multi-asset market data
        market_data = {
            'BTC-USD': {
                'price': 44500,
                'volume': 1800,
                'change_24h': -5.2,
                'rsi': 32,
                'macd': -200,
                'bollinger_upper': 46000,
                'bollinger_lower': 43000
            },
            'ETH-USD': {
                'price': 2950,
                'volume': 900,
                'change_24h': -1.1,
                'rsi': 48,
                'macd': 10,
                'bollinger_upper': 3100,
                'bollinger_lower': 2800
            },
            'SOL-USD': {
                'price': 125,
                'volume': 700,
                'change_24h': 4.8,
                'rsi': 68,
                'macd': 80,
                'bollinger_upper': 130,
                'bollinger_lower': 120
            }
        }
        
        portfolio_data = {
            'btc_amount': 0.05,
            'eth_amount': 1.2,
            'sol_amount': 25,
            'usd_amount': 8000,
            'total_value_usd': 18000
        }
        
        analyzer = LLMAnalyzer()
        result = analyzer.analyze_market_and_decide(market_data, portfolio_data)
        
        # Verify comprehensive analysis
        self.assertEqual(result['action'], 'buy')
        self.assertEqual(result['asset'], 'BTC-USD')
        self.assertEqual(result['confidence'], 76)
        self.assertIn('oversold', result['reasoning'].lower())
        self.assertEqual(result['amount'], 0.3)

if __name__ == '__main__':
    unittest.main()
