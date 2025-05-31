import logging
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime
from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer
from data_collector import DataCollector
from utils.trade_logger import TradeLogger
from utils.strategy_evaluator import StrategyEvaluator
from config import MAX_INVESTMENT_PER_TRADE_USD, RISK_LEVEL

logger = logging.getLogger(__name__)

class TradingStrategy:
    """Implements the trading strategy using LLM analysis"""
    
    def __init__(self, 
                coinbase_client: CoinbaseClient, 
                llm_analyzer: LLMAnalyzer,
                data_collector: DataCollector):
        """Initialize the trading strategy"""
        self.client = coinbase_client
        self.analyzer = llm_analyzer
        self.data_collector = data_collector
        self.risk_level = RISK_LEVEL
        self.max_investment = MAX_INVESTMENT_PER_TRADE_USD
        self.trade_logger = TradeLogger()
        self.strategy_evaluator = StrategyEvaluator()
        logger.info(f"Trading strategy initialized with risk level: {self.risk_level}")
    
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
            # Get historical data
            historical_data = self.data_collector.get_historical_data(
                product_id=product_id,
                granularity="ONE_HOUR",
                days_back=7
            )
            
            if historical_data.empty:
                logger.error(f"No historical data available for {product_id}")
                return {
                    "success": False,
                    "error": "No historical data available",
                    "product_id": product_id
                }
            
            # Get current market data
            market_data = self.data_collector.get_market_data(product_id)
            current_price = market_data.get("price", 0)
            
            if current_price == 0:
                logger.error(f"Could not get current price for {product_id}")
                return {
                    "success": False,
                    "error": "Could not get current price",
                    "product_id": product_id
                }
            
            # Calculate technical indicators
            indicators = self.data_collector.calculate_technical_indicators(historical_data)
            
            # Prepare data for LLM analysis
            analysis_data = {
                "product_id": product_id,
                "current_price": current_price,
                "historical_data": historical_data.tail(24).to_dict('records'),
                "indicators": indicators,
                "market_data": market_data
            }
            
            # Get LLM analysis
            analysis = self.analyzer.analyze_market(analysis_data)
            
            if not analysis:
                logger.error(f"LLM analysis failed for {product_id}")
                return {
                    "success": False,
                    "error": "LLM analysis failed",
                    "product_id": product_id
                }
            
            # Extract decision and confidence
            decision = analysis.get("decision", "HOLD")
            confidence = analysis.get("confidence", 0)
            
            # Log the decision
            logger.info(f"LLM decision for {product_id}: {decision} (confidence: {confidence}%)")
            
            # Check if confidence meets threshold
            confidence_threshold = self._get_confidence_threshold()
            
            if confidence < confidence_threshold:
                logger.info(f"Confidence ({confidence}%) below threshold ({confidence_threshold}%). Holding.")
                return {
                    "success": True,
                    "decision": "HOLD",
                    "reason": f"Confidence ({confidence}%) below threshold ({confidence_threshold}%)",
                    "product_id": product_id,
                    "price": current_price,
                    "confidence": confidence,
                    "analysis": analysis
                }
            
            # Execute trade based on decision
            trade_result = self._execute_trade(product_id, decision, current_price, analysis)
            
            # Add analysis to result
            trade_result["analysis"] = analysis
            trade_result["decision"] = decision
            trade_result["confidence"] = confidence
            trade_result["product_id"] = product_id
            trade_result["price"] = current_price
            
            return trade_result
            
        except Exception as e:
            logger.error(f"Error executing strategy for {product_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id
            }
    
    def _get_confidence_threshold(self) -> int:
        """Get confidence threshold based on risk level"""
        if self.risk_level == "low":
            return 80
        elif self.risk_level == "medium":
            return 70
        else:  # high risk
            return 60
    
    def _execute_trade(self, product_id: str, decision: str, current_price: float, analysis: Dict) -> Dict:
        """Execute a trade based on the decision"""
        try:
            # Determine trade parameters
            base_currency = product_id.split('-')[0]  # e.g., 'BTC' from 'BTC-USD'
            quote_currency = product_id.split('-')[1]  # e.g., 'USD' from 'BTC-USD'
            
            # Get market data and indicators for logging
            market_data = self.data_collector.get_market_data(product_id)
            historical_data = self.data_collector.get_historical_data(
                product_id=product_id,
                granularity="ONE_HOUR",
                days_back=1
            )
            indicators = self.data_collector.calculate_technical_indicators(historical_data)
            
            # Strategy parameters for logging
            strategy_params = {
                "risk_level": self.risk_level,
                "max_investment": self.max_investment,
                "confidence_threshold": self._get_confidence_threshold()
            }
            
            if decision == "BUY":
                # Calculate size based on max investment
                size = min(self.max_investment, self.client.get_account_balance(quote_currency))
                
                # Don't trade if size is too small
                if size < 10:  # Minimum $10 trade
                    return {
                        "success": False,
                        "error": f"Available balance ({size} {quote_currency}) is too small for trading",
                        "product_id": product_id
                    }
                
                # Place buy order
                order_result = self.client.place_market_order(
                    product_id=product_id,
                    side="BUY",
                    size=size
                )
                
                # Calculate crypto amount from USD
                crypto_amount = size / current_price
                
                # Log the trade
                trade_data = {
                    "timestamp": datetime.now().isoformat(),
                    "trade_id": order_result.get("order_id", ""),
                    "product_id": product_id,
                    "side": "buy",
                    "price": current_price,
                    "size": crypto_amount,
                    "value_usd": size,
                    "fee_usd": order_result.get("fee", 0.0),
                }
                self.trade_logger.log_trade(trade_data)
                
                # Log detailed strategy metrics
                self.strategy_evaluator.log_trade_decision(
                    trade_data=trade_data,
                    market_data=market_data,
                    indicators=indicators,
                    llm_analysis=analysis,
                    strategy_params=strategy_params
                )
                
                logger.info(f"Placed BUY order for {product_id}: {size} {quote_currency}")
                return {
                    "success": True,
                    "order_type": "BUY",
                    "size": size,
                    "currency": quote_currency,
                    "price": current_price,
                    "order_id": order_result.get("order_id"),
                    "stop_loss": analysis.get("stop_loss"),
                    "take_profit": analysis.get("take_profit")
                }
                
            elif decision == "SELL":
                # Calculate size based on available balance
                available_balance = self.client.get_account_balance(base_currency)
                
                # Don't trade if balance is too small
                if available_balance <= 0:
                    return {
                        "success": False,
                        "error": f"No {base_currency} available for selling",
                        "product_id": product_id
                    }
                
                # Place sell order
                order_result = self.client.place_market_order(
                    product_id=product_id,
                    side="SELL",
                    size=available_balance
                )
                
                # Log the trade
                trade_data = {
                    "timestamp": datetime.now().isoformat(),
                    "trade_id": order_result.get("order_id", ""),
                    "product_id": product_id,
                    "side": "sell",
                    "price": current_price,
                    "size": available_balance,
                    "value_usd": current_price * available_balance,
                    "fee_usd": order_result.get("fee", 0.0),
                }
                self.trade_logger.log_trade(trade_data)
                
                # Log detailed strategy metrics
                self.strategy_evaluator.log_trade_decision(
                    trade_data=trade_data,
                    market_data=market_data,
                    indicators=indicators,
                    llm_analysis=analysis,
                    strategy_params=strategy_params
                )
                
                logger.info(f"Placed SELL order for {product_id}: {available_balance} {base_currency}")
                return {
                    "success": True,
                    "order_type": "SELL",
                    "size": available_balance,
                    "currency": base_currency,
                    "price": current_price,
                    "order_id": order_result.get("order_id")
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Invalid decision: {decision}",
                    "product_id": product_id
                }
                
        except Exception as e:
            logger.error(f"Error executing trade for {product_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id
            }
