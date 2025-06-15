# Enhanced LLM Prompt with Trading Style Context
# Add this to your _create_analysis_prompt method

def _create_analysis_prompt_enhanced(self, market_summary: Dict, trading_pair: str, additional_context: Dict = None) -> str:
    """Create a prompt for the LLM to analyze market data with trading style context"""
    
    # Format values safely (existing code)
    price_24h = f"{market_summary['price_change_24h']:.2f}%" if market_summary['price_change_24h'] is not None else "N/A"
    price_7d = f"{market_summary['price_change_7d']:.2f}%" if market_summary['price_change_7d'] is not None else "N/A"
    ma50 = f"${market_summary['moving_average_50']:.2f}" if market_summary['moving_average_50'] is not None else "N/A"
    ma200 = f"${market_summary['moving_average_200']:.2f}" if market_summary['moving_average_200'] is not None else "N/A"
    volatility = f"{market_summary['volatility']:.2f}%" if market_summary['volatility'] is not None else "N/A"

    # NEW: Add trading style context
    base_prompt = f"""You are an AI trading advisor for SHORT-TERM/DAY TRADING operations.

TRADING CONTEXT:
- Strategy: Day Trading / Short-term Swing Trading
- Decision Frequency: Every 60 minutes
- Holding Period: Minutes to hours (not days/weeks)
- Rebalancing: Automatic every 3 hours
- Focus: Capitalize on intraday price movements and short-term trends

MARKET DATA for {trading_pair}:
Price: ${market_summary['current_price']}
24h Change: {price_24h}
7d Change: {price_7d}
MA50: {ma50}
MA200: {ma200}
Volatility: {volatility}"""

    # Add technical indicators if available (existing code)
    if additional_context and "indicators" in additional_context:
        indicators = additional_context["indicators"]
        if indicators:
            rsi = f"{indicators.get('rsi'):.1f}" if indicators.get('rsi') is not None else "N/A"
            macd = f"{indicators.get('macd_line'):.2f}" if indicators.get('macd_line') is not None else "N/A"
            signal = f"{indicators.get('macd_signal'):.2f}" if indicators.get('macd_signal') is not None else "N/A"
            bb_width = f"{indicators.get('bollinger_width'):.2f}" if indicators.get('bollinger_width') is not None else "N/A"

            base_prompt += f"""
TECHNICAL INDICATORS:
RSI: {rsi}
MACD: {macd}
Signal: {signal}
BB Width: {bb_width}"""

    # NEW: Add day-trading specific instructions
    base_prompt += """

DAY TRADING ANALYSIS REQUIREMENTS:
- Prioritize short-term momentum and trend reversals
- Focus on 1-4 hour price movements rather than daily/weekly trends
- Consider intraday support/resistance levels
- Evaluate volatility for quick profit opportunities
- Assess liquidity for fast entry/exit capability
- Weight recent price action more heavily than long-term trends

DECISION CRITERIA for Day Trading:
- BUY: Strong short-term upward momentum, oversold conditions with reversal signals
- SELL: Profit-taking opportunities, overbought conditions, momentum weakening
- HOLD: Unclear short-term direction, low volatility, waiting for better entry/exit points

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
