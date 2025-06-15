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
        self.BASE_CURRENCY = os.getenv("BASE_CURRENCY", "USD")  # Base currency for trading pairs
        self.DECISION_INTERVAL_MINUTES = int(os.getenv("DECISION_INTERVAL_MINUTES", "60"))
        self.RISK_LEVEL = os.getenv("RISK_LEVEL", "medium")
        self.SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"

        # Portfolio settings
        self.MAX_TRADE_PERCENTAGE = float(os.getenv("MAX_TRADE_PERCENTAGE", "25"))

        # Target allocation settings
        self.TARGET_CRYPTO_ALLOCATION = float(os.getenv("TARGET_CRYPTO_ALLOCATION", "80"))
        self.TARGET_BASE_ALLOCATION = float(os.getenv("TARGET_BASE_ALLOCATION", os.getenv("TARGET_USD_ALLOCATION", "20")))  # Backward compatibility

        # Calculate individual crypto allocations based on trading pairs
        self.CRYPTO_ASSETS = [pair.split("-")[0] for pair in self.TRADING_PAIRS]
        self.CRYPTO_ASSETS = list(set(self.CRYPTO_ASSETS))  # Remove duplicates
        self.INDIVIDUAL_CRYPTO_ALLOCATION = self.TARGET_CRYPTO_ALLOCATION / len(self.CRYPTO_ASSETS) if self.CRYPTO_ASSETS else 0

        # Create target allocation dictionary
        self.TARGET_ALLOCATION = {asset: self.INDIVIDUAL_CRYPTO_ALLOCATION for asset in self.CRYPTO_ASSETS}
        self.TARGET_ALLOCATION[self.BASE_CURRENCY] = self.TARGET_BASE_ALLOCATION

        # Dashboard settings
        self.DASHBOARD_TRADE_HISTORY_LIMIT = int(os.getenv("DASHBOARD_TRADE_HISTORY_LIMIT", "10"))
        
        # Web Server Sync settings
        self.WEBSERVER_SYNC_ENABLED = os.getenv("WEBSERVER_SYNC_ENABLED", "false").lower() == "true"
        self.WEBSERVER_SYNC_PATH = os.getenv("WEBSERVER_SYNC_PATH", "/var/www/html/crypto-bot")
        
        # Logging settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/crypto_bot.log")
        
        # Enhanced Trading Strategy Settings
        self.CONFIDENCE_THRESHOLD_BUY = float(os.getenv("CONFIDENCE_THRESHOLD_BUY", "60"))
        self.CONFIDENCE_THRESHOLD_SELL = float(os.getenv("CONFIDENCE_THRESHOLD_SELL", "60"))
        self.CONFIDENCE_BOOST_TREND_ALIGNED = float(os.getenv("CONFIDENCE_BOOST_TREND_ALIGNED", "10"))
        self.CONFIDENCE_PENALTY_COUNTER_TREND = float(os.getenv("CONFIDENCE_PENALTY_COUNTER_TREND", "5"))
        
        # Technical Analysis Settings
        self.RSI_NEUTRAL_MIN = float(os.getenv("RSI_NEUTRAL_MIN", "45"))
        self.RSI_NEUTRAL_MAX = float(os.getenv("RSI_NEUTRAL_MAX", "55"))
        self.MACD_SIGNAL_WEIGHT = float(os.getenv("MACD_SIGNAL_WEIGHT", "0.4"))
        self.RSI_SIGNAL_WEIGHT = float(os.getenv("RSI_SIGNAL_WEIGHT", "0.3"))
        self.BOLLINGER_SIGNAL_WEIGHT = float(os.getenv("BOLLINGER_SIGNAL_WEIGHT", "0.3"))
        
        # Risk Management Settings
        self.RISK_HIGH_POSITION_MULTIPLIER = float(os.getenv("RISK_HIGH_POSITION_MULTIPLIER", "0.5"))
        self.RISK_MEDIUM_POSITION_MULTIPLIER = float(os.getenv("RISK_MEDIUM_POSITION_MULTIPLIER", "0.75"))
        self.RISK_LOW_POSITION_MULTIPLIER = float(os.getenv("RISK_LOW_POSITION_MULTIPLIER", "1.0"))
        
        # Trade Size Limits
        self.MIN_TRADE_AMOUNT = float(os.getenv("MIN_TRADE_AMOUNT", os.getenv("MIN_TRADE_USD", "10.0")))  # Backward compatibility
        self.MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", os.getenv("MAX_POSITION_SIZE_USD", "1000.0")))  # Backward compatibility
        
        # Push Notification Settings
        self.NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "false").lower() == "true"
        self.PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
        self.PUSHOVER_USER = os.getenv("PUSHOVER_USER")
    
    def get_trading_pairs(self) -> List[str]:
        """Get list of trading pairs"""
        return self.TRADING_PAIRS
    
    def get_crypto_assets(self) -> List[str]:
        """Get list of crypto assets from trading pairs"""
        return self.CRYPTO_ASSETS
    
    def get_base_currency(self) -> str:
        """Get base currency"""
        return self.BASE_CURRENCY
    
    def get_base_currency_symbol(self) -> str:
        """Get base currency symbol for display"""
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'CAD': 'C$',
            'AUD': 'A$'
        }
        return symbols.get(self.BASE_CURRENCY, self.BASE_CURRENCY)
    
    def format_currency(self, amount: float) -> str:
        """Format currency amount with appropriate symbol"""
        symbol = self.get_base_currency_symbol()
        return f"{symbol}{amount:.2f}"

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
BASE_CURRENCY = config.BASE_CURRENCY
DECISION_INTERVAL_MINUTES = config.DECISION_INTERVAL_MINUTES
RISK_LEVEL = config.RISK_LEVEL
SIMULATION_MODE = config.SIMULATION_MODE

# Portfolio settings
MAX_TRADE_PERCENTAGE = config.MAX_TRADE_PERCENTAGE

# Target allocation settings
TARGET_CRYPTO_ALLOCATION = config.TARGET_CRYPTO_ALLOCATION
TARGET_BASE_ALLOCATION = config.TARGET_BASE_ALLOCATION
TARGET_USD_ALLOCATION = config.TARGET_BASE_ALLOCATION  # Backward compatibility
CRYPTO_ASSETS = config.CRYPTO_ASSETS
INDIVIDUAL_CRYPTO_ALLOCATION = config.INDIVIDUAL_CRYPTO_ALLOCATION
TARGET_ALLOCATION = config.TARGET_ALLOCATION

# Dashboard settings
DASHBOARD_TRADE_HISTORY_LIMIT = config.DASHBOARD_TRADE_HISTORY_LIMIT

# Web Server Sync settings
WEBSERVER_SYNC_ENABLED = config.WEBSERVER_SYNC_ENABLED
WEBSERVER_SYNC_PATH = config.WEBSERVER_SYNC_PATH

# Logging settings
LOG_LEVEL = config.LOG_LEVEL
LOG_FILE = config.LOG_FILE

# Trade Size Limits (backward compatibility)
MIN_TRADE_USD = config.MIN_TRADE_AMOUNT
MAX_POSITION_SIZE_USD = config.MAX_POSITION_SIZE

# Push Notification Settings
NOTIFICATIONS_ENABLED = config.NOTIFICATIONS_ENABLED
PUSHOVER_TOKEN = config.PUSHOVER_TOKEN
PUSHOVER_USER = config.PUSHOVER_USER
