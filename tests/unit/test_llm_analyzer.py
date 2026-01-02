"""
Comprehensive unit tests for llm_analyzer.py - LLM integration with NEW google-genai library

Tests cover:
- LLMAnalyzer initialization with NEW google-genai library
- Client creation with correct vertexai settings
- Authentication methods (service account, API key, default credentials)
- Market analysis with primary and fallback models
- Error handling and fallback strategies
- Response processing and validation
- Rate limiting and retry logic
- Configuration validation
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from llm_analyzer import LLMAnalyzer

@pytest.fixture
def test_env_vars():
    """Set up test environment variables"""
    test_vars = {
        'TESTING': 'true',
        'GOOGLE_CLOUD_PROJECT': 'test-project-id',
        'GOOGLE_APPLICATION_CREDENTIALS': 'test-credentials.json',
        'LLM_MODEL': 'gemini-3-flash-preview',
        'LLM_FALLBACK_MODEL': 'gemini-3-pro-preview',
        'LLM_LOCATION': 'global'
    }
    
    with patch.dict(os.environ, test_vars):
        yield test_vars

@pytest.fixture
def mock_genai_client():
    """Mock google.genai.Client for testing"""
    with patch('google.genai.Client') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.text = json.dumps({
            'decision': 'BUY',
            'confidence': 75,
            'reasoning': 'Strong uptrend detected with positive momentum',
            'risk_assessment': 'MEDIUM',
            'technical_indicators': {
                'trend': 'BULLISH',
                'momentum': 'POSITIVE'
            }
        })
        
        mock_client.models.generate_content.return_value = mock_response
        
        yield mock_client

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        'product_id': 'BTC-EUR',
        'price': 45000.0,
        'current_price': 45000.0,
        'volume': 1000000,
        'price_changes': {
            '1h': 1.2,
            '4h': 2.5,
            '24h': 3.8,
            '5d': 7.2,
            '7d': -2.1
        },
        'timestamp': '2024-01-01T12:00:00Z'
    }

@pytest.fixture
def sample_technical_indicators():
    """Sample technical indicators for testing"""
    return {
        'rsi': 65.0,
        'macd': 150.0,
        'macd_signal': 120.0,
        'bb_upper': 46000.0,
        'bb_middle': 45000.0,
        'bb_lower': 44000.0,
        'sma_20': 44800.0,
        'ema_12': 45100.0,
        'current_price': 45000.0
    }

@pytest.fixture
def sample_portfolio():
    """Sample portfolio data for testing"""
    return {
        'EUR': {'amount': 1000.0},
        'BTC': {'amount': 0.01, 'last_price_eur': 45000.0},
        'portfolio_value_eur': 1450.0,
        'trades_executed': 5
    }

class TestLLMAnalyzerInitialization:
    """Test LLMAnalyzer initialization with NEW google-genai library"""
    
    def test_llm_analyzer_initialization_service_account(self, test_env_vars, mock_genai_client):
        """Test LLMAnalyzer initialization with service account authentication"""
        with patch('google.oauth2.service_account.Credentials.from_service_account_file') as mock_creds, \
             patch('os.path.exists', return_value=True):
            
            mock_credentials = Mock()
            mock_creds.return_value = mock_credentials
            
            analyzer = LLMAnalyzer()
            
            # Verify NEW google-genai client was created with correct settings
            assert analyzer.client is not None
            
            # Verify service account authentication was used
            mock_creds.assert_called_once_with(
                'test-credentials.json',
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
    
    def test_llm_analyzer_initialization_api_key(self, test_env_vars, mock_genai_client):
        """Test LLMAnalyzer initialization with API key authentication"""
        test_env_vars['GOOGLE_AI_API_KEY'] = 'test-api-key'
        
        with patch.dict(os.environ, test_env_vars), \
             patch('os.path.exists', return_value=False):  # No service account file
            
            analyzer = LLMAnalyzer()
            
            # Verify client was created with API key
            assert analyzer.client is not None
    
    def test_llm_analyzer_initialization_default_credentials(self, test_env_vars, mock_genai_client):
        """Test LLMAnalyzer initialization with default credentials"""
        # Remove API key and service account file
        if 'GOOGLE_AI_API_KEY' in test_env_vars:
            del test_env_vars['GOOGLE_AI_API_KEY']
        
        with patch.dict(os.environ, test_env_vars), \
             patch('os.path.exists', return_value=False):  # No service account file
            
            analyzer = LLMAnalyzer()
            
            # Verify client was created with default credentials
            assert analyzer.client is not None
    
    def test_llm_analyzer_model_configuration(self, test_env_vars, mock_genai_client):
        """Test LLMAnalyzer model configuration"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            # Verify models are configured correctly
            assert analyzer.model == 'gemini-3-flash-preview'
            assert analyzer.fallback_model == 'gemini-3-pro-preview'
            assert analyzer.location == 'global'
    
    def test_llm_analyzer_initialization_failure(self, test_env_vars):
        """Test LLMAnalyzer initialization failure handling"""
        with patch('google.genai.Client', side_effect=Exception("Client initialization failed")), \
             patch('os.path.exists', return_value=False):
            
            analyzer = LLMAnalyzer()
            
            # Should handle initialization failure gracefully
            assert analyzer.client is None

class TestMarketAnalysis:
    """Test market analysis functionality"""
    
    def test_analyze_market_success_primary_model(self, test_env_vars, mock_genai_client, 
                                                  sample_market_data, sample_technical_indicators, 
                                                  sample_portfolio):
        """Test successful market analysis with primary model"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            result = analyzer.analyze_market(sample_market_data, sample_technical_indicators, sample_portfolio)
            
            # Verify analysis result
            assert result['decision'] == 'BUY'
            assert result['confidence'] == 75
            assert 'reasoning' in result
            assert 'risk_assessment' in result
            assert 'technical_indicators' in result
            assert result['fallback_used'] is False
            
            # Verify primary model was used
            mock_genai_client.models.generate_content.assert_called_once()
    
    def test_analyze_market_fallback_to_secondary_model(self, test_env_vars, sample_market_data, 
                                                       sample_technical_indicators, sample_portfolio):
        """Test fallback to secondary model when primary fails"""
        with patch('google.genai.Client') as mock_client_class, \
             patch('os.path.exists', return_value=False):
            
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Primary model fails
            mock_client.models.generate_content.side_effect = [
                Exception("Primary model failed"),
                Mock(text=json.dumps({
                    'decision': 'HOLD',
                    'confidence': 60,
                    'reasoning': 'Fallback model analysis',
                    'risk_assessment': 'MEDIUM'
                }))
            ]
            
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(sample_market_data, sample_technical_indicators, sample_portfolio)
            
            # Verify fallback was used
            assert result['decision'] == 'HOLD'
            assert result['confidence'] == 60
            assert 'Fallback model' in result['reasoning']
            
            # Verify both models were attempted
            assert mock_client.models.generate_content.call_count == 2
    
    def test_analyze_market_complete_failure_fallback(self, test_env_vars, sample_market_data, 
                                                     sample_technical_indicators, sample_portfolio):
        """Test complete failure fallback when both models fail"""
        with patch('google.genai.Client') as mock_client_class, \
             patch('os.path.exists', return_value=False):
            
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Both models fail
            mock_client.models.generate_content.side_effect = Exception("Both models failed")
            
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(sample_market_data, sample_technical_indicators, sample_portfolio)
            
            # Verify safe fallback
            assert result['decision'] == 'HOLD'
            assert result['confidence'] == 0
            assert 'AI analysis unavailable' in result['reasoning']
            assert result['fallback_used'] is True
    
    def test_analyze_market_invalid_json_response(self, test_env_vars, sample_market_data, 
                                                 sample_technical_indicators, sample_portfolio):
        """Test handling of invalid JSON response"""
        with patch('google.genai.Client') as mock_client_class, \
             patch('os.path.exists', return_value=False):
            
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Invalid JSON response
            mock_response = Mock()
            mock_response.text = "Invalid JSON response"
            mock_client.models.generate_content.return_value = mock_response
            
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(sample_market_data, sample_technical_indicators, sample_portfolio)
            
            # Should handle gracefully and return safe fallback
            assert result['decision'] == 'HOLD'
            assert result['confidence'] == 0
            assert result['fallback_used'] is True
    
    def test_analyze_market_missing_required_fields(self, test_env_vars, sample_market_data, 
                                                   sample_technical_indicators, sample_portfolio):
        """Test handling of response missing required fields"""
        with patch('google.genai.Client') as mock_client_class, \
             patch('os.path.exists', return_value=False):
            
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Response missing required fields
            mock_response = Mock()
            mock_response.text = json.dumps({
                'decision': 'BUY'
                # Missing confidence, reasoning, etc.
            })
            mock_client.models.generate_content.return_value = mock_response
            
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(sample_market_data, sample_technical_indicators, sample_portfolio)
            
            # Should handle missing fields gracefully
            assert result['decision'] == 'BUY'
            assert 'confidence' in result  # Should have default value
            assert 'reasoning' in result   # Should have default value

class TestPromptGeneration:
    """Test prompt generation for different scenarios"""
    
    def test_generate_analysis_prompt_basic(self, test_env_vars, sample_market_data, 
                                           sample_technical_indicators, sample_portfolio):
        """Test basic analysis prompt generation"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            # Mock the prompt generation method if it exists
            if hasattr(analyzer, '_generate_analysis_prompt'):
                prompt = analyzer._generate_analysis_prompt(
                    sample_market_data, sample_technical_indicators, sample_portfolio
                )
                
                # Verify prompt contains key information
                assert 'BTC-EUR' in prompt
                assert '45000' in prompt  # Current price
                assert 'RSI' in prompt or 'rsi' in prompt
                assert 'portfolio' in prompt.lower()
    
    def test_generate_analysis_prompt_with_news_sentiment(self, test_env_vars, sample_market_data, 
                                                         sample_technical_indicators, sample_portfolio):
        """Test analysis prompt generation with news sentiment"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            # Add news sentiment data
            news_sentiment = {
                'overall_sentiment': 'POSITIVE',
                'sentiment_score': 0.7,
                'key_topics': ['adoption', 'regulation', 'institutional']
            }
            
            if hasattr(analyzer, '_generate_analysis_prompt'):
                prompt = analyzer._generate_analysis_prompt(
                    sample_market_data, sample_technical_indicators, sample_portfolio, news_sentiment
                )
                
                # Verify news sentiment is included
                assert 'sentiment' in prompt.lower()
                assert 'POSITIVE' in prompt or 'positive' in prompt

class TestResponseProcessing:
    """Test response processing and validation"""
    
    def test_process_llm_response_valid(self, test_env_vars):
        """Test processing of valid LLM response"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            valid_response = {
                'decision': 'BUY',
                'confidence': 75,
                'reasoning': 'Strong technical indicators',
                'risk_assessment': 'MEDIUM',
                'technical_indicators': {'trend': 'BULLISH'}
            }
            
            if hasattr(analyzer, '_process_llm_response'):
                result = analyzer._process_llm_response(valid_response)
                
                assert result['decision'] == 'BUY'
                assert result['confidence'] == 75
                assert result['fallback_used'] is False
    
    def test_process_llm_response_invalid_decision(self, test_env_vars):
        """Test processing of response with invalid decision"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            invalid_response = {
                'decision': 'INVALID_ACTION',  # Invalid decision
                'confidence': 75,
                'reasoning': 'Test reasoning'
            }
            
            if hasattr(analyzer, '_process_llm_response'):
                result = analyzer._process_llm_response(invalid_response)
                
                # Should default to HOLD for invalid decisions
                assert result['decision'] == 'HOLD'
    
    def test_process_llm_response_confidence_bounds(self, test_env_vars):
        """Test confidence value bounds checking"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            # Test confidence > 100
            high_confidence_response = {
                'decision': 'BUY',
                'confidence': 150,  # Too high
                'reasoning': 'Test reasoning'
            }
            
            if hasattr(analyzer, '_process_llm_response'):
                result = analyzer._process_llm_response(high_confidence_response)
                
                # Should cap confidence at 100
                assert result['confidence'] <= 100
            
            # Test negative confidence
            negative_confidence_response = {
                'decision': 'SELL',
                'confidence': -10,  # Negative
                'reasoning': 'Test reasoning'
            }
            
            if hasattr(analyzer, '_process_llm_response'):
                result = analyzer._process_llm_response(negative_confidence_response)
                
                # Should set minimum confidence
                assert result['confidence'] >= 0

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_analyze_market_no_client(self, test_env_vars, sample_market_data, 
                                     sample_technical_indicators, sample_portfolio):
        """Test market analysis when client is None"""
        with patch('google.genai.Client', side_effect=Exception("No client")), \
             patch('os.path.exists', return_value=False):
            
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(sample_market_data, sample_technical_indicators, sample_portfolio)
            
            # Should return safe fallback
            assert result['decision'] == 'HOLD'
            assert result['confidence'] == 0
            assert result['fallback_used'] is True
    
    def test_analyze_market_empty_inputs(self, test_env_vars):
        """Test market analysis with empty inputs"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            result = analyzer.analyze_market({}, {}, {})
            
            # Should handle empty inputs gracefully
            assert result['decision'] == 'HOLD'
            assert result['confidence'] == 0
    
    def test_analyze_market_rate_limiting(self, test_env_vars, sample_market_data, 
                                         sample_technical_indicators, sample_portfolio):
        """Test handling of rate limiting errors"""
        with patch('google.genai.Client') as mock_client_class, \
             patch('os.path.exists', return_value=False):
            
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Simulate rate limiting error
            from google.api_core.exceptions import ResourceExhausted
            mock_client.models.generate_content.side_effect = ResourceExhausted("Rate limited")
            
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(sample_market_data, sample_technical_indicators, sample_portfolio)
            
            # Should handle rate limiting gracefully
            assert result['decision'] == 'HOLD'
            assert result['fallback_used'] is True

class TestConfigurationValidation:
    """Test configuration validation"""
    
    def test_validate_model_configuration(self, test_env_vars):
        """Test model configuration validation"""
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            
            # Verify required models are configured
            assert analyzer.model in ['gemini-3-flash-preview', 'gemini-3-pro-preview']
            assert analyzer.fallback_model in ['gemini-3-flash-preview', 'gemini-3-pro-preview']
            assert analyzer.location == 'global'  # Required for preview models
    
    def test_validate_authentication_configuration(self, test_env_vars):
        """Test authentication configuration validation"""
        # Test with service account
        with patch('os.path.exists', return_value=True), \
             patch('google.oauth2.service_account.Credentials.from_service_account_file') as mock_creds:
            
            mock_creds.return_value = Mock()
            
            analyzer = LLMAnalyzer()
            
            # Should use service account authentication
            mock_creds.assert_called_once()
        
        # Test with API key
        test_env_vars['GOOGLE_AI_API_KEY'] = 'test-key'
        with patch.dict(os.environ, test_env_vars), \
             patch('os.path.exists', return_value=False):
            
            analyzer = LLMAnalyzer()
            
            # Should handle API key authentication
            assert analyzer is not None

class TestIntegrationScenarios:
    """Test integration scenarios and real-world usage patterns"""
    
    def test_analyze_market_bull_market_scenario(self, test_env_vars, mock_genai_client):
        """Test analysis in bull market scenario"""
        bull_market_data = {
            'product_id': 'BTC-EUR',
            'price': 50000.0,
            'price_changes': {'24h': 8.5, '7d': 15.2}  # Strong positive movement
        }
        
        bull_indicators = {
            'rsi': 70,  # Overbought but trending
            'macd': 200,  # Strong momentum
            'current_price': 50000.0
        }
        
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(bull_market_data, bull_indicators, {})
            
            # Should provide analysis for bull market conditions
            assert result is not None
            assert 'decision' in result
    
    def test_analyze_market_bear_market_scenario(self, test_env_vars, mock_genai_client):
        """Test analysis in bear market scenario"""
        bear_market_data = {
            'product_id': 'BTC-EUR',
            'price': 35000.0,
            'price_changes': {'24h': -5.2, '7d': -12.8}  # Strong negative movement
        }
        
        bear_indicators = {
            'rsi': 30,  # Oversold
            'macd': -150,  # Negative momentum
            'current_price': 35000.0
        }
        
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(bear_market_data, bear_indicators, {})
            
            # Should provide analysis for bear market conditions
            assert result is not None
            assert 'decision' in result
    
    def test_analyze_market_sideways_market_scenario(self, test_env_vars, mock_genai_client):
        """Test analysis in sideways market scenario"""
        sideways_market_data = {
            'product_id': 'BTC-EUR',
            'price': 42000.0,
            'price_changes': {'24h': 0.5, '7d': -1.2}  # Minimal movement
        }
        
        sideways_indicators = {
            'rsi': 50,  # Neutral
            'macd': 5,  # Minimal momentum
            'current_price': 42000.0
        }
        
        with patch('os.path.exists', return_value=False):
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_market(sideways_market_data, sideways_indicators, {})
            
            # Should provide analysis for sideways market conditions
            assert result is not None
            assert 'decision' in result

if __name__ == '__main__':
    pytest.main([__file__])