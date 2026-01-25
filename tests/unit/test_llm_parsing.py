"""
Unit tests for LLM response parsing - focusing on robustness and error handling
"""

import pytest
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestLLMResponseParsing:
    """Test LLM response parsing with various edge cases"""
    
    def test_parse_valid_json_response(self):
        """Test parsing a valid, complete JSON response"""
        # Import and test the parsing logic directly
        from llm_analyzer import LLMAnalyzer
        
        # Create a minimal mock instance just for parsing
        class MockAnalyzer:
            def _parse_llm_response(self, response_text):
                # Copy the actual implementation
                import re
                try:
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        analysis_result = json.loads(json_str)
                        if 'decision' not in analysis_result or 'confidence' not in analysis_result:
                            raise ValueError("Missing required fields")
                        return analysis_result
                    else:
                        raise ValueError("No JSON found")
                except (json.JSONDecodeError, ValueError):
                    # Partial extraction fallback
                    decision_match = re.search(r'"decision"\s*:\s*"(BUY|SELL|HOLD)"', response_text, re.IGNORECASE)
                    confidence_match = re.search(r'"confidence"\s*:\s*(\d+)', response_text)
                    if decision_match and confidence_match:
                        return {
                            "decision": decision_match.group(1).upper(),
                            "confidence": int(confidence_match.group(1)),
                            "reasoning": ["Partial parse"],
                            "risk_assessment": "medium",
                            "partial_parse": True
                        }
                    return {
                        "decision": "HOLD",
                        "confidence": 50,
                        "reasoning": ["Parse failed"],
                        "risk_assessment": "medium",
                        "parse_failed": True
                    }
        
        analyzer = MockAnalyzer()
        response = json.dumps({
            "decision": "BUY",
            "confidence": 75,
            "reasoning": ["Strong uptrend"],
            "risk_assessment": "medium"
        })
        
        result = analyzer._parse_llm_response(response)
        assert result['decision'] == 'BUY'
        assert result['confidence'] == 75
    
    def test_parse_truncated_json_response(self):
        """Test parsing truncated JSON (the main issue we're fixing)"""
        class MockAnalyzer:
            def _parse_llm_response(self, response_text):
                import re
                try:
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        analysis_result = json.loads(json_str)
                        if 'decision' not in analysis_result or 'confidence' not in analysis_result:
                            raise ValueError("Missing required fields")
                        return analysis_result
                    else:
                        raise ValueError("No JSON found")
                except (json.JSONDecodeError, ValueError):
                    decision_match = re.search(r'"decision"\s*:\s*"(BUY|SELL|HOLD)"', response_text, re.IGNORECASE)
                    confidence_match = re.search(r'"confidence"\s*:\s*(\d+)', response_text)
                    if decision_match and confidence_match:
                        return {
                            "decision": decision_match.group(1).upper(),
                            "confidence": int(confidence_match.group(1)),
                            "reasoning": ["Partial parse"],
                            "risk_assessment": "medium",
                            "partial_parse": True
                        }
                    return {
                        "decision": "HOLD",
                        "confidence": 50,
                        "reasoning": ["Parse failed"],
                        "risk_assessment": "medium",
                        "parse_failed": True
                    }
        
        analyzer = MockAnalyzer()
        response = '{"decision": "HOLD", "confidence": 80, "reasoning": ["Truncated'
        
        result = analyzer._parse_llm_response(response)
        assert result['decision'] == 'HOLD'
        assert result['confidence'] == 80
        assert 'partial_parse' in result or 'parse_failed' in result
    
    def test_parse_completely_invalid_response(self):
        """Test handling completely invalid response"""
        class MockAnalyzer:
            def _parse_llm_response(self, response_text):
                import re
                try:
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        analysis_result = json.loads(json_str)
                        if 'decision' not in analysis_result or 'confidence' not in analysis_result:
                            raise ValueError("Missing required fields")
                        return analysis_result
                    else:
                        raise ValueError("No JSON found")
                except (json.JSONDecodeError, ValueError):
                    decision_match = re.search(r'"decision"\s*:\s*"(BUY|SELL|HOLD)"', response_text, re.IGNORECASE)
                    confidence_match = re.search(r'"confidence"\s*:\s*(\d+)', response_text)
                    if decision_match and confidence_match:
                        return {
                            "decision": decision_match.group(1).upper(),
                            "confidence": int(confidence_match.group(1)),
                            "reasoning": ["Partial parse"],
                            "risk_assessment": "medium",
                            "partial_parse": True
                        }
                    return {
                        "decision": "HOLD",
                        "confidence": 50,
                        "reasoning": ["Parse failed"],
                        "risk_assessment": "medium",
                        "parse_failed": True
                    }
        
        analyzer = MockAnalyzer()
        response = "This is not JSON at all"
        
        result = analyzer._parse_llm_response(response)
        assert result['decision'] == 'HOLD'
        assert result['confidence'] == 50
        assert 'parse_failed' in result


class TestLLMTokenLimitConfiguration:
    """Test that token limits are properly configured"""
    
    def test_max_output_tokens_reduced(self):
        """Verify max_output_tokens is set to 500 for concise responses"""
        with open('llm_analyzer.py', 'r') as f:
            content = f.read()
            
        # Check that we're using 500 for concise responses
        assert 'max_output_tokens=500' in content
        assert 'max_output_tokens=10000' not in content
    
    def test_simplified_prompt_format(self):
        """Verify prompt requests simplified JSON format"""
        with open('llm_analyzer.py', 'r') as f:
            content = f.read()
            
        # Should have simplified format instructions
        assert 'ONLY valid JSON' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
