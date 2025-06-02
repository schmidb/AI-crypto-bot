import logging
import time
import json
import schedule
from datetime import datetime
import os
from typing import Dict, List

from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer
from data_collector import DataCollector
from trading_strategy import TradingStrategy
from utils.dashboard_updater import DashboardUpdater
from utils.tax_report import TaxReportGenerator
from utils.strategy_evaluator import StrategyEvaluator
from config import TRADING_PAIRS, DECISION_INTERVAL_MINUTES, LOG_LEVEL, LOG_FILE

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingBot:
    """Main trading bot class that orchestrates the trading process"""
    
    def __init__(self):
        """Initialize the trading bot"""
        logger.info("Initializing trading bot")
        
        # Create necessary directories
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        
        # Initialize components
        self.coinbase_client = CoinbaseClient()
        self.llm_analyzer = LLMAnalyzer()
        self.data_collector = DataCollector(self.coinbase_client)
        self.trading_strategy = TradingStrategy(
            coinbase_client=self.coinbase_client,
            llm_analyzer=self.llm_analyzer,
            data_collector=self.data_collector
        )
        
        # Initialize portfolio with current market values
        self.trading_strategy.update_portfolio_values()
        
        # Initialize dashboard updater
        self.dashboard_updater = DashboardUpdater()
        
        # Initialize tax report generator
        self.tax_report_generator = TaxReportGenerator()
        
        # Initialize strategy evaluator
        self.strategy_evaluator = StrategyEvaluator()
        
        # Initialize dashboard with existing data
        self.initialize_dashboard()
        
        logger.info(f"Trading bot initialized with trading pairs: {TRADING_PAIRS}")
        
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
            
            # Update portfolio with current market values
            self.trading_strategy.update_portfolio_values()
            
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
    
    def run_trading_cycle(self):
        """Run a single trading cycle for all configured trading pairs"""
        logger.info(f"Starting trading cycle at {datetime.now()}")
        
        results = {}
        
        for product_id in TRADING_PAIRS:
            logger.info(f"Processing {product_id}")
            
            try:
                # Execute trading strategy
                result = self.trading_strategy.execute_strategy(product_id)
                results[product_id] = result
                
                # Save result to file
                self._save_result(product_id, result)
                
                # Log decision
                decision = result.get('action', result.get('decision', 'UNKNOWN'))
                confidence = result.get('confidence', 0)
                logger.info(f"Decision for {product_id}: {decision} (confidence: {confidence}%)")
                
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
            
            self.dashboard_updater.update_dashboard(dashboard_data, portfolio)
            logger.info("Dashboard updated successfully")
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
        
        logger.info(f"Trading cycle completed at {datetime.now()}")
        return results
    
    def _save_result(self, product_id: str, result: Dict):
        """Save trading result to a JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/{product_id.replace('-', '_')}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Saved result to {filename}")
    
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
        
        # Schedule portfolio rebalancing (once per day at 2 AM)
        schedule.every().day.at("02:00").do(self.trading_strategy.rebalance_portfolio)
        
        # Schedule dashboard updates every 5 minutes
        schedule.every(5).minutes.do(self.update_dashboard)
        
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
                
                # Explicitly update the dashboard with the latest portfolio data
                try:
                    # Get current portfolio data
                    portfolio = self.trading_strategy.portfolio
                    
                    # Create minimal dashboard data
                    dashboard_data = {
                        "status": "running",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Update the dashboard
                    self.dashboard_updater.update_dashboard(dashboard_data, portfolio)
                    logger.info("Dashboard updated with refreshed portfolio data")
                except Exception as e:
                    logger.error(f"Error updating dashboard after portfolio refresh: {e}")
                
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
            
    def update_dashboard(self):
        """Update the dashboard with latest data"""
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
            logger.info(f"Updating dashboard with portfolio - BTC: {portfolio['BTC']['amount']}, ETH: {portfolio['ETH']['amount']}, USD: {portfolio['USD']['amount']}, Total: ${portfolio['portfolio_value_usd']}")
            
            # Update dashboard
            self.dashboard_updater.update_dashboard(trading_data, portfolio)
            logger.info("Dashboard updated")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            
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
    try:
        bot = TradingBot()
        bot.start_scheduled_trading()
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    def refresh_portfolio(self):
        """Refresh portfolio data from Coinbase"""
        try:
            result = self.trading_strategy.refresh_portfolio_from_coinbase()
            logger.info(f"Portfolio refresh result: {result['status']}")
            return result
        except Exception as e:
            logger.error(f"Error refreshing portfolio: {e}")
            return {"status": "error", "message": str(e)}
