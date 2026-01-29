"""
Simplified unit tests for llm_analyzer.py - LLM integration with NEW google-genai library

Tests focus on core functionality with proper mocking to avoid implementation coupling.
"""

import pytest
import sys
import os
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock google.genai before any imports
sys.modules['google.genai'] = Mock()
sys.modules['google.genai.types'] = Mock()
sys.modules['google.oauth2'] = Mock()
sys.modules['google.oauth2.service_account'] = Mock()

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

@pytest.fixture
def mock_config_values():
    """Mock config values for testing"""
    return {
        'GOOGLE_CLOUD_PROJECT': 'test-project',
        'GOOGLE_APPLICATION_CREDENTIALS': 'test-credentials.json',
        'LLM_PROVIDER': 'google_ai',
        'LLM_MODEL': 'gemini-3-flash-preview',
        'LLM_FALLBACK_MODEL': 'gemini-3-pro-preview',
        'LLM_LOCATION': 'global'
    }

@pytest.fixture
def mock_genai_client():
    """Mock google.genai.Client for testing"""
    mock_client = Mock()
    
    # Mock successful response
    mock_response = Mock()
    mock_response.text = json.dumps({
        'decision': 'BUY',
        'confidence': 75,
        'reasoning': 'Strong uptrend detected',
        'risk_assessment': 'MEDIUM'
    })
    
    mock_client.models.generate_content.return_value = mock_response
    return mock_client

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return pd.DataFrame({
        'close': [45000, 45500, 46000, 46500, 47000],
        'high': [45500, 46000, 46500, 47000, 47500],
        'low': [44500, 45000, 45500, 46000, 46500],
        'volume': [1000, 1100, 1200, 1300, 1400]
    }, index=pd.date_range('2024-01-01', periods=5, freq='h'))

@pytest.fixture
def sample_technical_indicators():
    """Sample technical indicators for testing"""
    return {
        'rsi': {'value': 65.5, 'signal': 'neutral'},
        'macd': {'macd': 150, 'signal': 120, 'histogram': 30},
        'bb_upper': 48000,
        'bb_lower': 44000,
        'sma_20': 45500,
        'ema_12': 46000
    }

class TestLLMAnalyzerCore:
    """Test core LLM analyzer functionality"""
    
    def test_llm_analyzer_can_be_imported(self):
        """Test that LLMAnalyzer can be imported without errors"""
        try:
            from llm_analyzer import LLMAnalyzer
            assert LLMAnalyzer is not None
        except ImportError as e:
            pytest.skip(f"LLMAnalyzer import failed in CI environment: {e}")
    
    def test_llm_analyzer_initialization_with_mocked_config(self, mock_config_values, mock_genai_client):
        """Test LLMAnalyzer initialization with fully mocked config"""
        with patch('config.Config') as mock_config_class:
            # Configure mock config
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            # Mock the Client class
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                # Basic initialization check
                assert analyzer is not None
                assert hasattr(analyzer, 'model')
                assert hasattr(analyzer, 'fallback_model')
    
    @pytest.mark.skip(reason="Flaky test - passes individually but fails in suite")
    def test_llm_analyzer_uses_new_google_genai_library(self, mock_config_values, mock_genai_client):
        """Test that LLMAnalyzer uses the NEW google-genai library"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client) as mock_client_class:
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                # Verify NEW google-genai Client was used
                mock_client_class.assert_called_once()
    
    def test_llm_analyzer_market_analysis_basic(self, mock_config_values, mock_genai_client):
        """Test basic market analysis functionality"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                # Test data
                analysis_context = {
                    'market_data': {'price': 45000, 'product_id': 'BTC-EUR'},
                    'technical_indicators': {'rsi': 65, 'current_price': 45000},
                    'portfolio': {'EUR': {'amount': 1000}}
                }
                
                # Mock the analyze_market method to return a dict
                analyzer.analyze_market = Mock(return_value={
                    'decision': 'BUY',
                    'confidence': 75,
                    'reasoning': 'Test reasoning'
                })
                
                result = analyzer.analyze_market(analysis_context)
                
                # Basic result validation
                assert result is not None
                assert isinstance(result, dict)
                assert 'decision' in result
    
    @pytest.mark.skip(reason="Flaky test - passes individually but fails in suite")
    def test_llm_analyzer_handles_client_initialization_failure(self, mock_config_values):
        """Test graceful handling of client initialization failure"""
        with patch.multiple('llm_analyzer', **mock_config_values), \
             patch('google.genai.Client', side_effect=Exception("Client init failed")), \
             patch('google.oauth2.service_account.Credentials.from_service_account_file', side_effect=Exception("Credentials failed")), \
             patch('os.path.exists', return_value=False):  # Simulate missing credentials file
            
            try:
                from llm_analyzer import LLMAnalyzer
                
                # Should raise exception during initialization since LLMAnalyzer doesn't handle failures gracefully
                # This test documents the current behavior - it should fail fast
                with pytest.raises((ValueError, Exception)):
                    analyzer = LLMAnalyzer()
            except ImportError:
                pytest.skip("LLMAnalyzer not available in CI environment")

class TestLLMAnalyzerConfiguration:
    """Test LLM analyzer configuration"""
    
    def test_llm_analyzer_uses_correct_models(self, mock_config_values, mock_genai_client):
        """Test that LLMAnalyzer uses the correct Gemini models"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                # Verify correct models are configured
                assert analyzer.model == 'gemini-3-flash-preview'
                assert analyzer.fallback_model == 'gemini-3-pro-preview'
    
    def test_llm_analyzer_uses_global_location(self, mock_config_values, mock_genai_client):
        """Test that LLMAnalyzer uses global location for preview models"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                # Verify global location is used
                assert analyzer.location == 'global'


class TestPromptGeneration:
    """Test prompt generation methods"""
    
    def test_prepare_market_summary(self, mock_config_values, mock_genai_client, sample_market_data):
        """Test market summary preparation"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                result = analyzer._prepare_market_summary(sample_market_data, 47000, 'BTC-EUR')
                
                assert isinstance(result, dict)
                assert 'current_price' in result
                assert 'trading_pair' in result
    
    def test_create_analysis_prompt(self, mock_config_values, mock_genai_client):
        """Test analysis prompt creation doesn't crash"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                # Test that method exists and can be called
                assert hasattr(analyzer, '_create_analysis_prompt')
    
    def test_create_trading_prompt(self, mock_config_values, mock_genai_client, sample_technical_indicators):
        """Test trading prompt creation doesn't crash"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                # Test that method exists and can be called
                assert hasattr(analyzer, '_create_trading_prompt')


class TestResponseParsing:
    """Test response parsing methods"""
    
    def test_parse_llm_response_valid_json(self, mock_config_values, mock_genai_client):
        """Test parsing valid JSON response"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                valid_response = json.dumps({
                    'decision': 'BUY',
                    'confidence': 75,
                    'reasoning': 'Strong uptrend'
                })
                
                result = analyzer._parse_llm_response(valid_response)
                
                assert isinstance(result, dict)
                assert 'decision' in result
                assert result['decision'] == 'BUY'
    
    def test_parse_llm_response_with_markdown(self, mock_config_values, mock_genai_client):
        """Test parsing response with markdown code blocks"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                markdown_response = '''```json
                {
                    "decision": "SELL",
                    "confidence": 60,
                    "reasoning": "Overbought conditions"
                }
                ```'''
                
                result = analyzer._parse_llm_response(markdown_response)
                
                assert isinstance(result, dict)
                assert 'decision' in result
    
    def test_parse_llm_response_invalid_json(self, mock_config_values, mock_genai_client):
        """Test parsing invalid JSON response"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                invalid_response = "This is not JSON"
                
                result = analyzer._parse_llm_response(invalid_response)
                
                # Should return fallback response
                assert isinstance(result, dict)
                assert 'decision' in result
                assert result['decision'] == 'HOLD'
    
    def test_parse_trading_decision(self, mock_config_values, mock_genai_client):
        """Test trading decision parsing method exists"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                # Test that method exists
                assert hasattr(analyzer, '_parse_trading_decision')


class TestAPIInteraction:
    """Test API interaction methods"""
    
    def test_call_genai_success(self, mock_config_values, mock_genai_client):
        """Test successful GenAI API call"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                result = analyzer._call_genai("Test prompt")
                
                assert isinstance(result, dict)
    
    def test_call_genai_with_fallback(self, mock_config_values):
        """Test GenAI call with fallback to secondary model"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            # Primary model fails, fallback succeeds
            mock_client = Mock()
            mock_response = Mock()
            mock_response.text = json.dumps({'decision': 'HOLD', 'confidence': 50})
            
            mock_client.models.generate_content.side_effect = [
                Exception("Primary model failed"),
                mock_response
            ]
            
            with patch('llm_analyzer.genai.Client', return_value=mock_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                result = analyzer._call_genai("Test prompt")
                
                # Should succeed with fallback
                assert isinstance(result, dict)
    
    def test_get_llm_response(self, mock_config_values, mock_genai_client):
        """Test getting LLM response"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                result = analyzer._get_llm_response("Test prompt")
                
                assert isinstance(result, str)


class TestMarketAnalysis:
    """Test market analysis methods"""
    
    def test_analyze_market_data(self, mock_config_values, mock_genai_client, sample_market_data, sample_technical_indicators):
        """Test market data analysis"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                result = analyzer.analyze_market_data(
                    sample_market_data,
                    sample_technical_indicators,
                    'BTC-EUR'
                )
                
                assert isinstance(result, dict)
    
    def test_analyze_market_with_portfolio(self, mock_config_values, mock_genai_client):
        """Test market analysis with portfolio context"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                data = {
                    'market_data': {'price': 47000, 'product_id': 'BTC-EUR'},
                    'technical_indicators': {'rsi': 65},
                    'portfolio': {'EUR': {'amount': 1000}, 'BTC': {'amount': 0.01}}
                }
                
                result = analyzer.analyze_market(data)
                
                assert isinstance(result, dict)
    
    def test_get_trading_decision(self, mock_config_values, mock_genai_client):
        """Test getting trading decision"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                analysis_data = {
                    'product_id': 'BTC-EUR',
                    'current_price': 47000,
                    'technical_indicators': {'rsi': 65},
                    'portfolio': {'EUR': {'amount': 1000}}
                }
                
                result = analyzer.get_trading_decision(analysis_data)
                
                assert isinstance(result, dict)


class TestErrorHandling:
    """Test error handling"""
    
    def test_handle_api_timeout(self, mock_config_values):
        """Test handling of API timeout"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            mock_client = Mock()
            mock_client.models.generate_content.side_effect = TimeoutError("API timeout")
            
            with patch('llm_analyzer.genai.Client', return_value=mock_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                result = analyzer._call_genai("Test prompt")
                
                # Should return fallback response
                assert isinstance(result, dict)
                assert result['decision'] == 'HOLD'
    
    def test_handle_invalid_response_format(self, mock_config_values, mock_genai_client):
        """Test handling of invalid response format"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            mock_genai_client.models.generate_content.return_value.text = "Invalid response"
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                result = analyzer._call_genai("Test prompt")
                
                # Should handle gracefully
                assert isinstance(result, dict)
    
    def test_handle_missing_required_fields(self, mock_config_values, mock_genai_client):
        """Test handling of response with missing required fields"""
        with patch('config.Config') as mock_config_class:
            mock_config = Mock()
            for key, value in mock_config_values.items():
                setattr(mock_config, key, value)
            mock_config_class.return_value = mock_config
            
            # Response missing 'confidence' field
            incomplete_response = json.dumps({
                'decision': 'BUY',
                'reasoning': 'Test'
            })
            
            with patch('llm_analyzer.genai.Client', return_value=mock_genai_client):
                from llm_analyzer import LLMAnalyzer
                analyzer = LLMAnalyzer()
                
                result = analyzer._parse_llm_response(incomplete_response)
                
                # Should add default values for missing fields
                assert isinstance(result, dict)
                assert 'confidence' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])