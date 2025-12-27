"""
Market Volatility Analyzer for Phase 3
Analyzes market volatility and adjusts strategy weights accordingly
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class VolatilityAnalyzer:
    """Analyze market volatility and provide trading adjustments"""
    
    def __init__(self, data_dir: str = "data/volatility"):
        self.logger = logging.getLogger(__name__)
        self.data_dir = data_dir
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        self.volatility_cache = {}
        self.volatility_history_file = os.path.join(data_dir, "volatility_history.json")
        
        # Load historical volatility data
        self.volatility_history = self._load_volatility_history()
        
        self.logger.info("Volatility analyzer initialized")
    
    def analyze_volatility(self, 
                          product_id: str,
                          price_data: List[float],
                          time_periods: Dict[str, float]) -> Dict:
        """Analyze current market volatility"""
        
        try:
            # Calculate various volatility metrics
            volatility_metrics = self._calculate_volatility_metrics(price_data, time_periods)
            
            # Determine volatility regime
            volatility_regime = self._determine_volatility_regime(volatility_metrics)
            
            # Get strategy adjustments
            strategy_adjustments = self._get_volatility_strategy_adjustments(volatility_regime)
            
            # Store in cache and history
            volatility_analysis = {
                "product_id": product_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": volatility_metrics,
                "regime": volatility_regime,
                "strategy_adjustments": strategy_adjustments
            }
            
            self.volatility_cache[product_id] = volatility_analysis
            self._update_volatility_history(product_id, volatility_analysis)
            
            self.logger.info(f"Volatility analysis for {product_id}: {volatility_regime['category']} ({volatility_regime['score']:.2f})")
            return volatility_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing volatility for {product_id}: {e}")
            return self._get_default_volatility_analysis(product_id)
    
    def _calculate_volatility_metrics(self, price_data: List[float], time_periods: Dict[str, float]) -> Dict:
        """Calculate various volatility metrics"""
        
        if len(price_data) < 2:
            return {"error": "Insufficient price data"}
        
        # Convert to numpy array for calculations
        prices = np.array(price_data)
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Basic volatility (standard deviation of returns)
        basic_volatility = np.std(returns) if len(returns) > 0 else 0
        
        # Annualized volatility (assuming hourly data)
        annualized_volatility = basic_volatility * np.sqrt(24 * 365) if basic_volatility > 0 else 0
        
        # Price change volatility from time periods
        price_change_volatility = 0
        if time_periods:
            changes = [abs(change) for change in time_periods.values() if change is not None]
            if changes:
                price_change_volatility = np.std(changes)
        
        # Average True Range (simplified)
        if len(prices) >= 3:
            high_low = np.max(prices[-10:]) - np.min(prices[-10:]) if len(prices) >= 10 else np.max(prices) - np.min(prices)
            atr = high_low / prices[-1] * 100  # As percentage
        else:
            atr = 0
        
        # Volatility trend (comparing recent vs historical)
        if len(returns) >= 20:
            recent_vol = np.std(returns[-10:])
            historical_vol = np.std(returns[:-10])
            volatility_trend = (recent_vol - historical_vol) / historical_vol if historical_vol > 0 else 0
        else:
            volatility_trend = 0
        
        return {
            "basic_volatility": float(basic_volatility),
            "annualized_volatility": float(annualized_volatility),
            "price_change_volatility": float(price_change_volatility),
            "average_true_range": float(atr),
            "volatility_trend": float(volatility_trend),
            "data_points": len(price_data)
        }
    
    def _determine_volatility_regime(self, metrics: Dict) -> Dict:
        """Determine current volatility regime"""
        
        if "error" in metrics:
            return {"category": "unknown", "score": 0.5, "confidence": 0.3}
        
        # Combine multiple volatility indicators
        volatility_indicators = []
        
        # Basic volatility score (0-1 scale)
        basic_vol = metrics.get("basic_volatility", 0)
        if basic_vol > 0.05:  # > 5% volatility
            volatility_indicators.append(0.8)
        elif basic_vol > 0.03:  # > 3% volatility
            volatility_indicators.append(0.6)
        elif basic_vol > 0.01:  # > 1% volatility
            volatility_indicators.append(0.4)
        else:
            volatility_indicators.append(0.2)
        
        # Price change volatility
        price_change_vol = metrics.get("price_change_volatility", 0)
        if price_change_vol > 5:  # > 5% price change volatility
            volatility_indicators.append(0.8)
        elif price_change_vol > 3:
            volatility_indicators.append(0.6)
        elif price_change_vol > 1:
            volatility_indicators.append(0.4)
        else:
            volatility_indicators.append(0.2)
        
        # Average True Range
        atr = metrics.get("average_true_range", 0)
        if atr > 10:  # > 10% ATR
            volatility_indicators.append(0.9)
        elif atr > 5:
            volatility_indicators.append(0.7)
        elif atr > 2:
            volatility_indicators.append(0.5)
        else:
            volatility_indicators.append(0.3)
        
        # Calculate overall volatility score
        volatility_score = np.mean(volatility_indicators) if volatility_indicators else 0.5
        
        # Determine category
        if volatility_score > 0.7:
            category = "high"
        elif volatility_score > 0.5:
            category = "medium"
        else:
            category = "low"
        
        # Calculate confidence based on data consistency
        confidence = 1.0 - np.std(volatility_indicators) if len(volatility_indicators) > 1 else 0.7
        
        return {
            "category": category,
            "score": float(volatility_score),
            "confidence": float(confidence),
            "trend": "increasing" if metrics.get("volatility_trend", 0) > 0.1 else "decreasing" if metrics.get("volatility_trend", 0) < -0.1 else "stable"
        }
    
    def _get_volatility_strategy_adjustments(self, volatility_regime: Dict) -> Dict:
        """Get strategy weight adjustments based on volatility"""
        
        category = volatility_regime.get("category", "medium")
        score = volatility_regime.get("score", 0.5)
        
        # Base adjustments for different volatility regimes
        if category == "high":
            # High volatility: favor mean reversion and LLM, reduce trend following
            adjustments = {
                "trend_following": -0.1,
                "mean_reversion": +0.15,
                "momentum": -0.05,
                "llm_strategy": +0.1,
                "position_size_multiplier": 0.7,  # Reduce position sizes
                "confidence_threshold_adjustment": +10  # Require higher confidence
            }
        elif category == "low":
            # Low volatility: favor trend following and momentum
            adjustments = {
                "trend_following": +0.1,
                "mean_reversion": -0.05,
                "momentum": +0.05,
                "llm_strategy": -0.05,
                "position_size_multiplier": 1.2,  # Increase position sizes
                "confidence_threshold_adjustment": -5  # Lower confidence threshold
            }
        else:
            # Medium volatility: neutral adjustments
            adjustments = {
                "trend_following": 0.0,
                "mean_reversion": +0.02,
                "momentum": 0.0,
                "llm_strategy": +0.02,
                "position_size_multiplier": 1.0,
                "confidence_threshold_adjustment": 0
            }
        
        # Scale adjustments by volatility score confidence
        confidence = volatility_regime.get("confidence", 0.7)
        for key in adjustments:
            if key not in ["position_size_multiplier", "confidence_threshold_adjustment"]:
                adjustments[key] *= confidence
        
        return adjustments
    
    def get_market_volatility_summary(self) -> Dict:
        """Get summary of current market volatility across all assets"""
        
        if not self.volatility_cache:
            return {"status": "no_data", "overall_volatility": "unknown"}
        
        # Calculate overall market volatility
        volatility_scores = []
        regime_counts = {"high": 0, "medium": 0, "low": 0}
        
        for product_id, analysis in self.volatility_cache.items():
            regime = analysis.get("regime", {})
            score = regime.get("score", 0.5)
            category = regime.get("category", "medium")
            
            volatility_scores.append(score)
            regime_counts[category] += 1
        
        overall_volatility_score = np.mean(volatility_scores) if volatility_scores else 0.5
        
        # Determine overall market volatility
        if overall_volatility_score > 0.7:
            overall_category = "high"
        elif overall_volatility_score > 0.5:
            overall_category = "medium"
        else:
            overall_category = "low"
        
        return {
            "overall_volatility": overall_category,
            "overall_score": float(overall_volatility_score),
            "asset_count": len(self.volatility_cache),
            "regime_distribution": regime_counts,
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_volatility_history(self) -> Dict:
        """Load historical volatility data"""
        
        if not os.path.exists(self.volatility_history_file):
            return {}
        
        try:
            with open(self.volatility_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading volatility history: {e}")
            return {}
    
    def _update_volatility_history(self, product_id: str, analysis: Dict):
        """Update volatility history"""
        
        if product_id not in self.volatility_history:
            self.volatility_history[product_id] = []
        
        # Keep only last 100 entries per asset
        self.volatility_history[product_id].append(analysis)
        if len(self.volatility_history[product_id]) > 100:
            self.volatility_history[product_id] = self.volatility_history[product_id][-100:]
        
        # Save to file
        try:
            with open(self.volatility_history_file, 'w') as f:
                json.dump(self.volatility_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving volatility history: {e}")
    
    def _get_default_volatility_analysis(self, product_id: str) -> Dict:
        """Return default volatility analysis when calculation fails"""
        
        return {
            "product_id": product_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {"error": "calculation_failed"},
            "regime": {"category": "medium", "score": 0.5, "confidence": 0.3},
            "strategy_adjustments": {
                "trend_following": 0.0,
                "mean_reversion": 0.0,
                "momentum": 0.0,
                "llm_strategy": 0.0,
                "position_size_multiplier": 1.0,
                "confidence_threshold_adjustment": 0
            }
        }
