"""
Configuration settings for the crypto trading bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Coinbase API credentials
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")

# Google Cloud settings
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# LLM settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "vertex")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")  # Updated to use Gemini Flash
LLM_LOCATION = os.getenv("LLM_LOCATION", "us-central1")

# Trading settings
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "BTC-USD,ETH-USD").split(",")
DECISION_INTERVAL_MINUTES = int(os.getenv("DECISION_INTERVAL_MINUTES", "60"))
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"

# Risk settings
RISK_LEVEL = os.getenv("RISK_LEVEL", "medium")  # low, medium, high, hybrid
RISK_WEIGHTS = {
    "low": float(os.getenv("RISK_WEIGHT_LOW", "0.0")),
    "medium": float(os.getenv("RISK_WEIGHT_MEDIUM", "0.5")),
    "high": float(os.getenv("RISK_WEIGHT_HIGH", "0.5"))
}

# Portfolio settings
PORTFOLIO_REBALANCE = os.getenv("PORTFOLIO_REBALANCE", "true").lower() == "true"  # Whether to rebalance portfolio
MAX_TRADE_PERCENTAGE = float(os.getenv("MAX_TRADE_PERCENTAGE", "25"))  # Max percentage of holdings to trade at once

# Target allocation settings
TARGET_CRYPTO_ALLOCATION = float(os.getenv("TARGET_CRYPTO_ALLOCATION", "80"))  # Percentage for all crypto combined
TARGET_USD_ALLOCATION = float(os.getenv("TARGET_USD_ALLOCATION", "20"))  # Percentage for USD

# Calculate individual crypto allocations based on trading pairs
CRYPTO_ASSETS = [pair.split("-")[0] for pair in TRADING_PAIRS]
CRYPTO_ASSETS = list(set(CRYPTO_ASSETS))  # Remove duplicates
INDIVIDUAL_CRYPTO_ALLOCATION = TARGET_CRYPTO_ALLOCATION / len(CRYPTO_ASSETS) if CRYPTO_ASSETS else 0

# Create target allocation dictionary
TARGET_ALLOCATION = {asset: INDIVIDUAL_CRYPTO_ALLOCATION for asset in CRYPTO_ASSETS}
TARGET_ALLOCATION["USD"] = TARGET_USD_ALLOCATION

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/crypto_bot.log")
