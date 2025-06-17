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
from google.oauth2 import service_account

from config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_APPLICATION_CREDENTIALS,
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_LOCATION,
    TRADING_STYLE,
    TRADING_TIMEFRAME,
    EXPECTED_HOLDING_PERIOD,
    DECISION_INTERVAL_MINUTES
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
            # Call Vertex AI
            analysis_result = self._call_vertex_ai(prompt)
            
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
              "reasoning": ["detailed reason 1", "detailed reason 2", "detailed reason 3"],
              "risk_assessment": "low|medium|high",
              "technical_indicators": {{
                "rsi": {{
                  "value": <rsi_value>,
                  "signal": "oversold|neutral|overbought",
                  "weight": 0.3
                }},
                "macd": {{
                  "macd_line": <macd_value>,
                  "signal_line": <signal_value>,
                  "histogram": <histogram_value>,
                  "signal": "bullish|bearish|neutral",
                  "weight": 0.4
                }},
                "bollinger_bands": {{
                  "signal": "breakout_upper|breakout_lower|squeeze|normal",
                  "weight": 0.3
                }}
              }},
              "market_conditions": {{
                "trend": "bullish|bearish|sideways",
                "volatility": "low|moderate|high",
                "volume": "below_average|average|above_average"
              }}
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
        """Create a prompt for the LLM to analyze market data with trading style context"""
        # Format values safely
        price_24h = f"{market_summary['price_change_24h']:.2f}%" if market_summary['price_change_24h'] is not None else "N/A"
        price_7d = f"{market_summary['price_change_7d']:.2f}%" if market_summary['price_change_7d'] is not None else "N/A"
        ma50 = f"${market_summary['moving_average_50']:.2f}" if market_summary['moving_average_50'] is not None else "N/A"
        ma200 = f"${market_summary['moving_average_200']:.2f}" if market_summary['moving_average_200'] is not None else "N/A"
        volatility = f"{market_summary['volatility']:.2f}%" if market_summary['volatility'] is not None else "N/A"

        # Determine trading style description
        style_descriptions = {
            "day_trading": "Day Trading / Intraday Trading",
            "swing_trading": "Swing Trading / Short-term Position Trading", 
            "long_term": "Long-term Investment / Position Trading"
        }
        
        timeframe_descriptions = {
            "short_term": "Short-term (minutes to hours)",
            "medium_term": "Medium-term (hours to days)",
            "long_term": "Long-term (days to weeks)"
        }
        
        style_desc = style_descriptions.get(TRADING_STYLE, "Day Trading")
        timeframe_desc = timeframe_descriptions.get(TRADING_TIMEFRAME, "Short-term")

        # Create enhanced prompt with trading context
        base_prompt = f"""You are an AI trading advisor for {style_desc.upper()} operations.

TRADING CONTEXT:
- Strategy: {style_desc}
- Timeframe: {timeframe_desc}
- Decision Frequency: Every {DECISION_INTERVAL_MINUTES} minutes
- Expected Holding Period: {EXPECTED_HOLDING_PERIOD}
- Focus: {"Capitalize on intraday movements and short-term trends" if TRADING_STYLE == "day_trading" else "Medium-term trend following and momentum trading" if TRADING_STYLE == "swing_trading" else "Long-term value and growth investing"}

MARKET DATA for {trading_pair}:
Price: ${market_summary['current_price']}
24h Change: {price_24h}
7d Change: {price_7d}
MA50: {ma50}
MA200: {ma200}
Volatility: {volatility}"""

        # Add optimized technical indicators if available
        if additional_context and "indicators" in additional_context:
            indicators = additional_context["indicators"]
            if indicators:
                # Get trading style specific indicator info
                metadata = indicators.get('_metadata', {})
                bb_timeframe = metadata.get('bb_timeframe_hours', 20)
                trading_style = metadata.get('trading_style', 'unknown')
                
                rsi = f"{indicators.get('rsi'):.1f}" if indicators.get('rsi') is not None else "N/A"
                macd = f"{indicators.get('macd'):.4f}" if indicators.get('macd') is not None else "N/A"
                signal = f"{indicators.get('macd_signal'):.4f}" if indicators.get('macd_signal') is not None else "N/A"
                histogram = f"{indicators.get('macd_histogram'):.4f}" if indicators.get('macd_histogram') is not None else "N/A"
                
                bb_upper = f"${indicators.get('bb_upper'):.2f}" if indicators.get('bb_upper') is not None else "N/A"
                bb_middle = f"${indicators.get('bb_middle'):.2f}" if indicators.get('bb_middle') is not None else "N/A"
                bb_lower = f"${indicators.get('bb_lower'):.2f}" if indicators.get('bb_lower') is not None else "N/A"
                bb_width = f"{indicators.get('bb_width'):.2f}%" if indicators.get('bb_width') is not None else "N/A"
                bb_position = f"{indicators.get('bb_position'):.2f}" if indicators.get('bb_position') is not None else "N/A"

                base_prompt += f"""

OPTIMIZED TECHNICAL INDICATORS (for {trading_style.upper()}):
RSI (14): {rsi}
MACD: {macd} | Signal: {signal} | Histogram: {histogram}
Bollinger Bands ({bb_timeframe}h timeframe):
  - Upper: {bb_upper}
  - Middle: {bb_middle}  
  - Lower: {bb_lower}
  - Width: {bb_width} (volatility measure)
  - Position: {bb_position} (0=lower band, 1=upper band, 0.5=middle)"""

                # Add day trading specific indicators
                if TRADING_STYLE == "day_trading":
                    if 'stoch_rsi' in indicators:
                        stoch_rsi = f"{indicators.get('stoch_rsi'):.1f}" if indicators.get('stoch_rsi') is not None else "N/A"
                        base_prompt += f"""
Stochastic RSI: {stoch_rsi} (day trading momentum)"""
                    
                    if 'vwap' in indicators:
                        vwap = f"${indicators.get('vwap'):.2f}" if indicators.get('vwap') is not None else "N/A"
                        base_prompt += f"""
VWAP: {vwap} (volume-weighted average price)"""

        # Add trading style specific instructions
        if TRADING_STYLE == "day_trading":
            base_prompt += """

DAY TRADING ANALYSIS REQUIREMENTS:
- Prioritize short-term momentum and trend reversals
- Focus on 1-4 hour price movements rather than daily/weekly trends
- **CRITICAL**: Bollinger Bands are now calculated on 4-hour timeframe (optimal for day trading)
- Consider intraday support/resistance levels
- Evaluate volatility for quick profit opportunities
- Assess liquidity for fast entry/exit capability
- Weight recent price action more heavily than long-term trends
- Use BB position: <0.2 = oversold, >0.8 = overbought, 0.4-0.6 = neutral zone

BOLLINGER BANDS INTERPRETATION (4-hour timeframe):
- BB Position < 0.2: Strong oversold, potential BUY signal
- BB Position > 0.8: Strong overbought, potential SELL signal  
- BB Width > 4%: High volatility, good for breakout trades
- BB Width < 2%: Low volatility, expect breakout soon
- Price touching upper band + high RSI (>70): Strong SELL signal
- Price touching lower band + low RSI (<30): Strong BUY signal

DECISION CRITERIA for Day Trading:
- BUY: Strong short-term upward momentum, oversold conditions with reversal signals, BB position < 0.3
- SELL: Profit-taking opportunities, overbought conditions, momentum weakening, BB position > 0.7
- HOLD: Unclear short-term direction, low volatility, waiting for better entry/exit points"""

        elif TRADING_STYLE == "swing_trading":
            base_prompt += """

SWING TRADING ANALYSIS REQUIREMENTS:
- Focus on 1-7 day price movements and trend continuations
- Identify swing highs and lows for entry/exit points
- Consider both technical and fundamental momentum
- Evaluate medium-term trend strength and sustainability
- Balance short-term signals with longer-term context
- Bollinger Bands calculated on 20-hour timeframe (standard for swing trading)

DECISION CRITERIA for Swing Trading:
- BUY: Trend continuation signals, breakouts from consolidation, oversold bounces
- SELL: Trend exhaustion signals, resistance levels, profit targets reached
- HOLD: Consolidation phases, mixed signals, waiting for clearer direction"""

        else:  # long_term
            base_prompt += """

LONG-TERM TRADING ANALYSIS REQUIREMENTS:
- Focus on weekly and monthly trends and fundamentals
- Consider long-term value propositions and market cycles
- Evaluate sustainable growth patterns and adoption trends
- Balance technical analysis with fundamental strength
- Prioritize position building over quick profits
- Bollinger Bands calculated on 50-hour timeframe (smoothed for long-term)

DECISION CRITERIA for Long-term Trading:
- BUY: Strong fundamental outlook, major trend reversals, accumulation opportunities
- SELL: Fundamental deterioration, major trend breaks, profit realization
- HOLD: Stable trends, minor corrections, building positions gradually"""

        # Add request for enhanced JSON response
        base_prompt += """

Respond with ONLY a JSON object in this format:
{
  "decision": "BUY|SELL|HOLD",
  "confidence": <0-100>,
  "reasoning": ["detailed reason 1", "detailed reason 2", "detailed reason 3"],
  "risk_assessment": "low|medium|high",
  "timeframe_analysis": {
    "short_term_trend": "bullish|bearish|neutral",
    "momentum_strength": "strong|moderate|weak",
    "entry_timing": "excellent|good|poor"
  },
  "technical_indicators": {
    "rsi": {
      "value": <rsi_value>,
      "signal": "oversold|neutral|overbought",
      "weight": 0.3
    },
    "macd": {
      "macd_line": <macd_value>,
      "signal_line": <signal_value>,
      "histogram": <histogram_value>,
      "signal": "bullish|bearish|neutral",
      "weight": 0.4
    },
    "bollinger_bands": {
      "signal": "breakout_upper|breakout_lower|squeeze|normal",
      "position": <bb_position_value>,
      "timeframe_hours": <bb_timeframe>,
      "weight": 0.3
    }
  },
  "market_conditions": {
    "trend": "bullish|bearish|sideways",
    "volatility": "low|moderate|high",
    "volume": "below_average|average|above_average"
  }
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
            # Extract action - check for all possible actions including HOLD
            response_lower = response.lower()
            if "action: buy" in response_lower:
                decision["action"] = "buy"
            elif "action: sell" in response_lower:
                decision["action"] = "sell"
            elif "action: hold" in response_lower:
                decision["action"] = "hold"

            # Extract confidence
            confidence_match = re.search(r"CONFIDENCE:\s*(\d+)", response, re.IGNORECASE)
            if confidence_match:
                confidence = int(confidence_match.group(1))
                decision["confidence"] = min(max(confidence, 0), 100)  # Ensure between 0-100

            # Extract reason - improved regex to capture multi-line reasons
            reason_match = re.search(r"REASON:\s*(.*?)(?=\n\s*$|\Z)", response, re.DOTALL | re.IGNORECASE)
            if reason_match:
                reason_text = reason_match.group(1).strip()
                # Clean up the reason text - remove extra whitespace, line breaks, and formatting
                reason_text = re.sub(r'\s+', ' ', reason_text)
                reason_text = re.sub(r'^\*+\s*', '', reason_text)  # Remove leading asterisks
                reason_text = re.sub(r'\s*\*+$', '', reason_text)  # Remove trailing asterisks
                decision["reason"] = reason_text

            return decision

        except Exception as e:
            logger.error(f"Error parsing trading decision: {e}")
            return decision
    def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM using Vertex AI"""
        try:
            # Call Vertex AI directly
            result = self._call_vertex_ai(prompt)
            # Convert dict response to JSON string for compatibility
            import json
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return f"ERROR: {str(e)}"
