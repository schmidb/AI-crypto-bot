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
        
        logger.info(f"Trading bot initialized with trading pairs: {TRADING_PAIRS}")
    
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
                decision = result.get('decision', 'UNKNOWN')
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
            # Convert results to a proper format for the dashboard
            dashboard_data = {
                "trading_results": results,
                "status": "running",
                "timestamp": datetime.now().isoformat()
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

        # Store a reference to the trading bot instance for the handler to use
        trading_bot_instance = self

        class APIHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    # Get the path
                    parsed_path = urllib.parse.urlparse(self.path)
                    
                    # Handle refresh portfolio endpoint
                    if parsed_path.path == '/api/refresh_portfolio':
                        # Get request body length
                        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
                        
                        # Call the refresh portfolio method on the trading bot instance
                        result = trading_bot_instance.refresh_portfolio()
                        
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
        # No need to set trading_bot attribute on server since we're using closure
        
        logger.info(f"API server started on port {port}")
        httpd.serve_forever()
            
    def update_dashboard(self):
        """Update the dashboard with latest data"""
        try:
            # Get trading data
            trading_data = {
                "recent_trades": self.trading_strategy.trade_logger.get_recent_trades(10),
                "market_data": {
                    product_id: self.data_collector.get_market_data(product_id)
                    for product_id in TRADING_PAIRS
                }
            }
            
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
