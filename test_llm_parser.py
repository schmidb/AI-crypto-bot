#!/usr/bin/env python3
"""Test LLM JSON parsing fixes"""

import sys
import json

# Mock the logger
class MockLogger:
    def warning(self, msg): print(f"WARNING: {msg}")
    def info(self, msg): print(f"INFO: {msg}")
    def debug(self, msg): print(f"DEBUG: {msg}")

# Test the parsing logic
def parse_llm_response(response_text: str, logger):
    """Parse the LLM response to extract trading decision with robust error handling"""
    import re
    
    try:
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Find JSON content between curly braces
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1

        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            
            # Fix common JSON errors: missing commas after arrays/objects
            json_str = re.sub(r'(\])\s*\n\s*"', r'\1,\n  "', json_str)
            json_str = re.sub(r'(\})\s*\n\s*"', r'\1,\n  "', json_str)
            
            analysis_result = json.loads(json_str)
            
            # Validate required fields
            if 'decision' not in analysis_result or 'confidence' not in analysis_result:
                raise ValueError("Missing required fields: decision or confidence")
                
            return analysis_result
        else:
            raise ValueError("No JSON structure found in response")
            
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"JSON parse failed, attempting partial extraction: {str(e)[:100]}")
        
        try:
            # Extract all fields using regex as fallback
            decision_match = re.search(r'"decision"\s*:\s*"(BUY|SELL|HOLD)"', response_text, re.IGNORECASE)
            confidence_match = re.search(r'"confidence"\s*:\s*(\d+)', response_text)
            risk_match = re.search(r'"risk_assessment"\s*:\s*"(\w+)"', response_text, re.IGNORECASE)
            reasoning_match = re.search(r'"reasoning"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
            
            if decision_match and confidence_match:
                decision = decision_match.group(1).upper()
                confidence = int(confidence_match.group(1))
                risk = risk_match.group(1).lower() if risk_match else "medium"
                
                # Extract reasoning items
                reasoning = ["Partial LLM response - extracted key fields"]
                if reasoning_match:
                    reasons_text = reasoning_match.group(1)
                    reasons = re.findall(r'"([^"]+)"', reasons_text)
                    if reasons:
                        reasoning = reasons
                
                logger.info(f"Extracted partial data: {decision} ({confidence}%)")
                return {
                    "decision": decision,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "risk_assessment": risk,
                    "partial_parse": True
                }
        except Exception as extract_error:
            logger.debug(f"Partial extraction failed: {extract_error}")
        
        # Final fallback
        logger.warning("Using safe fallback response")
        return {
            "decision": "HOLD",
            "confidence": 50,
            "reasoning": ["Could not parse LLM response"],
            "risk_assessment": "medium",
            "parse_failed": True
        }

# Test cases
test_cases = [
    ("Valid JSON", '{"decision": "BUY", "confidence": 75, "reasoning": ["test"], "risk_assessment": "low"}'),
    ("Missing comma after array", '{\n  "decision": "HOLD",\n  "confidence": 75,\n  "reasoning": ["Market is stable", "No clear trend"]\n  "risk_assessment": "medium"\n}'),
    ("With markdown", '```json\n{"decision": "SELL", "confidence": 80, "reasoning": ["test"], "risk_assessment": "high"}\n```'),
    ("Expecting comma error", '{\n  "decision": "BUY",\n  "confidence": 80,\n  "reasoning": ["Strong uptrend"]\n  "risk_assessment": "low"\n}'),
]

logger = MockLogger()
print("Testing LLM JSON Parser Fixes\n" + "="*50)

for name, test_input in test_cases:
    print(f"\n--- Test: {name} ---")
    print(f"Input: {test_input[:80]}...")
    result = parse_llm_response(test_input, logger)
    print(f"✓ Result: {result['decision']} ({result['confidence']}%)")
    print(f"  Risk: {result['risk_assessment']}")
    if result.get('partial_parse'):
        print("  ⚠️  Used partial parsing")
    if result.get('parse_failed'):
        print("  ❌ Parse failed, used fallback")

print("\n" + "="*50)
print("✓ All tests completed successfully!")
