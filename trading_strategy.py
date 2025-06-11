import json
import logging
import os
from typing import Dict, Any, Tuple, List
from datetime import datetime
from config import Config
from utils.trade_logger import TradeLogger
from coinbase_client import CoinbaseClient

logger = logging.getLogger(__name__)

class TradingStrategy:
    """Implements trading strategy with risk management"""
    
    def __init__(self, config: Config, llm_analyzer=None, data_collector=None):
        """Initialize trading strategy with configuration"""
        self.config = config
        self.risk_level = config.RISK_LEVEL
        self.llm_analyzer = llm_analyzer
        self.data_collector = data_collector
        
        # Initialize components
        self.trade_logger = TradeLogger()
        self.coinbase_client = CoinbaseClient()
        
        # Load initial portfolio
        self.portfolio = self._load_portfolio()
        
        logger.info(f"Trading strategy initialized with risk level: {self.risk_level}")
        logger.info(f"Initial portfolio: {self.portfolio}")
    
    def _load_portfolio(self) -> Dict:
        """Load portfolio data"""
        try:
            with open("data/portfolio/portfolio.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
            return {}
    
    def _save_portfolio(self) -> None:
        """Save portfolio data"""
        try:
            os.makedirs("data/portfolio", exist_ok=True)
            with open("data/portfolio/portfolio.json", "w") as f:
                json.dump(self.portfolio, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")
    
    def refresh_portfolio_from_coinbase(self) -> Dict[str, Any]:
        """
        Refresh portfolio data from Coinbase
        
        Returns:
            Dict with status and message
        """
        try:
            # Get current portfolio from Coinbase
            coinbase_portfolio = self.coinbase_client.get_portfolio()
            
            if not coinbase_portfolio:
                return {"status": "error", "message": "Failed to get portfolio from Coinbase"}
            
            # Update local portfolio with Coinbase data
            self.portfolio.update(coinbase_portfolio)
            
            # Add timestamp
            self.portfolio["last_updated"] = datetime.utcnow().isoformat()
            
            # Save updated portfolio
            self._save_portfolio()
            
            logger.info("Portfolio successfully refreshed from Coinbase")
            return {"status": "success", "message": "Portfolio refreshed successfully"}
            
        except Exception as e:
            error_msg = f"Error refreshing portfolio from Coinbase: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def get_trading_decision(self, market_data: Dict[str, Any], indicators: Dict[str, float]) -> Tuple[str, float, str]:
        """
        Get trading decision based on market data and indicators
        
        Args:
            market_data: Current market data
            indicators: Technical indicators
            
        Returns:
            Tuple of (decision, confidence, reasoning)
        """
        try:
            # Extract key indicators (convert numpy types to Python types)
            rsi = float(indicators.get('rsi', 50))
            macd = float(indicators.get('macd', 0))
            macd_signal = float(indicators.get('macd_signal', 0))
            bb_upper = float(indicators.get('bb_upper', 0))
            bb_lower = float(indicators.get('bb_lower', 0))
            current_price = float(indicators.get('current_price', 0))
            
            # Initialize confidence scores
            buy_confidence = 0
            sell_confidence = 0
            
            # RSI Analysis (30% weight)
            if rsi < 30:  # Oversold
                buy_confidence += 30
            elif rsi > 70:  # Overbought
                sell_confidence += 30
            
            # MACD Analysis (40% weight)
            if macd > macd_signal:  # Bullish crossover
                buy_confidence += 40
            elif macd < macd_signal:  # Bearish crossover
                sell_confidence += 40
            
            # Bollinger Bands Analysis (30% weight)
            if current_price < bb_lower:  # Price below lower band
                buy_confidence += 30
            elif current_price > bb_upper:  # Price above upper band
                sell_confidence += 30
            
            # Apply risk level adjustments
            if self.risk_level == "low":
                confidence_threshold = 80
            elif self.risk_level == "medium":
                confidence_threshold = 70
            else:  # high
                confidence_threshold = 60
            
            # Determine decision
            if buy_confidence >= confidence_threshold:
                return "buy", buy_confidence, f"Strong buy signals: RSI={rsi:.2f}, MACD crossover positive, price near support"
            elif sell_confidence >= confidence_threshold:
                return "sell", sell_confidence, f"Strong sell signals: RSI={rsi:.2f}, MACD crossover negative, price near resistance"
            else:
                return "hold", max(buy_confidence, sell_confidence), f"No clear signals: RSI={rsi:.2f}, MACD neutral"
                
        except Exception as e:
            logger.error(f"Error getting trading decision: {e}")
            return "hold", 0, f"Error during analysis: {str(e)}"
    
    def calculate_position_size(self, decision: str, confidence: float, available_balance: float) -> float:
        """
        Calculate position size based on confidence and risk level
        
        Args:
            decision: Trading decision (buy/sell/hold)
            confidence: Decision confidence (0-100)
            available_balance: Available balance for trading
            
        Returns:
            Position size in USD
        """
        try:
            # Base position size on confidence
            base_size = available_balance * (confidence / 100)
            
            # Apply risk level multipliers using the centralized function
            risk_multiplier = self._get_risk_multiplier()
                
            position_size = base_size * risk_multiplier
            
            # Apply min/max constraints
            min_trade = float(self.config.MIN_TRADE_USD)
            max_position = float(self.config.MAX_POSITION_SIZE_USD)
            
            if position_size < min_trade:
                return 0  # Don't trade if below minimum
            
            return min(position_size, max_position)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def update_portfolio(self, trade_result: Dict[str, Any]) -> None:
        """
        Update portfolio after a trade
        
        Args:
            trade_result: Trade execution result
        """
        try:
            # Update portfolio with trade result
            if trade_result.get("success"):
                self.portfolio = self._load_portfolio()  # Reload from file
                logger.info(f"Portfolio updated after trade: {self.portfolio}")
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
    
    def rebalance_portfolio(self) -> Dict[str, Any]:
        """
        Rebalance portfolio to maintain target allocations
        
        Returns:
            Dict with rebalancing results
        """
        try:
            logger.info("Starting portfolio rebalancing...")
            
            # Get current portfolio from Coinbase
            refresh_result = self.refresh_portfolio_from_coinbase()
            if refresh_result.get("status") != "success":
                return {"status": "error", "message": "Failed to refresh portfolio before rebalancing"}
            
            # Define target allocation (Enhanced Trading Strategy)
            target_allocation = {
                'BTC': 26.7,  # 26.7% of total portfolio
                'ETH': 26.7,  # 26.7% of total portfolio  
                'SOL': 26.7,  # 26.7% of total portfolio
                'USD': 20.0   # 20% of total portfolio for liquidity
            }
            
            # Check if rebalancing is needed
            current_allocation = self._get_current_allocation()
            rebalance_needed = self._check_rebalancing_needed(current_allocation, target_allocation)
            
            if not rebalance_needed:
                logger.info("Portfolio is within target allocation ranges - no rebalancing needed")
                return {
                    "status": "success", 
                    "message": "Portfolio is within target ranges",
                    "actions_taken": [],
                    "current_allocation": current_allocation,
                    "target_allocation": target_allocation
                }
            
            # Calculate required rebalancing actions
            from utils.portfolio import Portfolio
            portfolio_util = Portfolio()
            portfolio_util.data = self.portfolio
            
            try:
                rebalance_actions = portfolio_util.calculate_rebalance_actions(target_allocation)
            except Exception as e:
                logger.error(f"Error calculating rebalance actions: {e}")
                return {"status": "error", "message": f"Failed to calculate rebalance actions: {str(e)}"}
            
            if not rebalance_actions:
                logger.info("No rebalancing actions required")
                return {
                    "status": "success",
                    "message": "No rebalancing actions required", 
                    "actions_taken": [],
                    "current_allocation": current_allocation,
                    "target_allocation": target_allocation
                }
            
            # Execute rebalancing trades
            executed_actions = []
            failed_actions = []
            
            logger.info(f"Executing {len(rebalance_actions)} rebalancing actions...")
            
            for action in rebalance_actions:
                try:
                    result = self._execute_rebalance_action(action)
                    if result.get("success"):
                        executed_actions.append({**action, "execution_result": result})
                        logger.info(f"Successfully executed: {action['action'].upper()} {action['amount']:.6f} {action['asset']}")
                    else:
                        failed_actions.append({**action, "error": result.get("error", "Unknown error")})
                        logger.warning(f"Failed to execute: {action['action'].upper()} {action['amount']:.6f} {action['asset']} - {result.get('error')}")
                        
                except Exception as e:
                    failed_actions.append({**action, "error": str(e)})
                    logger.error(f"Exception executing rebalance action: {e}")
                
                # Add delay between trades to avoid rate limiting
                import time
                time.sleep(2)
            
            # Update portfolio after rebalancing
            if executed_actions:
                logger.info("Refreshing portfolio after rebalancing...")
                self.refresh_portfolio_from_coinbase()
                updated_allocation = self._get_current_allocation()
            else:
                updated_allocation = current_allocation
            
            # Prepare result summary
            result = {
                "status": "success" if executed_actions else "partial_failure",
                "message": f"Rebalancing completed: {len(executed_actions)} successful, {len(failed_actions)} failed",
                "actions_executed": len(executed_actions),
                "actions_failed": len(failed_actions),
                "executed_actions": executed_actions,
                "failed_actions": failed_actions,
                "current_allocation": current_allocation,
                "updated_allocation": updated_allocation,
                "target_allocation": target_allocation
            }
            
            logger.info(f"Portfolio rebalancing completed: {len(executed_actions)} actions executed, {len(failed_actions)} failed")
            return result
            
        except Exception as e:
            error_msg = f"Error during portfolio rebalancing: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def _get_current_allocation(self) -> Dict[str, float]:
        """Get current portfolio allocation percentages"""
        try:
            total_value = self.portfolio.get("portfolio_value_usd", 0)
            if total_value <= 0:
                return {}
            
            allocation = {}
            for asset in ['BTC', 'ETH', 'SOL']:
                asset_data = self.portfolio.get(asset, {})
                if isinstance(asset_data, dict):
                    amount = asset_data.get("amount", 0)
                    price = asset_data.get("last_price_usd", 0)
                    value = amount * price
                    allocation[asset] = (value / total_value) * 100
                else:
                    allocation[asset] = 0
            
            # USD allocation
            usd_amount = self.portfolio.get("USD", {}).get("amount", 0)
            allocation["USD"] = (usd_amount / total_value) * 100
            
            return allocation
            
        except Exception as e:
            logger.error(f"Error calculating current allocation: {e}")
            return {}

    def _check_rebalancing_needed(self, current: Dict[str, float], target: Dict[str, float]) -> bool:
        """Check if rebalancing is needed based on threshold"""
        try:
            threshold = getattr(self.config, 'REBALANCE_THRESHOLD_PERCENT', 5.0)
            
            for asset in target.keys():
                current_pct = current.get(asset, 0)
                target_pct = target.get(asset, 0)
                deviation = abs(current_pct - target_pct)
                
                if deviation > threshold:
                    logger.info(f"Rebalancing needed: {asset} deviation {deviation:.1f}% > {threshold}% threshold")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rebalancing threshold: {e}")
            return False

    def _execute_rebalance_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single rebalancing action (buy or sell)"""
        try:
            asset = action["asset"]
            amount = action["amount"]
            action_type = action["action"].upper()
            
            # Create product ID for trading
            product_id = f"{asset}-USD"
            
            # Prepare trade parameters
            if action_type == "SELL":
                # Execute sell order
                result = self.coinbase_client.place_sell_order(
                    product_id=product_id,
                    amount=amount,
                    order_type="market"
                )
            elif action_type == "BUY":
                # Execute buy order  
                usd_amount = action["usd_value"]
                result = self.coinbase_client.place_buy_order(
                    product_id=product_id,
                    usd_amount=usd_amount,
                    order_type="market"
                )
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
            
            if result and result.get("success"):
                # Log the rebalancing trade
                self.trade_logger.log_rebalance_trade(
                    product_id=product_id,
                    action=action_type,
                    amount=amount,
                    usd_value=action["usd_value"],
                    reason="portfolio_rebalancing"
                )
                
                return {
                    "success": True,
                    "order_id": result.get("order_id"),
                    "executed_amount": result.get("executed_amount", amount),
                    "executed_price": result.get("executed_price", 0),
                    "fees": result.get("fees", 0)
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Trade execution failed")
                }
                
        except Exception as e:
            logger.error(f"Error executing rebalance action: {e}")
            return {"success": False, "error": str(e)}

    def check_and_rebalance(self) -> Dict[str, Any]:
        """
        Intelligently check if rebalancing is needed and execute if optimal
        Uses market conditions and trading context to make smart rebalancing decisions
        """
        try:
            # Only rebalance if enabled in config
            if not getattr(self.config, 'PORTFOLIO_REBALANCE', True):
                return {"status": "disabled", "message": "Portfolio rebalancing is disabled"}
            
            logger.info("Checking if intelligent portfolio rebalancing is needed...")
            
            # Get current portfolio state
            refresh_result = self.refresh_portfolio_from_coinbase()
            if refresh_result.get("status") != "success":
                return {"status": "error", "message": "Failed to refresh portfolio before rebalancing check"}
            
            # Define target allocation
            target_allocation = {
                'BTC': 26.7, 'ETH': 26.7, 'SOL': 26.7, 'USD': 20.0
            }
            
            # Get current allocation and check if rebalancing is needed
            current_allocation = self._get_current_allocation()
            rebalance_analysis = self._analyze_rebalancing_need(current_allocation, target_allocation)
            
            if not rebalance_analysis["needed"]:
                logger.info(f"Portfolio is balanced - max deviation: {rebalance_analysis['max_deviation']:.1f}%")
                return {
                    "status": "success",
                    "message": f"Portfolio is balanced (max deviation: {rebalance_analysis['max_deviation']:.1f}%)",
                    "rebalancing_needed": False,
                    "current_allocation": current_allocation,
                    "target_allocation": target_allocation
                }
            
            # Rebalancing is needed - check if it's a good time to execute
            market_conditions = self._assess_market_conditions_for_rebalancing()
            timing_decision = self._evaluate_rebalancing_timing(rebalance_analysis, market_conditions)
            
            if not timing_decision["should_rebalance"]:
                logger.info(f"Rebalancing needed but timing not optimal: {timing_decision['reason']}")
                return {
                    "status": "deferred",
                    "message": f"Rebalancing deferred: {timing_decision['reason']}",
                    "rebalancing_needed": True,
                    "timing_reason": timing_decision["reason"],
                    "next_check": timing_decision.get("next_check", "next cycle"),
                    "current_allocation": current_allocation,
                    "deviation_analysis": rebalance_analysis
                }
            
            # Execute intelligent rebalancing
            logger.info(f"Executing intelligent rebalancing: {timing_decision['reason']}")
            return self._execute_intelligent_rebalancing(target_allocation, rebalance_analysis, market_conditions)
            
        except Exception as e:
            error_msg = f"Error in intelligent rebalancing check: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def _analyze_rebalancing_need(self, current: Dict[str, float], target: Dict[str, float]) -> Dict[str, Any]:
        """Analyze if rebalancing is needed and how urgent it is"""
        try:
            threshold = getattr(self.config, 'REBALANCE_THRESHOLD_PERCENT', 5.0)
            deviations = {}
            max_deviation = 0
            urgent_assets = []
            
            for asset in target.keys():
                current_pct = current.get(asset, 0)
                target_pct = target.get(asset, 0)
                deviation = abs(current_pct - target_pct)
                deviations[asset] = {
                    "current": current_pct,
                    "target": target_pct,
                    "deviation": deviation,
                    "over_threshold": deviation > threshold
                }
                
                max_deviation = max(max_deviation, deviation)
                
                # Mark as urgent if deviation is very high
                if deviation > threshold * 2:  # 10% for urgent
                    urgent_assets.append(asset)
            
            return {
                "needed": max_deviation > threshold,
                "urgent": len(urgent_assets) > 0,
                "max_deviation": max_deviation,
                "threshold": threshold,
                "deviations": deviations,
                "urgent_assets": urgent_assets,
                "severity": "critical" if max_deviation > 15 else "high" if max_deviation > 10 else "moderate"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing rebalancing need: {e}")
            return {"needed": False, "error": str(e)}

    def _assess_market_conditions_for_rebalancing(self) -> Dict[str, Any]:
        """Assess current market conditions to determine optimal rebalancing timing"""
        try:
            market_conditions = {
                "volatility": "unknown",
                "trend": "unknown", 
                "trading_volume": "unknown",
                "spread_conditions": "unknown",
                "overall_assessment": "neutral"
            }
            
            # Analyze recent market data for each asset
            assets_analysis = {}
            for asset in ['BTC', 'ETH', 'SOL']:
                try:
                    product_id = f"{asset}-USD"
                    market_data = self.data_collector.get_market_data(product_id) if self.data_collector else {}
                    
                    # Get recent price volatility
                    recent_prices = market_data.get("recent_prices", [])
                    if len(recent_prices) >= 5:
                        price_changes = []
                        for i in range(1, len(recent_prices)):
                            change = abs(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
                            price_changes.append(change)
                        
                        avg_volatility = sum(price_changes) / len(price_changes) if price_changes else 0
                        volatility_level = "high" if avg_volatility > 0.05 else "medium" if avg_volatility > 0.02 else "low"
                    else:
                        volatility_level = "unknown"
                    
                    assets_analysis[asset] = {
                        "volatility": volatility_level,
                        "current_price": market_data.get("price", 0),
                        "volume": market_data.get("volume", 0)
                    }
                    
                except Exception as e:
                    logger.warning(f"Error analyzing market conditions for {asset}: {e}")
                    assets_analysis[asset] = {"volatility": "unknown"}
            
            # Determine overall market conditions
            volatility_levels = [data.get("volatility", "unknown") for data in assets_analysis.values()]
            high_vol_count = volatility_levels.count("high")
            
            if high_vol_count >= 2:
                market_conditions["volatility"] = "high"
                market_conditions["overall_assessment"] = "volatile"
            elif high_vol_count == 1:
                market_conditions["volatility"] = "medium"
                market_conditions["overall_assessment"] = "mixed"
            else:
                market_conditions["volatility"] = "low"
                market_conditions["overall_assessment"] = "stable"
            
            market_conditions["assets_analysis"] = assets_analysis
            return market_conditions
            
        except Exception as e:
            logger.error(f"Error assessing market conditions: {e}")
            return {"overall_assessment": "unknown", "error": str(e)}

    def _evaluate_rebalancing_timing(self, rebalance_analysis: Dict, market_conditions: Dict) -> Dict[str, Any]:
        """
        Intelligently evaluate if now is a good time to rebalance based on:
        - Urgency of rebalancing need
        - Market conditions
        - Trading opportunities
        - Risk factors
        """
        try:
            severity = rebalance_analysis.get("severity", "moderate")
            max_deviation = rebalance_analysis.get("max_deviation", 0)
            urgent_assets = rebalance_analysis.get("urgent_assets", [])
            market_assessment = market_conditions.get("overall_assessment", "unknown")
            
            # Critical situations - always rebalance immediately
            if severity == "critical" or max_deviation > 20:
                return {
                    "should_rebalance": True,
                    "reason": f"Critical rebalancing needed (max deviation: {max_deviation:.1f}%)",
                    "priority": "critical"
                }
            
            # USD shortage is critical for trading - prioritize getting USD
            usd_deviation = rebalance_analysis.get("deviations", {}).get("USD", {}).get("deviation", 0)
            if usd_deviation > 15:  # Less than 5% USD when target is 20%
                return {
                    "should_rebalance": True,
                    "reason": f"Critical USD shortage for trading (deviation: {usd_deviation:.1f}%)",
                    "priority": "high"
                }
            
            # High severity with stable markets - good time to rebalance
            if severity == "high" and market_assessment in ["stable", "mixed"]:
                return {
                    "should_rebalance": True,
                    "reason": f"High deviation ({max_deviation:.1f}%) with favorable market conditions",
                    "priority": "high"
                }
            
            # Moderate severity - consider market conditions
            if severity == "moderate":
                if market_assessment == "volatile":
                    return {
                        "should_rebalance": False,
                        "reason": f"Moderate deviation ({max_deviation:.1f}%) but high market volatility - waiting for stability",
                        "next_check": "next cycle"
                    }
                else:
                    return {
                        "should_rebalance": True,
                        "reason": f"Moderate deviation ({max_deviation:.1f}%) with acceptable market conditions",
                        "priority": "medium"
                    }
            
            # Default to not rebalancing if conditions are unclear
            return {
                "should_rebalance": False,
                "reason": f"Conditions not optimal for rebalancing (severity: {severity}, market: {market_assessment})",
                "next_check": "next cycle"
            }
            
        except Exception as e:
            logger.error(f"Error evaluating rebalancing timing: {e}")
            # Default to rebalancing if there's an error in evaluation
            return {
                "should_rebalance": True,
                "reason": f"Evaluation error - proceeding with rebalancing: {str(e)}",
                "priority": "medium"
            }

    def _execute_intelligent_rebalancing(self, target_allocation: Dict, rebalance_analysis: Dict, market_conditions: Dict) -> Dict[str, Any]:
        """Execute rebalancing with intelligent trade ordering and timing"""
        try:
            logger.info("Executing intelligent portfolio rebalancing...")
            
            # Calculate required rebalancing actions
            from utils.portfolio import Portfolio
            portfolio_util = Portfolio()
            portfolio_util.data = self.portfolio
            
            try:
                rebalance_actions = portfolio_util.calculate_rebalance_actions(target_allocation)
            except Exception as e:
                logger.error(f"Error calculating rebalance actions: {e}")
                return {"status": "error", "message": f"Failed to calculate rebalance actions: {str(e)}"}
            
            if not rebalance_actions:
                logger.info("No rebalancing actions required after recalculation")
                return {
                    "status": "success",
                    "message": "No rebalancing actions required",
                    "actions_taken": []
                }
            
            # Intelligently order trades based on market conditions and urgency
            ordered_actions = self._optimize_trade_order(rebalance_actions, market_conditions, rebalance_analysis)
            
            # Execute trades with intelligent timing
            executed_actions = []
            failed_actions = []
            
            logger.info(f"Executing {len(ordered_actions)} intelligently ordered rebalancing actions...")
            
            for i, action in enumerate(ordered_actions):
                try:
                    # Add intelligent delay based on market conditions
                    if i > 0:  # Don't delay the first trade
                        delay = self._calculate_trade_delay(market_conditions, action)
                        if delay > 0:
                            logger.info(f"Intelligent delay: {delay}s before {action['action']} {action['asset']}")
                            import time
                            time.sleep(delay)
                    
                    result = self._execute_rebalance_action(action)
                    if result.get("success"):
                        executed_actions.append({**action, "execution_result": result})
                        logger.info(f"Successfully executed: {action['action'].upper()} {action['amount']:.6f} {action['asset']}")
                    else:
                        failed_actions.append({**action, "error": result.get("error", "Unknown error")})
                        logger.warning(f"Failed to execute: {action['action'].upper()} {action['amount']:.6f} {action['asset']} - {result.get('error')}")
                        
                except Exception as e:
                    failed_actions.append({**action, "error": str(e)})
                    logger.error(f"Exception executing rebalance action: {e}")
            
            # Update portfolio after rebalancing
            if executed_actions:
                logger.info("Refreshing portfolio after intelligent rebalancing...")
                self.refresh_portfolio_from_coinbase()
                updated_allocation = self._get_current_allocation()
            else:
                updated_allocation = self._get_current_allocation()
            
            # Prepare comprehensive result
            result = {
                "status": "success" if executed_actions else "partial_failure",
                "message": f"Intelligent rebalancing completed: {len(executed_actions)} successful, {len(failed_actions)} failed",
                "rebalancing_type": "intelligent_autonomous",
                "actions_executed": len(executed_actions),
                "actions_failed": len(failed_actions),
                "executed_actions": executed_actions,
                "failed_actions": failed_actions,
                "market_conditions": market_conditions,
                "rebalance_analysis": rebalance_analysis,
                "updated_allocation": updated_allocation,
                "target_allocation": target_allocation
            }
            
            logger.info(f"Intelligent portfolio rebalancing completed: {len(executed_actions)} actions executed, {len(failed_actions)} failed")
            return result
            
        except Exception as e:
            error_msg = f"Error during intelligent rebalancing execution: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def _optimize_trade_order(self, actions: List[Dict], market_conditions: Dict, rebalance_analysis: Dict) -> List[Dict]:
        """Intelligently order trades for optimal execution"""
        try:
            # Separate SELL and BUY actions
            sell_actions = [a for a in actions if a["action"].upper() == "SELL"]
            buy_actions = [a for a in actions if a["action"].upper() == "BUY"]
            
            # Sort SELL actions by urgency (highest deviation first)
            deviations = rebalance_analysis.get("deviations", {})
            sell_actions.sort(key=lambda x: deviations.get(x["asset"], {}).get("deviation", 0), reverse=True)
            
            # Sort BUY actions by market conditions (most stable assets first)
            assets_analysis = market_conditions.get("assets_analysis", {})
            buy_actions.sort(key=lambda x: 0 if assets_analysis.get(x["asset"], {}).get("volatility") == "low" else 1)
            
            # Execute SELLs first to generate USD, then BUYs
            ordered_actions = sell_actions + buy_actions
            
            logger.info(f"Optimized trade order: {len(sell_actions)} SELLs first, then {len(buy_actions)} BUYs")
            return ordered_actions
            
        except Exception as e:
            logger.warning(f"Error optimizing trade order, using original order: {e}")
            return actions

    def _calculate_trade_delay(self, market_conditions: Dict, action: Dict) -> int:
        """Calculate intelligent delay between trades based on market conditions"""
        try:
            base_delay = 2  # Base 2 second delay
            
            # Increase delay in volatile markets
            if market_conditions.get("volatility") == "high":
                return base_delay * 2  # 4 seconds in high volatility
            elif market_conditions.get("volatility") == "medium":
                return base_delay + 1  # 3 seconds in medium volatility
            else:
                return base_delay  # 2 seconds in stable markets
                
        except Exception as e:
            logger.warning(f"Error calculating trade delay: {e}")
            return 2  # Default delay
    
    def execute_strategy(self, product_id: str) -> Dict[str, Any]:
        """
        Execute trading strategy for a specific product
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            
        Returns:
            Dict with trading decision and details
        """
        try:
            logger.info(f"Executing strategy for {product_id}")
            
            # Check if we have the required components
            if not self.llm_analyzer:
                logger.warning("LLM analyzer not available, returning HOLD decision")
                return {
                    "action": "HOLD",
                    "decision": "HOLD", 
                    "confidence": 50,
                    "reasoning": "LLM analyzer not available - holding position",
                    "product_id": product_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            if not self.data_collector:
                logger.warning("Data collector not available, returning HOLD decision")
                return {
                    "action": "HOLD",
                    "decision": "HOLD", 
                    "confidence": 50,
                    "reasoning": "Data collector not available - holding position",
                    "product_id": product_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # 1. Get market data and indicators
            logger.info(f"Collecting market data for {product_id}")
            
            # Get current market data
            current_market_data = self.data_collector.get_market_data(product_id)
            current_price = current_market_data.get("price", 0)
            
            if current_price == 0:
                logger.warning(f"No current price available for {product_id}")
                return {
                    "action": "HOLD",
                    "decision": "HOLD", 
                    "confidence": 50,
                    "reasoning": "No current price available - holding position",
                    "product_id": product_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Get historical data for analysis
            historical_data = self.data_collector.get_historical_data(product_id, "ONE_HOUR", days_back=7)
            
            if historical_data.empty:
                logger.warning(f"No historical data available for {product_id}")
                return {
                    "action": "HOLD",
                    "decision": "HOLD", 
                    "confidence": 50,
                    "reasoning": "No historical data available - holding position",
                    "product_id": product_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # 2. Use LLM analyzer to make decisions
            logger.info(f"Analyzing market data with LLM for {product_id}")
            start_time = datetime.utcnow()
            analysis_result = self.llm_analyzer.analyze_market_data(
                market_data=historical_data,
                current_price=current_price,
                trading_pair=product_id
            )
            analysis_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if not analysis_result:
                logger.warning(f"LLM analysis failed for {product_id}")
                return {
                    "action": "HOLD",
                    "decision": "HOLD", 
                    "confidence": 50,
                    "reasoning": "LLM analysis failed - holding position",
                    "product_id": product_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # 3. Process the LLM decision
            decision = analysis_result.get("decision", "HOLD")
            confidence = analysis_result.get("confidence", 50)
            reasoning = analysis_result.get("reasoning", "AI analysis completed")
            
            # 4. Apply risk management and position sizing
            risk_adjusted_result = self._apply_risk_management(decision, confidence, product_id, analysis_result)
            
            # 5. Build enhanced result structure
            enhanced_result = self._build_enhanced_result(
                risk_adjusted_result, 
                analysis_result, 
                product_id, 
                len(historical_data),
                analysis_duration
            )
            
            return enhanced_result
            
        except Exception as e:
            error_msg = f"Error executing strategy for {product_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "action": "ERROR",
                "decision": "ERROR",
                "confidence": 0,
                "reasoning": error_msg,
                "product_id": product_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _apply_risk_management(self, decision: str, confidence: int, product_id: str, analysis_result: Dict = None) -> Dict[str, Any]:
        """
        Apply risk management rules to trading decisions
        
        Args:
            decision: Original AI decision (BUY/SELL/HOLD)
            confidence: AI confidence level (0-100)
            product_id: Trading pair
            analysis_result: Full analysis result with technical indicators
            
        Returns:
            Dict with risk-adjusted decision
        """
        try:
            # Get confidence thresholds from config
            buy_threshold = getattr(self.config, 'CONFIDENCE_THRESHOLD_BUY', 60)
            sell_threshold = getattr(self.config, 'CONFIDENCE_THRESHOLD_SELL', 60)
            
            original_decision = decision
            original_confidence = confidence
            risk_adjustment = "none"
            confidence_adjustments = []
            
            # Apply enhanced confidence adjustments based on technical indicators
            if analysis_result:
                confidence = self._apply_confidence_adjustments(confidence, decision, analysis_result, confidence_adjustments)
            
            # Apply confidence thresholds
            if decision == "BUY" and confidence < buy_threshold:
                decision = "HOLD"
                risk_adjustment = f"confidence_too_low_for_buy ({confidence}% < {buy_threshold}%)"
                logger.info(f"Risk management: Changed BUY to HOLD for {product_id} - confidence too low")
                
            elif decision == "SELL" and confidence < sell_threshold:
                decision = "HOLD"
                risk_adjustment = f"confidence_too_low_for_sell ({confidence}% < {sell_threshold}%)"
                logger.info(f"Risk management: Changed SELL to HOLD for {product_id} - confidence too low")
            
            # Check available balances BEFORE finalizing BUY/SELL decisions
            if decision == "BUY":
                try:
                    # Check USD balance for BUY orders
                    accounts = self.coinbase_client.get_accounts()
                    usd_account = next((acc for acc in accounts if acc.get('currency') == 'USD'), None)
                    usd_available = float(usd_account.get('available_balance', {}).get('value', 0)) if usd_account else 0.0
                    
                    if usd_available <= 10.0:  # Minimum $10 for any trade
                        decision = "HOLD"
                        risk_adjustment = f"insufficient_usd_balance (${usd_available:.2f} available, minimum $10 required)"
                        logger.info(f"Risk management: Changed BUY to HOLD for {product_id} - insufficient USD balance")
                except Exception as e:
                    logger.warning(f"Could not check USD balance for {product_id}: {e}")
                    decision = "HOLD"
                    risk_adjustment = "balance_check_failed"
                    
            elif decision == "SELL":
                try:
                    # Check crypto balance for SELL orders
                    asset = product_id.split('-')[0]  # Extract BTC from BTC-USD
                    accounts = self.coinbase_client.get_accounts()
                    asset_account = next((acc for acc in accounts if acc.get('currency') == asset), None)
                    asset_available = float(asset_account.get('available_balance', {}).get('value', 0)) if asset_account else 0.0
                    
                    # Get current price to calculate minimum crypto amount for $10 trade
                    current_market_data = self.data_collector.get_market_data(product_id) if self.data_collector else {}
                    current_price = current_market_data.get("price", 1)
                    min_crypto_amount = 10.0 / current_price if current_price > 0 else 0.01
                    
                    if asset_available <= min_crypto_amount:
                        decision = "HOLD"
                        risk_adjustment = f"insufficient_{asset.lower()}_balance ({asset_available:.8f} available, minimum {min_crypto_amount:.8f} required for $10 trade)"
                        logger.info(f"Risk management: Changed SELL to HOLD for {product_id} - insufficient {asset} balance")
                except Exception as e:
                    logger.warning(f"Could not check {asset} balance for {product_id}: {e}")
                    decision = "HOLD"
                    risk_adjustment = "balance_check_failed"
            
            # Apply position sizing based on risk level (only if still BUY/SELL after balance checks)
            if decision in ["BUY", "SELL"]:
                risk_multiplier = self._get_risk_multiplier()
                if risk_multiplier < 1.0:
                    risk_adjustment += f", position_size_reduced_by_{int((1-risk_multiplier)*100)}%"
                    logger.info(f"Risk management: Position size reduced by {int((1-risk_multiplier)*100)}% for {product_id}")
            
            # Build appropriate reasoning based on final decision
            if decision == "HOLD" and original_decision != "HOLD":
                reasoning = f"AI recommended {original_decision} but changed to HOLD ({risk_adjustment})"
            else:
                confidence_change = f" (confidence: {original_confidence}% → {confidence}%)" if confidence != original_confidence else ""
                reasoning = f"Risk-adjusted decision: {original_decision} → {decision}{confidence_change}" + (f" ({risk_adjustment})" if risk_adjustment != "none" else "")
            
            return {
                "action": decision,
                "decision": decision,
                "confidence": confidence,
                "original_confidence": original_confidence,
                "confidence_adjustments": confidence_adjustments,
                "reasoning": reasoning,
                "risk_adjustment": risk_adjustment,
                "original_decision": original_decision
            }
            
        except Exception as e:
            logger.error(f"Error in risk management for {product_id}: {str(e)}")
            return {
                "action": "HOLD",
                "decision": "HOLD",
                "confidence": 50,
                "reasoning": f"Risk management error - defaulting to HOLD: {str(e)}",
                "risk_adjustment": "error_fallback"
            }

    def _apply_confidence_adjustments(self, confidence: int, decision: str, analysis_result: Dict, adjustments_log: list) -> int:
        """
        Apply enhanced confidence adjustments based on technical indicators and trend alignment
        
        Args:
            confidence: Original AI confidence
            decision: AI decision (BUY/SELL/HOLD)
            analysis_result: Full analysis with technical indicators
            adjustments_log: List to track adjustments made
            
        Returns:
            Adjusted confidence level
        """
        try:
            adjusted_confidence = confidence
            
            # Get configuration values
            trend_boost = getattr(self.config, 'CONFIDENCE_BOOST_TREND_ALIGNED', 10)
            counter_trend_penalty = getattr(self.config, 'CONFIDENCE_PENALTY_COUNTER_TREND', 5)
            
            # Extract technical indicators from analysis - check both locations
            technical_indicators = analysis_result.get('technical_indicators', {})
            if not technical_indicators and 'ai_analysis' in analysis_result:
                technical_indicators = analysis_result.get('ai_analysis', {}).get('technical_indicators', {})
            
            if technical_indicators:
                # Check for trend alignment (multiple indicators agreeing)
                indicators_agreeing = 0
                total_indicators = 0
                
                # RSI alignment check
                rsi_data = technical_indicators.get('rsi', {})
                if rsi_data and 'value' in rsi_data:
                    total_indicators += 1
                    rsi = rsi_data['value']
                    rsi_neutral_min = getattr(self.config, 'RSI_NEUTRAL_MIN', 45)
                    rsi_neutral_max = getattr(self.config, 'RSI_NEUTRAL_MAX', 55)
                    
                    if decision == "BUY" and rsi < rsi_neutral_min:  # Oversold supports BUY
                        indicators_agreeing += 1
                    elif decision == "SELL" and rsi > rsi_neutral_max:  # Overbought supports SELL
                        indicators_agreeing += 1
                    elif decision == "HOLD" and rsi_neutral_min <= rsi <= rsi_neutral_max:  # Neutral supports HOLD
                        indicators_agreeing += 1
                
                # MACD alignment check
                macd_data = technical_indicators.get('macd', {})
                if macd_data and 'signal' in macd_data:
                    total_indicators += 1
                    macd_signal = macd_data['signal']
                    if (decision == "BUY" and macd_signal == "bullish") or \
                       (decision == "SELL" and macd_signal == "bearish") or \
                       (decision == "HOLD" and macd_signal == "neutral"):
                        indicators_agreeing += 1
                
                # Bollinger Bands alignment check
                bb_data = technical_indicators.get('bollinger_bands', {})
                if bb_data and 'signal' in bb_data:
                    total_indicators += 1
                    bb_signal = bb_data['signal']
                    if (decision == "BUY" and bb_signal in ["oversold", "breakout_up"]) or \
                       (decision == "SELL" and bb_signal in ["overbought", "breakout_down"]) or \
                       (decision == "HOLD" and bb_signal in ["neutral", "squeeze"]):
                        indicators_agreeing += 1
                
                # Apply trend alignment adjustments
                if total_indicators > 0:
                    agreement_ratio = indicators_agreeing / total_indicators
                    
                    if agreement_ratio >= 0.67:  # 2/3 or more indicators agree
                        adjusted_confidence += trend_boost
                        adjustments_log.append(f"trend_aligned_bonus: +{trend_boost}%")
                        logger.info(f"Confidence boost applied: {agreement_ratio:.1%} indicator agreement ({indicators_agreeing}/{total_indicators})")
                    elif agreement_ratio <= 0.33:  # 1/3 or fewer indicators agree (counter-trend)
                        adjusted_confidence -= counter_trend_penalty
                        adjustments_log.append(f"counter_trend_penalty: -{counter_trend_penalty}%")
                        logger.info(f"Confidence penalty applied: {agreement_ratio:.1%} indicator agreement ({indicators_agreeing}/{total_indicators})")
                    else:
                        adjustments_log.append(f"neutral_indicators: {agreement_ratio:.1%} agreement, no adjustment")
                        logger.info(f"No confidence adjustment: {agreement_ratio:.1%} indicator agreement ({indicators_agreeing}/{total_indicators})")
            else:
                adjustments_log.append("no_technical_indicators_available")
                logger.warning("No technical indicators available for confidence adjustment")
            
            # Ensure confidence stays within bounds
            adjusted_confidence = max(0, min(100, adjusted_confidence))
            
            return adjusted_confidence
            
        except Exception as e:
            logger.warning(f"Error applying confidence adjustments: {e}")
            adjustments_log.append(f"error: {str(e)}")
            return confidence
    
    def _get_risk_multiplier(self) -> float:
        """Get position size multiplier based on risk level"""
        risk_multipliers = {
            "LOW": getattr(self.config, 'RISK_LOW_POSITION_MULTIPLIER', 1.0),
            "MEDIUM": getattr(self.config, 'RISK_MEDIUM_POSITION_MULTIPLIER', 0.75),
            "HIGH": getattr(self.config, 'RISK_HIGH_POSITION_MULTIPLIER', 0.5)
        }
        # Handle case-insensitive risk level
        risk_level_upper = self.risk_level.upper() if self.risk_level else "MEDIUM"
        return risk_multipliers.get(risk_level_upper, 0.75)
    
    def _build_enhanced_result(self, risk_adjusted_result: Dict, analysis_result: Dict, 
                             product_id: str, data_points: int, analysis_duration: float) -> Dict[str, Any]:
        """
        Build enhanced result structure with detailed AI analysis and bot decision logic
        
        Args:
            risk_adjusted_result: Result from risk management
            analysis_result: Raw result from LLM analysis
            product_id: Trading pair
            data_points: Number of data points analyzed
            analysis_duration: Time taken for analysis in milliseconds
            
        Returns:
            Enhanced result dictionary with detailed information
        """
        try:
            # Get configuration values
            buy_threshold = getattr(self.config, 'CONFIDENCE_THRESHOLD_BUY', 60)
            sell_threshold = getattr(self.config, 'CONFIDENCE_THRESHOLD_SELL', 60)
            max_position_size = getattr(self.config, 'MAX_POSITION_SIZE_USD', 1000.0)
            
            # Extract AI analysis details
            ai_decision = analysis_result.get("decision", "HOLD")
            ai_confidence = analysis_result.get("confidence", 50)
            ai_reasoning = analysis_result.get("reasoning", [])
            risk_assessment = analysis_result.get("risk_assessment", "medium")
            
            # Convert reasoning to list if it's a string
            if isinstance(ai_reasoning, str):
                ai_reasoning = [ai_reasoning]
            
            # Build technical indicators section (if available)
            technical_indicators = analysis_result.get("technical_indicators", {})
            
            # Build AI analysis section
            ai_analysis = {
                "raw_decision": ai_decision,
                "raw_confidence": ai_confidence,
                "detailed_reasoning": ai_reasoning,
                "technical_indicators": technical_indicators,
                "risk_assessment": risk_assessment,
                "market_conditions": analysis_result.get("market_conditions", {})
            }
            
            # Build bot decision logic section
            final_decision = risk_adjusted_result.get("action", "HOLD")
            threshold = buy_threshold if ai_decision == "BUY" else sell_threshold if ai_decision == "SELL" else 50
            
            # Determine if confidence threshold was passed
            confidence_passed = True
            if ai_decision in ["BUY", "SELL"]:
                confidence_passed = ai_confidence >= threshold
            
            # Get risk multiplier and calculate position sizing info
            risk_multiplier = self._get_risk_multiplier()
            position_reduction = int((1 - risk_multiplier) * 100) if risk_multiplier < 1.0 else 0
            
            # Build final decision reasoning
            decision_reasons = []
            if ai_decision != "HOLD":
                if confidence_passed:
                    decision_reasons.append(f"AI recommendation {ai_decision} with {ai_confidence}% confidence exceeds threshold of {threshold}%")
                else:
                    decision_reasons.append(f"AI recommendation {ai_decision} with {ai_confidence}% confidence below threshold of {threshold}%, changed to HOLD")
            
            if position_reduction > 0:
                decision_reasons.append(f"Risk management applied position sizing reduction of {position_reduction}% due to {self.risk_level.lower()} risk conditions")
            
            if not decision_reasons:
                decision_reasons.append("Standard HOLD decision applied")
            
            bot_decision_logic = {
                "ai_recommendation": ai_decision,
                "confidence_threshold_check": {
                    "required_threshold": threshold,
                    "ai_confidence": ai_confidence,
                    "passed": confidence_passed
                },
                "risk_management_applied": {
                    "position_sizing": {
                        "risk_level": self.risk_level.lower(),
                        "multiplier": risk_multiplier,
                        "reason": f"{self.risk_level.title()} risk conditions detected" + (f", reducing position size by {position_reduction}%" if position_reduction > 0 else "")
                    },
                    "portfolio_constraints": {
                        "max_position_size": max_position_size,
                        "within_limits": True  # Could be enhanced with actual portfolio checks
                    }
                },
                "final_decision_reason": " ".join(decision_reasons),
                "overrides_applied": []
            }
            
            # Build execution context
            execution_context = {
                "market_data_quality": "good" if data_points > 50 else "limited",
                "data_points_analyzed": data_points,
                "analysis_duration_ms": round(analysis_duration, 2),
                "llm_model_used": getattr(self.config, 'LLM_MODEL', 'unknown'),
                "strategy_version": "enhanced_v2.1"
            }
            
            # Build the complete enhanced result
            enhanced_result = {
                # Original structure (for backward compatibility)
                "action": risk_adjusted_result.get("action", "HOLD"),
                "decision": risk_adjusted_result.get("decision", "HOLD"),
                "confidence": risk_adjusted_result.get("confidence", 50),
                "reasoning": risk_adjusted_result.get("reasoning", "Enhanced analysis completed"),
                "product_id": product_id,
                "timestamp": datetime.utcnow().isoformat(),
                "original_confidence": ai_confidence,
                "risk_adjustment": risk_adjusted_result.get("risk_adjustment", "none"),
                
                # Enhanced sections
                "ai_analysis": ai_analysis,
                "bot_decision_logic": bot_decision_logic,
                "execution_context": execution_context
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error building enhanced result for {product_id}: {str(e)}")
            # Fallback to basic structure
            return {
                "action": risk_adjusted_result.get("action", "HOLD"),
                "decision": risk_adjusted_result.get("decision", "HOLD"),
                "confidence": risk_adjusted_result.get("confidence", 50),
                "reasoning": f"Enhanced analysis error: {str(e)}",
                "product_id": product_id,
                "timestamp": datetime.utcnow().isoformat(),
                "original_confidence": analysis_result.get("confidence", 50),
                "risk_adjustment": risk_adjusted_result.get("risk_adjustment", "error")
            }
