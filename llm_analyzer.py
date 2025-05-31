import logging
import json
from typing import Dict, List, Any
import pandas as pd
import os
import requests
import google.auth
import google.auth.transport.requests

from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from google.oauth2 import service_account

from config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_APPLICATION_CREDENTIALS,
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_LOCATION
)

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """Uses Google Cloud Vertex AI LLMs to analyze market data and make trading decisions"""
    
    def __init__(self, 
                provider: str = LLM_PROVIDER, 
                model: str = LLM_MODEL,
                location: str = LLM_LOCATION):
        """Initialize the LLM analyzer"""
        self.provider = provider
        self.model = model
        self.location = location
        
        # Initialize Google Cloud credentials
        if GOOGLE_APPLICATION_CREDENTIALS:
            try:
                self.credentials = service_account.Credentials.from_service_account_file(
                    GOOGLE_APPLICATION_CREDENTIALS
                )
                aiplatform.init(
                    project=GOOGLE_CLOUD_PROJECT,
                    location=self.location,
                    credentials=self.credentials
                )
                logger.info(f"Initialized Google Cloud with project: {GOOGLE_CLOUD_PROJECT}")
            except Exception as e:
                logger.error(f"Error initializing Google Cloud credentials: {e}")
                raise
        else:
            # Use default credentials
            try:
                aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=self.location)
                logger.info(f"Initialized Google Cloud with default credentials")
            except Exception as e:
                logger.error(f"Error initializing Google Cloud with default credentials: {e}")
                raise
        
        logger.info(f"LLM Analyzer initialized with provider: {provider}, model: {model}")
    
    def analyze_market_data(self, 
                           market_data: pd.DataFrame, 
                           current_price: float,
                           trading_pair: str,
                           additional_context: Dict = None) -> Dict:
        """
        Analyze market data using LLM and generate trading decision
        
        Args:
            market_data: DataFrame with OHLCV data
            current_price: Current price of the asset
            trading_pair: Trading pair being analyzed (e.g., 'BTC-USD')
            additional_context: Additional context to provide to the LLM
            
        Returns:
            Dictionary with trading decision and analysis
        """
        # Prepare market data summary
        market_summary = self._prepare_market_summary(market_data, current_price, trading_pair)
        
        # Prepare prompt for LLM
        prompt = self._create_analysis_prompt(market_summary, trading_pair, additional_context)
        
        try:
            # Call appropriate LLM based on provider
            if self.provider == "vertex_ai":
                analysis_result = self._call_vertex_ai(prompt)
            elif self.provider == "palm":
                analysis_result = self._call_palm(prompt)
            elif self.provider == "gemini":
                analysis_result = self._call_gemini(prompt)
            else:
                logger.error(f"Unsupported LLM provider: {self.provider}")
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
            
            logger.info(f"LLM analysis completed for {trading_pair}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}")
            return {
                "decision": "HOLD",
                "confidence": 0,
                "reasoning": f"Error during analysis: {str(e)}",
                "risk_assessment": "high"
            }
    
    def _call_vertex_ai(self, prompt: str) -> Dict:
        """Call Vertex AI for text generation using REST API"""
        try:
            # Create the endpoint URL
            url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{GOOGLE_CLOUD_PROJECT}/locations/{self.location}/publishers/google/models/{self.model}:predict"
            
            # Create the request payload
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            # Get the access token
            credentials, project = google.auth.default()
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            
            # Make the request
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Extract the prediction text
            prediction_text = response.json()["predictions"][0]
            
            # Parse the response
            try:
                # Try to parse as JSON
                result_text = prediction_text
                # Find JSON content between curly braces
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                else:
                    # Fallback to default response
                    logger.warning(f"Could not find JSON in response: {result_text}")
                    analysis_result = {
                        "decision": "HOLD",
                        "confidence": 50,
                        "reasoning": "Could not parse LLM response as JSON",
                        "risk_assessment": "medium"
                    }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from response: {str(prediction_text)}")
                analysis_result = {
                    "decision": "HOLD",
                    "confidence": 50,
                    "reasoning": "Could not parse LLM response as JSON",
                    "risk_assessment": "medium"
                }
                
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error calling Vertex AI: {e}")
            raise
    
    def _call_palm(self, prompt: str) -> Dict:
        """Call PaLM API for text generation"""
        try:
            from google.cloud import aiplatform
            from vertexai.language_models import TextGenerationModel
            
            # Initialize Vertex AI
            aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=self.location)
            
            # Load the model
            generation_model = TextGenerationModel.from_pretrained(self.model)
            
            # Generate text
            response = generation_model.predict(
                prompt=prompt,
                temperature=0.2,
                max_output_tokens=1024,
                top_k=40,
                top_p=0.8,
            )
            
            # Parse the response
            try:
                # Try to parse as JSON
                result_text = response.text
                # Find JSON content between curly braces
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                else:
                    # Fallback to default response
                    logger.warning(f"Could not find JSON in response: {result_text}")
                    analysis_result = {
                        "decision": "HOLD",
                        "confidence": 50,
                        "reasoning": "Could not parse LLM response as JSON",
                        "risk_assessment": "medium"
                    }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from response: {response.text}")
                analysis_result = {
                    "decision": "HOLD",
                    "confidence": 50,
                    "reasoning": "Could not parse LLM response as JSON",
                    "risk_assessment": "medium"
                }
                
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error calling PaLM API: {e}")
            raise
    
    def _call_gemini(self, prompt: str) -> Dict:
        """Call Gemini API for text generation"""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # Initialize Vertex AI
            vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=self.location)
            
            # Load the model
            model = GenerativeModel(self.model)
            
            # Generate content
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            # Parse the response
            try:
                # Try to parse as JSON
                result_text = response.text
                # Find JSON content between curly braces
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                else:
                    # Fallback to default response
                    logger.warning(f"Could not find JSON in response: {result_text}")
                    analysis_result = {
                        "decision": "HOLD",
                        "confidence": 50,
                        "reasoning": "Could not parse LLM response as JSON",
                        "risk_assessment": "medium"
                    }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from response: {response.text}")
                analysis_result = {
                    "decision": "HOLD",
                    "confidence": 50,
                    "reasoning": "Could not parse LLM response as JSON",
                    "risk_assessment": "medium"
                }
                
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
    
    def _prepare_market_summary(self, market_data: pd.DataFrame, current_price: float, trading_pair: str) -> Dict:
        """Prepare a summary of market data for the LLM"""
        # Calculate basic metrics
        price_change_24h = ((current_price - market_data['close'].iloc[-24]) / market_data['close'].iloc[-24]) * 100 if len(market_data) >= 24 else 0
        price_change_7d = ((current_price - market_data['close'].iloc[-168]) / market_data['close'].iloc[-168]) * 100 if len(market_data) >= 168 else 0
        
        # Calculate moving averages
        ma_50 = market_data['close'].rolling(window=50).mean().iloc[-1] if len(market_data) >= 50 else None
        ma_200 = market_data['close'].rolling(window=200).mean().iloc[-1] if len(market_data) >= 200 else None
        
        # Calculate volatility (standard deviation of returns)
        returns = market_data['close'].pct_change().dropna()
        volatility = returns.std() * 100  # Convert to percentage
        
        # Prepare volume information
        avg_volume_7d = market_data['volume'].iloc[-168:].mean() if len(market_data) >= 168 else None
        latest_volume = market_data['volume'].iloc[-1]
        
        # Prepare price levels
        recent_high = market_data['high'].iloc[-24:].max() if len(market_data) >= 24 else None
        recent_low = market_data['low'].iloc[-24:].min() if len(market_data) >= 24 else None
        
        return {
            "trading_pair": trading_pair,
            "current_price": current_price,
            "price_change_24h": price_change_24h,
            "price_change_7d": price_change_7d,
            "moving_average_50": ma_50,
            "moving_average_200": ma_200,
            "volatility": volatility,
            "average_volume_7d": avg_volume_7d,
            "latest_volume": latest_volume,
            "recent_high": recent_high,
            "recent_low": recent_low,
            "data_points": len(market_data)
        }
    
    def _create_analysis_prompt(self, market_summary: Dict, trading_pair: str, additional_context: Dict = None) -> str:
        """Create a prompt for the LLM to analyze market data"""
        base_prompt = f"""
Please analyze the following market data for {trading_pair} and provide a trading recommendation:

Market Summary:
- Current Price: ${market_summary['current_price']}
- 24h Price Change: {market_summary['price_change_24h']:.2f}%
- 7d Price Change: {market_summary['price_change_7d']:.2f}%
- 50-period Moving Average: ${market_summary['moving_average_50'] if market_summary['moving_average_50'] else 'N/A'}
- 200-period Moving Average: ${market_summary['moving_average_200'] if market_summary['moving_average_200'] else 'N/A'}
- Volatility: {market_summary['volatility']:.2f}%
- Recent High: ${market_summary['recent_high'] if market_summary['recent_high'] else 'N/A'}
- Recent Low: ${market_summary['recent_low'] if market_summary['recent_low'] else 'N/A'}
- Latest Volume: {market_summary['latest_volume']}
- Average 7d Volume: {market_summary['average_volume_7d'] if market_summary['average_volume_7d'] else 'N/A'}
"""

        if additional_context:
            base_prompt += "\nAdditional Context:\n"
            for key, value in additional_context.items():
                base_prompt += f"- {key}: {value}\n"
        
        base_prompt += """
Based on this information, provide a trading recommendation in the following JSON format:
{
  "decision": "BUY", "SELL", or "HOLD",
  "confidence": [value between 0-100],
  "reasoning": "detailed explanation of your analysis and recommendation",
  "risk_assessment": "low", "medium", or "high",
  "suggested_entry_price": [if BUY decision],
  "suggested_exit_price": [if SELL decision],
  "stop_loss": [suggested stop loss price],
  "take_profit": [suggested take profit price]
}

Respond with ONLY the JSON object and no other text.
"""
        return base_prompt
    def analyze_market(self, data: Dict) -> Dict:
        """
        Alias for analyze_market_data to maintain compatibility with trading_strategy.py
        
        Args:
            data: Dictionary containing market data and indicators
            
        Returns:
            Dictionary with trading decision and analysis
        """
        try:
            # Extract required data from the input dictionary
            product_id = data.get("product_id", "")
            
            # Ensure current_price is a float
            try:
                current_price = float(data.get("current_price", 0.0))
            except (ValueError, TypeError):
                current_price = 0.0
                
            # Get historical data
            historical_data = data.get("historical_data", [])
            
            # Convert historical data to DataFrame and ensure numeric columns
            if historical_data:
                historical_df = pd.DataFrame(historical_data)
                # Convert numeric columns to float
                for col in ['close', 'open', 'high', 'low', 'volume']:
                    if col in historical_df.columns:
                        historical_df[col] = pd.to_numeric(historical_df[col], errors='coerce')
            else:
                historical_df = pd.DataFrame({
                    'close': [current_price],
                    'open': [current_price],
                    'high': [current_price],
                    'low': [current_price],
                    'volume': [0.0]
                })
            
            # Get indicators and market data
            indicators = data.get("indicators", {})
            market_data = data.get("market_data", {})
            
            # Create additional context from indicators
            additional_context = {
                "indicators": indicators,
                "market_data": market_data
            }
            
            # Call the actual analysis method
            return self.analyze_market_data(
                market_data=historical_df,
                current_price=current_price,
                trading_pair=product_id,
                additional_context=additional_context
            )
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            return {
                "decision": "HOLD",
                "confidence": 0,
                "reasoning": [f"Error during analysis: {str(e)}"]
            }
