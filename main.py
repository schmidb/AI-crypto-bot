import logging
import time
import json
import schedule
import signal
import sys
from datetime import datetime, timedelta
import os
from typing import Dict, List, Any

from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer
from data_collector import DataCollector
from trading_strategy import TradingStrategy
from utils.dashboard_updater import DashboardUpdater
from utils.webserver_sync import WebServerSync
from utils.tax_report import TaxReportGenerator
from utils.strategy_evaluator import StrategyEvaluator
from utils.logger import get_supervisor_logger, log_bot_shutdown
from config import TRADING_PAIRS, DECISION_INTERVAL_MINUTES, WEBSERVER_SYNC_ENABLED, SIMULATION_MODE, RISK_LEVEL, Config

# Configure logging with daily rotation
logger = get_supervisor_logger()

class TradingBot:
    """Main trading bot class that orchestrates the trading process"""
    
    def __init__(self):
        """Initialize the trading bot"""
        logger.info("Initializing trading bot")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Log trading mode clearly
        if SIMULATION_MODE:
            logger.info("🔄 SIMULATION MODE - No real trades will be executed")
        else:
            logger.info("💰 LIVE TRADING MODE - Real trades will be executed")
            logger.info("📊 Portfolio will be synced with Coinbase before each trading cycle")
        
        # Create necessary directories
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        
        # Initialize components
        config = Config()
        self.coinbase_client = CoinbaseClient()
        self.llm_analyzer = LLMAnalyzer()
        self.data_collector = DataCollector(self.coinbase_client)
        self.trading_strategy = TradingStrategy(config, self.llm_analyzer, self.data_collector)
        
        # Initialize dashboard updater (local data only)
        self.dashboard_updater = DashboardUpdater()
        
        # Initialize web server sync (if enabled)
        self.webserver_sync = WebServerSync()
        
        # Initialize tax report generator
        self.tax_report_generator = TaxReportGenerator()
        
        # Initialize strategy evaluator
        self.strategy_evaluator = StrategyEvaluator()
        
        # Initialize dashboard with existing data
        self.initialize_dashboard()
        
        # Perform initial web server sync
        self.sync_to_webserver()
        
        # Record bot startup time
        self.record_startup_time()
        
        logger.info(f"Trading bot initialized with trading pairs: {TRADING_PAIRS}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.record_shutdown_time()
        sys.exit(0)
        
    def sync_to_webserver(self):
        """Centralized web server sync - only place where web server sync happens"""
        try:
            if WEBSERVER_SYNC_ENABLED:
                logger.info("Syncing dashboard to web server")
                self.webserver_sync.sync_to_webserver()
            else:
                logger.debug("Web server sync disabled")
        except Exception as e:
            logger.error(f"Error syncing to web server: {e}")
        
    def update_next_decision_time(self):
        """Update the next decision time in bot_startup.json"""
        try:
            # Read current startup data
            with open("data/cache/bot_startup.json", "r") as f:
                startup_data = json.load(f)
            
            # Update next decision time
            next_decision_time = datetime.utcnow() + timedelta(minutes=DECISION_INTERVAL_MINUTES)
            startup_data["next_decision_time"] = next_decision_time.isoformat()
            startup_data["last_decision_time"] = datetime.utcnow().isoformat()
            
            # Write back to file
            with open("data/cache/bot_startup.json", "w") as f:
                json.dump(startup_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating next decision time: {e}")
    
    def record_startup_time(self):
        """Record the bot startup time for uptime tracking"""
        try:
            startup_time = datetime.utcnow()
            next_decision_time = startup_time + timedelta(minutes=DECISION_INTERVAL_MINUTES)
            
            startup_data = {
                "startup_time": startup_time.isoformat(),
                "next_decision_time": next_decision_time.isoformat(),
                "pid": os.getpid(),
                "trading_pairs": TRADING_PAIRS,
                "decision_interval_minutes": DECISION_INTERVAL_MINUTES,
                "simulation_mode": SIMULATION_MODE,
                "risk_level": RISK_LEVEL,
                "status": "online"
            }
            
            os.makedirs("data/cache", exist_ok=True)
            with open("data/cache/bot_startup.json", "w") as f:
                json.dump(startup_data, f, indent=2)
            
            mode_text = "SIMULATION" if SIMULATION_MODE else "LIVE TRADING"
            logger.info(f"Bot startup time recorded: {startup_data['startup_time']} - Mode: {mode_text}")
            
        except Exception as e:
            logger.error(f"Error recording startup time: {e}")
    
    def record_shutdown_time(self):
        """Record the bot shutdown time and set status to offline"""
        try:
            shutdown_time = datetime.utcnow()
            
            # Try to read existing startup data first
            startup_data = {}
            try:
                with open("data/cache/bot_startup.json", "r") as f:
                    startup_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                # If file doesn't exist or is corrupted, create minimal data
                startup_data = {
                    "startup_time": shutdown_time.isoformat(),
                    "trading_pairs": TRADING_PAIRS,
                    "decision_interval_minutes": DECISION_INTERVAL_MINUTES,
                    "simulation_mode": SIMULATION_MODE,
                    "risk_level": RISK_LEVEL
                }
            
            # Update with shutdown information
            startup_data.update({
                "status": "offline",
                "shutdown_time": shutdown_time.isoformat(),
                "last_seen": shutdown_time.isoformat()
            })
            
            # Remove PID since process is stopping
            if "pid" in startup_data:
                del startup_data["pid"]
            
            os.makedirs("data/cache", exist_ok=True)
            with open("data/cache/bot_startup.json", "w") as f:
                json.dump(startup_data, f, indent=2)
            
            logger.info(f"Bot shutdown time recorded: {shutdown_time.isoformat()}")
            
            # Also sync to web server if enabled
            if WEBSERVER_SYNC_ENABLED:
                try:
                    from utils.webserver_sync import WebServerSync
                    web_sync = WebServerSync()
                    web_sync.sync_to_webserver()
                    logger.info("Dashboard synced to web server with offline status")
                except Exception as e:
                    logger.error(f"Error syncing offline status to web server: {e}")
            
        except Exception as e:
            logger.error(f"Error recording shutdown time: {e}")
        
        
    def initialize_dashboard(self):
        """Initialize dashboard with existing data on bot startup"""
        try:
            logger.info("Initializing dashboard with existing data")
            
            # First, ensure we have current market prices for all trading pairs
            market_data = {}
            for product_id in TRADING_PAIRS:
                try:
                    # Fetch current market data with retry logic
                    for attempt in range(3):  # Try up to 3 times
                        try:
                            market_data[product_id] = self.data_collector.get_market_data(product_id)
                            logger.info(f"Successfully fetched market data for {product_id} during initialization")
                            break
                        except Exception as e:
                            if attempt < 2:  # Don't log on final attempt as we'll log below
                                logger.warning(f"Attempt {attempt+1} failed to get market data for {product_id}: {e}")
                                time.sleep(1)  # Wait before retry
                except Exception as e:
                    logger.error(f"Error getting market data for {product_id} during initialization: {e}")
            
            # Load existing trade history
            trades = self.trading_strategy.trade_logger.get_recent_trades(10)
            
            # If we have market data but no trades or trades with missing prices, create placeholder trades
            if market_data and (not trades or any(trade.get('price', 0) == 0 for trade in trades)):
                logger.info("Creating placeholder trades with current market data")
                for product_id, data in market_data.items():
                    # Check if we already have a recent trade for this product
                    existing_trade = next((t for t in trades if t.get('product_id') == product_id), None)
                    
                    if not existing_trade or existing_trade.get('price', 0) == 0:
                        # Create a placeholder "hold" trade with current price
                        placeholder_trade = {
                            "timestamp": datetime.utcnow().isoformat(),  # Use UTC time for consistency
                            "product_id": product_id,
                            "action": "hold",
                            "price": data.get("price", 0),
                            "crypto_amount": 0,
                            "trade_amount_usd": 0,
                            "confidence": 0,
                            "reason": "Initial state after restart",
                            "status": "success"
                        }
                        
                        # Add to trades list
                        if existing_trade:
                            # Replace existing trade with zero price
                            trades = [placeholder_trade if t.get('product_id') == product_id else t for t in trades]
                        else:
                            # Add new trade
                            trades.append(placeholder_trade)
            
            # Create trading data structure
            trading_data = {
                "recent_trades": trades,
                "market_data": market_data
            }
            
            # Get portfolio data
            portfolio = self.trading_strategy.portfolio
            
            # Update dashboard with loaded data
            self.dashboard_updater.update_dashboard(trading_data, portfolio)
            logger.info("Dashboard initialized with existing data")
        except Exception as e:
            logger.error(f"Error initializing dashboard: {e}")
    
    def _sync_portfolio_with_coinbase(self) -> bool:
        """
        Sync internal portfolio with actual Coinbase balances (live trading only)
        Returns True if sync successful, False otherwise
        """
        try:
            logger.info("Syncing portfolio with Coinbase...")
            
            # Get current internal portfolio state
            current_portfolio = self.trading_strategy.portfolio.copy()
            
            # Refresh portfolio from Coinbase
            sync_result = self.trading_strategy.refresh_portfolio_from_coinbase()
            
            if sync_result.get("status") == "success":
                # Get updated portfolio state
                updated_portfolio = self.trading_strategy.portfolio
                
                # Log any significant discrepancies
                discrepancies_found = False
                total_discrepancy_value = 0.0
                
                for asset in ['USD', 'BTC', 'ETH', 'SOL']:
                    if asset in current_portfolio and asset in updated_portfolio:
                        if isinstance(current_portfolio[asset], dict) and isinstance(updated_portfolio[asset], dict):
                            old_amount = current_portfolio[asset].get('amount', 0)
                            new_amount = updated_portfolio[asset].get('amount', 0)
                            
                            # Check for significant differences (more than 0.00001 for crypto, $0.01 for USD)
                            threshold = 0.01 if asset == 'USD' else 0.00001
                            if abs(old_amount - new_amount) > threshold:
                                discrepancies_found = True
                                difference = new_amount - old_amount
                                
                                # Calculate USD value of discrepancy for crypto assets
                                if asset != 'USD':
                                    last_price = updated_portfolio[asset].get('last_price_usd', 0)
                                    discrepancy_value = difference * last_price
                                    total_discrepancy_value += abs(discrepancy_value)
                                    logger.warning(f"Portfolio discrepancy detected for {asset}: "
                                                 f"Internal={old_amount:.8f}, Coinbase={new_amount:.8f} "
                                                 f"(${discrepancy_value:+.2f})")
                                else:
                                    total_discrepancy_value += abs(difference)
                                    logger.warning(f"Portfolio discrepancy detected for {asset}: "
                                                 f"Internal=${old_amount:.2f}, Coinbase=${new_amount:.2f} "
                                                 f"(${difference:+.2f})")
                
                if discrepancies_found:
                    logger.info(f"Portfolio discrepancies found and corrected (total value: ${total_discrepancy_value:.2f})")
                    
                    # If discrepancies are very large, log a warning
                    if total_discrepancy_value > 50.0:  # More than $50 difference
                        logger.warning(f"Large portfolio discrepancy detected: ${total_discrepancy_value:.2f}")
                        logger.warning("This could indicate manual trades or failed order executions")
                else:
                    logger.info("Portfolio sync completed - no discrepancies found")
                
                return True
            else:
                logger.error(f"Portfolio sync failed: {sync_result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error during portfolio sync: {e}")
            return False
    
    def run_trading_cycle(self):
        """Run a single trading cycle for all configured trading pairs"""
        logger.info(f"Starting trading cycle at {datetime.now()}")
        
        # Sync portfolio with Coinbase before trading (live trading only)
        if not SIMULATION_MODE:
            logger.info("Live trading mode - syncing portfolio with Coinbase")
            sync_result = self._sync_portfolio_with_coinbase()
            if not sync_result:
                logger.error("Portfolio sync failed - skipping this trading cycle for safety")
                return {"error": "Portfolio sync failed", "skipped": True}
        else:
            logger.info("Simulation mode - skipping portfolio sync")
        
        results = {}
        
        for product_id in TRADING_PAIRS:
            logger.info(f"Processing {product_id}")
            
            try:
                # Execute trading strategy (get decision)
                decision_result = self.trading_strategy.execute_strategy(product_id)
                
                # Execute the actual trade based on the decision
                trade_result = self._execute_trade(product_id, decision_result)
                
                # Log all trading decisions (executed, skipped, or held)
                self._log_trade_decision(product_id, decision_result, trade_result)
                
                # Combine decision and execution results
                result = {**decision_result, **trade_result}
                results[product_id] = result
                
                # Save result to file
                self._save_result(product_id, result)
                
                # Log decision and execution
                decision = result.get('action', result.get('decision', 'UNKNOWN'))
                confidence = result.get('confidence', 0)
                execution_status = result.get('execution_status', 'unknown')
                logger.info(f"Decision for {product_id}: {decision} (confidence: {confidence}%) - Execution: {execution_status}")
                
                # Add delay between API calls to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {product_id}: {e}")
                results[product_id] = {
                    "success": False,
                    "error": str(e),
                    "product_id": product_id
                }
        
        # Update the dashboard with the results
        try:
            # Get current market data for all trading pairs to ensure fresh prices
            market_data = {}
            for product_id in TRADING_PAIRS:
                try:
                    market_data[product_id] = self.data_collector.get_market_data(product_id)
                    logger.info(f"Got fresh market data for {product_id}: price=${market_data[product_id].get('price', 0)}")
                except Exception as e:
                    logger.error(f"Error getting market data for {product_id}: {e}")
            
            # Get recent trades with the latest decisions
            recent_trades = self.trading_strategy.trade_logger.get_recent_trades(10)
            
            # Convert results to a proper format for the dashboard
            dashboard_data = {
                "trading_results": results,
                "recent_trades": recent_trades,
                "market_data": market_data,
                "status": "running",
                "timestamp": datetime.utcnow().isoformat()  # Use UTC time for consistency
            }
            
            # Get current portfolio data
            portfolio = self.trading_strategy.portfolio
            
            # Ensure portfolio is a dictionary
            if isinstance(portfolio, str):
                try:
                    portfolio = json.loads(portfolio)
                except json.JSONDecodeError:
                    portfolio = {
                        "portfolio_value_usd": 0,
                        "initial_value_usd": 0,
                        "BTC": {"amount": 0, "last_price_usd": 0},
                        "ETH": {"amount": 0, "last_price_usd": 0},
                        "USD": {"amount": 0},
                        "trades_executed": 0
                    }
            
            # Update local dashboard data
            self.dashboard_updater.update_dashboard(dashboard_data, portfolio)
            logger.info("Local dashboard updated successfully")
            
            # Update next decision time
            self.update_next_decision_time()
            
            # Sync to web server (centralized sync point)
            self.sync_to_webserver()
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
        
        logger.info(f"Trading cycle completed at {datetime.now()}")
        return results
    
    def _save_result(self, product_id: str, result: Dict):
        """Save trading result to a JSON file with market data and price changes"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/{product_id.replace('-', '_')}_{timestamp}.json"
        
        # Add current market data to the result
        try:
            # Get current price
            current_price_data = self.data_collector.client.get_product_price(product_id)
            current_price = float(current_price_data.get("price", 0))
            
            # Calculate price changes by looking at historical files
            price_changes = self._calculate_price_changes(product_id, current_price)
            
            # Add market data to result
            result["market_data"] = {
                "price": current_price,
                "price_changes": price_changes,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Added market data to result: price=${current_price}, changes={price_changes}")
            
        except Exception as e:
            logger.error(f"Error adding market data to result: {e}")
            # Add empty market data as fallback
            result["market_data"] = {
                "price": 0,
                "price_changes": {"1h": 0.0, "4h": 0.0, "24h": 0.0, "5d": 0.0},
                "timestamp": datetime.now().isoformat()
            }
        
        # Save the enhanced result
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Saved result with market data to {filename}")
    
    def _log_trade_decision(self, product_id: str, decision_result: Dict[str, Any], trade_result: Dict[str, Any]) -> None:
        """Log all trading decisions (executed, skipped, or held) to trade history"""
        try:
            action = decision_result.get('action', 'UNKNOWN')
            original_decision = decision_result.get('original_decision', action)
            execution_status = trade_result.get('execution_status', 'unknown')
            risk_adjustment = decision_result.get('risk_adjustment', '')
            
            # Determine what to log based on the decision type
            should_log = False
            log_action = action
            log_reason = ""
            
            if action in ['BUY', 'SELL']:
                # Log actual BUY/SELL attempts (these made it through risk management)
                should_log = True
                log_action = action
                
                # Build comprehensive reasoning for failed attempts
                if not trade_result.get('trade_executed'):
                    if execution_status == 'insufficient_usd':
                        usd_available = trade_result.get('available_usd', 0)
                        log_reason = f"AI recommended {action} but insufficient USD balance (${usd_available:.2f} available, minimum $10 required)"
                    elif execution_status == 'insufficient_crypto':
                        crypto_available = trade_result.get('available_crypto', 0)
                        asset = product_id.split('-')[0]
                        log_reason = f"AI recommended {action} but insufficient {asset} balance ({crypto_available:.8f} available)"
                    else:
                        log_reason = f"AI recommended {action} but execution failed: {trade_result.get('execution_message', '')}"
                else:
                    log_reason = f"AI recommended {action} - trade executed successfully"
                    
            elif action == 'HOLD':
                # Log HOLD decisions to show bot activity, but with clear reasoning
                should_log = True
                log_action = 'HOLD'
                
                if original_decision and original_decision != 'HOLD':
                    # This was changed from BUY/SELL to HOLD
                    if 'insufficient' in risk_adjustment:
                        log_reason = f"AI recommended {original_decision} but insufficient funds - changed to HOLD"
                    elif 'confidence_too_low' in risk_adjustment:
                        confidence = decision_result.get('confidence', 0)
                        threshold = 60  # Default threshold
                        log_reason = f"AI recommended {original_decision} but confidence too low ({confidence}% < {threshold}%) - changed to HOLD"
                    else:
                        log_reason = f"AI recommended {original_decision} but risk management changed to HOLD ({risk_adjustment})"
                else:
                    # Original HOLD decision
                    log_reason = "AI analysis recommends HOLD - no trading action needed"
            
            if should_log:
                # Create enhanced trade record for dashboard visibility
                enhanced_trade_result = {
                    **trade_result,
                    'action': log_action,
                    'status': 'executed' if trade_result.get('trade_executed') else 'hold' if log_action == 'HOLD' else 'attempted',
                    'reason': log_reason,
                    'intended_action': log_action,
                    'ai_recommendation': original_decision or action,
                    'skip_reason': execution_status if not trade_result.get('trade_executed') and log_action != 'HOLD' else None,
                    'execution_message': trade_result.get('execution_message', ''),
                    'ai_reasoning': decision_result.get('reasoning', '')
                }
                
                # Use the trading strategy's trade logger
                self.trading_strategy.trade_logger.log_trade(product_id, decision_result, enhanced_trade_result)
                logger.info(f"Trade decision logged for {product_id}: {log_action} - {execution_status}")
            
        except Exception as e:
            logger.error(f"Error logging trade decision for {product_id}: {e}")

    def _execute_trade(self, product_id: str, decision_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute actual trade based on AI decision
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            decision_result: Result from trading strategy
            
        Returns:
            Dict with execution results
        """
        try:
            action = decision_result.get('action', 'HOLD')
            confidence = decision_result.get('confidence', 0)
            
            # Initialize execution result
            execution_result = {
                'execution_status': 'not_executed',
                'execution_message': 'No execution needed',
                'trade_executed': False,
                'crypto_amount': 0,
                'trade_amount_usd': 0,
                'execution_price': 0
            }
            
            # Skip execution for HOLD decisions
            if action == 'HOLD':
                execution_result.update({
                    'execution_status': 'skipped_hold',
                    'execution_message': 'HOLD decision - no trade executed'
                })
                return execution_result
            
            # Get current portfolio state
            portfolio = self.trading_strategy.portfolio
            asset = product_id.split('-')[0]  # Extract asset (BTC, ETH, SOL)
            
            # Get current market price
            try:
                current_price = self.data_collector.get_current_price(product_id)
                execution_result['execution_price'] = current_price
            except Exception as e:
                logger.error(f"Failed to get current price for {product_id}: {e}")
                execution_result.update({
                    'execution_status': 'failed',
                    'execution_message': f'Failed to get current price: {e}'
                })
                return execution_result
            
            # Calculate trade size based on confidence and available funds
            if action == 'BUY':
                return self._execute_buy_order(product_id, asset, current_price, confidence, portfolio, execution_result)
            elif action == 'SELL':
                return self._execute_sell_order(product_id, asset, current_price, confidence, portfolio, execution_result)
            else:
                execution_result.update({
                    'execution_status': 'unknown_action',
                    'execution_message': f'Unknown action: {action}'
                })
                return execution_result
                
        except Exception as e:
            logger.error(f"Error executing trade for {product_id}: {e}")
            return {
                'execution_status': 'error',
                'execution_message': f'Execution error: {e}',
                'trade_executed': False,
                'crypto_amount': 0,
                'trade_amount_usd': 0,
                'execution_price': 0
            }
    
    def _execute_buy_order(self, product_id: str, asset: str, current_price: float, confidence: int, portfolio: Dict, execution_result: Dict) -> Dict[str, Any]:
        """Execute BUY order with USD balance validation"""
        try:
            # Check USD balance
            usd_available = portfolio.get('USD', {}).get('amount', 0)
            
            if usd_available <= 10.0:  # Minimum $10 for any trade
                execution_result.update({
                    'execution_status': 'insufficient_usd',
                    'execution_message': f'Insufficient USD balance: ${usd_available:.2f} (minimum $10 required)',
                    'available_usd': usd_available
                })
                logger.warning(f"BUY order skipped for {product_id}: Insufficient USD (${usd_available:.2f})")
                return execution_result
            
            # Calculate trade size based on confidence and risk management
            max_trade_usd = min(usd_available * 0.3, 1000.0)  # Max 30% of USD or $1000
            confidence_multiplier = confidence / 100.0
            risk_multiplier = self.trading_strategy._get_risk_multiplier()
            
            trade_amount_usd = max_trade_usd * confidence_multiplier * risk_multiplier
            trade_amount_usd = max(10.0, min(trade_amount_usd, usd_available - 1.0))  # Keep $1 buffer
            
            crypto_amount = trade_amount_usd / current_price
            
            if SIMULATION_MODE:
                # Simulate the trade
                execution_result.update({
                    'execution_status': 'simulated',
                    'execution_message': f'SIMULATED BUY: {crypto_amount:.8f} {asset} for ${trade_amount_usd:.2f}',
                    'trade_executed': True,
                    'crypto_amount': crypto_amount,
                    'trade_amount_usd': trade_amount_usd
                })
                logger.info(f"SIMULATED BUY: {crypto_amount:.8f} {asset} for ${trade_amount_usd:.2f}")
            else:
                # Execute real trade
                try:
                    order_result = self.coinbase_client.place_market_order(
                        product_id=product_id,
                        side='BUY',
                        size=trade_amount_usd
                    )
                    
                    if order_result.get('success'):
                        execution_result.update({
                            'execution_status': 'executed',
                            'execution_message': f'BUY order executed: {crypto_amount:.8f} {asset} for ${trade_amount_usd:.2f}',
                            'trade_executed': True,
                            'crypto_amount': crypto_amount,
                            'trade_amount_usd': trade_amount_usd,
                            'order_id': order_result.get('order_id')
                        })
                        logger.info(f"BUY order executed: {crypto_amount:.8f} {asset} for ${trade_amount_usd:.2f}")
                        
                        # Update portfolio
                        self.trading_strategy.portfolio['USD']['amount'] -= trade_amount_usd
                        if asset not in self.trading_strategy.portfolio:
                            self.trading_strategy.portfolio[asset] = {'amount': 0, 'last_price_usd': current_price}
                        self.trading_strategy.portfolio[asset]['amount'] += crypto_amount
                        self.trading_strategy.portfolio[asset]['last_price_usd'] = current_price
                        
                        # Save updated portfolio
                        self.trading_strategy._save_portfolio()
                        
                    else:
                        execution_result.update({
                            'execution_status': 'failed',
                            'execution_message': f'BUY order failed: {order_result.get("message", "Unknown error")}'
                        })
                        logger.error(f"BUY order failed for {product_id}: {order_result.get('message')}")
                        
                except Exception as e:
                    execution_result.update({
                        'execution_status': 'failed',
                        'execution_message': f'BUY order execution error: {e}'
                    })
                    logger.error(f"BUY order execution error for {product_id}: {e}")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error in BUY order execution for {product_id}: {e}")
            execution_result.update({
                'execution_status': 'error',
                'execution_message': f'BUY execution error: {e}'
            })
            return execution_result
    
    def _execute_sell_order(self, product_id: str, asset: str, current_price: float, confidence: int, portfolio: Dict, execution_result: Dict) -> Dict[str, Any]:
        """Execute SELL order with asset balance validation"""
        try:
            # Check asset balance
            asset_available = portfolio.get(asset, {}).get('amount', 0)
            min_trade_value = 10.0  # Minimum $10 trade value
            min_crypto_amount = min_trade_value / current_price
            
            if asset_available <= min_crypto_amount:
                execution_result.update({
                    'execution_status': 'insufficient_crypto',
                    'execution_message': f'Insufficient {asset} balance: {asset_available:.8f} (minimum {min_crypto_amount:.8f} required for $10 trade)',
                    'available_crypto': asset_available
                })
                logger.warning(f"SELL order skipped for {product_id}: Insufficient {asset} ({asset_available:.8f})")
                return execution_result
            
            # Calculate trade size based on confidence and risk management
            max_crypto_amount = asset_available * 0.3  # Max 30% of holdings
            confidence_multiplier = confidence / 100.0
            risk_multiplier = self.trading_strategy._get_risk_multiplier()
            
            crypto_amount = max_crypto_amount * confidence_multiplier * risk_multiplier
            crypto_amount = max(min_crypto_amount, min(crypto_amount, asset_available * 0.95))  # Keep 5% buffer
            
            trade_amount_usd = crypto_amount * current_price
            
            if SIMULATION_MODE:
                # Simulate the trade
                execution_result.update({
                    'execution_status': 'simulated',
                    'execution_message': f'SIMULATED SELL: {crypto_amount:.8f} {asset} for ${trade_amount_usd:.2f}',
                    'trade_executed': True,
                    'crypto_amount': crypto_amount,
                    'trade_amount_usd': trade_amount_usd
                })
                logger.info(f"SIMULATED SELL: {crypto_amount:.8f} {asset} for ${trade_amount_usd:.2f}")
            else:
                # Execute real trade
                try:
                    order_result = self.coinbase_client.place_market_order(
                        product_id=product_id,
                        side='SELL',
                        size=crypto_amount
                    )
                    
                    if order_result.get('success'):
                        execution_result.update({
                            'execution_status': 'executed',
                            'execution_message': f'SELL order executed: {crypto_amount:.8f} {asset} for ${trade_amount_usd:.2f}',
                            'trade_executed': True,
                            'crypto_amount': crypto_amount,
                            'trade_amount_usd': trade_amount_usd,
                            'order_id': order_result.get('order_id')
                        })
                        logger.info(f"SELL order executed: {crypto_amount:.8f} {asset} for ${trade_amount_usd:.2f}")
                        
                        # Update portfolio
                        self.trading_strategy.portfolio[asset]['amount'] -= crypto_amount
                        if 'USD' not in self.trading_strategy.portfolio:
                            self.trading_strategy.portfolio['USD'] = {'amount': 0}
                        self.trading_strategy.portfolio['USD']['amount'] += trade_amount_usd
                        
                        # Save updated portfolio
                        self.trading_strategy._save_portfolio()
                        
                    else:
                        execution_result.update({
                            'execution_status': 'failed',
                            'execution_message': f'SELL order failed: {order_result.get("message", "Unknown error")}'
                        })
                        logger.error(f"SELL order failed for {product_id}: {order_result.get('message')}")
                        
                except Exception as e:
                    execution_result.update({
                        'execution_status': 'failed',
                        'execution_message': f'SELL order execution error: {e}'
                    })
                    logger.error(f"SELL order execution error for {product_id}: {e}")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error in SELL order execution for {product_id}: {e}")
            execution_result.update({
                'execution_status': 'error',
                'execution_message': f'SELL execution error: {e}'
            })
            return execution_result

    def _calculate_price_changes(self, product_id: str, current_price: float) -> Dict[str, float]:
        """Calculate price changes using Coinbase historical candle data"""
        changes = {"1h": 0.0, "4h": 0.0, "24h": 0.0, "5d": 0.0}
        
        try:
            from datetime import datetime, timedelta
            
            now = datetime.utcnow()
            
            # Time periods to calculate
            periods = {
                "1h": {"delta": timedelta(hours=1), "granularity": "ONE_HOUR"},
                "4h": {"delta": timedelta(hours=4), "granularity": "ONE_HOUR"}, 
                "24h": {"delta": timedelta(hours=24), "granularity": "ONE_HOUR"},
                "5d": {"delta": timedelta(days=5), "granularity": "ONE_DAY"}
            }
            
            for period_name, config in periods.items():
                try:
                    # Calculate start time
                    start_time = now - config["delta"]
                    
                    # Get historical candle data from Coinbase
                    historical_data = self.data_collector.client.get_market_data(
                        product_id=product_id,
                        granularity=config["granularity"],
                        start_time=start_time.isoformat() + 'Z',
                        end_time=now.isoformat() + 'Z'
                    )
                    
                    if historical_data and len(historical_data) > 0:
                        # Get the earliest candle (closest to our target time)
                        # Candles are returned as list of dicts or objects
                        historical_candle = historical_data[-1]  # Last item is earliest
                        
                        # Extract historical price from candle
                        if isinstance(historical_candle, dict):
                            # Try different price fields
                            historical_price = (
                                historical_candle.get('open') or 
                                historical_candle.get('close') or 
                                historical_candle.get('low') or 
                                historical_candle.get('high')
                            )
                        else:
                            # Handle object response
                            historical_price = (
                                getattr(historical_candle, 'open', None) or
                                getattr(historical_candle, 'close', None) or
                                getattr(historical_candle, 'low', None) or
                                getattr(historical_candle, 'high', None)
                            )
                        
                        if historical_price and float(historical_price) > 0:
                            historical_price = float(historical_price)
                            # Calculate percentage change
                            change_percent = ((current_price - historical_price) / historical_price) * 100
                            changes[period_name] = round(change_percent, 2)
                            logger.info(f"Calculated {period_name} change for {product_id}: {current_price} vs {historical_price} = {change_percent:.2f}%")
                        else:
                            logger.warning(f"No valid historical price found for {period_name} change calculation")
                    else:
                        logger.warning(f"No historical data returned for {period_name} change calculation")
                        
                except Exception as e:
                    logger.warning(f"Error calculating {period_name} change for {product_id}: {e}")
                    continue
            
            logger.info(f"Final calculated price changes for {product_id}: {changes}")
            
        except Exception as e:
            logger.error(f"Error calculating price changes for {product_id}: {e}")
        
        return changes
    
    def start_scheduled_trading(self):
        """Start scheduled trading at regular intervals"""
        logger.info(f"Starting scheduled trading every {DECISION_INTERVAL_MINUTES} minutes")
        
        # Run once immediately
        self.run_trading_cycle()
        
        # Schedule regular runs
        schedule.every(DECISION_INTERVAL_MINUTES).minutes.do(self.run_trading_cycle)
        
        # Schedule daily tax report generation at midnight
        schedule.every().day.at("00:00").do(self.generate_tax_report)
        
        # Schedule weekly strategy performance report on Sunday at 1 AM
        schedule.every().sunday.at("01:00").do(self.generate_strategy_report)
        
        # Schedule portfolio rebalancing based on configured interval
        rebalance_interval = getattr(self.config, 'REBALANCE_CHECK_INTERVAL_MINUTES', 180)
        schedule.every(rebalance_interval).minutes.do(self.trading_strategy.check_and_rebalance)
        logger.info(f"Scheduled portfolio rebalancing every {rebalance_interval} minutes")
        
        # Schedule web server sync every 30 minutes (only sync point)
        schedule.every(30).minutes.do(self.sync_to_webserver)
        
        # Start a simple API server for dashboard interactions
        import threading
        api_thread = threading.Thread(target=self._start_api_server)
        api_thread.daemon = True
        api_thread.start()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    def _start_api_server(self):
        """Start a simple API server for dashboard interactions"""
        import http.server
        import socketserver
        import json
        import urllib.parse
        
        # Define a function that will be accessible to the handler
        def handle_refresh_portfolio():
            try:
                # Refresh portfolio from Coinbase
                result = self.trading_strategy.refresh_portfolio_from_coinbase()
                
                # Update local dashboard data only
                try:
                    # Get current portfolio data
                    portfolio = self.trading_strategy.portfolio
                    
                    # Create minimal dashboard data
                    dashboard_data = {
                        "status": "running",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Update the local dashboard
                    self.dashboard_updater.update_dashboard(dashboard_data, portfolio)
                    logger.info("Local dashboard updated with refreshed portfolio data")
                except Exception as e:
                    logger.error(f"Error updating local dashboard after portfolio refresh: {e}")
                
                return result
            except Exception as e:
                logger.error(f"Error in handle_refresh_portfolio: {e}")
                return {"status": "error", "message": str(e)}

        class APIHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    # Get the path
                    parsed_path = urllib.parse.urlparse(self.path)
                    
                    # Handle refresh portfolio endpoint
                    if parsed_path.path == '/api/refresh_portfolio':
                        # Call the refresh portfolio function directly
                        result = handle_refresh_portfolio()
                        
                        # Send response
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                    
                    else:
                        self.send_response(404)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "error", "message": "Endpoint not found"}).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
            
            def do_OPTIONS(self):
                # Handle CORS preflight requests
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
            
            def log_message(self, format, *args):
                # Use our logger instead of printing to stderr
                logger.info(f"API: {format % args}")

        # Create server
        port = 5000
        handler = APIHandler
        httpd = socketserver.TCPServer(("", port), handler)
        
        logger.info(f"API server started on port {port}")
        httpd.serve_forever()
            
    def update_local_dashboard(self):
        """Update local dashboard data only (no web server sync)"""
        try:
            # Get trading data
            trading_data = {
                "recent_trades": self.trading_strategy.trade_logger.get_recent_trades(10),
                "market_data": {}
            }
            
            # Get current market data for all trading pairs
            for product_id in TRADING_PAIRS:
                try:
                    market_data = self.data_collector.get_market_data(product_id)
                    trading_data["market_data"][product_id] = market_data
                except Exception as e:
                    logger.error(f"Error getting market data for {product_id}: {e}")
            
            # Get portfolio data - ensure it's a dictionary
            portfolio = self.trading_strategy.portfolio
            
            # Check if portfolio is a string and try to convert it to a dictionary
            if isinstance(portfolio, str):
                logger.warning(f"Portfolio is a string, attempting to convert to dictionary: {portfolio[:50]}...")
                try:
                    # Try to parse as JSON
                    portfolio = json.loads(portfolio)
                except json.JSONDecodeError:
                    logger.error("Failed to convert portfolio string to dictionary")
                    # Create a minimal valid portfolio
                    portfolio = {
                        "portfolio_value_usd": 0,
                        "initial_value_usd": 0,
                        "BTC": {"amount": 0, "last_price_usd": 0},
                        "ETH": {"amount": 0, "last_price_usd": 0},
                        "USD": {"amount": 0},
                        "trades_executed": 0
                    }
            
            # Validate portfolio is a dictionary
            if not isinstance(portfolio, dict):
                logger.error(f"Portfolio is not a dictionary: {type(portfolio)}")
                # Create a minimal valid portfolio
                portfolio = {
                    "portfolio_value_usd": 0,
                    "initial_value_usd": 0,
                    "BTC": {"amount": 0, "last_price_usd": 0},
                    "ETH": {"amount": 0, "last_price_usd": 0},
                    "USD": {"amount": 0},
                    "trades_executed": 0
                }
            
            # Ensure required keys exist
            required_keys = ["portfolio_value_usd", "initial_value_usd", "BTC", "ETH", "USD"]
            for key in required_keys:
                if key not in portfolio:
                    if key.endswith("_usd"):
                        portfolio[key] = 0
                    else:
                        portfolio[key] = {"amount": 0}
                        if key != "USD":
                            portfolio[key]["last_price_usd"] = 0
            
            # Log portfolio values before updating dashboard
            asset_summary = []
            asset_keys = [key for key in portfolio.keys() 
                         if isinstance(portfolio[key], dict) and 
                         key not in ["portfolio_value_usd", "initial_value_usd", "total_return", "last_updated"]]
            
            for asset in sorted(asset_keys):  # Sort for consistent logging
                if asset in portfolio and isinstance(portfolio[asset], dict):
                    amount = portfolio[asset].get("amount", 0)
                    asset_summary.append(f"{asset}: {amount}")
            
            logger.info(f"Updating local dashboard with portfolio - {', '.join(asset_summary)}, Total: ${portfolio['portfolio_value_usd']}")
            
            # Update local dashboard only
            self.dashboard_updater.update_dashboard(trading_data, portfolio)
            logger.info("Local dashboard updated")
            
        except Exception as e:
            logger.error(f"Error updating local dashboard: {e}")
            
    def generate_tax_report(self):
        """Generate a tax report with current year's data"""
        try:
            current_year = datetime.now().year
            output_file = f"reports/tax_report_{current_year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            logger.info(f"Generating tax report for year {current_year}")
            success = self.tax_report_generator.generate_report(output_file, current_year)
            
            if success:
                logger.info(f"Tax report generated successfully: {output_file}")
            else:
                logger.error("Failed to generate tax report")
                
            return success
        except Exception as e:
            logger.error(f"Error generating tax report: {e}")
            return False
            
    def generate_strategy_report(self):
        """Generate a strategy performance report"""
        try:
            output_file = f"reports/strategy_performance_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            logger.info("Generating strategy performance report")
            success = self.strategy_evaluator.generate_performance_report(output_file)
            
            if success:
                logger.info(f"Strategy performance report generated successfully: {output_file}")
            else:
                logger.error("Failed to generate strategy performance report")
                
            return success
        except Exception as e:
            logger.error(f"Error generating strategy performance report: {e}")
            return False

if __name__ == "__main__":
    bot = None
    try:
        bot = TradingBot()
        bot.start_scheduled_trading()
    except KeyboardInterrupt:
        from utils.logger import log_bot_shutdown
        if bot:
            bot.record_shutdown_time()
        log_bot_shutdown(logger)
        logger.info("Trading bot stopped by user")
    except Exception as e:
        from utils.logger import log_bot_shutdown
        if bot:
            bot.record_shutdown_time()
        log_bot_shutdown(logger)
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        # Ensure we always log shutdown and record offline status
        from utils.logger import log_bot_shutdown
        if bot:
            bot.record_shutdown_time()
        log_bot_shutdown(logger)
