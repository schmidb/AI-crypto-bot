import logging
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime
import json
import os
from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer
from data_collector import DataCollector
from utils.trade_logger import TradeLogger
from utils.strategy_evaluator import StrategyEvaluator
from utils.portfolio import Portfolio
from config import (
    RISK_LEVEL, 
    PORTFOLIO_REBALANCE,
    MAX_TRADE_PERCENTAGE
)

logger = logging.getLogger(__name__)

class TradingStrategy:
    """Implements the trading strategy using LLM analysis and portfolio management"""
    
    def __init__(self, 
                coinbase_client: CoinbaseClient, 
                llm_analyzer: LLMAnalyzer,
                data_collector: DataCollector):
        """Initialize the trading strategy"""
        self.client = coinbase_client
        self.analyzer = llm_analyzer
        self.data_collector = data_collector
        self.risk_level = RISK_LEVEL
        self.trade_logger = TradeLogger()
        self.strategy_evaluator = StrategyEvaluator()
        
        # Initialize portfolio
        self.portfolio_manager = Portfolio(portfolio_file="data/portfolio.json")
        
        # For backward compatibility, expose portfolio data as property
        self._portfolio = self.portfolio_manager.to_dict()
        
        logger.info(f"Trading strategy initialized with risk level: {self.risk_level}")
        logger.info(f"Initial portfolio: {self._portfolio}")
    
    @property
    def portfolio(self):
        """Get current portfolio data"""
        self._portfolio = self.portfolio_manager.to_dict()
        return self._portfolio
    
    def update_portfolio_values(self) -> None:
        """Update portfolio with current market prices"""
        try:
            # Get current prices
            btc_price_data = self.client.get_product_price("BTC-USD")
            eth_price_data = self.client.get_product_price("ETH-USD")
            
            # Extract price values as floats
            btc_price = float(btc_price_data.get("price", 0))
            eth_price = float(eth_price_data.get("price", 0))
            
            # Update portfolio with current prices
            self.portfolio_manager.update_prices(btc_price, eth_price)
            
            # Update local portfolio copy
            self._portfolio = self.portfolio_manager.to_dict()
            
            logger.info(f"Portfolio updated: Total value ${self._portfolio['portfolio_value_usd']:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating portfolio values: {e}")
    
    def execute_strategy(self, product_id: str) -> Dict:
        """
        Execute the trading strategy for a specific product
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing trading strategy for {product_id}")
        
        try:
            # Update portfolio with current market values
            self.update_portfolio_values()
            
            # Get historical data
            historical_data = self.data_collector.get_historical_data(
                product_id=product_id,
                granularity="ONE_HOUR",
                days_back=7
            )
            
            if historical_data.empty:
                logger.error(f"No historical data available for {product_id}")
                return {"status": "error", "message": "No historical data available"}
            
            # Calculate technical indicators
            indicators = self.data_collector.calculate_indicators(historical_data)
            
            # Get market sentiment
            market_data = self.data_collector.get_market_data(product_id)
            
            # Prepare data for LLM analysis
            analysis_data = {
                "product_id": product_id,
                "current_price": market_data.get("price", 0),
                "historical_data": historical_data.tail(24).to_dict(orient="records"),
                "indicators": indicators,
                "risk_level": self.risk_level,
                "portfolio": self._portfolio
            }
            
            # Get trading decision from LLM
            decision = self.analyzer.get_trading_decision(analysis_data)
            
            # Execute the decision
            result = self._execute_decision(product_id, decision)
            
            # Log the trade
            self.trade_logger.log_trade(product_id, decision, result)
            
            # Evaluate strategy performance
            self.strategy_evaluator.evaluate(self._portfolio)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing strategy for {product_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def _execute_decision(self, product_id: str, decision: Dict) -> Dict:
        """
        Execute a trading decision
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            decision: Decision from LLM analyzer
            
        Returns:
            Dictionary with execution results
        """
        action = decision.get("action", "hold")
        confidence = decision.get("confidence", 0)
        reason = decision.get("reason", "No reason provided")
        
        logger.info(f"Decision for {product_id}: {action} (confidence: {confidence})")
        logger.info(f"Reason: {reason}")
        
        # Get current market data for price information
        market_data = self.data_collector.get_market_data(product_id)
        current_price = market_data.get("price", 0)
        price_changes = market_data.get("price_changes", {})
        
        result = {
            "status": "success",
            "action": action,
            "product_id": product_id,
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "reason": reason,
            "current_price": current_price,
            "price_changes": price_changes
        }
        
        # Extract the base currency (BTC or ETH) from the product ID
        base_currency = product_id.split("-")[0]
        
        if action == "buy":
            # Calculate how much USD to use for buying
            available_usd = self.portfolio_manager.get_asset_amount("USD")
            
            if available_usd <= 0:
                logger.info(f"No USD available for buying {base_currency}")
                result["status"] = "skipped"
                result["message"] = f"No USD available for buying {base_currency}"
                return result
            
            # Calculate trade size based on confidence and max trade percentage
            trade_percentage = (confidence / 100) * MAX_TRADE_PERCENTAGE
            trade_amount_usd = available_usd * (trade_percentage / 100)
            
            # Minimum trade amount
            min_trade = 10.0  # $10 minimum
            if trade_amount_usd < min_trade and available_usd >= min_trade:
                trade_amount_usd = min_trade
            
            if trade_amount_usd < 5.0:  # Too small to trade
                logger.info(f"Trade amount too small: ${trade_amount_usd:.2f}")
                result["status"] = "skipped"
                result["message"] = f"Trade amount too small: ${trade_amount_usd:.2f}"
                return result
            
            # Execute buy order
            try:
                current_price = float(self.client.get_product_price(product_id).get("price", 0))
                crypto_amount = trade_amount_usd / current_price
                
                # In a real implementation, this would call the actual order placement
                # order = self.client.place_market_order(product_id, "buy", trade_amount_usd)
                
                # Execute trade through portfolio manager
                trade_result = self.portfolio_manager.execute_trade(
                    asset=base_currency,
                    action="buy",
                    amount=crypto_amount,
                    price=current_price
                )
                
                if not trade_result.get("success", False):
                    result["status"] = "error"
                    result["message"] = trade_result.get("message", "Trade execution failed")
                    return result
                
                # Update local portfolio copy
                self._portfolio = self.portfolio_manager.to_dict()
                
                result["trade_amount_usd"] = trade_amount_usd
                result["crypto_amount"] = crypto_amount
                result["price"] = current_price
                
                logger.info(f"Bought {crypto_amount:.8f} {base_currency} for ${trade_amount_usd:.2f}")
                
            except Exception as e:
                logger.error(f"Error executing buy order: {e}")
                result["status"] = "error"
                result["message"] = str(e)
        
        elif action == "sell":
            # Calculate how much crypto to sell
            available_crypto = self.portfolio_manager.get_asset_amount(base_currency)
            
            if available_crypto <= 0:
                logger.info(f"No {base_currency} available for selling")
                result["status"] = "skipped"
                result["message"] = f"No {base_currency} available for selling"
                return result
            
            # Calculate trade size based on confidence and max trade percentage
            trade_percentage = (confidence / 100) * MAX_TRADE_PERCENTAGE
            crypto_amount = available_crypto * (trade_percentage / 100)
            
            # Minimum trade amount (0.001 BTC or 0.01 ETH)
            min_trade = 0.001 if base_currency == "BTC" else 0.01
            if crypto_amount < min_trade and available_crypto >= min_trade:
                crypto_amount = min_trade
            
            current_price = float(self.client.get_product_price(product_id).get("price", 0))
            if crypto_amount * current_price < 5.0:  # Too small to trade
                logger.info(f"Trade amount too small: {crypto_amount:.8f} {base_currency}")
                result["status"] = "skipped"
                result["message"] = f"Trade amount too small: {crypto_amount:.8f} {base_currency}"
                return result
            
            # Execute sell order
            try:
                # In a real implementation, this would call the actual order placement
                # order = self.client.place_market_order(product_id, "sell", crypto_amount)
                
                # Execute trade through portfolio manager
                trade_result = self.portfolio_manager.execute_trade(
                    asset=base_currency,
                    action="sell",
                    amount=crypto_amount,
                    price=current_price
                )
                
                if not trade_result.get("success", False):
                    result["status"] = "error"
                    result["message"] = trade_result.get("message", "Trade execution failed")
                    return result
                
                # Update local portfolio copy
                self._portfolio = self.portfolio_manager.to_dict()
                
                trade_amount_usd = crypto_amount * current_price
                result["trade_amount_usd"] = trade_amount_usd
                result["crypto_amount"] = crypto_amount
                result["price"] = current_price
                
                logger.info(f"Sold {crypto_amount:.8f} {base_currency} for ${trade_amount_usd:.2f}")
                
            except Exception as e:
                logger.error(f"Error executing sell order: {e}")
                result["status"] = "error"
                result["message"] = str(e)
        
        else:  # hold
            logger.info(f"Holding {base_currency} position")
            result["message"] = f"Holding {base_currency} position"
        
        return result
    
    def rebalance_portfolio(self) -> Dict:
        """
        Rebalance portfolio to maintain target allocation
        
        Returns:
            Dictionary with rebalance results
        """
        if not PORTFOLIO_REBALANCE:
            return {"status": "skipped", "message": "Portfolio rebalancing is disabled"}
        
        logger.info("Rebalancing portfolio")
        
        try:
            # Update portfolio with current market values
            self.update_portfolio_values()
            
            # Define target allocation from config
            from config import TARGET_ALLOCATION
            target_allocation = TARGET_ALLOCATION
            
            logger.info(f"Target allocation: {target_allocation}")
            
            # Calculate rebalance actions
            actions = self.portfolio_manager.calculate_rebalance_actions(target_allocation)
            
            if not actions:
                logger.info("Portfolio is balanced, no rebalancing needed")
                return {"status": "skipped", "message": "Portfolio is balanced"}
            
            # Execute rebalance actions
            executed_actions = []
            for action in actions:
                asset = action["asset"]
                trade_action = action["action"]
                amount = action["amount"]
                
                # Get current price
                price = float(self.client.get_product_price(f"{asset}-USD").get("price", 0))
                
                # Execute trade
                trade_result = self.portfolio_manager.execute_trade(
                    asset=asset,
                    action=trade_action,
                    amount=amount,
                    price=price
                )
                
                if trade_result.get("success", False):
                    executed_actions.append({
                        "asset": asset,
                        "action": trade_action,
                        "amount": amount,
                        "price": price,
                        "usd_value": amount * price
                    })
                else:
                    logger.warning(f"Failed to execute rebalance action: {trade_result.get('message')}")
            
            # Update local portfolio copy
            self._portfolio = self.portfolio_manager.to_dict()
            
            logger.info("Portfolio rebalanced")
            return {
                "status": "success", 
                "message": "Portfolio rebalanced",
                "actions": executed_actions
            }
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {e}")
            return {"status": "error", "message": str(e)}
            
    def refresh_portfolio_from_coinbase(self) -> Dict[str, Any]:
        """Refresh portfolio data from Coinbase"""
        try:
            # Get fresh portfolio data from Coinbase
            coinbase_portfolio = self.client.get_portfolio()
            
            if coinbase_portfolio:
                # Update portfolio with data from Coinbase
                update_result = self.portfolio_manager.update_from_exchange(coinbase_portfolio)
                
                if update_result.get("success", False):
                    # Update local portfolio copy
                    self._portfolio = self.portfolio_manager.to_dict()
                    
                    # Update portfolio values with current market prices
                    self.update_portfolio_values()
                    
                    logger.info("Portfolio refreshed from Coinbase")
                    return {"status": "success", "message": "Portfolio refreshed from Coinbase"}
                else:
                    logger.error(f"Failed to update portfolio: {update_result.get('message')}")
                    return {"status": "error", "message": update_result.get('message')}
            else:
                logger.error("Failed to refresh portfolio from Coinbase")
                return {"status": "error", "message": "Failed to refresh portfolio from Coinbase"}
        except Exception as e:
            logger.error(f"Error refreshing portfolio from Coinbase: {e}")
            return {"status": "error", "message": f"Error refreshing portfolio: {str(e)}"}
