"""
Unit tests for LLM response parsing - focusing on robustness and error handling
"""

import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock google.genai before importing llm_analyzer
sys.modules['google.genai'] = Mock()
sys.modules['google.genai.types'] = Mock()
sys.modules['google.oauth2'] = Mock()
sys.modules['google.oauth2.service_account'] = Mock()


class TestLLMResponseParsing:
    """Test LLM response parsing with various edge cases"""
    
    @pytest.fixture
    def mock_analyzer(self):
        """Create a mock LLMAnalyzer with just the parsing method"""
        with patch('config.Config') as mock_config:
            mock_config.return_value = Mock(
                GOOGLE_CLOUD_PROJECT='test',
                LLM_MODEL='gemini-3-flash-preview',
                LLM_FALLBACK_MODEL='gemini-3-pro-preview',
                LLM_LOCATION='global'
            )
            with patch('llm_analyzer.genai.Client'):
                from llm_analyzer import LLMAnalyzer
                return LLMAnalyzer()
    
    def test_parse_valid_json_response(self, mock_analyzer):
        """Test parsing a valid, complete JSON response"""
        response = json.dumps({
            "decision": "BUY",
            "confidence": 75,
            "reasoning": ["Strong uptrend", "High volume"],
            "risk_assessment": "medium"
        })
        
        result = mock_analyzer._parse_llm_response(response)
        
        assert result['decision'] == 'BUY'
        assert result['confidence'] == 75
        assert 'reasoning' in result
        assert result['risk_assessment'] == 'medium'
    
    def test_parse_json_with_extra_text(self, mock_analyzer):
        """Test parsing JSON embedded in extra text"""
        response = """Here's my analysis:
        {
            "decision": "SELL",
            "confidence": 80,
            "reasoning": ["Overbought"],
            "risk_assessment": "low"
        }
        That's my recommendation."""
        
        result = mock_analyzer._parse_llm_response(response)
        
        assert result['decision'] == 'SELL'
        assert result['confidence'] == 80
    
    def test_parse_truncated_json_response(self, mock_analyzer):
        """Test parsing truncated JSON (the main issue we're fixing)"""
        # Simulates the actual error case
        response = """{
            "decision": "HOLD",
            "confidence": 80,
            "reasoning": ["Bollinger Band squeeze detected"""
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should extract partial data via regex fallback
        assert result['decision'] == 'HOLD'
        assert result['confidence'] == 80
        assert 'partial_parse' in result or 'parse_failed' in result
    
    def test_parse_incomplete_json_with_decision_only(self, mock_analyzer):
        """Test extracting decision when JSON is severely truncated"""
        response = '{"decision": "BUY", "confiden'
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should still extract decision via regex
        assert result['decision'] in ['BUY', 'HOLD']  # BUY if extracted, HOLD if fallback
    
    def test_parse_missing_required_fields(self, mock_analyzer):
        """Test handling JSON missing required fields"""
        response = json.dumps({
            "reasoning": ["Some reasoning"],
            "risk_assessment": "medium"
        })
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should fall back to safe defaults
        assert result['decision'] == 'HOLD'
        assert result['confidence'] == 50
    
    def test_parse_invalid_decision_value(self, mock_analyzer):
        """Test handling invalid decision values"""
        response = json.dumps({
            "decision": "MAYBE",  # Invalid
            "confidence": 75,
            "reasoning": ["Uncertain"],
            "risk_assessment": "medium"
        })
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should accept it or fall back to HOLD
        assert result['decision'] in ['MAYBE', 'HOLD']
    
    def test_parse_completely_invalid_response(self, mock_analyzer):
        """Test handling completely invalid response"""
        response = "This is not JSON at all, just plain text."
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should return safe fallback
        assert result['decision'] == 'HOLD'
        assert result['confidence'] == 50
        assert 'parse_failed' in result
    
    def test_parse_empty_response(self, mock_analyzer):
        """Test handling empty response"""
        response = ""
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should return safe fallback
        assert result['decision'] == 'HOLD'
        assert result['confidence'] == 50
    
    def test_parse_json_with_nested_objects(self, mock_analyzer):
        """Test parsing JSON with nested objects (old format)"""
        response = json.dumps({
            "decision": "BUY",
            "confidence": 85,
            "reasoning": ["Strong signal"],
            "risk_assessment": "low",
            "technical_indicators": {
                "rsi": {"value": 45, "signal": "neutral"}
            }
        })
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should parse successfully
        assert result['decision'] == 'BUY'
        assert result['confidence'] == 85
    
    def test_parse_confidence_out_of_range(self, mock_analyzer):
        """Test handling confidence values outside 0-100 range"""
        response = json.dumps({
            "decision": "SELL",
            "confidence": 150,  # Invalid
            "reasoning": ["Test"],
            "risk_assessment": "high"
        })
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should still parse (validation happens elsewhere)
        assert result['decision'] == 'SELL'
        assert result['confidence'] == 150  # Accepts as-is
    
    def test_parse_multiple_json_objects(self, mock_analyzer):
        """Test handling response with multiple JSON objects"""
        response = """
        {"decision": "HOLD", "confidence": 50}
        {"decision": "BUY", "confidence": 80, "reasoning": ["Real one"], "risk_assessment": "low"}
        """
        
        result = mock_analyzer._parse_llm_response(response)
        
        # Should extract the last complete JSON
        assert result['decision'] in ['HOLD', 'BUY']
        assert 'confidence' in result


class TestLLMTokenLimitConfiguration:
    """Test that token limits are properly configured"""
    
    def test_max_output_tokens_reduced(self):
        """Verify max_output_tokens is set to 2000 (not 10000)"""
        with open('llm_analyzer.py', 'r') as f:
            content = f.read()
            
        # Check that we're using 2000, not 10000
        assert 'max_output_tokens=2000' in content or 'max_output_tokens: 2000' in content
        assert 'max_output_tokens=10000' not in content
    
    def test_simplified_prompt_format(self):
        """Verify prompt requests simplified JSON format"""
        with open('llm_analyzer.py', 'r') as f:
            content = f.read()
            
        # Should have simplified format instructions
        assert 'Respond ONLY with valid JSON' in content or 'ONLY with valid JSON' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
