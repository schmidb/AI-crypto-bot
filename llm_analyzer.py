"""
LLM Analyzer for the crypto trading bot
Uses Google Cloud Vertex AI to analyze market data and make trading decisions
"""

import logging
import json
import os
from typing import Dict, Any, List
import google.auth
from google.cloud import aiplatform
from risk_models import hybrid_risk_strategy

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """Uses LLM to analyze market data and make trading decisions"""
    
    def __init__(self):
        """Initialize the LLM analyzer"""
        from config import LLM_PROVIDER, LLM_MODEL, LLM_LOCATION, GOOGLE_CLOUD_PROJECT, RISK_WEIGHTS
        
        self.provider = LLM_PROVIDER
        self.model = LLM_MODEL
        self.location = LLM_LOCATION
        self.project_id = GOOGLE_CLOUD_PROJECT
        self.risk_weights = RISK_WEIGHTS
        
        logger.info(f"LLM analyzer initialized with {self.provider} provider and {self.model} model")
        logger.info(f"Risk weights: low={self.risk_weights['low']}, medium={self.risk_weights['medium']}, high={self.risk_weights['high']}")
    
    def get_trading_decision(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get trading decision from LLM
        
        Args:
            analysis_data: Dictionary with market data for analysis
            
        Returns:
            Dictionary with trading decision
        """
        try:
            # Log the model being used
            logger.info(f"Using model: {self.model}")
            
            # Format the prompt
            prompt = self._format_prompt(analysis_data)
            
            # Get raw LLM response
            llm_response = self._get_llm_response(prompt)
            
            # Parse the response
            llm_decision = self._parse_response(llm_response)
            
            # Apply hybrid risk strategy
            decision = hybrid_risk_strategy(
                analysis_data, 
                llm_decision,
                low_weight=self.risk_weights["low"],
                medium_weight=self.risk_weights["medium"],
                high_weight=self.risk_weights["high"]
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error getting trading decision: {e}")
            return {"action": "hold", "confidence": 0, "reason": f"Error: {str(e)}"}
    
    def _format_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """
        Format the prompt for the LLM
        
        Args:
            analysis_data: Dictionary with market data for analysis
            
        Returns:
            Formatted prompt string
        """
        product_id = analysis_data.get("product_id", "")
        current_price = analysis_data.get("current_price", 0)
        risk_level = analysis_data.get("risk_level", "medium")
        
        # Get indicators
        indicators = analysis_data.get("indicators", {})
        rsi = indicators.get("rsi", {})
        macd = indicators.get("macd", {})
        bollinger_bands = indicators.get("bollinger_bands", {})
        
        # Format the prompt
        prompt = f"""
You are a cryptocurrency trading expert. Analyze the following market data for {product_id} and make a trading decision.

Current price: ${current_price}

Technical Indicators:
- RSI: {rsi.get('value', 'N/A')} ({rsi.get('signal', 'neutral')})
- MACD: {macd.get('value', 'N/A')} (Signal: {macd.get('signal', 'N/A')}, Histogram: {macd.get('histogram', 'N/A')}, Trend: {macd.get('trend', 'neutral')})
- Bollinger Bands: Upper: ${bollinger_bands.get('upper', 'N/A')}, Middle: ${bollinger_bands.get('middle', 'N/A')}, Lower: ${bollinger_bands.get('lower', 'N/A')}, Signal: {bollinger_bands.get('signal', 'neutral')}

Risk level: {risk_level}

Based on this data, decide whether to buy, sell, or hold {product_id.split('-')[0]}.

Provide your decision in the following JSON format:
{{
  "action": "buy|sell|hold",
  "confidence": <0-100>,
  "reason": "<brief explanation>"
}}
"""
        return prompt
    
    def _get_llm_response(self, prompt: str) -> str:
        """
        Get response from LLM
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            LLM response string
        """
        if self.provider == "vertex" or self.provider == "vertex_ai":
            return self._get_vertex_response(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _get_vertex_response(self, prompt: str) -> str:
        """
        Get response from Google Cloud Vertex AI
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            Vertex AI response string
        """
        try:
            # Map model name to API model ID if needed
            model_id = self._map_model_name(self.model)
            logger.info(f"Mapped model name '{self.model}' to API model ID: {model_id}")
            
            # Initialize Vertex AI
            aiplatform.init(project=self.project_id, location=self.location)
            
            # Create endpoint URL for logging
            endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_id}:generateContent"
            logger.info(f"Making API request to: {endpoint}")
            
            # Use the appropriate method based on what's available in the environment
            try:
                # Try using the newer Vertex AI Gemini API
                import vertexai
                from vertexai.generative_models import GenerativeModel
                
                vertexai.init(project=self.project_id, location=self.location)
                model = GenerativeModel(model_id)
                response = model.generate_content(prompt)
                response_text = response.text
                
            except (ImportError, AttributeError):
                # Fall back to the older aiplatform API
                from google.cloud import aiplatform
                
                # Create the endpoint
                endpoint = aiplatform.Endpoint(
                    endpoint_name=f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_id}"
                )
                
                # Create the request
                instances = [{"prompt": prompt}]
                parameters = {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024,
                    "topK": 40,
                    "topP": 0.95
                }
                
                # Make the prediction
                response = endpoint.predict(instances=instances, parameters=parameters)
                response_text = response.predictions[0]
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error getting Vertex AI response: {e}")
            raise
    
    def _map_model_name(self, model_name: str) -> str:
        """
        Map friendly model name to API model ID
        
        Args:
            model_name: Friendly model name
            
        Returns:
            API model ID
        """
        model_mapping = {
            "text-bison": "text-bison",
            "text-bison-32k": "text-bison-32k",
            "gemini-pro": "gemini-pro",
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
            "gemini-2.5-flash-preview-05-20": "gemini-2.5-flash-preview-05-20"
        }
        
        return model_mapping.get(model_name, model_name)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract trading decision
        
        Args:
            response: LLM response string
            
        Returns:
            Dictionary with trading decision
        """
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
                
            json_str = response[json_start:json_end]
            
            # Parse JSON
            decision = json.loads(json_str)
            
            # Validate required fields
            if "action" not in decision:
                raise ValueError("Missing 'action' field in decision")
                
            if "confidence" not in decision:
                raise ValueError("Missing 'confidence' field in decision")
                
            if "reason" not in decision:
                raise ValueError("Missing 'reason' field in decision")
                
            # Normalize action to lowercase
            decision["action"] = decision["action"].lower()
            
            # Validate action
            valid_actions = ["buy", "sell", "hold"]
            if decision["action"] not in valid_actions:
                raise ValueError(f"Invalid action: {decision['action']}")
                
            # Ensure confidence is an integer between 0 and 100
            decision["confidence"] = int(decision["confidence"])
            decision["confidence"] = max(0, min(100, decision["confidence"]))
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from response: {e}")
            logger.error(f"Response: {response}")
            return {"action": "hold", "confidence": 0, "reason": f"Error parsing response: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            logger.error(f"Response: {response}")
            return {"action": "hold", "confidence": 0, "reason": f"Error: {str(e)}"}
