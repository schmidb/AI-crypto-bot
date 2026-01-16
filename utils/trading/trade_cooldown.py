"""
Trade Cooldown Manager
Prevents overtrading by enforcing minimum time between trades on same asset
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

class TradeCooldownManager:
    """Manages cooldown periods between trades to prevent overtrading"""
    
    def __init__(self, min_hours_between_trades: float = 0):
        try:
            self.min_hours = float(min_hours_between_trades) if min_hours_between_trades else 0
        except (TypeError, ValueError):
            # Handle Mock objects in tests
            self.min_hours = 0
        self.last_trade_times: Dict[str, datetime] = {}
        self.logger = logging.getLogger("supervisor")
        
        if self.min_hours > 0:
            self.logger.info(f"🕐 Trade cooldown enabled: {self.min_hours} hours between trades")
    
    def can_trade(self, product_id: str, action: str) -> tuple[bool, Optional[str]]:
        """Check if enough time has passed since last trade on this asset"""
        
        if self.min_hours == 0:
            return True, None
        
        if product_id not in self.last_trade_times:
            return True, None
        
        last_trade = self.last_trade_times[product_id]
        time_since_trade = datetime.now() - last_trade
        required_cooldown = timedelta(hours=self.min_hours)
        
        if time_since_trade < required_cooldown:
            remaining = required_cooldown - time_since_trade
            hours = remaining.total_seconds() / 3600
            reason = f"Cooldown active: {hours:.1f}h remaining (last trade: {last_trade.strftime('%H:%M')})"
            return False, reason
        
        return True, None
    
    def record_trade(self, product_id: str, action: str):
        """Record a trade execution time"""
        self.last_trade_times[product_id] = datetime.now()
        self.logger.debug(f"Trade recorded for {product_id}: {action} at {datetime.now().strftime('%H:%M:%S')}")
    
    def get_cooldown_status(self, product_id: str) -> Optional[str]:
        """Get human-readable cooldown status for an asset"""
        
        if self.min_hours == 0 or product_id not in self.last_trade_times:
            return None
        
        last_trade = self.last_trade_times[product_id]
        time_since_trade = datetime.now() - last_trade
        required_cooldown = timedelta(hours=self.min_hours)
        
        if time_since_trade < required_cooldown:
            remaining = required_cooldown - time_since_trade
            hours = remaining.total_seconds() / 3600
            return f"Cooldown: {hours:.1f}h remaining"
        
        return "Ready to trade"
