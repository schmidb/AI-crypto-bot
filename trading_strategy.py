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
from config import (
    RISK_LEVEL, 
    INITIAL_BTC_AMOUNT, 
    INITIAL_ETH_AMOUNT, 
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
        
        # Portfolio tracking
        self.portfolio_file = "data/portfolio.json"
        self.portfolio = self._load_portfolio()
        
        logger.info(f"Trading strategy initialized with risk level: {self.risk_level}")
        logger.info(f"Initial portfolio: {self.portfolio}")
    
    def _load_portfolio(self) -> Dict:
        """Load portfolio from file or initialize with data from Coinbase"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading portfolio: {e}")
        
        # Initialize with actual data from Coinbase instead of default values
        logger.info("Fetching portfolio data from Coinbase")
        portfolio = self.client.get_portfolio()
        
        # If getting data from Coinbase failed, fall back to config values
        if not portfolio:
            logger.info("Using default portfolio values from config")
            portfolio = {
                "BTC": {
                    "amount": INITIAL_BTC_AMOUNT,
                    "initial_amount": INITIAL_BTC_AMOUNT,
                    "last_price_usd": 0.0
                },
                "ETH": {
                    "amount": INITIAL_ETH_AMOUNT,
                    "initial_amount": INITIAL_ETH_AMOUNT,
                    "last_price_usd": 0.0
                },
                "USD": {
                    "amount": 0.0,
                    "initial_amount": 0.0
                },
                "trades_executed": 0,
                "portfolio_value_usd": 0.0,
                "initial_value_usd": 0.0,
                "last_updated": datetime.now().isoformat()
            }
        
        self._save_portfolio(portfolio)
        return portfolio
    
    def _save_portfolio(self, portfolio: Dict = None) -> None:
        """Save portfolio to file"""
        if portfolio is None:
            portfolio = self.portfolio
        
        # Update last updated timestamp
        portfolio["last_updated"] = datetime.now().isoformat()
        
        try:
            os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
            with open(self.portfolio_file, 'w') as f:
                json.dump(portfolio, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")
    
    def update_portfolio_values(self) -> None:
        """Update portfolio with current market prices"""
        try:
            # Get current prices
            btc_price_data = self.client.get_product_price("BTC-USD")
            eth_price_data = self.client.get_product_price("ETH-USD")
            
            # Extract price values as floats
            btc_price = float(btc_price_data.get("price", 0))
            eth_price = float(eth_price_data.get("price", 0))
            
            # Update portfolio
            self.portfolio["BTC"]["last_price_usd"] = btc_price
            self.portfolio["ETH"]["last_price_usd"] = eth_price
            
            # Calculate total portfolio value
            btc_value = self.portfolio["BTC"]["amount"] * btc_price
            eth_value = self.portfolio["ETH"]["amount"] * eth_price
            usd_value = self.portfolio["USD"]["amount"]
            
            total_value = btc_value + eth_value + usd_value
            self.portfolio["portfolio_value_usd"] = total_value
            
            # Calculate initial value if not set
            if self.portfolio["initial_value_usd"] == 0.0:
                initial_btc_value = self.portfolio["BTC"]["initial_amount"] * btc_price
                initial_eth_value = self.portfolio["ETH"]["initial_amount"] * eth_price
                initial_value = initial_btc_value + initial_eth_value
                self.portfolio["initial_value_usd"] = initial_value
            
            self._save_portfolio()
            logger.info(f"Portfolio updated: Total value ${total_value:.2f}")
            
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
                "portfolio": self.portfolio
            }
            
            # Get trading decision from LLM
            decision = self.analyzer.get_trading_decision(analysis_data)
            
            # Execute the decision
            result = self._execute_decision(product_id, decision)
            
            # Log the trade
            self.trade_logger.log_trade(product_id, decision, result)
            
            # Evaluate strategy performance
            self.strategy_evaluator.evaluate(self.portfolio)
            
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
        
        result = {
            "status": "success",
            "action": action,
            "product_id": product_id,
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "reason": reason
        }
        
        # Extract the base currency (BTC or ETH) from the product ID
        base_currency = product_id.split("-")[0]
        
        if action == "buy":
            # Calculate how much USD to use for buying
            available_usd = self.portfolio["USD"]["amount"]
            
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
                current_price = self.client.get_product_price(product_id)
                crypto_amount = trade_amount_usd / current_price
                
                # In a real implementation, this would call the actual order placement
                # order = self.client.place_market_order(product_id, "buy", trade_amount_usd)
                
                # Update portfolio
                self.portfolio["USD"]["amount"] -= trade_amount_usd
                self.portfolio[base_currency]["amount"] += crypto_amount
                self.portfolio["trades_executed"] += 1
                self._save_portfolio()
                
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
            available_crypto = self.portfolio[base_currency]["amount"]
            
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
            
            if crypto_amount * self.portfolio[base_currency]["last_price_usd"] < 5.0:  # Too small to trade
                logger.info(f"Trade amount too small: {crypto_amount:.8f} {base_currency}")
                result["status"] = "skipped"
                result["message"] = f"Trade amount too small: {crypto_amount:.8f} {base_currency}"
                return result
            
            # Execute sell order
            try:
                current_price = self.client.get_product_price(product_id)
                trade_amount_usd = crypto_amount * current_price
                
                # In a real implementation, this would call the actual order placement
                # order = self.client.place_market_order(product_id, "sell", crypto_amount)
                
                # Update portfolio
                self.portfolio[base_currency]["amount"] -= crypto_amount
                self.portfolio["USD"]["amount"] += trade_amount_usd
                self.portfolio["trades_executed"] += 1
                self._save_portfolio()
                
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
            
            # Calculate current allocation
            btc_value = self.portfolio["BTC"]["amount"] * self.portfolio["BTC"]["last_price_usd"]
            eth_value = self.portfolio["ETH"]["amount"] * self.portfolio["ETH"]["last_price_usd"]
            usd_value = self.portfolio["USD"]["amount"]
            total_value = self.portfolio["portfolio_value_usd"]
            
            # Target allocation (example: 40% BTC, 40% ETH, 20% USD)
            target_btc = 0.40
            target_eth = 0.40
            target_usd = 0.20
            
            # Calculate current allocation percentages
            current_btc = btc_value / total_value if total_value > 0 else 0
            current_eth = eth_value / total_value if total_value > 0 else 0
            current_usd = usd_value / total_value if total_value > 0 else 0
            
            # Threshold for rebalancing (5% deviation)
            threshold = 0.05
            
            rebalance_needed = (
                abs(current_btc - target_btc) > threshold or
                abs(current_eth - target_eth) > threshold or
                abs(current_usd - target_usd) > threshold
            )
            
            if not rebalance_needed:
                logger.info("Portfolio is balanced, no rebalancing needed")
                return {"status": "skipped", "message": "Portfolio is balanced"}
            
            # Rebalance logic would go here
            # This would involve selling overweight assets and buying underweight assets
            
            logger.info("Portfolio rebalanced")
            return {"status": "success", "message": "Portfolio rebalanced"}
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {e}")
            return {"status": "error", "message": str(e)}
    def refresh_portfolio_from_coinbase(self) -> Dict[str, Any]:
        """Refresh portfolio data from Coinbase"""
        try:
            # Get fresh portfolio data from Coinbase
            coinbase_portfolio = self.client.get_portfolio()
            
            if coinbase_portfolio:
                # Preserve trade history and other metadata
                coinbase_portfolio["trades_executed"] = self.portfolio.get("trades_executed", 0)
                
                # Update the portfolio
                self.portfolio = coinbase_portfolio
                self._save_portfolio()
                
                # Update portfolio values with current market prices
                self.update_portfolio_values()
                
                logger.info("Portfolio refreshed from Coinbase")
                return {"status": "success", "message": "Portfolio refreshed from Coinbase"}
            else:
                logger.error("Failed to refresh portfolio from Coinbase")
                return {"status": "error", "message": "Failed to refresh portfolio from Coinbase"}
        except Exception as e:
            logger.error(f"Error refreshing portfolio from Coinbase: {e}")
            return {"status": "error", "message": f"Error refreshing portfolio: {str(e)}"}
