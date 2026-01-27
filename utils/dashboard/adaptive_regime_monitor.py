"""
Adaptive Regime Monitor - Tracks and displays current market regime and active thresholds
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

class AdaptiveRegimeMonitor:
    """Monitor and log adaptive strategy regime changes"""
    
    def __init__(self, data_dir: str = "data/adaptive_regime"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.current_regime_file = os.path.join(data_dir, "current_regime.json")
        self.regime_history_file = os.path.join(data_dir, "regime_history.json")
    
    def update_regime(self, regime: str, market_data: Dict, active_thresholds: Dict):
        """Update current regime and log to history"""
        
        regime_data = {
            "regime": regime,
            "timestamp": datetime.now().isoformat(),
            "market_data": {
                "24h_change": market_data.get("price_changes", {}).get("24h", 0),
                "5d_change": market_data.get("price_changes", {}).get("5d", 0),
                "7d_change": market_data.get("price_changes", {}).get("7d", 0),
                "bb_width_pct": self._calculate_bb_width(market_data)
            },
            "active_thresholds": active_thresholds,
            "strategy_priority": self._get_strategy_priority(regime)
        }
        
        # Save current regime
        with open(self.current_regime_file, 'w') as f:
            json.dump(regime_data, f, indent=2)
        
        # Append to history (check if regime changed)
        self._append_to_history(regime_data)
        
        return regime_data
    
    def _calculate_bb_width(self, market_data: Dict) -> float:
        """Calculate Bollinger Band width percentage"""
        try:
            indicators = market_data.get("indicators", {})
            bb_upper = float(indicators.get("bb_upper", 0))
            bb_lower = float(indicators.get("bb_lower", 0))
            bb_middle = float(indicators.get("bb_middle", 1))
            
            if bb_middle > 0:
                return ((bb_upper - bb_lower) / bb_middle) * 100
        except:
            pass
        return 0.0
    
    def _get_strategy_priority(self, regime: str) -> list:
        """Get strategy priority for regime"""
        priorities = {
            "trending": ["trend_following", "momentum", "llm_strategy", "mean_reversion"],
            "ranging": ["mean_reversion", "llm_strategy", "momentum", "trend_following"],
            "volatile": ["llm_strategy", "mean_reversion", "trend_following", "momentum"],
            "bear_ranging": ["llm_strategy"]
        }
        return priorities.get(regime, ["llm_strategy"])
    
    def _append_to_history(self, regime_data: Dict):
        """Append regime change to history"""
        history = []
        
        # Load existing history
        if os.path.exists(self.regime_history_file):
            try:
                with open(self.regime_history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Check if regime actually changed
        if history and history[-1].get("regime") == regime_data["regime"]:
            # Same regime, just update timestamp
            history[-1] = regime_data
        else:
            # New regime, append
            history.append(regime_data)
        
        # Keep last 100 regime changes
        history = history[-100:]
        
        # Save history
        with open(self.regime_history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_current_regime(self) -> Optional[Dict]:
        """Get current regime data"""
        if os.path.exists(self.current_regime_file):
            try:
                with open(self.current_regime_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def get_regime_history(self, limit: int = 20) -> list:
        """Get recent regime history"""
        if os.path.exists(self.regime_history_file):
            try:
                with open(self.regime_history_file, 'r') as f:
                    history = json.load(f)
                    return history[-limit:]
            except:
                pass
        return []
    
    def get_regime_stats(self) -> Dict:
        """Get statistics about regime distribution"""
        history = self.get_regime_history(limit=100)
        
        if not history:
            return {}
        
        regime_counts = {}
        for entry in history:
            regime = entry.get("regime", "unknown")
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        total = len(history)
        regime_percentages = {
            regime: (count / total) * 100 
            for regime, count in regime_counts.items()
        }
        
        return {
            "total_changes": total,
            "regime_counts": regime_counts,
            "regime_percentages": regime_percentages,
            "current_regime": history[-1].get("regime") if history else None
        }
