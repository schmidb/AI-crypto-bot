import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class TradeLogger:
    """Logs and retrieves trade history"""
    
    def __init__(self, log_file="data/trades/trade_history.json"):
        """Initialize the trade logger"""
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create trade history file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump([], f)
    
    def log_rebalance_trade(self, product_id: str, action: str, amount: float, usd_value: float, reason: str = "portfolio_rebalancing") -> None:
        """
        Log a rebalancing trade to the trade history file
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            action: BUY or SELL
            amount: Amount of crypto traded
            usd_value: USD value of the trade
            reason: Reason for the trade (default: portfolio_rebalancing)
        """
        try:
            # Create rebalancing trade record
            trade_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "product_id": product_id,
                "action": action,
                "amount": amount,
                "usd_value": usd_value,
                "reason": f"Portfolio rebalancing: {action} {amount:.6f} {product_id.split('-')[0]} for ${usd_value:.2f}",
                "status": "executed",
                "trade_type": "rebalancing",
                "ai_recommendation": "REBALANCE",
                "confidence": 100,  # Rebalancing is always 100% confidence
                "execution_status": "executed",
                "trade_executed": True
            }
            
            # Load existing trades
            trades = []
            try:
                with open(self.log_file, 'r') as f:
                    trades = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                trades = []
            
            # Add new trade
            trades.append(trade_record)
            
            # Save updated trades
            with open(self.log_file, 'w') as f:
                json.dump(trades, f, indent=2)
            
            logger.info(f"Rebalancing trade logged: {action} {amount:.6f} {product_id} for ${usd_value:.2f}")
            
        except Exception as e:
            logger.error(f"Error logging rebalancing trade: {e}")

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
            
            # Ensure we have a valid price - check multiple possible fields
            price = result.get("price", 0) or result.get("execution_price", 0)
            if price == 0:
                logger.warning(f"Missing price for {product_id}, attempting to fetch current price")
                try:
                    from coinbase_client import CoinbaseClient
                    client = CoinbaseClient()
                    price_data = client.get_product_price(product_id)
                    price = float(price_data.get("price", 0))
                    logger.info(f"Successfully fetched current price for {product_id}: ${price}")
                except Exception as e:
                    logger.error(f"Failed to fetch current price for {product_id}: {e}")
                    # Set a default price to avoid logging with 0
                    price = 0
            
            # Create trade record with enhanced reasoning and fee information
            trade = {
                "timestamp": datetime.utcnow().isoformat(),  # Use UTC time for consistency
                "product_id": product_id,
                "action": result.get("action", "unknown"),
                "price": price,
                "crypto_amount": result.get("crypto_amount", 0),
                "trade_amount_usd": result.get("trade_amount_base", result.get("trade_amount_usd", 0)),  # Use trade_amount_base as primary
                "confidence": decision.get("confidence", 0),
                "reason": result.get("reason", decision.get("reason", "No reason provided")),  # Use result reason first
                "status": result.get("status", "unknown"),
                # Enhanced fields for better understanding
                "intended_action": result.get("intended_action", result.get("action", "unknown")),
                "skip_reason": result.get("skip_reason", None),
                "ai_recommendation": decision.get("action", "unknown"),
                "execution_message": result.get("execution_message", result.get("message", "")),
                # Fee information from Coinbase API - use the fee_percentage directly from execution result
                "total_fees": result.get("total_fees", 0),
                "total_value_after_fees": result.get("total_value_after_fees", 0),
                "filled_size": result.get("filled_size", 0),
                "average_filled_price": result.get("average_filled_price", price),
                "actual_eur_spent": result.get("actual_eur_spent", result.get("trade_amount_base", result.get("trade_amount_usd", 0))),
                "fee_percentage": result.get("fee_percentage", 0)  # Use fee_percentage directly from execution result
            }
            
            # If fee_percentage wasn't provided but we have fee data, calculate it
            if trade["fee_percentage"] == 0 and trade["total_fees"] > 0:
                # Use actual_eur_spent as the base for fee percentage calculation
                base_amount = trade["actual_eur_spent"] if trade["actual_eur_spent"] > 0 else trade["trade_amount_usd"]
                if base_amount > 0:
                    trade["fee_percentage"] = (trade["total_fees"] / base_amount) * 100
            
            # Add trade to history
            trades.append(trade)
            
            # Save updated trade history
            with open(self.log_file, 'w') as f:
                json.dump(trades, f, indent=2)
                
            # Enhanced logging message with fee information
            log_msg = f"Trade logged: {trade['action']} {trade['crypto_amount']} {product_id.split('-')[0]} at €{trade['price']}"
            if trade['total_fees'] > 0:
                log_msg += f" (fees: €{trade['total_fees']:.4f}, {trade['fee_percentage']:.3f}%)"
            logger.info(log_msg)
            
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
