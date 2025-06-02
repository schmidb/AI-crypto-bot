"""
Risk models for the crypto trading bot
Defines different risk strategies and a hybrid approach
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def low_risk_strategy(analysis_data: Dict[str, Any], llm_decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Low risk trading strategy - conservative approach
    - Reduces confidence for buy decisions
    - Increases confidence for sell decisions when in profit
    - More likely to hold
    
    Args:
        analysis_data: Market and portfolio data
        llm_decision: Original decision from LLM
        
    Returns:
        Modified decision with low risk profile
    """
    decision = llm_decision.copy()
    action = decision.get("action", "hold")
    confidence = decision.get("confidence", 0)
    
    # Get current price and indicators
    current_price = analysis_data.get("current_price", 0)
    indicators = analysis_data.get("indicators", {})
    
    # Get RSI and volatility
    rsi = indicators.get("rsi", {}).get("value", 50)
    volatility = indicators.get("bollinger_bands", {}).get("width", 0.05) * 100
    
    # Adjust confidence based on risk profile
    if action == "buy":
        # More conservative on buys
        if rsi > 60:  # Higher RSI means potentially overbought
            confidence *= 0.7  # Reduce confidence significantly
        if volatility > 5:  # Higher volatility means more risk
            confidence *= 0.8  # Reduce confidence
            
        # Set minimum threshold for buy actions
        if confidence < 70:
            action = "hold"
            decision["reason"] = f"Low risk strategy converted buy to hold due to insufficient confidence ({confidence:.0f}%)"
    
    elif action == "sell":
        # More aggressive on sells when in profit
        portfolio = analysis_data.get("portfolio", {})
        asset = analysis_data.get("product_id", "").split("-")[0]
        
        if asset in portfolio:
            asset_data = portfolio.get(asset, {})
            avg_price = asset_data.get("avg_price", 0)
            
            if current_price > avg_price * 1.05:  # 5% profit
                confidence *= 1.2  # Increase confidence
                confidence = min(confidence, 95)  # Cap at 95%
    
    # Update decision
    decision["action"] = action
    decision["confidence"] = round(confidence)
    decision["risk_level"] = "low"
    
    return decision

def medium_risk_strategy(analysis_data: Dict[str, Any], llm_decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Medium risk trading strategy - balanced approach
    - Slightly adjusts confidence based on technical indicators
    - Maintains most of the original LLM decision
    
    Args:
        analysis_data: Market and portfolio data
        llm_decision: Original decision from LLM
        
    Returns:
        Modified decision with medium risk profile
    """
    decision = llm_decision.copy()
    action = decision.get("action", "hold")
    confidence = decision.get("confidence", 0)
    
    # Get indicators
    indicators = analysis_data.get("indicators", {})
    
    # Get MACD and trend
    macd = indicators.get("macd", {})
    macd_histogram = macd.get("histogram", 0)
    market_trend = indicators.get("market_trend", "neutral")
    
    # Adjust confidence based on risk profile
    if action == "buy":
        # Boost confidence if MACD histogram is positive and increasing
        if macd_histogram > 0:
            confidence *= 1.1  # Slight boost
            confidence = min(confidence, 95)  # Cap at 95%
        
        # Reduce confidence if market trend doesn't align with action
        if market_trend == "bearish":
            confidence *= 0.9
    
    elif action == "sell":
        # Boost confidence if MACD histogram is negative and decreasing
        if macd_histogram < 0:
            confidence *= 1.1  # Slight boost
            confidence = min(confidence, 95)  # Cap at 95%
        
        # Reduce confidence if market trend doesn't align with action
        if market_trend == "bullish":
            confidence *= 0.9
    
    # Set minimum threshold for actions
    if confidence < 60 and action != "hold":
        action = "hold"
        decision["reason"] = f"Medium risk strategy converted {llm_decision.get('action')} to hold due to insufficient confidence ({confidence:.0f}%)"
    
    # Update decision
    decision["action"] = action
    decision["confidence"] = round(confidence)
    decision["risk_level"] = "medium"
    
    return decision

def high_risk_strategy(analysis_data: Dict[str, Any], llm_decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    High risk trading strategy - aggressive approach
    - Increases confidence for decisive actions
    - More willing to take trades based on short-term indicators
    - Lower threshold for taking action
    
    Args:
        analysis_data: Market and portfolio data
        llm_decision: Original decision from LLM
        
    Returns:
        Modified decision with high risk profile
    """
    decision = llm_decision.copy()
    action = decision.get("action", "hold")
    confidence = decision.get("confidence", 0)
    
    # Get current price and indicators
    indicators = analysis_data.get("indicators", {})
    
    # Get Bollinger Bands info
    bb = indicators.get("bollinger_bands", {})
    bb_signal = bb.get("signal", "neutral")
    
    # Get price changes
    market_data = analysis_data.get("market_data", {})
    price_changes = market_data.get("price_changes", {})
    price_change_1h = price_changes.get("1h", 0)
    
    # Adjust confidence based on risk profile
    if action == "buy":
        # Boost confidence for oversold conditions
        if bb_signal == "oversold":
            confidence *= 1.25  # Significant boost
            confidence = min(confidence, 98)  # Cap at 98%
        
        # Boost confidence for positive short-term momentum
        if price_change_1h > 1.0:  # >1% gain in last hour
            confidence *= 1.15
            confidence = min(confidence, 98)
    
    elif action == "sell":
        # Boost confidence for overbought conditions
        if bb_signal == "overbought":
            confidence *= 1.25  # Significant boost
            confidence = min(confidence, 98)  # Cap at 98%
        
        # Boost confidence for negative short-term momentum
        if price_change_1h < -1.0:  # >1% loss in last hour
            confidence *= 1.15
            confidence = min(confidence, 98)
    
    elif action == "hold":
        # High risk strategy is more likely to convert holds to actions
        # Check if we're near Bollinger Band extremes
        if bb_signal == "oversold":
            action = "buy"
            confidence = 70
            decision["reason"] = "High risk strategy converted hold to buy due to oversold conditions"
        elif bb_signal == "overbought":
            action = "sell"
            confidence = 70
            decision["reason"] = "High risk strategy converted hold to sell due to overbought conditions"
    
    # Update decision
    decision["action"] = action
    decision["confidence"] = round(confidence)
    decision["risk_level"] = "high"
    
    return decision

def hybrid_risk_strategy(analysis_data: Dict[str, Any], llm_decision: Dict[str, Any], 
                         low_weight: float = 0.0, medium_weight: float = 0.5, high_weight: float = 0.5) -> Dict[str, Any]:
    """
    Hybrid risk strategy that combines multiple risk levels
    
    Args:
        analysis_data: Market and portfolio data
        llm_decision: Original decision from LLM
        low_weight: Weight for low risk strategy (0.0 to 1.0)
        medium_weight: Weight for medium risk strategy (0.0 to 1.0)
        high_weight: Weight for high risk strategy (0.0 to 1.0)
        
    Returns:
        Combined decision based on weighted risk strategies
    """
    # Normalize weights to ensure they sum to 1.0
    total_weight = low_weight + medium_weight + high_weight
    if total_weight == 0:
        # Default to medium risk if all weights are zero
        return medium_risk_strategy(analysis_data, llm_decision)
    
    low_weight = low_weight / total_weight
    medium_weight = medium_weight / total_weight
    high_weight = high_weight / total_weight
    
    # Get decisions from each risk strategy
    low_decision = low_risk_strategy(analysis_data, llm_decision) if low_weight > 0 else None
    medium_decision = medium_risk_strategy(analysis_data, llm_decision) if medium_weight > 0 else None
    high_decision = high_risk_strategy(analysis_data, llm_decision) if high_weight > 0 else None
    
    # Collect all active decisions
    active_decisions = []
    if low_decision:
        active_decisions.append((low_decision, low_weight))
    if medium_decision:
        active_decisions.append((medium_decision, medium_weight))
    if high_decision:
        active_decisions.append((high_decision, high_weight))
    
    # Count votes for each action
    action_votes = {"buy": 0, "sell": 0, "hold": 0}
    for decision, weight in active_decisions:
        action = decision.get("action", "hold")
        action_votes[action] += weight
    
    # Determine the winning action
    winning_action = max(action_votes, key=action_votes.get)
    
    # Calculate weighted confidence for the winning action
    total_confidence = 0
    total_weight_for_action = 0
    reasons = []
    
    for decision, weight in active_decisions:
        if decision.get("action") == winning_action:
            total_confidence += decision.get("confidence", 0) * weight
            total_weight_for_action += weight
            reasons.append(f"{decision.get('risk_level', 'unknown')} risk: {decision.get('reason', 'No reason')}")
    
    # Avoid division by zero
    if total_weight_for_action > 0:
        weighted_confidence = total_confidence / total_weight_for_action
    else:
        weighted_confidence = 0
    
    # Create the hybrid decision
    hybrid_decision = {
        "action": winning_action,
        "confidence": round(weighted_confidence),
        "reason": " | ".join(reasons) if reasons else "No reason provided",
        "risk_level": "hybrid",
        "risk_weights": {
            "low": low_weight,
            "medium": medium_weight,
            "high": high_weight
        }
    }
    
    logger.info(f"Hybrid risk strategy: {winning_action} with {weighted_confidence:.0f}% confidence")
    logger.info(f"Risk weights: low={low_weight:.2f}, medium={medium_weight:.2f}, high={high_weight:.2f}")
    
    return hybrid_decision
