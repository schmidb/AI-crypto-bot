import logging
import json
import re
from typing import Dict, List, Any
import pandas as pd
import os
import google.genai as genai  # NEW google-genai library
from google.genai import types
from google.oauth2 import service_account

from config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_APPLICATION_CREDENTIALS,
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_FALLBACK_MODEL,
    LLM_LOCATION,
    TRADING_STYLE,
    TRADING_TIMEFRAME,
    EXPECTED_HOLDING_PERIOD,
    DECISION_INTERVAL_MINUTES
)

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """Uses NEW google-genai library with genai.Client() to analyze market data and make trading decisions"""

    def __init__(self,
                provider: str = LLM_PROVIDER,
                model: str = LLM_MODEL,
                fallback_model: str = LLM_FALLBACK_MODEL,
                location: str = LLM_LOCATION):
        """Initialize the LLM analyzer following AI_MODEL_STEERING.md guidelines"""
        self.provider = provider
        self.model = model
        self.fallback_model = fallback_model
        self.location = location

        # Initialize NEW google-genai library with genai.Client()
        try:
            if GOOGLE_APPLICATION_CREDENTIALS:
                # Option 1: Service Account (Recommended for Production)
                credentials = service_account.Credentials.from_service_account_file(
                    GOOGLE_APPLICATION_CREDENTIALS,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                
                self.client = genai.Client(
                    vertexai=True,  # CRITICAL: Use Vertex AI for service account authentication
                    project=GOOGLE_CLOUD_PROJECT,
                    location=self.location,
                    credentials=credentials
                )
                
                logger.info(f"Initialized NEW google-genai library with service account credentials (Vertex AI)")
                
            elif os.getenv('GOOGLE_AI_API_KEY'):
                # Option 2: API Key (Alternative) - uses Google AI Studio
                api_key = os.getenv('GOOGLE_AI_API_KEY')
                
                self.client = genai.Client(
                    vertexai=False,  # Use Google AI Studio for API key authentication
                    api_key=api_key
                )
                
                logger.info("Initialized NEW google-genai library with API key authentication (Google AI Studio)")
                
            else:
                # Option 3: Default Credentials (ADC) - uses Vertex AI
                self.client = genai.Client(
                    vertexai=True,  # CRITICAL: Use Vertex AI for GCP default credentials
                    project=GOOGLE_CLOUD_PROJECT,
                    location=self.location
                )
                
                logger.info("Initialized NEW google-genai library with default credentials (Vertex AI)")
                
            logger.info(f"Models: {self.model} (primary), {self.fallback_model} (fallback)")
            logger.info(f"Location: {self.location} (required for preview models)")
            
        except Exception as e:
            logger.error(f"Failed to initialize NEW google-genai library: {e}")
            raise ValueError(f"Could not initialize google-genai client: {str(e)}")

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
        try:
            # Prepare market data summary
            market_summary = self._prepare_market_summary(market_data, current_price, trading_pair)

            # Prepare prompt for LLM
            prompt = self._create_analysis_prompt(market_summary, trading_pair, additional_context)

            # Call Google GenAI
            analysis_result = self._call_genai(prompt)
            
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

    def _call_genai(self, prompt: str) -> Dict:
        """Call NEW google-genai library for text generation"""
        try:
            # Enhanced prompt with strict JSON formatting instructions
            enhanced_prompt = f"""
{prompt}

CRITICAL: Respond with ONLY valid JSON. No explanations, no markdown, no extra text.

Required format (copy this structure exactly):
{{"decision": "BUY", "confidence": 75, "reasoning": ["reason1", "reason2"], "risk_assessment": "medium"}}

Rules:
- decision: Must be "BUY", "SELL", or "HOLD"
- confidence: Integer 0-100
- reasoning: Array of 2-3 short strings
- risk_assessment: Must be "low", "medium", or "high"

Your JSON response:
"""

            try:
                # Try primary model first using NEW google-genai API
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[enhanced_prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.1,  # Lower temperature for more consistent formatting
                        max_output_tokens=500,  # Reduced to force concise responses
                        top_p=0.9,
                        top_k=20
                    )
                )
                
                # Extract the response text
                prediction_text = response.text if hasattr(response, 'text') and response.text else str(response)
                
            except Exception as primary_error:
                logger.warning(f"Primary model {self.model} failed: {primary_error}, trying fallback")
                
                # Try fallback model with same strict config
                response = self.client.models.generate_content(
                    model=self.fallback_model,
                    contents=[enhanced_prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.1,  # Lower temperature for consistency
                        max_output_tokens=500,  # Reduced for concise responses
                        top_p=0.9,
                        top_k=20
                    )
                )
                
                # Extract the response text
                prediction_text = response.text if hasattr(response, 'text') and response.text else str(response)
                logger.info(f"Successfully used fallback model: {self.fallback_model}")
            
            logger.debug(f"GenAI response: {prediction_text[:100]}...")

            # Parse the response to extract trading decision
            return self._parse_llm_response(prediction_text)

        except Exception as e:
            logger.error(f"Error calling NEW google-genai library: {e}")
            # Return safe fallback analysis
            return {
                'decision': 'HOLD',
                'confidence': 0,
                'reasoning': [f'AI analysis unavailable: {str(e)}', 'Defaulting to HOLD for safety'],
                'risk_assessment': 'HIGH',
                'technical_indicators': {},
                'fallback_used': True
            }

    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse the LLM response to extract trading decision with robust error handling"""
        import re
        
        try:
            # Clean the response
            response_text = response_text.strip()
            
            # Remove markdown code blocks
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            
            # Find JSON object - look for outermost braces
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                
                # Fix common JSON formatting issues
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # Remove trailing commas
                json_str = re.sub(r'(\])\s*\n\s*"', r'\1,\n  "', json_str)  # Add missing commas after arrays
                json_str = re.sub(r'(\})\s*\n\s*"', r'\1,\n  "', json_str)  # Add missing commas after objects
                
                # Parse JSON
                analysis_result = json.loads(json_str)
                
                # Validate required fields
                if 'decision' not in analysis_result or 'confidence' not in analysis_result:
                    raise ValueError("Missing required fields: decision or confidence")
                
                # Normalize and validate
                analysis_result['decision'] = str(analysis_result['decision']).upper()
                if analysis_result['decision'] not in ['BUY', 'SELL', 'HOLD']:
                    raise ValueError(f"Invalid decision: {analysis_result['decision']}")
                
                analysis_result['confidence'] = int(float(analysis_result['confidence']))
                if not 0 <= analysis_result['confidence'] <= 100:
                    analysis_result['confidence'] = max(0, min(100, analysis_result['confidence']))
                
                # Ensure reasoning is a list
                if 'reasoning' not in analysis_result:
                    analysis_result['reasoning'] = ["LLM analysis completed"]
                elif isinstance(analysis_result['reasoning'], str):
                    analysis_result['reasoning'] = [analysis_result['reasoning']]
                
                # Ensure risk_assessment exists and is valid
                if 'risk_assessment' not in analysis_result:
                    analysis_result['risk_assessment'] = 'medium'
                else:
                    risk = str(analysis_result['risk_assessment']).lower()
                    if risk not in ['low', 'medium', 'high']:
                        analysis_result['risk_assessment'] = 'medium'
                    else:
                        analysis_result['risk_assessment'] = risk
                    
                return analysis_result
            else:
                raise ValueError("No JSON structure found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: Extract fields using regex
            logger.warning(f"JSON parse failed, using regex extraction: {str(e)[:80]}")
            
            try:
                # Try multiple extraction patterns
                
                # Pattern 1: Standard JSON fields
                decision_match = re.search(r'"?decision"?\s*:\s*"?(BUY|SELL|HOLD)"?', response_text, re.IGNORECASE)
                confidence_match = re.search(r'"?confidence"?\s*:\s*(\d+)', response_text)
                
                # Pattern 2: Look for decision/action words in text
                if not decision_match:
                    if re.search(r'\b(buy|buying|purchase)\b', response_text, re.IGNORECASE):
                        decision = "BUY"
                    elif re.search(r'\b(sell|selling)\b', response_text, re.IGNORECASE):
                        decision = "SELL"
                    else:
                        decision = "HOLD"
                else:
                    decision = decision_match.group(1).upper()
                
                # Pattern 3: Extract confidence from various formats
                if confidence_match:
                    confidence = int(confidence_match.group(1))
                else:
                    # Look for percentage patterns
                    pct_match = re.search(r'(\d+)\s*%', response_text)
                    confidence = int(pct_match.group(1)) if pct_match else 65
                
                # Clamp confidence to valid range
                confidence = max(0, min(100, confidence))
                
                # Extract risk assessment
                risk_match = re.search(r'"?risk_assessment"?\s*:\s*"?(low|medium|high)"?', response_text, re.IGNORECASE)
                risk = risk_match.group(1).lower() if risk_match else "medium"
                
                # Extract reasoning array
                reasoning = []
                reasoning_match = re.search(r'"?reasoning"?\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
                if reasoning_match:
                    reasons_text = reasoning_match.group(1)
                    reasoning = re.findall(r'"([^"]+)"', reasons_text)
                
                if not reasoning:
                    reasoning = [f"Extracted {decision} signal from LLM response"]
                
                logger.info(f"✓ Regex extraction successful: {decision} ({confidence}%)")
                return {
                    "decision": decision,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "risk_assessment": risk,
                    "partial_parse": True
                }
                    
            except Exception as extract_error:
                logger.warning(f"Regex extraction failed: {extract_error}")
            
            # Final fallback
            logger.warning("Using safe fallback response")
            return {
                "decision": "HOLD",
                "confidence": 50,
                "reasoning": ["Could not parse LLM response"],
                "risk_assessment": "medium",
                "parse_failed": True
            }

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

        # Add portfolio balance context if available
        if additional_context and "portfolio" in additional_context:
            portfolio = additional_context["portfolio"]
            eur_balance = portfolio.get('EUR', {}).get('amount', 0)
            portfolio_value = portfolio.get('portfolio_value_eur', {}).get('amount', 1)
            eur_pct = (eur_balance / portfolio_value) * 100 if portfolio_value > 0 else 0
            
            # Get target from config
            from config import config
            target_eur_pct = config.TARGET_EUR_ALLOCATION
            
            base_prompt += f"""

PORTFOLIO BALANCE CONTEXT:
- EUR Available: €{eur_balance:.2f}
- EUR Allocation: {eur_pct:.1f}% (Target: {target_eur_pct:.0f}%)
- Portfolio Value: €{portfolio_value:.2f}"""
            
            # Add capital constraint guidance
            if eur_pct < target_eur_pct * 0.6:  # Critical low
                base_prompt += f"""
- ⚠️ CRITICAL: EUR balance is VERY LOW ({eur_pct:.1f}% vs {target_eur_pct:.0f}% target)
- STRONGLY PREFER SELL signals to replenish EUR reserves
- Avoid BUY signals unless extremely compelling (>85% confidence)"""
            elif eur_pct < target_eur_pct:  # Below target
                base_prompt += f"""
- ⚠️ WARNING: EUR balance is below target ({eur_pct:.1f}% vs {target_eur_pct:.0f}%)
- PREFER SELL signals to increase EUR reserves
- Be cautious with BUY signals"""
            elif eur_pct > target_eur_pct * 1.5:  # Too much cash
                base_prompt += f"""
- ✅ EUR balance is HIGH ({eur_pct:.1f}% vs {target_eur_pct:.0f}% target)
- Good opportunity for BUY signals
- Consider deploying excess capital"""

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

        # Add request for simplified JSON response (more reliable)
        base_prompt += """

RESPONSE FORMAT (CRITICAL):
Respond with ONLY this JSON structure. No other text.

{
  "decision": "BUY",
  "confidence": 75,
  "reasoning": ["reason 1", "reason 2"],
  "risk_assessment": "medium"
}

RULES:
- decision: "BUY", "SELL", or "HOLD" (uppercase)
- confidence: 0-100 (integer)
- reasoning: 2-4 short strings
- risk_assessment: "low", "medium", or "high" (lowercase)

Start response with {:
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
            portfolio = data.get("portfolio", {})  # Get portfolio data
            
            # Debug logging to verify LLM input data
            logger.info(f"🔍 LLM INPUT DEBUG for {product_id}:")
            logger.info(f"  Current Price: {current_price}")
            logger.info(f"  Market Data: {market_data}")
            logger.info(f"  Key Indicators:")
            for key in ['rsi', 'macd', 'macd_histogram', 'bb_upper', 'bb_lower', 'bb_middle']:
                if key in indicators:
                    logger.info(f"    {key}: {indicators[key]}")
            logger.info(f"  Historical Data Points: {len(historical_data)}")
            
            # Log portfolio context if available
            if portfolio:
                eur_balance = portfolio.get('EUR', {}).get('amount', 0)
                portfolio_value = portfolio.get('portfolio_value_eur', {}).get('amount', 1)
                eur_pct = (eur_balance / portfolio_value) * 100 if portfolio_value > 0 else 0
                logger.info(f"  Portfolio: EUR €{eur_balance:.2f} ({eur_pct:.1f}%)")

            # Create additional context from indicators and portfolio
            additional_context = {
                "indicators": indicators,
                "market_data": market_data,
                "portfolio": portfolio  # Include portfolio in context
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
        """Get response from LLM using NEW google-genai library"""
        try:
            # Call NEW google-genai library directly
            result = self._call_genai(prompt)
            # Convert dict response to JSON string for compatibility
            import json
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return f"ERROR: {str(e)}"
