import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Coinbase API configuration
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")

# Google Cloud configuration
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# LLM configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "vertex_ai")  # vertex_ai, palm, gemini
LLM_MODEL = os.getenv("LLM_MODEL", "text-bison@002")  # text-bison@002, gemini-pro, etc.
LLM_LOCATION = os.getenv("LLM_LOCATION", "us-central1")  # Google Cloud region

# Trading parameters
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "BTC-USD,ETH-USD").split(",")
MAX_INVESTMENT_PER_TRADE_USD = float(os.getenv("MAX_INVESTMENT_PER_TRADE_USD", "100"))
RISK_LEVEL = os.getenv("RISK_LEVEL", "medium")  # low, medium, high
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "False").lower() == "true"

# Trading strategy parameters
ANALYSIS_TIMEFRAME = "1h"  # 1h, 4h, 1d
DECISION_INTERVAL_MINUTES = 60  # How often to make trading decisions

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "trading_bot.log"
