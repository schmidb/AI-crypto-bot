import logging
from config import config
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
from strategies.adaptive_strategy_manager import AdaptiveStrategyManager
from utils.portfolio import Portfolio
from utils.capital_manager import CapitalManager
from utils.dashboard_updater import DashboardUpdater
from utils.webserver_sync import WebServerSync
from utils.tax_report import TaxReportGenerator
from utils.strategy_evaluator import StrategyEvaluator
from utils.logger import get_supervisor_logger, log_bot_shutdown
from utils.notification_service import NotificationService
from utils.cleanup_manager import CleanupManager

# Import performance tracking
try:
    from utils.performance_tracker import PerformanceTracker
    PERFORMANCE_TRACKING_AVAILABLE = True
except ImportError:
    PERFORMANCE_TRACKING_AVAILABLE = False

from config import TRADING_PAIRS, DECISION_INTERVAL_MINUTES, WEBSERVER_SYNC_ENABLED, SIMULATION_MODE, RISK_LEVEL, TRADING_STYLE, TRADING_TIMEFRAME, EXPECTED_HOLDING_PERIOD, Config

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
        self.config = Config()
        self.coinbase_client = CoinbaseClient()
        self.llm_analyzer = LLMAnalyzer()
        self.data_collector = DataCollector(self.coinbase_client)
        
        logger.info(f"✅ LLM analyzer initialized: {self.llm_analyzer is not None}")
        
        # Initialize new multi-strategy framework with Phase 3 support
        from utils.news_sentiment import NewsSentimentAnalyzer
        from utils.volatility_analyzer import VolatilityAnalyzer
        
        # Initialize Phase 3 analyzers
        self.news_sentiment_analyzer = NewsSentimentAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
        
        logger.info(f"✅ Phase 3 analyzers initialized - News: {self.news_sentiment_analyzer is not None}, Volatility: {self.volatility_analyzer is not None}")
        
        self.strategy_manager = AdaptiveStrategyManager(
            self.config, 
            self.llm_analyzer,
            self.news_sentiment_analyzer,
            self.volatility_analyzer
        )
        
        # Initialize capital manager for sustainable trading
        self.capital_manager = CapitalManager(self.config)
        
        logger.info("✅ Strategy manager initialized successfully")
        self.portfolio = Portfolio("data/portfolio.json")
        
        # Initialize trade logger (extracted from old TradingStrategy)
        from utils.trade_logger import TradeLogger
        self.trade_logger = TradeLogger()
        
        # Initialize dashboard updater (local data only)
        self.dashboard_updater = DashboardUpdater()
        
        # Initialize performance tracker
        self.performance_tracker = None
        if PERFORMANCE_TRACKING_AVAILABLE:
            try:
                self.performance_tracker = PerformanceTracker()
                logger.info("Performance tracker initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize performance tracker: {e}")
                self.performance_tracker = None
        
        # Initialize web server sync (if enabled)
        self.webserver_sync = WebServerSync()
        
        # Initialize tax report generator
        self.tax_report_generator = TaxReportGenerator()
        
        # Initialize strategy evaluator
        self.strategy_evaluator = StrategyEvaluator()
        
        # Initialize notification service
        self.notification_service = NotificationService()
        
        # Initialize cleanup manager
        self.cleanup_manager = CleanupManager()
        
        # Initialize dashboard with existing data
        self.initialize_dashboard()
        
        # Perform initial web server sync
        self.sync_to_webserver()
        
        # Record bot startup time
        self.record_startup_time()
        
        # Send startup notification
        try:
            mode_text = "SIMULATION" if SIMULATION_MODE else "LIVE TRADING"
            self.notification_service.send_status_notification(
                f"🚀 AI Crypto Bot Started\n\nMode: {mode_text}\nPairs: {', '.join(TRADING_PAIRS)}\nRisk Level: {RISK_LEVEL}"
            )
        except Exception as e:
            logger.warning(f"Failed to send startup notification: {e}")
        
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
        """Record the bot startup time"""
        try:
            startup_time = datetime.utcnow()
            next_decision_time = startup_time + timedelta(minutes=DECISION_INTERVAL_MINUTES)
            
            startup_data = {
                "startup_time": startup_time.isoformat(),
                "next_decision_time": next_decision_time.isoformat(),
                "pid": os.getpid(),
                "trading_pairs": TRADING_PAIRS,
                "decision_interval_minutes": DECISION_INTERVAL_MINUTES,
                "trading_style": TRADING_STYLE,
                "trading_timeframe": TRADING_TIMEFRAME,
                "expected_holding_period": EXPECTED_HOLDING_PERIOD,
                "simulation_mode": SIMULATION_MODE,
                "risk_level": RISK_LEVEL,
                "status": "online"
            }
            
            # Save startup data
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
                    "trading_style": TRADING_STYLE,
                    "trading_timeframe": TRADING_TIMEFRAME,
                    "expected_holding_period": EXPECTED_HOLDING_PERIOD,
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
    
    def _take_performance_snapshot(self, portfolio: Dict[str, Any]) -> None:
        """Take a performance snapshot of the current portfolio"""
        try:
            if not self.performance_tracker:
                logger.debug("Performance tracker not available, skipping snapshot")
                return
            
            if not self.performance_tracker.is_tracking_enabled():
                logger.debug("Performance tracking not enabled, skipping snapshot")
                return
            
            # Check if tracking is initialized by looking at tracking_start_date
            tracking_info = self.performance_tracker.get_tracking_info()
            if not tracking_info.get("tracking_start_date"):
                logger.info("Initializing performance tracking with current portfolio")
                
                # Calculate portfolio value
                portfolio_value = portfolio.get("portfolio_value_eur", 0)
                if portfolio_value == 0:
                    # Try to calculate from individual holdings
                    portfolio_value = sum([
                        holding.get("value_eur", 0) 
                        for holding in portfolio.values() 
                        if isinstance(holding, dict) and "value_eur" in holding
                    ])
                
                success = self.performance_tracker.initialize_tracking(
                    initial_portfolio_value=portfolio_value,
                    initial_portfolio_composition=portfolio
                )
                if not success:
                    logger.error("Failed to initialize performance tracking")
                    return
            
            # Format portfolio data for performance tracker
            formatted_portfolio = {
                "total_value_eur": portfolio.get("portfolio_value_eur", 0),
                "portfolio_composition": {
                    asset: {
                        "amount": data.get("amount", 0),
                        "value_eur": data.get("amount", 0) * data.get("last_price_eur", 0)
                    }
                    for asset, data in portfolio.items()
                    if isinstance(data, dict) and "amount" in data
                },
                "asset_prices": {
                    asset: data.get("last_price_eur", 0)
                    for asset, data in portfolio.items()
                    if isinstance(data, dict) and "last_price_eur" in data
                },
                "snapshot_type": "scheduled",
                "trading_session_id": f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Take the snapshot
            success = self.performance_tracker.take_portfolio_snapshot(formatted_portfolio)
            
            if success:
                logger.info("Performance snapshot taken successfully")
            else:
                logger.warning("Failed to take performance snapshot")
                
        except Exception as e:
            logger.error(f"Error taking performance snapshot: {e}")
        
        
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
            trades = self.trade_logger.get_recent_trades(10)
            
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
                            "trade_amount_base": 0,
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
            portfolio = self.portfolio.to_dict()
            
            # Update dashboard with loaded data
            self.dashboard_updater.update_dashboard(trading_data, portfolio)
            logger.info("Dashboard initialized with existing data")
            
            # Take initial performance snapshot
            self._take_performance_snapshot(portfolio)
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
            current_portfolio = self.portfolio.to_dict().copy()
            
            # Refresh portfolio from Coinbase
            # Get complete portfolio data from Coinbase (includes EUR prices)
            logger.info("Calling get_portfolio() from Coinbase client...")
            portfolio_data = self.coinbase_client.get_portfolio()
            logger.info(f"Received portfolio data keys: {list(portfolio_data.keys()) if portfolio_data else 'None'}")
            if portfolio_data:
                sync_result = self.portfolio.update_from_exchange(portfolio_data)
                logger.info(f"Portfolio sync result: {sync_result.get('status', 'unknown')}")
            else:
                sync_result = {"status": "error", "message": "Failed to get portfolio data from Coinbase"}
            
            if sync_result.get("status") == "success":
                # Get updated portfolio state
                updated_portfolio = self.portfolio.to_dict()
                
                # Log any significant discrepancies
                discrepancies_found = False
                total_discrepancy_value = 0.0
                
                for asset in [config.BASE_CURRENCY, 'BTC', 'ETH', 'SOL']:
                    if asset in current_portfolio and asset in updated_portfolio:
                        if isinstance(current_portfolio[asset], dict) and isinstance(updated_portfolio[asset], dict):
                            old_amount = current_portfolio[asset].get('amount', 0)
                            new_amount = updated_portfolio[asset].get('amount', 0)
                            
                            # Check for significant differences (more than 0.00001 for crypto, €0.01 for base currency)
                            threshold = 0.01 if asset == config.BASE_CURRENCY else 0.00001
                            if abs(old_amount - new_amount) > threshold:
                                discrepancies_found = True
                                difference = new_amount - old_amount
                                
                                # Calculate base currency value of discrepancy for crypto assets
                                if asset != config.BASE_CURRENCY:
                                    last_price = updated_portfolio[asset].get(f'last_price_{config.BASE_CURRENCY.lower()}', 0)
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
                    if total_discrepancy_value > 50.0:  # More than €50 difference
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
    
    def _execute_multi_strategy_analysis(self, product_id: str) -> Dict[str, Any]:
        """Execute multi-strategy analysis for a trading pair"""
        try:
            # Get market data and technical indicators
            market_data = self.data_collector.get_market_data(product_id)
            
            # Get historical data for technical indicators (use ONE_HOUR granularity)
            historical_data = self.data_collector.get_historical_data(product_id, "ONE_HOUR", days_back=7)
            technical_indicators = self.data_collector.calculate_indicators(historical_data)
            
            # Add current price to technical indicators
            technical_indicators['current_price'] = market_data.get('current_price', 0)
            
            # Get current portfolio state
            portfolio_data = self.portfolio.to_dict()
            
            # Get combined signal from all strategies
            combined_signal = self.strategy_manager.get_combined_signal(
                market_data, technical_indicators, portfolio_data
            )
            
            # Get individual strategy analysis for detailed reporting
            individual_strategies = self.strategy_manager.analyze_all_strategies(
                market_data, technical_indicators, portfolio_data
            )
            
            # Format result to match expected structure
            result = {
                "action": combined_signal.action,
                "decision": combined_signal.action,
                "confidence": combined_signal.confidence,
                "reasoning": combined_signal.reasoning,
                "product_id": product_id,
                "timestamp": datetime.now().isoformat(),
                "current_price": technical_indicators.get('current_price', 0),
                "indicators": technical_indicators,
                "strategy_details": {
                    "market_regime": getattr(self.strategy_manager, 'current_market_regime', 'sideways'),
                    "strategy_weights": self.strategy_manager.strategy_weights,
                    "individual_strategies": {
                        name: {
                            "action": signal.action,
                            "confidence": signal.confidence,
                            "reasoning": signal.reasoning,
                            "position_multiplier": getattr(signal, 'position_multiplier', 1.0)
                        }
                        for name, signal in individual_strategies.items()
                    },
                    "combined_signal": {
                        "action": combined_signal.action,
                        "confidence": combined_signal.confidence,
                        "reasoning": combined_signal.reasoning,
                        "position_multiplier": getattr(combined_signal, 'position_multiplier', 1.0)
                    }
                },
                "market_data": market_data,
                "execution_status": "pending",
                "trade_executed": False
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-strategy analysis for {product_id}: {e}")
            return {
                "action": "HOLD",
                "decision": "HOLD", 
                "confidence": 0,
                "reasoning": f"Analysis error: {str(e)}",
                "product_id": product_id,
                "timestamp": datetime.now().isoformat(),
                "execution_status": "error",
                "trade_executed": False
            }

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
                # Execute new multi-strategy analysis
                decision_result = self._execute_multi_strategy_analysis(product_id)
                
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
            for product_id in config.TRADING_PAIRS:
                try:
                    market_data[product_id] = self.data_collector.get_market_data(product_id)
                    logger.info(f"Got fresh market data for {product_id}: price=${market_data[product_id].get('price', 0)}")
                except Exception as e:
                    logger.error(f"Error getting market data for {product_id}: {e}")
            
            # Get recent trades with the latest decisions
            recent_trades = self.trade_logger.get_recent_trades(10)
            
            # Convert results to a proper format for the dashboard
            dashboard_data = {
                "trading_results": results,
                "recent_trades": recent_trades,
                "market_data": market_data,
                "status": "running",
                "timestamp": datetime.utcnow().isoformat()  # Use UTC time for consistency
            }
            
            # Get current portfolio data
            portfolio = self.portfolio.to_dict()
            
            # Ensure portfolio is a dictionary
            if isinstance(portfolio, str):
                try:
                    portfolio = json.loads(portfolio)
                except json.JSONDecodeError:
                    portfolio = {
                        f"portfolio_value_{config.BASE_CURRENCY.lower()}": 0,
                        f"initial_value_{config.BASE_CURRENCY.lower()}": 0,
                        "BTC": {"amount": 0, f"last_price_{config.BASE_CURRENCY.lower()}": 0},
                        "ETH": {"amount": 0, f"last_price_{config.BASE_CURRENCY.lower()}": 0},
                        config.BASE_CURRENCY: {"amount": 0},
                        "trades_executed": 0
                    }
            
            # Update local dashboard data
            self.dashboard_updater.update_dashboard(dashboard_data, portfolio)
            logger.info("Local dashboard updated successfully")
            
            # Take performance snapshot after portfolio update
            self._take_performance_snapshot(portfolio)
            
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
                    if execution_status == 'insufficient_base':
                        base_available = trade_result.get('available_base', 0)
                        log_reason = f"AI recommended {action} but insufficient EUR balance (${base_available:.2f} available, minimum €10 required)"
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
                # Ensure we have a valid price for logging
                log_price = trade_result.get('execution_price', 0)
                if log_price == 0:
                    # Try to get current price for HOLD decisions or failed trades
                    try:
                        log_price = self.data_collector.get_current_price(product_id)
                        logger.debug(f"Using current price {log_price} for {product_id} trade logging")
                    except Exception as e:
                        logger.warning(f"Could not get current price for {product_id} logging: {e}")
                        log_price = 0
                
                # Create enhanced trade record for dashboard visibility
                enhanced_trade_result = {
                    **trade_result,
                    'action': log_action,
                    'price': log_price,  # Ensure price is always included
                    'status': 'executed' if trade_result.get('trade_executed') else 'hold' if log_action == 'HOLD' else 'attempted',
                    'reason': log_reason,
                    'intended_action': log_action,
                    'ai_recommendation': original_decision or action,
                    'skip_reason': execution_status if not trade_result.get('trade_executed') and log_action != 'HOLD' else None,
                    'execution_message': trade_result.get('execution_message', ''),
                    'ai_reasoning': decision_result.get('reasoning', '')
                }
                
                # Use the trade logger
                self.trade_logger.log_trade(product_id, decision_result, enhanced_trade_result)
                logger.info(f"Trade decision logged for {product_id}: {log_action} - {execution_status}")
            
        except Exception as e:
            logger.error(f"Error logging trade decision for {product_id}: {e}")

    def _execute_trade(self, product_id: str, decision_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute actual trade based on AI decision with capital management
        
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
                'trade_amount_base': 0,
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
            portfolio = self.portfolio.to_dict()
            asset = product_id.split('-')[0]  # Extract asset (BTC, ETH, SOL)
            
            # Check portfolio health and rebalancing needs
            health_report = self.capital_manager.get_portfolio_health_report(portfolio)
            logger.info(f"💰 Portfolio health: {health_report['status']} (EUR: {health_report['eur_percent']*100:.1f}%, Trading capital: €{health_report['available_trading_capital']:.2f})")
            
            # Check if rebalancing is needed (overrides trading signals)
            rebalance_target = self.capital_manager.get_rebalancing_target(portfolio)
            if rebalance_target:
                logger.warning(f"🔄 Rebalancing needed: {rebalance_target}")
                if rebalance_target['action'] != action:
                    execution_result.update({
                        'execution_status': 'rebalancing_override',
                        'execution_message': f"Rebalancing required: {rebalance_target['reason']}"
                    })
                    return execution_result
            
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
            strategy_details = decision_result.get('strategy_details', {})
            
            if action == 'BUY':
                return self._execute_buy_order(product_id, asset, current_price, confidence, portfolio, execution_result, strategy_details)
            elif action == 'SELL':
                return self._execute_sell_order(product_id, asset, current_price, confidence, portfolio, execution_result, strategy_details)
            else:
                execution_result.update({
                    'execution_status': 'unknown_action',
                    'execution_message': f'Unknown action: {action}'
                })
                return execution_result
                
        except Exception as e:
            logger.error(f"Error executing trade for {product_id}: {e}")
            # Send critical error notification
            try:
                self.notification_service.send_error_notification(
                    f"Trade execution failed for {product_id}: {str(e)[:100]}",
                    f"Product: {product_id}, Action: {decision_result.get('action', 'UNKNOWN')}"
                )
            except:
                pass  # Don't fail if notification fails
            
            return {
                'execution_status': 'error',
                'execution_message': f'Execution error: {e}',
                'trade_executed': False,
                'crypto_amount': 0,
                'trade_amount_base': 0,
                'execution_price': 0
            }
    
    def _execute_buy_order(self, product_id: str, asset: str, current_price: float, confidence: int, portfolio: Dict, execution_result: Dict, strategy_details: Dict = None) -> Dict[str, Any]:
        f"""Execute BUY order with capital management and {config.BASE_CURRENCY} balance validation"""
        try:
            # Calculate original trade size using confidence-based sizing
            base_available = portfolio.get(config.BASE_CURRENCY, {}).get('amount', 0)
            base_trade_percentage = 0.10 + (confidence / 100.0 * 0.15)  # 10% to 25%
            
            # Apply strategy multiplier if available
            strategy_multiplier = 1.0
            if strategy_details and 'combined_signal' in strategy_details:
                strategy_multiplier = strategy_details['combined_signal'].get('position_multiplier', 1.0)
            
            # Calculate original trade size
            original_trade_size = base_available * base_trade_percentage * strategy_multiplier
            
            # Use capital manager to calculate safe trade size
            safe_trade_size, capital_reason = self.capital_manager.calculate_safe_trade_size(
                "BUY", asset, portfolio, original_trade_size
            )
            
            logger.info(f"💰 Capital management: {capital_reason}")
            
            if safe_trade_size <= 0:
                execution_result.update({
                    'execution_status': 'capital_management_block',
                    'execution_message': f'Capital management blocked trade: {capital_reason}',
                    'available_base': base_available,
                    'original_size': original_trade_size,
                    'safe_size': safe_trade_size
                })
                logger.warning(f"BUY order blocked by capital management for {product_id}: {capital_reason}")
                return execution_result
            
            # Check minimum trade amount
            if safe_trade_size < config.MIN_TRADE_AMOUNT:
                execution_result.update({
                    'execution_status': 'insufficient_size',
                    'execution_message': f'Safe trade size (€{safe_trade_size:.2f}) below minimum (€{config.MIN_TRADE_AMOUNT})',
                    'available_base': base_available,
                    'safe_size': safe_trade_size
                })
                logger.warning(f"BUY order skipped for {product_id}: Safe trade size too small")
                return execution_result
            
            # Use the safe trade size calculated by capital manager
            trade_amount_base = safe_trade_size
            crypto_amount = trade_amount_base / current_price
            
            logger.info(f"💰 Position sizing for {product_id}: confidence={confidence}%, "
                       f"available=€{base_available:.2f}, "
                       f"original_size=€{original_trade_size:.2f}, "
                       f"safe_size=€{trade_amount_base:.2f}")
            
            if SIMULATION_MODE:
                # Simulate the trade
                execution_result.update({
                    'execution_status': 'simulated',
                    'execution_message': f'SIMULATED BUY: {crypto_amount:.8f} {asset} for €{trade_amount_base:.2f}',
                    'trade_executed': True,
                    'crypto_amount': crypto_amount,
                    'trade_amount_base': trade_amount_base
                })
                logger.info(f"SIMULATED BUY: {crypto_amount:.8f} {asset} for ${trade_amount_base:.2f}")
            else:
                # Execute real trade
                try:
                    order_result = self.coinbase_client.place_market_order(
                        product_id=product_id,
                        side='BUY',
                        size=trade_amount_base,
                        confidence=confidence
                    )
                    
                    if order_result.get('success'):
                        execution_result.update({
                            'execution_status': 'executed',
                            'execution_message': f'BUY order executed: {crypto_amount:.8f} {asset} for ${trade_amount_base:.2f}',
                            'trade_executed': True,
                            'crypto_amount': crypto_amount,
                            'trade_amount_base': trade_amount_base,
                            'order_id': order_result.get('order_id'),
                            # Add fee information from Coinbase client
                            'total_fees': order_result.get('fees', 0),
                            'fee_percentage': order_result.get('fee_percentage', 0),
                            'total_value_after_fees': order_result.get('actual_eur_spent', 0),
                            'filled_size': order_result.get('filled_size', crypto_amount),
                            'average_filled_price': order_result.get('average_filled_price', 0),
                            'actual_eur_spent': order_result.get('actual_eur_spent', trade_amount_base)
                        })
                        logger.info(f"BUY order executed: {crypto_amount:.8f} {asset} for €{trade_amount_base:.2f}")
                        
                        # Record trade in capital manager for limit tracking
                        portfolio_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
                        self.capital_manager.record_trade(asset, trade_amount_base, portfolio_value)
                        
                        # Update portfolio
                        self.portfolio.update_asset_amount('EUR', -trade_amount_base)
                        self.portfolio.update_asset_amount(asset, crypto_amount)
                        self.portfolio.update_asset_price(asset, current_price, current_price)  # Assuming EUR price
                        
                        # Save updated portfolio
                        self.portfolio.save()
                        
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
    
    def _execute_sell_order(self, product_id: str, asset: str, current_price: float, confidence: int, portfolio: Dict, execution_result: Dict, strategy_details: Dict = None) -> Dict[str, Any]:
        """Execute SELL order with capital management and asset balance validation"""
        try:
            # Check asset balance
            asset_available = portfolio.get(asset, {}).get('amount', 0)
            min_trade_value = config.MIN_TRADE_AMOUNT  # Use configured minimum trade amount (€30)
            min_crypto_amount = min_trade_value / current_price
            
            # Calculate original trade size with dynamic position sizing
            base_trade_percentage = 0.10 + (confidence / 100.0 * 0.15)  # 10% to 25%
            
            # Apply strategy-based position multiplier
            dynamic_multiplier = 1.0
            if strategy_details and 'combined_signal' in strategy_details:
                dynamic_multiplier = strategy_details['combined_signal'].get('position_multiplier', 1.0)
            
            # Apply dynamic sizing and risk management
            adjusted_percentage = base_trade_percentage * dynamic_multiplier
            risk_multiplier = 0.5 if confidence < 70 else 1.0  # Reduce for low confidence
            
            max_crypto_amount = asset_available * adjusted_percentage * risk_multiplier
            original_trade_value = max_crypto_amount * current_price
            
            # Use capital manager to calculate safe trade size
            safe_trade_value, capital_reason = self.capital_manager.calculate_safe_trade_size(
                "SELL", asset, portfolio, original_trade_value
            )
            
            logger.info(f"💰 Capital management: {capital_reason}")
            
            if safe_trade_value <= 0:
                execution_result.update({
                    'execution_status': 'capital_management_block',
                    'execution_message': f'Capital management blocked trade: {capital_reason}',
                    'available_crypto': asset_available,
                    'original_value': original_trade_value,
                    'safe_value': safe_trade_value
                })
                logger.warning(f"SELL order blocked by capital management for {product_id}: {capital_reason}")
                return execution_result
            
            # Convert safe trade value back to crypto amount
            crypto_amount = safe_trade_value / current_price
            trade_amount_base = safe_trade_value
            
            # Final validation
            if crypto_amount > asset_available:
                crypto_amount = asset_available
                trade_amount_base = crypto_amount * current_price
            
            if trade_amount_base < min_trade_value:
                execution_result.update({
                    'execution_status': 'insufficient_size',
                    'execution_message': f'Safe trade value (€{trade_amount_base:.2f}) below minimum (€{min_trade_value})',
                    'available_crypto': asset_available,
                    'safe_value': safe_trade_value
                })
                logger.warning(f"SELL order skipped for {product_id}: Safe trade size too small")
                return execution_result
            crypto_amount = max(min_crypto_amount, min(crypto_amount, asset_available * 0.90))  # Keep 10% buffer
            
            trade_amount_base = crypto_amount * current_price
            
            if SIMULATION_MODE:
                # Simulate the trade
                execution_result.update({
                    'execution_status': 'simulated',
                    'execution_message': f'SIMULATED SELL: {crypto_amount:.8f} {asset} for ${trade_amount_base:.2f}',
                    'trade_executed': True,
                    'crypto_amount': crypto_amount,
                    'trade_amount_base': trade_amount_base
                })
                logger.info(f"SIMULATED SELL: {crypto_amount:.8f} {asset} for ${trade_amount_base:.2f}")
            else:
                # Execute real trade
                try:
                    order_result = self.coinbase_client.place_market_order(
                        product_id=product_id,
                        side='SELL',
                        size=crypto_amount,
                        confidence=confidence
                    )
                    
                    if order_result.get('success'):
                        execution_result.update({
                            'execution_status': 'executed',
                            'execution_message': f'SELL order executed: {crypto_amount:.8f} {asset} for ${trade_amount_base:.2f}',
                            'trade_executed': True,
                            'crypto_amount': crypto_amount,
                            'trade_amount_base': trade_amount_base,
                            'order_id': order_result.get('order_id'),
                            # Add fee information from Coinbase client
                            'total_fees': order_result.get('fees', 0),
                            'fee_percentage': order_result.get('fee_percentage', 0),
                            'total_value_after_fees': order_result.get('actual_eur_spent', 0),
                            'filled_size': order_result.get('filled_size', crypto_amount),
                            'average_filled_price': order_result.get('average_filled_price', 0),
                            'actual_eur_spent': order_result.get('actual_eur_spent', trade_amount_base)
                        })
                        logger.info(f"SELL order executed: {crypto_amount:.8f} {asset} for €{trade_amount_base:.2f}")
                        
                        # Record trade in capital manager for limit tracking
                        portfolio_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
                        self.capital_manager.record_trade(asset, trade_amount_base, portfolio_value)
                        
                        # Update portfolio
                        self.portfolio.update_asset_amount(asset, -crypto_amount)
                        self.portfolio.update_asset_amount('EUR', trade_amount_base)
                        
                        # Save updated portfolio
                        self.portfolio.save()
                        
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
    
    def run_trading_cycle(self):
        """Execute one complete trading cycle for all trading pairs"""
        try:
            logger.info("🔄 Starting trading cycle")
            
            # Sync portfolio with Coinbase before trading
            if not self._sync_portfolio_with_coinbase():
                logger.warning("Portfolio sync failed, continuing with cached data")
            
            # Execute trading analysis for each pair
            for product_id in self.config.TRADING_PAIRS:
                try:
                    logger.info(f"📊 Analyzing {product_id}")
                    
                    # Execute multi-strategy analysis
                    decision_result = self._execute_multi_strategy_analysis(product_id)
                    
                    # Execute trade based on decision
                    trade_result = self._execute_trade(product_id, decision_result)
                    
                    # Log the decision and trade result
                    self._log_trade_decision(product_id, decision_result, trade_result)
                    
                    # Save results for dashboard
                    self._save_result(product_id, {**decision_result, **trade_result})
                    
                except Exception as e:
                    logger.error(f"Error processing {product_id}: {e}")
                    continue
            
            # Update dashboard after all trades
            self.update_local_dashboard()
            
            # Update next decision time
            self.update_next_decision_time()
            
            logger.info("✅ Trading cycle completed")
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            # Still update dashboard to show error status
            try:
                self.update_local_dashboard()
            except Exception as dashboard_error:
                logger.error(f"Failed to update dashboard after error: {dashboard_error}")

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
        
        # Schedule portfolio rebalancing every 3 hours
        # TODO: Implement portfolio rebalancing method
        # schedule.every(180).minutes.do(self.portfolio.check_and_rebalance)
        logger.info("Portfolio rebalancing scheduled (currently disabled)")
        
        # Schedule web server sync every 30 minutes (only sync point)
        schedule.every(30).minutes.do(self.sync_to_webserver)
        
        # Schedule daily cleanup at 2 AM
        schedule.every().day.at("02:00").do(self.run_daily_cleanup)
        
        # Schedule integrated analysis tasks
        schedule.every().day.at("06:00").do(self.run_daily_health_check_task)
        schedule.every().monday.at("07:00").do(self.run_weekly_validation_task)
        schedule.every().month.at("08:00").do(self.run_monthly_stability_task)
        
        logger.info("📅 Scheduled tasks configured:")
        logger.info("  - Daily health check: 6:00 AM daily")
        logger.info("  - Weekly validation: 7:00 AM Mondays")
        logger.info("  - Monthly stability: 8:00 AM 1st of month")

        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)
            

            
    def update_local_dashboard(self):
        """Update local dashboard data only (no web server sync)"""
        try:
            # Get trading data
            trading_data = {
                "recent_trades": self.trade_logger.get_recent_trades(10),
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
            portfolio = self.portfolio.to_dict()
            
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
                        "portfolio_value_eur": 0,
                        "initial_value_eur": 0,
                        "BTC": {"amount": 0, "last_price_eur": 0},
                        "ETH": {"amount": 0, "last_price_eur": 0},
                        "EUR": {"amount": 0},
                        "trades_executed": 0
                    }
            
            # Validate portfolio is a dictionary
            if not isinstance(portfolio, dict):
                logger.error(f"Portfolio is not a dictionary: {type(portfolio)}")
                # Create a minimal valid portfolio
                portfolio = {
                    "portfolio_value_eur": 0,
                    "initial_value_eur": 0,
                    "BTC": {"amount": 0, "last_price_eur": 0},
                    "ETH": {"amount": 0, "last_price_eur": 0},
                    "EUR": {"amount": 0},
                    "trades_executed": 0
                }
            
            # Ensure required keys exist
            required_keys = ["portfolio_value_eur", "initial_value_eur", "BTC", "ETH", "EUR"]
            for key in required_keys:
                if key not in portfolio:
                    if key.endswith("_usd"):
                        portfolio[key] = 0
                    else:
                        portfolio[key] = {"amount": 0}
                        if key != "EUR":
                            portfolio[key]["last_price_eur"] = 0
            
            # Log portfolio values before updating dashboard
            asset_summary = []
            asset_keys = [key for key in portfolio.keys() 
                         if isinstance(portfolio[key], dict) and 
                         key not in ["portfolio_value_eur", "initial_value_eur", "total_return", "last_updated"]]
            
            for asset in sorted(asset_keys):  # Sort for consistent logging
                if asset in portfolio and isinstance(portfolio[asset], dict):
                    amount = portfolio[asset].get("amount", 0)
                    asset_summary.append(f"{asset}: {amount}")
            
            logger.info(f"Updating local dashboard with portfolio - {', '.join(asset_summary)}, Total: €{portfolio['portfolio_value_eur']}")
            
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
    
    def run_daily_health_check_task(self):
        """Scheduled task wrapper for daily health check"""
        try:
            logger.info("🏥 Running scheduled daily health check...")
            
            # Import and run the daily health check
            from run_daily_health_check import run_daily_health_check
            success = run_daily_health_check(sync_gcs=True)
            
            if success:
                logger.info("✅ Scheduled daily health check completed successfully")
                # Send notification
                try:
                    self.notification_service.send_status_notification(
                        "🏥 Daily Health Check Complete\n\nAll systems analyzed and report generated successfully."
                    )
                except Exception as e:
                    logger.warning(f"Failed to send health check notification: {e}")
            else:
                logger.error("❌ Scheduled daily health check failed")
                # Send error notification
                try:
                    self.notification_service.send_error_notification(
                        "Daily Health Check Failed",
                        "The scheduled daily health check encountered errors. Please review the logs."
                    )
                except Exception as e:
                    logger.warning(f"Failed to send health check error notification: {e}")
                    
            return success
        except Exception as e:
            logger.error(f"Error in scheduled daily health check: {e}")
            return False
    
    def run_weekly_validation_task(self):
        """Scheduled task wrapper for weekly validation"""
        try:
            logger.info("📊 Running scheduled weekly validation...")
            
            # Import and run the weekly validation
            from run_weekly_validation import run_weekly_validation
            success = run_weekly_validation(sync_gcs=True)
            
            if success:
                logger.info("✅ Scheduled weekly validation completed successfully")
                # Send notification
                try:
                    self.notification_service.send_status_notification(
                        "📊 Weekly Validation Complete\n\nStrategy validation and backtesting completed successfully."
                    )
                except Exception as e:
                    logger.warning(f"Failed to send weekly validation notification: {e}")
            else:
                logger.error("❌ Scheduled weekly validation failed")
                # Send error notification
                try:
                    self.notification_service.send_error_notification(
                        "Weekly Validation Failed",
                        "The scheduled weekly validation encountered errors. Please review the logs."
                    )
                except Exception as e:
                    logger.warning(f"Failed to send weekly validation error notification: {e}")
                    
            return success
        except Exception as e:
            logger.error(f"Error in scheduled weekly validation: {e}")
            return False
    
    def run_monthly_stability_task(self):
        """Scheduled task wrapper for monthly stability analysis"""
        try:
            logger.info("🔬 Running scheduled monthly stability analysis...")
            
            # Import and run the monthly stability analysis
            from run_monthly_stability import run_monthly_stability
            success = run_monthly_stability(sync_gcs=True)
            
            if success:
                logger.info("✅ Scheduled monthly stability analysis completed successfully")
                # Send notification
                try:
                    self.notification_service.send_status_notification(
                        "🔬 Monthly Stability Analysis Complete\n\nParameter stability analysis completed successfully."
                    )
                except Exception as e:
                    logger.warning(f"Failed to send monthly stability notification: {e}")
            else:
                logger.error("❌ Scheduled monthly stability analysis failed")
                # Send error notification
                try:
                    self.notification_service.send_error_notification(
                        "Monthly Stability Analysis Failed",
                        "The scheduled monthly stability analysis encountered errors. Please review the logs."
                    )
                except Exception as e:
                    logger.warning(f"Failed to send monthly stability error notification: {e}")
                    
            return success
        except Exception as e:
            logger.error(f"Error in scheduled monthly stability analysis: {e}")
            return False

    def run_daily_cleanup(self):
        """Run daily cleanup of old logs and data files"""
        try:
            logger.info("🧹 Starting daily cleanup...")
            result = self.cleanup_manager.run_cleanup()
            
            # Send notification if significant cleanup occurred
            if result['total_files'] > 0:
                try:
                    cleanup_msg = f"🧹 Daily Cleanup Complete\n\n"
                    cleanup_msg += f"Files deleted: {result['total_files']}\n"
                    cleanup_msg += f"Space freed: {result['space_saved_mb']:.1f}MB\n\n"
                    
                    for category, count in result['files_deleted'].items():
                        if count > 0:
                            cleanup_msg += f"• {category.replace('_', ' ').title()}: {count}\n"
                    
                    self.notification_service.send_status_notification(cleanup_msg)
                except Exception as e:
                    logger.warning(f"Failed to send cleanup notification: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error during daily cleanup: {e}")
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
        
        # Send critical error notification
        try:
            from utils.notification_service import NotificationService
            notification_service = NotificationService()
            notification_service.send_error_notification(
                f"Trading bot crashed: {str(e)[:100]}",
                "The bot has stopped due to a critical error and needs attention"
            )
        except:
            pass  # Don't fail if notification fails
        
        raise
    finally:
        # Ensure we always log shutdown and record offline status
        from utils.logger import log_bot_shutdown
        if bot:
            bot.record_shutdown_time()
        log_bot_shutdown(logger)
