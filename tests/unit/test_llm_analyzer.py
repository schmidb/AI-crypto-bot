"""
Unit tests for LLM Analyzer.

This module tests the LLMAnalyzer class and all AI-related functionality
to ensure proper market analysis, decision making, and error handling.
Tests the Google GenAI provider implementation.
"""

import pytest
import pandas as pd
import json
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from llm_analyzer import LLMAnalyzer


class TestLLMAnalyzerInitialization:
    """Test LLMAnalyzer initialization and authentication."""
    
    @patch('llm_analyzer.genai.Client')
    @patch('llm_analyzer.service_account')
    @patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', '/path/to/credentials.json')
    @patch('llm_analyzer.GOOGLE_CLOUD_PROJECT', 'test-project')
    def test_initialization_with_service_account(self, mock_service_account, mock_genai_client):
        """Test LLMAnalyzer initialization with service account credentials."""
        # Setup mocks
        mock_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        # Initialize analyzer
        analyzer = LLMAnalyzer(provider="vertex_ai", model="gemini-3-flash-preview", location="us-central1")
        
        # Verify initialization
        assert analyzer.provider == "vertex_ai"
        assert analyzer.model == "gemini-3-flash-preview"
        assert analyzer.location == "us-central1"
        
        # Verify service account credentials were loaded
        mock_service_account.Credentials.from_service_account_file.assert_called_once()
        
        # Verify GenAI Client was created
        mock_genai_client.assert_called_once_with(
            vertexai=True, 
            credentials=mock_credentials,
            project='test-project',
            location='us-central1'
        )
    
    @patch('llm_analyzer.genai.Client')
    @patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None)
    @patch('llm_analyzer.GOOGLE_CLOUD_PROJECT', 'test-project')
    def test_initialization_with_default_credentials(self, mock_genai_client):
        """Test LLMAnalyzer initialization with default credentials."""
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        # Initialize analyzer
        analyzer = LLMAnalyzer()
        
        # Verify GenAI Client was created with default credentials
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project='test-project',
            location='us-central1'
        )
    
    @patch('llm_analyzer.service_account')
    @patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', '/invalid/path.json')
    def test_initialization_with_invalid_credentials(self, mock_service_account):
        """Test LLMAnalyzer initialization with invalid credentials raises exception."""
        # Setup mock to raise exception
        mock_service_account.Credentials.from_service_account_file.side_effect = Exception("Invalid credentials")
        
        # Verify exception is raised
        with pytest.raises(Exception, match="Invalid credentials"):
            LLMAnalyzer()
    
    @patch('llm_analyzer.genai.Client')
    @patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None)
    def test_initialization_with_custom_parameters(self, mock_genai_client):
        """Test LLMAnalyzer initialization with custom parameters."""
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        analyzer = LLMAnalyzer(
            provider="vertex_ai",
            model="gemini-2.5-pro",
            location="europe-west1"
        )
        
        assert analyzer.provider == "vertex_ai"
        assert analyzer.model == "gemini-2.5-pro"
        assert analyzer.location == "europe-west1"


class TestMarketDataAnalysis:
    """Test market data analysis functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a mock LLMAnalyzer for testing."""
        with patch('llm_analyzer.genai.Client'), \
             patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None):
            
            return LLMAnalyzer()
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        return pd.DataFrame({
            'timestamp': dates,
            'open': [50000 + i * 10 for i in range(100)],
            'high': [50100 + i * 10 for i in range(100)],
            'low': [49900 + i * 10 for i in range(100)],
            'close': [50050 + i * 10 for i in range(100)],
            'volume': [1000 + i * 5 for i in range(100)]
        })
    
    def test_analyze_market_data_success(self, analyzer, sample_market_data):
        """Test successful market data analysis."""
        # Mock the LLM call
        mock_response = {
            "decision": "BUY",
            "confidence": 85,
            "reasoning": "Strong upward trend with high volume",
            "risk_assessment": "medium"
        }
        
        with patch.object(analyzer, '_call_genai', return_value=mock_response):
            result = analyzer.analyze_market_data(
                market_data=sample_market_data,
                current_price=51000.0,
                trading_pair="BTC-EUR"
            )
            
            assert result["decision"] == "BUY"
            assert result["confidence"] == 85
            assert "upward trend" in result["reasoning"]
            assert result["risk_assessment"] == "medium"
    
    def test_analyze_market_data_with_additional_context(self, analyzer, sample_market_data):
        """Test market data analysis with additional context."""
        additional_context = {
            "portfolio_allocation": {"BTC": 0.3, "EUR": 0.7},
            "recent_trades": ["SELL BTC", "BUY ETH"]
        }
        
        mock_response = {
            "decision": "HOLD",
            "confidence": 60,
            "reasoning": "Considering portfolio allocation",
            "risk_assessment": "low"
        }
        
        with patch.object(analyzer, '_call_genai', return_value=mock_response) as mock_call:
            result = analyzer.analyze_market_data(
                market_data=sample_market_data,
                current_price=51000.0,
                trading_pair="BTC-EUR",
                additional_context=additional_context
            )
            
            # Verify the call was made and context was passed
            mock_call.assert_called_once()
            assert result["decision"] == "HOLD"
    
    def test_analyze_market_data_llm_error_handling(self, analyzer, sample_market_data):
        """Test error handling when LLM call fails."""
        with patch.object(analyzer, '_call_genai', side_effect=Exception("API Error")):
            result = analyzer.analyze_market_data(
                market_data=sample_market_data,
                current_price=51000.0,
                trading_pair="BTC-EUR"
            )
            
            # Should return safe defaults on error
            assert result["decision"] == "HOLD"
            assert result["confidence"] == 0
            assert "Error during analysis" in result["reasoning"]
            assert result["risk_assessment"] == "high"


class TestVertexAIProviderCalls:
    """Test GenAI provider implementation."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a mock LLMAnalyzer for testing."""
        with patch('llm_analyzer.genai.Client'), \
             patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None):
            
            return LLMAnalyzer()
    
    def test_call_genai_success(self, analyzer):
        """Test successful GenAI API call."""
        # Mock the client's generate_content method
        mock_response = MagicMock()
        mock_response.text = '{"decision": "BUY", "confidence": 80, "reasoning": "Test reasoning", "risk_assessment": "medium"}'
        
        analyzer.client.models.generate_content = MagicMock(return_value=mock_response)
        
        result = analyzer._call_genai("test prompt")
        
        assert result["decision"] == "BUY"
        assert result["confidence"] == 80
        assert result["reasoning"] == "Test reasoning"
    
    def test_call_genai_api_error(self, analyzer):
        """Test GenAI API error handling."""
        # Mock API error
        analyzer.client.models.generate_content = MagicMock(side_effect=Exception("API Error"))
        
        # The method should raise the exception
        with pytest.raises(Exception, match="API Error"):
            analyzer._call_genai("test prompt")


class TestDataProcessing:
    """Test data processing and preparation methods."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a mock LLMAnalyzer for testing."""
        with patch('llm_analyzer.genai.Client'), \
             patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None):
            
            # Setup mock to return proper tuple
            
            return LLMAnalyzer()
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=200, freq='1H')  # More data for calculations
        return pd.DataFrame({
            'timestamp': dates,
            'open': [50000 + i * 10 for i in range(200)],
            'high': [50100 + i * 10 for i in range(200)],
            'low': [49900 + i * 10 for i in range(200)],
            'close': [50050 + i * 10 for i in range(200)],
            'volume': [1000 + i * 5 for i in range(200)]
        })
    
    def test_prepare_market_summary(self, analyzer, sample_market_data):
        """Test market data summary preparation."""
        summary = analyzer._prepare_market_summary(
            market_data=sample_market_data,
            current_price=51000.0,
            trading_pair="BTC-EUR"
        )
        
        # Verify summary contains expected keys (based on actual implementation)
        assert "current_price" in summary
        assert "price_change_24h" in summary
        assert "price_change_7d" in summary
        assert "latest_volume" in summary
        assert "average_volume_7d" in summary
        assert "volatility" in summary
        assert "trading_pair" in summary
        
        # Verify values
        assert summary["current_price"] == 51000.0
        assert summary["trading_pair"] == "BTC-EUR"
    
    def test_create_analysis_prompt(self, analyzer):
        """Test analysis prompt creation."""
        market_summary = {
            "current_price": 50000.0,
            "price_change_24h": 2.5,
            "price_change_7d": 5.0,
            "moving_average_50": 49500.0,  # Add missing field
            "moving_average_200": 48000.0,  # Add missing field
            "latest_volume": 1000000,
            "average_volume_7d": 900000,
            "volatility": 2.5,
            "recent_high": 51000.0,  # Add missing field
            "recent_low": 49000.0,   # Add missing field
            "trading_pair": "BTC-EUR"
        }
        
        prompt = analyzer._create_analysis_prompt(
            market_summary=market_summary,
            trading_pair="BTC-EUR"
        )
        
        # Verify prompt contains key information
        assert "BTC-EUR" in prompt
        assert "50000.0" in prompt
        assert "2.5" in prompt
        assert "JSON" in prompt  # Should request JSON response
    
    def test_create_analysis_prompt_with_context(self, analyzer):
        """Test analysis prompt creation with additional context."""
        market_summary = {
            "current_price": 50000.0,
            "price_change_24h": 2.5,
            "price_change_7d": 5.0,
            "moving_average_50": 49500.0,
            "moving_average_200": 48000.0,
            "volatility": 2.5,
            "recent_high": 51000.0,
            "recent_low": 49000.0,
            "latest_volume": 1000000,
            "average_volume_7d": 900000,
            "trading_pair": "BTC-EUR"
        }
        
        # Use the correct additional_context structure that the method expects
        additional_context = {
            "indicators": {
                "rsi": 65.5,
                "macd": 0.0123,
                "macd_signal": 0.0098,
                "macd_histogram": 0.0025,
                "bb_upper": 52000.0,
                "bb_middle": 50000.0,
                "bb_lower": 48000.0,
                "bb_width": 8.0,
                "bb_position": 0.5,
                "_metadata": {
                    "bb_timeframe_hours": 4,
                    "trading_style": "day_trading"
                }
            }
        }
        
        prompt = analyzer._create_analysis_prompt(
            market_summary=market_summary,
            trading_pair="BTC-EUR",
            additional_context=additional_context
        )
        
        # Verify additional context indicators are included
        assert "65.5" in prompt  # RSI value
        assert "0.0123" in prompt  # MACD value
        assert "$52000.00" in prompt  # BB upper


class TestResponseParsing:
    """Test LLM response parsing and validation."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a mock LLMAnalyzer for testing."""
        with patch('llm_analyzer.genai.Client'), \
             patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None):
            
            # Setup mock to return proper tuple
            
            return LLMAnalyzer()
    
    def test_parse_llm_response_valid_json(self, analyzer):
        """Test parsing valid JSON response."""
        response_text = '''
        {
            "decision": "BUY",
            "confidence": 85,
            "reasoning": "Strong technical indicators",
            "risk_assessment": "medium"
        }
        '''
        
        result = analyzer._parse_llm_response(response_text)
        
        assert result["decision"] == "BUY"
        assert result["confidence"] == 85
        assert result["reasoning"] == "Strong technical indicators"
        assert result["risk_assessment"] == "medium"
    
    def test_parse_llm_response_with_markdown(self, analyzer):
        """Test parsing JSON response wrapped in markdown."""
        response_text = '''
        Here's my analysis:
        
        ```json
        {
            "decision": "SELL",
            "confidence": 70,
            "reasoning": "Market showing weakness",
            "risk_assessment": "high"
        }
        ```
        
        This is my recommendation.
        '''
        
        result = analyzer._parse_llm_response(response_text)
        
        assert result["decision"] == "SELL"
        assert result["confidence"] == 70
    
    def test_parse_llm_response_invalid_json(self, analyzer):
        """Test parsing invalid JSON response."""
        response_text = "This is not valid JSON"
        
        result = analyzer._parse_llm_response(response_text)
        
        # Should return safe defaults (based on actual implementation)
        assert result["decision"] == "HOLD"
        assert result["confidence"] == 50  # Default confidence from implementation
        assert "Could not parse LLM response as JSON" in result["reasoning"]
    
    def test_parse_llm_response_missing_fields(self, analyzer):
        """Test parsing JSON response with missing required fields."""
        response_text = '''
        {
            "decision": "BUY",
            "reasoning": "Good opportunity"
        }
        '''
        
        result = analyzer._parse_llm_response(response_text)
        
        # Should return the parsed JSON as-is (implementation doesn't fill missing fields)
        assert result["decision"] == "BUY"
        assert result["reasoning"] == "Good opportunity"
        # Missing fields won't be present in the result


class TestTradingDecisionMaking:
    """Test trading decision making functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a mock LLMAnalyzer for testing."""
        with patch('llm_analyzer.genai.Client'), \
             patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None):
            
            # Setup mock to return proper tuple
            
            return LLMAnalyzer()
    
    def test_get_trading_decision_buy_signal(self, analyzer):
        """Test BUY signal generation."""
        analysis_data = {
            "product_id": "BTC-EUR",
            "current_price": 50000.0,
            "indicators": {
                "rsi": {
                    "value": 30,
                    "signal": "oversold"
                },
                "macd": {
                    "value": 100,
                    "signal": "bullish",
                    "trend": "up"
                },
                "bollinger_bands": {
                    "upper": 52000,
                    "middle": 50000,
                    "lower": 48000,
                    "signal": "normal"
                }
            },
            "risk_level": "medium"
        }
        
        # Mock response in the format expected by _parse_trading_decision
        mock_response = """
        ACTION: buy
        CONFIDENCE: 80
        REASON: RSI oversold with bullish MACD signal indicates strong buy opportunity
        """
        
        with patch.object(analyzer, '_get_llm_response', return_value=mock_response):
            result = analyzer.get_trading_decision(analysis_data)
            
            # Based on actual implementation, returns different keys
            assert result["action"] == "buy"
            assert result["confidence"] == 80
            assert "RSI" in result["reason"]
    
    def test_get_trading_decision_sell_signal(self, analyzer):
        """Test SELL signal generation."""
        analysis_data = {
            "product_id": "ETH-EUR",
            "current_price": 3000.0,
            "indicators": {
                "rsi": {
                    "value": 80,
                    "signal": "overbought"
                },
                "macd": {
                    "value": -50,
                    "signal": "bearish",
                    "trend": "down"
                },
                "bollinger_bands": {
                    "upper": 3200,
                    "middle": 3000,
                    "lower": 2800,
                    "signal": "breakout_upper"
                }
            },
            "risk_level": "low"
        }
        
        # Mock response in the format expected by _parse_trading_decision
        mock_response = """
        ACTION: sell
        CONFIDENCE: 75
        REASON: RSI overbought with bearish MACD signal indicates sell opportunity
        """
        
        with patch.object(analyzer, '_get_llm_response', return_value=mock_response):
            result = analyzer.get_trading_decision(analysis_data)
            
            assert result["action"] == "sell"
            assert result["confidence"] == 75
    
    def test_get_trading_decision_hold_signal(self, analyzer):
        """Test HOLD signal generation."""
        analysis_data = {
            "product_id": "SOL-EUR",
            "current_price": 100.0,
            "indicators": {
                "rsi": {
                    "value": 50,
                    "signal": "neutral"
                },
                "macd": {
                    "value": 0,
                    "signal": "neutral",
                    "trend": "sideways"
                },
                "bollinger_bands": {
                    "upper": 105,
                    "middle": 100,
                    "lower": 95,
                    "signal": "squeeze"
                }
            },
            "risk_level": "medium"
        }
        
        # Mock response in the format expected by _parse_trading_decision
        mock_response = """
        ACTION: hold
        CONFIDENCE: 60
        REASON: Neutral indicators suggest waiting for clearer signals
        """
        
        with patch.object(analyzer, '_get_llm_response', return_value=mock_response):
            result = analyzer.get_trading_decision(analysis_data)
            
            assert result["action"] == "hold"
            assert result["confidence"] == 60


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a mock LLMAnalyzer for testing."""
        with patch('llm_analyzer.genai.Client'), \
             patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None):
            
            # Setup mock to return proper tuple
            
            return LLMAnalyzer()
    
    def test_empty_market_data(self, analyzer):
        """Test handling of empty market data."""
        empty_data = pd.DataFrame()
        
        # This will cause an error in _prepare_market_summary, which should now be caught
        result = analyzer.analyze_market_data(
            market_data=empty_data,
            current_price=50000.0,
            trading_pair="BTC-EUR"
        )
        
        # Should handle gracefully and return error response
        assert result["decision"] == "HOLD"
        assert result["confidence"] == 0
        assert "Error during analysis" in result["reasoning"]
        assert result["risk_assessment"] == "high"
    
    def test_invalid_current_price(self, analyzer):
        """Test handling of invalid current price."""
        sample_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [50000.0],
            'high': [50100.0],
            'low': [49900.0],
            'close': [50000.0],
            'volume': [1000.0]
        })
        
        # Should handle gracefully even with negative price
        result = analyzer.analyze_market_data(
            market_data=sample_data,
            current_price=-100.0,  # Invalid negative price
            trading_pair="BTC-EUR"
        )
        
        # Should either process or return error response
        assert "decision" in result
    
    def test_network_timeout_handling(self, analyzer):
        """Test handling of network timeouts."""
        with patch.object(analyzer, '_get_llm_response', side_effect=TimeoutError("Network timeout")):
            analysis_data = {
                "product_id": "BTC-EUR",
                "current_price": 50000.0,
                "indicators": {},
                "risk_level": "medium"
            }
            
            result = analyzer.get_trading_decision(analysis_data)
            
            # Should return error response
            assert result["action"] == "hold"
            assert result["confidence"] == 0
            assert "error" in result["reason"].lower()
    
    def test_malformed_response_handling(self, analyzer):
        """Test handling of malformed LLM responses."""
        with patch.object(analyzer, '_get_llm_response', return_value="Malformed response without JSON"):
            analysis_data = {
                "product_id": "BTC-EUR", 
                "current_price": 50000.0,
                "indicators": {},
                "risk_level": "medium"
            }
            
            result = analyzer.get_trading_decision(analysis_data)
            
            # Should return error response
            assert result["action"] == "hold"
            assert result["confidence"] == 0


class TestConfigurationValidation:
    """Test configuration validation and parameter handling."""
    
    @patch('llm_analyzer.genai.Client')
    @patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None)
    def test_vertex_ai_provider_configuration(self, mock_genai_client):
        """Test vertex_ai provider configuration."""
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        analyzer = LLMAnalyzer(provider="vertex_ai")
        
        # Should initialize successfully
        assert analyzer.provider == "vertex_ai"
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project='intense-base-456414-u5',
            location='us-central1'
        )
    
    @patch('llm_analyzer.genai.Client')
    @patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None)
    def test_model_configuration(self, mock_genai_client):
        """Test model configuration."""
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        analyzer = LLMAnalyzer(model="gemini-1.5-pro")
        
        # Should handle model configuration
        assert analyzer.model == "gemini-1.5-pro"
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project='intense-base-456414-u5',
            location='us-central1'
        )
    
    @patch('llm_analyzer.genai.Client')
    @patch('llm_analyzer.GOOGLE_APPLICATION_CREDENTIALS', None)
    def test_location_configuration(self, mock_genai_client):
        """Test location configuration."""
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        analyzer = LLMAnalyzer(location="europe-west1")
        
        # Should initialize with custom location
        assert analyzer.location == "europe-west1"
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project='intense-base-456414-u5',
            location='europe-west1'
        )


if __name__ == "__main__":
    pytest.main([__file__])
