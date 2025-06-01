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
MAX_INVESTMENT_PER_TRADE_USD = float(os.getenv("MAX_INVESTMENT_PER_TRADE_USD", "100"))
RISK_LEVEL = os.getenv("RISK_LEVEL", "medium")  # low, medium, high
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/crypto_bot.log")
