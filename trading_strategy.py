import logging
import pandas as pd
from typing import Dict, List, Tuple
from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer
from data_collector import DataCollector
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
            
            # Calculate technical indicators
            data_with_indicators = self.data_collector.calculate_technical_indicators(historical_data)
            
            # Get current market data
            current_market_data = self.data_collector.get_current_market_data([product_id])
            current_price = current_market_data.get(product_id, {}).get('price')
            
            if not current_price:
                logger.error(f"Could not get current price for {product_id}")
                return {
                    "success": False,
                    "error": "Could not get current price",
                    "product_id": product_id
                }
            
            # Prepare additional context
            additional_context = self._prepare_additional_context(product_id, data_with_indicators)
            
            # Get LLM analysis
            analysis = self.analyzer.analyze_market_data(
                market_data=data_with_indicators,
                current_price=current_price,
                trading_pair=product_id,
                additional_context=additional_context
            )
            
            # Make trading decision
            decision = analysis.get('decision', 'HOLD')
            confidence = analysis.get('confidence', 0)
            
            # Execute trade if confidence is high enough
            result = {
                "success": True,
                "product_id": product_id,
                "decision": decision,
                "confidence": confidence,
                "reasoning": analysis.get('reasoning', ''),
                "risk_assessment": analysis.get('risk_assessment', 'medium'),
                "current_price": current_price,
                "trade_executed": False
            }
            
            # Only execute trades if confidence is above threshold
            confidence_threshold = self._get_confidence_threshold()
            
            if decision != "HOLD" and confidence >= confidence_threshold:
                trade_result = self._execute_trade(product_id, decision, current_price, analysis)
                result.update({
                    "trade_executed": trade_result.get("success", False),
                    "trade_details": trade_result
                })
            
            logger.info(f"Strategy execution completed for {product_id} with decision: {decision}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing strategy for {product_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id
            }
    
    def _prepare_additional_context(self, product_id: str, data: pd.DataFrame) -> Dict:
        """Prepare additional context for LLM analysis"""
        # Get account balance
        base_currency = product_id.split('-')[0]  # e.g., 'BTC' from 'BTC-USD'
        quote_currency = product_id.split('-')[1]  # e.g., 'USD' from 'BTC-USD'
        
        base_balance = self.client.get_account_balance(base_currency)
        quote_balance = self.client.get_account_balance(quote_currency)
        
        # Calculate some additional metrics
        latest_rsi = data['rsi'].iloc[-1] if 'rsi' in data.columns and not pd.isna(data['rsi'].iloc[-1]) else None
        macd_signal = data['macd_signal'].iloc[-1] if 'macd_signal' in data.columns and not pd.isna(data['macd_signal'].iloc[-1]) else None
        macd_hist = data['macd_hist'].iloc[-1] if 'macd_hist' in data.columns and not pd.isna(data['macd_hist'].iloc[-1]) else None
        
        # Determine if price is above or below moving averages
        price_vs_sma50 = "above" if data['close'].iloc[-1] > data['sma_50'].iloc[-1] else "below" if not pd.isna(data['sma_50'].iloc[-1]) else "unknown"
        price_vs_sma200 = "above" if data['close'].iloc[-1] > data['sma_200'].iloc[-1] else "below" if not pd.isna(data['sma_200'].iloc[-1]) else "unknown"
        
        return {
            f"{base_currency}_balance": base_balance,
            f"{quote_currency}_balance": quote_balance,
            "risk_level": self.risk_level,
            "max_investment": self.max_investment,
            "latest_rsi": latest_rsi,
            "macd_signal": macd_signal,
            "macd_histogram": macd_hist,
            "price_vs_sma50": price_vs_sma50,
            "price_vs_sma200": price_vs_sma200
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
