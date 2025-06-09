import logging
import json
import re
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

# Define OAuth scopes needed for Vertex AI
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/cloud-language'
]

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
                    GOOGLE_APPLICATION_CREDENTIALS,
                    scopes=SCOPES  # Add the scopes here
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
            # Use default credentials with scopes
            try:
                credentials, _ = google.auth.default(scopes=SCOPES)  # Add scopes here too
                aiplatform.init(
                    project=GOOGLE_CLOUD_PROJECT,
                    location=self.location,
                    credentials=credentials
                )
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
            # Determine if we should use streaming endpoint
            use_streaming = "gemini" in self.model.lower()

            # Create the endpoint URL
            endpoint_suffix = "generateContent" if use_streaming else "predict"  # Changed from streamGenerateContent to generateContent
            url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{GOOGLE_CLOUD_PROJECT}/locations/{self.location}/publishers/google/models/{self.model}:{endpoint_suffix}"

            # Log the URL being called
            logger.debug(f"Calling Vertex AI endpoint: {url}")

            # Enhance prompt to explicitly request JSON
            enhanced_prompt = f"""
            {prompt}

            IMPORTANT: Your response MUST be in valid JSON format with the following structure:
            {{
              "decision": "BUY|SELL|HOLD",
              "confidence": <number between 0-100>,
              "reasoning": ["reason1", "reason2", "reason3"],
              "risk_assessment": "low|medium|high"
            }}

            Do not include any text outside of the JSON structure.
            """

            # Create the request payload based on model type
            if use_streaming:
                # Gemini model format
                payload = {
                    "contents": [{
                        "role": "user",
                        "parts": [
                            {
                                "text": enhanced_prompt
                            }
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 10000,  # Increased from 1024 to 4096
                        "topP": 0.8,
                        "topK": 40
                    }
                }
            else:
                # Standard text model format (text-bison, etc.)
                payload = {
                    "instances": [{"prompt": enhanced_prompt}],
                    "parameters": {
                        "temperature": 0.2,
                        "maxOutputTokens": 10000,  # Increased from 1024 to 4096
                        "topP": 0.8,
                        "topK": 40
                    }
                }

            # Get the access token with the proper scopes
            if hasattr(self, 'credentials'):
                credentials = self.credentials
            else:
                credentials, _ = google.auth.default(scopes=SCOPES)

            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)

            # Make the request
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json"
            }

            # Log the payload (excluding sensitive data)
            logger.debug(f"Sending request to Vertex AI with payload structure: {list(payload.keys())}")

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            # Log the raw response for debugging
            logger.debug(f"Raw response from Vertex AI: {response.text}")

            # Extract the prediction text based on model type
            response_json = response.json()
            logger.debug(f"Response JSON structure: {list(response_json.keys()) if isinstance(response_json, dict) else 'Not a dictionary'}")

            if use_streaming:
                # Handle Gemini response
                prediction_text = ""

                # Try different response structures
                if isinstance(response_json, dict):
                    # Try candidates path
                    candidates = response_json.get("candidates", [])
                    if candidates and isinstance(candidates, list) and len(candidates) > 0:
                        content = candidates[0].get("content", {})
                        if content:
                            parts = content.get("parts", [])
                            if parts and len(parts) > 0:
                                part = parts[0]
                                if isinstance(part, dict):
                                    prediction_text = part.get("text", "")
                                else:
                                    prediction_text = str(part)

                    # Try text path
                    if not prediction_text and "text" in response_json:
                        prediction_text = response_json["text"]

                    # Try content path
                    if not prediction_text and "content" in response_json:
                        content = response_json["content"]
                        if isinstance(content, dict) and "text" in content:
                            prediction_text = content["text"]
                        else:
                            prediction_text = str(content)

                # If still no text, use the whole response
                if not prediction_text:
                    prediction_text = str(response_json)
            else:
                # Handle standard response
                if isinstance(response_json, dict):
                    predictions = response_json.get("predictions", [])
                    prediction_text = predictions[0] if predictions else ""
                else:
                    prediction_text = str(response_json)

            # Log the extracted prediction text
            logger.debug(f"Extracted prediction text: {prediction_text[:100]}...")

            # Parse the response to extract trading decision
            return self._parse_llm_response(prediction_text)

        except Exception as e:
            logger.error(f"Error calling Vertex AI: {e}")
            raise

    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse the LLM response to extract trading decision"""
        try:
            # Try to parse as JSON
            # Find JSON content between curly braces
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                analysis_result = json.loads(json_str)
            else:
                # Fallback to default response
                logger.warning(f"Could not find JSON in response: {response_text}")
                analysis_result = {
                    "decision": "HOLD",
                    "confidence": 50,
                    "reasoning": "Could not parse LLM response as JSON",
                    "risk_assessment": "medium"
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from response: {str(response_text)}")
            analysis_result = {
                "decision": "HOLD",
                "confidence": 50,
                "reasoning": "Could not parse LLM response as JSON",
                "risk_assessment": "medium"
            }

        return analysis_result

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
                max_output_tokens=10000,  # Increased from 1024 to 4096
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
                    "max_output_tokens": 10000,  # Increased from 1024 to 4096
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
        # Format values safely
        price_24h = f"{market_summary['price_change_24h']:.2f}%" if market_summary['price_change_24h'] is not None else "N/A"
        price_7d = f"{market_summary['price_change_7d']:.2f}%" if market_summary['price_change_7d'] is not None else "N/A"
        ma50 = f"${market_summary['moving_average_50']:.2f}" if market_summary['moving_average_50'] is not None else "N/A"
        ma200 = f"${market_summary['moving_average_200']:.2f}" if market_summary['moving_average_200'] is not None else "N/A"
        volatility = f"{market_summary['volatility']:.2f}%" if market_summary['volatility'] is not None else "N/A"

        # Create a more concise prompt to reduce token usage
        base_prompt = f"""Analyze {trading_pair} market data and provide a trading recommendation.

Price: ${market_summary['current_price']}
24h Change: {price_24h}
7d Change: {price_7d}
MA50: {ma50}
MA200: {ma200}
Volatility: {volatility}"""

        # Add technical indicators if available
        if additional_context and "indicators" in additional_context:
            indicators = additional_context["indicators"]
            if indicators:
                rsi = f"{indicators.get('rsi'):.1f}" if indicators.get('rsi') is not None else "N/A"
                macd = f"{indicators.get('macd_line'):.2f}" if indicators.get('macd_line') is not None else "N/A"
                signal = f"{indicators.get('macd_signal'):.2f}" if indicators.get('macd_signal') is not None else "N/A"
                bb_width = f"{indicators.get('bollinger_width'):.2f}" if indicators.get('bollinger_width') is not None else "N/A"

                base_prompt += f"""
RSI: {rsi}
MACD: {macd}
Signal: {signal}
BB Width: {bb_width}"""

        # Add request for JSON response
        base_prompt += """

Respond with ONLY a JSON object in this format:
{
  "decision": "BUY|SELL|HOLD",
  "confidence": <0-100>,
  "reasoning": ["reason1", "reason2"],
  "risk_assessment": "low|medium|high"
}"""
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
    def get_trading_decision(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get trading decision from LLM based on market analysis

        Args:
            analysis_data: Dictionary with market data and indicators

        Returns:
            Dictionary with trading decision
        """
        try:
            # Extract key data for the prompt
            product_id = analysis_data.get("product_id", "")
            current_price = analysis_data.get("current_price", 0)
            indicators = analysis_data.get("indicators", {})
            risk_level = analysis_data.get("risk_level", "medium")

            # Create prompt for LLM
            prompt = self._create_trading_prompt(
                product_id=product_id,
                current_price=current_price,
                indicators=indicators,
                risk_level=risk_level
            )

            # Get response from LLM
            response = self._get_llm_response(prompt)

            # Parse response to extract decision
            decision = self._parse_trading_decision(response)

            return decision

        except Exception as e:
            logger.error(f"Error getting trading decision: {e}")
            return {"action": "hold", "confidence": 0, "reason": f"Error: {str(e)}"}

    def _create_trading_prompt(self, product_id: str, current_price: float,
                              indicators: Dict[str, Any], risk_level: str) -> str:
        """Create prompt for LLM to analyze market data and make trading decision"""

        # Extract indicator values for cleaner prompt
        rsi_value = indicators.get("rsi", {}).get("value", "N/A")
        rsi_signal = indicators.get("rsi", {}).get("signal", "N/A")

        macd_value = indicators.get("macd", {}).get("value", "N/A")
        macd_signal = indicators.get("macd", {}).get("signal", "N/A")
        macd_trend = indicators.get("macd", {}).get("trend", "N/A")

        bb_upper = indicators.get("bollinger_bands", {}).get("upper", "N/A")
        bb_middle = indicators.get("bollinger_bands", {}).get("middle", "N/A")
        bb_lower = indicators.get("bollinger_bands", {}).get("lower", "N/A")
        bb_signal = indicators.get("bollinger_bands", {}).get("signal", "N/A")

        prompt = f"""
        You are an expert cryptocurrency trading advisor. Analyze the following market data for {product_id} and provide a trading decision.
        Use the new lowered thresholds and improved indicator logic for more active trading.

        Current price: ${current_price}
        Risk level: {risk_level} (Note: High risk reduces position size but doesn't prevent trades)

        TECHNICAL ANALYSIS (Weighted Decision):
        1. MACD (40% weight): {macd_value} (Trend: {macd_trend})
           - Primary trend indicator
           - Strong buy signal if positive and trending up
           - Strong sell signal if negative and trending down

        2. RSI (30% weight): {rsi_value} ({rsi_signal})
           - Narrowed ranges: < 45 oversold (buy), > 55 overbought (sell)
           - 45-55 is neutral zone
           - Trend confirmation when aligned with MACD

        3. Bollinger Bands (30% weight): 
           - Current: {bb_signal}
           - Upper: ${bb_upper}
           - Middle: ${bb_middle}
           - Lower: ${bb_lower}
           - Breakouts with trend confirmation are strong signals

        TRADING THRESHOLDS (Lowered for More Activity):
        - Buy signals need only 60% confidence (was 80%)
        - Sell signals need only 60% confidence (was 80%)
        - Add 10% confidence when multiple indicators align
        - Subtract 5% confidence for counter-trend signals

        RISK ADJUSTMENTS:
        - High risk: Reduce position size by 50%
        - Medium risk: Reduce position size by 25%
        - Low risk: Full position size

        Based on this data, provide a trading decision in the following format:
        ACTION: [buy/sell/hold]
        CONFIDENCE: [0-100]
        REASON: [brief explanation including specific indicator analysis]
        """

        return prompt

    def _parse_trading_decision(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract trading decision"""

        # Default decision (hold with 0 confidence)
        decision = {
            "action": "hold",
            "confidence": 0,
            "reason": "No clear signal"
        }

        try:
            # Extract action
            if "ACTION: buy" in response.lower():
                decision["action"] = "buy"
            elif "ACTION: sell" in response.lower():
                decision["action"] = "sell"

            # Extract confidence
            confidence_match = re.search(r"CONFIDENCE: (\d+)", response)
            if confidence_match:
                confidence = int(confidence_match.group(1))
                decision["confidence"] = min(max(confidence, 0), 100)  # Ensure between 0-100

            # Extract reason
            reason_match = re.search(r"REASON: (.*?)($|\n)", response, re.DOTALL)
            if reason_match:
                decision["reason"] = reason_match.group(1).strip()

            return decision

        except Exception as e:
            logger.error(f"Error parsing trading decision: {e}")
            return decision
    def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM"""
        try:
            # Normalize provider name to handle different variations
            provider_normalized = self.provider.lower().replace('_', '')

            if provider_normalized == "vertex" or provider_normalized == "vertexai":
                if "gemini" in self.model.lower():
                    return self._call_gemini(prompt)
                elif "palm" in self.model.lower() or "text-bison" in self.model.lower():
                    return self._call_palm(prompt)
                else:
                    return self._call_vertex_ai(prompt)
            else:
                logger.error(f"Unsupported LLM provider: {self.provider}")
                return "ERROR: Unsupported LLM provider"
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return f"ERROR: {str(e)}"
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API using direct REST API approach"""
        try:
            # Log the model name being used
            logger.info(f"Using model: {self.model}")

            # Get authentication token
            import subprocess
            auth_process = subprocess.run(
                ["gcloud", "auth", "application-default", "print-access-token"],
                capture_output=True,
                text=True,
                check=True
            )
            auth_token = auth_process.stdout.strip()

            # Determine model ID - ensure we're mapping to the correct API model name
            model_id = None

            # Normalize model name for comparison
            model_id = self.model.lower()

            logger.info(f"Mapped model name '{self.model}' to API model ID: {model_id}")

            # Prepare request
            url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{GOOGLE_CLOUD_PROJECT}/locations/{self.location}/publishers/google/models/{model_id}:generateContent"

            logger.info(f"Making API request to: {url}")

            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 10000,
                    "topP": 0.8,
                    "topK": 40
                }
            }

            # Make the API call
            import requests
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raise exception for HTTP errors

            # Parse the response
            response_json = response.json()

            # Extract text from response
            try:
                text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                return text
            except (KeyError, IndexError):
                logger.warning(f"Unexpected response format: {response_json}")
                return str(response_json)

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            # Fallback to a default trading decision
            return """
            ACTION: hold
            CONFIDENCE: 50
            REASON: Unable to connect to Gemini API for analysis. Defaulting to hold position as a precaution.
            """
