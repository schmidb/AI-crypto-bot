#!/usr/bin/env python3
"""
Main entry point for the crypto trading bot with AWS Secrets Manager integration
"""

import logging
import time
import json
import schedule
from datetime import datetime
import os
from typing import Dict, List
import sys

# Add the aws_setup directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'aws_setup'))

# Try to load secrets from AWS Secrets Manager
try:
    from aws_setup.use_secrets_manager import load_secrets_to_env
    secrets_loaded = load_secrets_to_env()
    if secrets_loaded:
        print("Successfully loaded secrets from AWS Secrets Manager")
    else:
        print("Failed to load secrets from AWS Secrets Manager, falling back to .env file")
        from dotenv import load_dotenv
        load_dotenv()
except ImportError:
    print("AWS Secrets Manager integration not available, falling back to .env file")
    from dotenv import load_dotenv
    load_dotenv()

from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer
from data_collector import DataCollector
from trading_strategy import TradingStrategy
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
        
        # Initialize components
        self.coinbase_client = CoinbaseClient()
        self.llm_analyzer = LLMAnalyzer()
        self.data_collector = DataCollector(self.coinbase_client)
        self.trading_strategy = TradingStrategy(
            coinbase_client=self.coinbase_client,
            llm_analyzer=self.llm_analyzer,
            data_collector=self.data_collector
        )
        
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
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.start_scheduled_trading()
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
