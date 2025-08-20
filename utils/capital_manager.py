"""
Capital Management Module
Prevents "all money in one coin" problem by managing trading reserves and position sizes
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

class CapitalManager:
    """
    Manages trading capital to ensure sustainable day trading
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("supervisor")
        
        # Capital management settings with fallback defaults
        self.min_eur_reserve = float(getattr(config, 'MIN_EUR_RESERVE', 50.0))
        self.max_eur_usage_per_trade = float(getattr(config, 'MAX_EUR_USAGE_PER_TRADE', 30.0)) / 100.0
        self.target_eur_allocation = float(getattr(config, 'TARGET_EUR_ALLOCATION', 25.0)) / 100.0
        
        # Position limits
        self.max_position_size_percent = float(getattr(config, 'MAX_POSITION_SIZE_PERCENT', 35.0)) / 100.0
        self.min_position_size_eur = float(getattr(config, 'MIN_POSITION_SIZE_EUR', 40.0))
        
        # Rebalancing triggers
        self.rebalance_trigger_eur_percent = float(getattr(config, 'REBALANCE_TRIGGER_EUR_PERCENT', 15.0)) / 100.0
        self.rebalance_target_eur_percent = float(getattr(config, 'REBALANCE_TARGET_EUR_PERCENT', 25.0)) / 100.0
        self.max_crypto_allocation = float(getattr(config, 'MAX_CRYPTO_ALLOCATION', 80.0)) / 100.0
        
        # Trading limits
        self.max_trades_per_day = int(getattr(config, 'MAX_TRADES_PER_DAY', 15))
        self.min_time_between_trades = int(getattr(config, 'MIN_TIME_BETWEEN_TRADES', 20))
        self.max_daily_trading_volume = float(getattr(config, 'MAX_DAILY_TRADING_VOLUME', 30.0)) / 100.0
        
        # Trade tracking
        self.daily_trades = {}
        self.last_trade_time = {}
        
        self.logger.info(f"💰 Capital Manager initialized:")
        self.logger.info(f"  Min EUR reserve: €{self.min_eur_reserve}")
        self.logger.info(f"  Max EUR usage per trade: {self.max_eur_usage_per_trade*100:.1f}%")
        self.logger.info(f"  Target EUR allocation: {self.target_eur_allocation*100:.1f}%")
    
    def calculate_safe_trade_size(self, action: str, asset: str, portfolio: Dict, 
                                 original_trade_size: float) -> Tuple[float, str]:
        """
        Calculate safe trade size that preserves capital and maintains trading ability
        
        Returns: (safe_trade_size, reason)
        """
        
        total_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
        eur_balance = portfolio.get('EUR', {}).get('amount', 0)
        
        if total_value <= 0:
            return 0, "Invalid portfolio value"
        
        # Check if rebalancing is needed first
        rebalance_action = self.check_rebalancing_needed(portfolio)
        if rebalance_action and rebalance_action != action:
            return 0, f"Rebalancing needed: {rebalance_action} required, but signal is {action}"
        
        if action == "BUY":
            return self._calculate_safe_buy_size(asset, portfolio, original_trade_size, total_value, eur_balance)
        elif action == "SELL":
            return self._calculate_safe_sell_size(asset, portfolio, original_trade_size, total_value)
        else:
            return 0, "Invalid action"
    
    def _calculate_safe_buy_size(self, asset: str, portfolio: Dict, original_trade_size: float, 
                                total_value: float, eur_balance: float) -> Tuple[float, str]:
        """Calculate safe BUY trade size"""
        
        # Check minimum EUR reserve
        if eur_balance <= self.min_eur_reserve:
            return 0, f"EUR balance (€{eur_balance:.2f}) at or below minimum reserve (€{self.min_eur_reserve})"
        
        # Calculate available EUR for trading (above reserve)
        available_eur = eur_balance - self.min_eur_reserve
        
        # Limit to percentage of available EUR
        max_trade_from_available = available_eur * self.max_eur_usage_per_trade
        
        # Check position size limits
        current_asset_value = 0
        if asset in portfolio:
            asset_data = portfolio[asset]
            if isinstance(asset_data, dict) and 'amount' in asset_data:
                current_asset_value = asset_data['amount'] * asset_data.get('last_price_eur', 0)
        
        # Calculate what position size would be after trade
        potential_position_value = current_asset_value + min(original_trade_size, max_trade_from_available)
        potential_position_percent = potential_position_value / total_value
        
        if potential_position_percent > self.max_position_size_percent:
            # Reduce trade size to stay within position limits
            max_additional = (self.max_position_size_percent * total_value) - current_asset_value
            max_trade_from_position = max(0, max_additional)
            safe_size = min(max_trade_from_available, max_trade_from_position, original_trade_size)
        else:
            safe_size = min(max_trade_from_available, original_trade_size)
        
        # Check trading limits
        if not self._check_trading_limits(asset, safe_size, total_value):
            return 0, "Daily trading limits exceeded"
        
        if safe_size < getattr(self.config, 'MIN_TRADE_AMOUNT', 30.0):
            return 0, f"Safe trade size (€{safe_size:.2f}) below minimum (€{getattr(self.config, 'MIN_TRADE_AMOUNT', 30.0)})"
        
            reason = f"Safe BUY: €{safe_size:.2f} (from €{original_trade_size:.2f}), available: €{available_eur:.2f}"
        return safe_size, reason
    
    def _calculate_safe_sell_size(self, asset: str, portfolio: Dict, original_trade_size: float, 
                                 total_value: float) -> Tuple[float, str]:
        """Calculate safe SELL trade size"""
        
        if asset not in portfolio:
            return 0, f"No {asset} position to sell"
        
        asset_data = portfolio[asset]
        if not isinstance(asset_data, dict) or 'amount' not in asset_data:
            return 0, f"Invalid {asset} position data"
        
        current_asset_value = asset_data['amount'] * asset_data.get('last_price_eur', 0)
        
        # Don't sell if it would make position too small
        remaining_value_after_sell = current_asset_value - original_trade_size
        if remaining_value_after_sell > 0 and remaining_value_after_sell < self.min_position_size_eur:
            # Either sell everything or don't sell
            if current_asset_value >= float(getattr(self.config, 'MIN_TRADE_AMOUNT', 30.0)):
                safe_size = current_asset_value  # Sell entire position
                reason = f"Selling entire {asset} position (€{safe_size:.2f}) to avoid small remainder"
            else:
                return 0, f"Position too small to sell (€{current_asset_value:.2f})"
        else:
            safe_size = min(original_trade_size, current_asset_value)
            reason = f"Safe SELL: €{safe_size:.2f} from {asset} position"
        
        # Check trading limits
        if not self._check_trading_limits(asset, safe_size, total_value):
            return 0, "Daily trading limits exceeded"
        
        return safe_size, reason
    
    def check_rebalancing_needed(self, portfolio: Dict) -> Optional[str]:
        """
        Check if portfolio rebalancing is needed to maintain trading ability
        
        Returns: "FORCE_SELL" if need to sell crypto for EUR, None if balanced
        """
        
        total_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
        eur_balance = portfolio.get('EUR', {}).get('amount', 0)
        
        if total_value <= 0:
            return None
        
        eur_percent = eur_balance / total_value
        crypto_percent = 1 - eur_percent
        
        # Check if EUR allocation is too low
        if eur_percent < self.rebalance_trigger_eur_percent:
            self.logger.warning(f"⚠️  EUR allocation too low: {eur_percent*100:.1f}% (trigger: {self.rebalance_trigger_eur_percent*100:.1f}%)")
            return "FORCE_SELL"
        
        # Check if crypto allocation is too high
        if crypto_percent > self.max_crypto_allocation:
            self.logger.warning(f"⚠️  Crypto allocation too high: {crypto_percent*100:.1f}% (max: {self.max_crypto_allocation*100:.1f}%)")
            return "FORCE_SELL"
        
        return None
    
    def get_rebalancing_target(self, portfolio: Dict) -> Optional[Dict]:
        """
        Calculate rebalancing trades needed to restore target allocations
        
        Returns: {"action": "SELL", "asset": "BTC", "amount": 50.0} or None
        """
        
        rebalance_action = self.check_rebalancing_needed(portfolio)
        if not rebalance_action:
            return None
        
        total_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
        eur_balance = portfolio.get('EUR', {}).get('amount', 0)
        target_eur_value = total_value * self.rebalance_target_eur_percent
        eur_needed = target_eur_value - eur_balance
        
        if eur_needed <= 0:
            return None
        
        # Find largest crypto position to sell from
        largest_asset = None
        largest_value = 0
        
        for asset, data in portfolio.items():
            if asset in ['EUR', 'USD', 'portfolio_value_eur', 'initial_value_eur', 'trades_executed', 'last_updated']:
                continue
            
            if isinstance(data, dict) and 'amount' in data:
                asset_value = data['amount'] * data.get('last_price_eur', 0)
                if asset_value > largest_value:
                    largest_value = asset_value
                    largest_asset = asset
        
        if largest_asset and largest_value > eur_needed:
            return {
                "action": "SELL",
                "asset": largest_asset,
                "amount": min(eur_needed, largest_value * 0.5),  # Sell max 50% of position
                "reason": f"Rebalancing: restore EUR to {self.rebalance_target_eur_percent*100:.1f}%"
            }
        
        return None
    
    def _check_trading_limits(self, asset: str, trade_size: float, total_value: float) -> bool:
        """Check if trade is within daily limits"""
        
        today = datetime.now().date()
        
        # Initialize daily tracking
        if today not in self.daily_trades:
            self.daily_trades[today] = {"count": 0, "volume": 0.0}
        
        # Check trade count limit
        if self.daily_trades[today]["count"] >= self.max_trades_per_day:
            self.logger.warning(f"Daily trade limit reached: {self.daily_trades[today]['count']}/{self.max_trades_per_day}")
            return False
        
        # Check volume limit
        trade_volume_percent = trade_size / total_value
        daily_volume_percent = self.daily_trades[today]["volume"] / total_value
        
        if daily_volume_percent + trade_volume_percent > self.max_daily_trading_volume:
            self.logger.warning(f"Daily volume limit would be exceeded: {(daily_volume_percent + trade_volume_percent)*100:.1f}% > {self.max_daily_trading_volume*100:.1f}%")
            return False
        
        # Check time between trades
        asset_key = f"{asset}_{today}"
        if asset_key in self.last_trade_time:
            time_since_last = datetime.now() - self.last_trade_time[asset_key]
            if time_since_last.total_seconds() < self.min_time_between_trades * 60:
                self.logger.warning(f"Too soon since last {asset} trade: {time_since_last.total_seconds()/60:.1f}min < {self.min_time_between_trades}min")
                return False
        
        return True
    
    def record_trade(self, asset: str, trade_size: float, total_value: float):
        """Record trade for limit tracking"""
        
        today = datetime.now().date()
        
        if today not in self.daily_trades:
            self.daily_trades[today] = {"count": 0, "volume": 0.0}
        
        self.daily_trades[today]["count"] += 1
        self.daily_trades[today]["volume"] += trade_size
        
        asset_key = f"{asset}_{today}"
        self.last_trade_time[asset_key] = datetime.now()
        
        self.logger.info(f"📊 Trade recorded: {asset} €{trade_size:.2f} (daily: {self.daily_trades[today]['count']}/{self.max_trades_per_day} trades, {(self.daily_trades[today]['volume']/total_value)*100:.1f}% volume)")
    
    def get_portfolio_health_report(self, portfolio: Dict) -> Dict:
        """Generate portfolio health report"""
        
        total_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
        eur_balance = portfolio.get('EUR', {}).get('amount', 0)
        
        if total_value <= 0:
            return {"status": "error", "message": "Invalid portfolio"}
        
        eur_percent = eur_balance / total_value
        available_eur = max(0, eur_balance - self.min_eur_reserve)
        
        # Calculate position sizes
        positions = {}
        for asset, data in portfolio.items():
            if asset in ['EUR', 'USD', 'portfolio_value_eur', 'initial_value_eur', 'trades_executed', 'last_updated']:
                continue
            
            if isinstance(data, dict) and 'amount' in data:
                asset_value = data['amount'] * data.get('last_price_eur', 0)
                positions[asset] = {
                    "value": asset_value,
                    "percent": asset_value / total_value,
                    "overlimit": asset_value / total_value > self.max_position_size_percent
                }
        
        # Check health status
        health_issues = []
        
        if eur_percent < self.rebalance_trigger_eur_percent:
            health_issues.append(f"EUR too low: {eur_percent*100:.1f}% < {self.rebalance_trigger_eur_percent*100:.1f}%")
        
        if available_eur < float(getattr(self.config, 'MIN_TRADE_AMOUNT', 30.0)):
            health_issues.append(f"Insufficient trading capital: €{available_eur:.2f}")
        
        for asset, pos in positions.items():
            if pos["overlimit"]:
                health_issues.append(f"{asset} position too large: {pos['percent']*100:.1f}% > {self.max_position_size_percent*100:.1f}%")
        
        status = "healthy" if not health_issues else "needs_attention"
        
        return {
            "status": status,
            "total_value": total_value,
            "eur_percent": eur_percent,
            "available_trading_capital": available_eur,
            "positions": positions,
            "issues": health_issues,
            "rebalancing_needed": self.check_rebalancing_needed(portfolio)
        }
