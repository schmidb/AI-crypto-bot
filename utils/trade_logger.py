import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class TradeLogger:
    """Logs and retrieves trade history"""
    
    def __init__(self, log_file="data/trade_history.json"):
        """Initialize the trade logger"""
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create trade history file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump([], f)
    
    def log_trade(self, product_id: str, decision: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Log a trade to the trade history file
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            decision: Decision from LLM analyzer
            result: Result of trade execution
        """
        try:
            # Load existing trade history
            trades = []
            try:
                with open(self.log_file, 'r') as f:
                    trades = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                trades = []
            
            # Create trade record
            trade = {
                "timestamp": datetime.now().isoformat(),
                "product_id": product_id,
                "action": result.get("action", "unknown"),
                "price": result.get("price", 0),
                "crypto_amount": result.get("crypto_amount", 0),
                "trade_amount_usd": result.get("trade_amount_usd", 0),
                "confidence": decision.get("confidence", 0),
                "reason": decision.get("reason", "No reason provided"),
                "status": result.get("status", "unknown")
            }
            
            # Add trade to history
            trades.append(trade)
            
            # Save updated trade history
            with open(self.log_file, 'w') as f:
                json.dump(trades, f, indent=2)
                
            logger.info(f"Trade logged: {trade['action']} {trade['crypto_amount']} {product_id.split('-')[0]} at ${trade['price']}")
            
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent trades from the trade history
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of recent trades
        """
        try:
            # Check if file exists
            if not os.path.exists(self.log_file):
                logger.warning(f"Trade history file not found: {self.log_file}")
                return []
                
            # Check if file is empty
            if os.path.getsize(self.log_file) == 0:
                logger.warning(f"Trade history file is empty: {self.log_file}")
                return []
                
            try:
                with open(self.log_file, 'r') as f:
                    trades = json.load(f)
                
                # Validate trades is a list
                if not isinstance(trades, list):
                    logger.warning(f"Trade history is not a list: {type(trades)}")
                    return []
                    
                # Sort trades by timestamp (newest first)
                trades.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                
                # Return limited number of trades
                return trades[:limit]
            except json.JSONDecodeError:
                logger.error(f"Error decoding trade history JSON: {self.log_file}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    def get_trades_by_product(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Get trades for a specific product
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            List of trades for the specified product
        """
        try:
            with open(self.log_file, 'r') as f:
                trades = json.load(f)
            
            # Filter trades by product ID
            filtered_trades = [trade for trade in trades if trade.get("product_id") == product_id]
            
            # Sort trades by timestamp (newest first)
            filtered_trades.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return filtered_trades
            
        except Exception as e:
            logger.error(f"Error getting trades by product: {e}")
            return []
