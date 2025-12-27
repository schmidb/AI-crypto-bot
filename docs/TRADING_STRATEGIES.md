# Trading Strategies

The AI crypto trading bot implements three complementary trading strategies that work together to identify optimal trading opportunities across different market conditions.

## Strategy Overview

The bot uses a **multi-strategy approach** where each strategy contributes to the final trading decision based on:
- Market regime detection (bull, bear, sideways)
- Strategy suitability for current conditions
- Weighted signal combination
- AI-powered market analysis overlay

## 1. Trend Following Strategy

### Concept
Identifies and follows established market trends, buying during uptrends and selling during downtrends.

### Technical Indicators
- **MACD (Moving Average Convergence Divergence)**
  - Signal: MACD line crossing above/below signal line
  - Strength: Distance between MACD and signal line
  - Momentum: MACD histogram values

- **Bollinger Bands**
  - Position relative to bands indicates trend strength
  - Price above upper band = strong uptrend
  - Price below lower band = strong downtrend

- **RSI (Relative Strength Index)**
  - Confirms trend direction
  - Filters out overbought/oversold conditions

### Signal Generation
```python
def analyze_trend_following(indicators, portfolio):
    # Calculate trend strength (0-100)
    trend_strength = calculate_trend_strength(indicators)
    
    # Determine trend direction
    if macd > macd_signal and price > bb_middle:
        direction = "UP"
    elif macd < macd_signal and price < bb_middle:
        direction = "DOWN"
    else:
        direction = "SIDEWAYS"
    
    # Generate signal based on strength and direction
    if trend_strength > 70 and direction == "UP":
        return "BUY"
    elif trend_strength > 70 and direction == "DOWN":
        return "SELL"
    else:
        return "HOLD"
```

### Market Regime Suitability
- **Bull Markets**: High suitability (0.9) - trends are strong and persistent
- **Bear Markets**: High suitability (0.8) - downtrends can be profitable
- **Sideways Markets**: Low suitability (0.3) - trends are weak and unreliable

### Position Sizing
- Strong trends (>80 strength): 1.2x position multiplier
- Moderate trends (60-80): 1.0x position multiplier
- Weak trends (<60): 0.7x position multiplier

## 2. Mean Reversion Strategy

### Concept
Exploits temporary price deviations from the mean, buying oversold conditions and selling overbought conditions.

### Technical Indicators
- **RSI (Relative Strength Index)**
  - RSI < 30: Oversold (potential buy)
  - RSI > 70: Overbought (potential sell)
  - Extreme levels (<20, >80) for stronger signals

- **Bollinger Bands**
  - Price touching lower band: Oversold
  - Price touching upper band: Overbought
  - Distance from middle band indicates deviation severity

### Signal Generation
```python
def analyze_mean_reversion(indicators, portfolio):
    rsi = indicators.get('rsi', 50)
    bb_position = calculate_bb_position(indicators)
    
    # Combine RSI and Bollinger Band signals
    if rsi < 30 and bb_position < -1.5:  # Strong oversold
        return {"signal": "BUY", "confidence": 80}
    elif rsi < 35 and bb_position < -1.0:  # Moderate oversold
        return {"signal": "BUY", "confidence": 60}
    elif rsi > 70 and bb_position > 1.5:  # Strong overbought
        return {"signal": "SELL", "confidence": 80}
    elif rsi > 65 and bb_position > 1.0:  # Moderate overbought
        return {"signal": "SELL", "confidence": 60}
    else:
        return {"signal": "HOLD", "confidence": 40}
```

### Market Regime Suitability
- **Bull Markets**: Moderate suitability (0.6) - fewer oversold opportunities
- **Bear Markets**: Moderate suitability (0.6) - fewer overbought opportunities
- **Sideways Markets**: High suitability (0.9) - frequent mean reversion opportunities

### Position Sizing
- Strong signals (confidence >75): 1.1x position multiplier
- Moderate signals (confidence 60-75): 1.0x position multiplier
- Weak signals (confidence <60): 0.8x position multiplier

## 3. Momentum Strategy

### Concept
Identifies and capitalizes on accelerating price movements and volume surges.

### Technical Indicators
- **Price Momentum**
  - 1-hour, 4-hour, and 24-hour price changes
  - Acceleration in price movement
  - Consistency across timeframes

- **Volume Analysis**
  - Current volume vs. average volume
  - Volume spikes indicate strong momentum
  - Volume confirmation of price moves

- **Technical Momentum**
  - RSI momentum (rate of RSI change)
  - MACD momentum (histogram values)
  - Combined technical acceleration

### Signal Generation
```python
def analyze_momentum(indicators, portfolio):
    price_momentum = calculate_price_momentum(indicators)
    volume_momentum = calculate_volume_momentum(indicators)
    technical_momentum = calculate_technical_momentum(indicators)
    
    # Combine all momentum factors
    total_momentum = (
        price_momentum * 0.4 +
        volume_momentum * 0.3 +
        technical_momentum * 0.3
    )
    
    # Generate signals based on momentum strength
    if total_momentum > 70:
        return {"signal": "BUY", "confidence": min(total_momentum, 95)}
    elif total_momentum < -70:
        return {"signal": "SELL", "confidence": min(abs(total_momentum), 95)}
    else:
        return {"signal": "HOLD", "confidence": 50}
```

### Market Regime Suitability
- **Bull Markets**: High suitability (0.8) - strong upward momentum
- **Bear Markets**: High suitability (0.8) - strong downward momentum
- **Sideways Markets**: Low suitability (0.4) - weak momentum signals

### Position Sizing
- Very strong momentum (>85): 1.3x position multiplier
- Strong momentum (70-85): 1.1x position multiplier
- Moderate momentum (50-70): 0.9x position multiplier
- Weak momentum (<50): 0.7x position multiplier

## Strategy Combination

### Market Regime Detection
The bot automatically detects market conditions:

```python
def detect_market_regime(indicators):
    price_trend = calculate_price_trend(indicators)
    volatility = calculate_volatility(indicators)
    volume_trend = calculate_volume_trend(indicators)
    
    if price_trend > 0.02 and volatility < 0.3:
        return "BULL"
    elif price_trend < -0.02 and volatility < 0.3:
        return "BEAR"
    else:
        return "SIDEWAYS"
```

### Weight Adjustment
Strategy weights are dynamically adjusted based on market regime:

| Strategy | Bull Market | Bear Market | Sideways Market |
|----------|-------------|-------------|-----------------|
| Trend Following | 45% | 40% | 15% |
| Mean Reversion | 30% | 30% | 50% |
| Momentum | 25% | 30% | 35% |

### Signal Combination
```python
def combine_signals(trend_signal, mean_reversion_signal, momentum_signal, weights):
    # Weight each strategy's contribution
    weighted_decision = (
        trend_signal.confidence * weights['trend'] +
        mean_reversion_signal.confidence * weights['mean_reversion'] +
        momentum_signal.confidence * weights['momentum']
    )
    
    # Determine final action
    if weighted_decision > 55:
        return "BUY"
    elif weighted_decision < 45:
        return "SELL"
    else:
        return "HOLD"
```

## AI Enhancement Layer

### Gemini Analysis
Each strategy's signals are enhanced by AI analysis:

```python
def enhance_with_ai(technical_signals, market_data):
    prompt = f"""
    Analyze this crypto market data and technical signals:
    
    Technical Signals:
    - Trend Following: {technical_signals['trend']}
    - Mean Reversion: {technical_signals['mean_reversion']}
    - Momentum: {technical_signals['momentum']}
    
    Market Data:
    - Current Price: {market_data['price']}
    - 24h Change: {market_data['change_24h']}
    - Volume: {market_data['volume']}
    
    Provide analysis with confidence score (0-100) and reasoning.
    """
    
    ai_analysis = llm_analyzer.analyze_with_llm(prompt)
    return ai_analysis
```

### AI Signal Integration
- AI analysis provides additional confidence adjustment
- Helps identify market anomalies or news impacts
- Can override technical signals in extreme conditions
- Provides reasoning for trading decisions

## Risk Integration

Each strategy incorporates risk management:

### Position Sizing
- Base position size determined by risk level
- Strategy-specific multipliers applied
- Maximum position limits enforced
- EUR reserve requirements maintained

### Stop Conditions
- RSI extreme levels (>90, <10) trigger holds
- Volatility spikes reduce position sizes
- Conflicting signals between strategies reduce confidence

### Safety Mechanisms
- Minimum trade amounts enforced
- Maximum daily trade limits
- Emergency stop conditions
- Portfolio allocation limits

## Performance Monitoring

### Strategy-Specific Metrics
- Individual strategy win rates
- Strategy contribution to overall performance
- Market regime performance analysis
- Signal accuracy tracking

### Adaptive Learning
- Strategy weights adjust based on recent performance
- Market regime detection improves over time
- AI prompts refined based on accuracy
- Risk parameters adjusted based on volatility

## Configuration

### Strategy Parameters
```env
# Trend Following
TREND_STRENGTH_THRESHOLD=60
TREND_RSI_OVERBOUGHT=75
TREND_RSI_OVERSOLD=25

# Mean Reversion
MR_RSI_OVERSOLD=30
MR_RSI_OVERBOUGHT=70
MR_BB_DEVIATION_THRESHOLD=1.5

# Momentum
MOMENTUM_PRICE_THRESHOLD=0.02
MOMENTUM_VOLUME_THRESHOLD=1.5
MOMENTUM_TECHNICAL_THRESHOLD=60
```

### Strategy Weights
```env
# Default weights (adjusted dynamically)
TREND_FOLLOWING_WEIGHT=0.4
MEAN_REVERSION_WEIGHT=0.3
MOMENTUM_WEIGHT=0.3
```

This multi-strategy approach provides robust trading decisions across various market conditions while maintaining strict risk management principles.