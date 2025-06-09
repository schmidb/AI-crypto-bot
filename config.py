"""
Configuration settings for the crypto trading bot
"""

import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the crypto trading bot"""
    
    def __init__(self):
        # Coinbase API credentials
        self.COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
        self.COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")

        # Google Cloud settings
        self.GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        # LLM settings
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "vertex")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        self.LLM_LOCATION = os.getenv("LLM_LOCATION", "us-central1")

        # Trading settings
        self.TRADING_PAIRS = os.getenv("TRADING_PAIRS", "BTC-USD,ETH-USD").split(",")
        self.DECISION_INTERVAL_MINUTES = int(os.getenv("DECISION_INTERVAL_MINUTES", "60"))
        self.RISK_LEVEL = os.getenv("RISK_LEVEL", "medium")
        self.SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"

        # Portfolio settings
        self.PORTFOLIO_REBALANCE = os.getenv("PORTFOLIO_REBALANCE", "true").lower() == "true"
        self.MAX_TRADE_PERCENTAGE = float(os.getenv("MAX_TRADE_PERCENTAGE", "25"))

        # Target allocation settings
        self.TARGET_CRYPTO_ALLOCATION = float(os.getenv("TARGET_CRYPTO_ALLOCATION", "80"))
        self.TARGET_USD_ALLOCATION = float(os.getenv("TARGET_USD_ALLOCATION", "20"))

        # Calculate individual crypto allocations based on trading pairs
        self.CRYPTO_ASSETS = [pair.split("-")[0] for pair in self.TRADING_PAIRS]
        self.CRYPTO_ASSETS = list(set(self.CRYPTO_ASSETS))  # Remove duplicates
        self.INDIVIDUAL_CRYPTO_ALLOCATION = self.TARGET_CRYPTO_ALLOCATION / len(self.CRYPTO_ASSETS) if self.CRYPTO_ASSETS else 0

        # Create target allocation dictionary
        self.TARGET_ALLOCATION = {asset: self.INDIVIDUAL_CRYPTO_ALLOCATION for asset in self.CRYPTO_ASSETS}
        self.TARGET_ALLOCATION["USD"] = self.TARGET_USD_ALLOCATION

        # Dashboard settings
        self.DASHBOARD_TRADE_HISTORY_LIMIT = int(os.getenv("DASHBOARD_TRADE_HISTORY_LIMIT", "10"))
        
        # Logging settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/crypto_bot.log")
    
    def get_trading_pairs(self) -> List[str]:
        """Get list of trading pairs"""
        return self.TRADING_PAIRS
    
    def get_crypto_assets(self) -> List[str]:
        """Get list of crypto assets from trading pairs"""
        return self.CRYPTO_ASSETS
    
    def get_target_allocation(self) -> dict:
        """Get target allocation dictionary"""
        return self.TARGET_ALLOCATION

# For backward compatibility, create module-level variables
config = Config()

# Coinbase API credentials
COINBASE_API_KEY = config.COINBASE_API_KEY
COINBASE_API_SECRET = config.COINBASE_API_SECRET

# Google Cloud settings
GOOGLE_CLOUD_PROJECT = config.GOOGLE_CLOUD_PROJECT
GOOGLE_APPLICATION_CREDENTIALS = config.GOOGLE_APPLICATION_CREDENTIALS

# LLM settings
LLM_PROVIDER = config.LLM_PROVIDER
LLM_MODEL = config.LLM_MODEL
LLM_LOCATION = config.LLM_LOCATION

# Trading settings
TRADING_PAIRS = config.TRADING_PAIRS
DECISION_INTERVAL_MINUTES = config.DECISION_INTERVAL_MINUTES
RISK_LEVEL = config.RISK_LEVEL
SIMULATION_MODE = config.SIMULATION_MODE

# Portfolio settings
PORTFOLIO_REBALANCE = config.PORTFOLIO_REBALANCE
MAX_TRADE_PERCENTAGE = config.MAX_TRADE_PERCENTAGE

# Target allocation settings
TARGET_CRYPTO_ALLOCATION = config.TARGET_CRYPTO_ALLOCATION
TARGET_USD_ALLOCATION = config.TARGET_USD_ALLOCATION
CRYPTO_ASSETS = config.CRYPTO_ASSETS
INDIVIDUAL_CRYPTO_ALLOCATION = config.INDIVIDUAL_CRYPTO_ALLOCATION
TARGET_ALLOCATION = config.TARGET_ALLOCATION

# Dashboard settings
DASHBOARD_TRADE_HISTORY_LIMIT = config.DASHBOARD_TRADE_HISTORY_LIMIT

# Logging settings
LOG_LEVEL = config.LOG_LEVEL
LOG_FILE = config.LOG_FILE
