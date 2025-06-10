# AI-Powered Crypto Trading Bot

A Python-based cryptocurrency trading bot that uses Google Cloud Vertex AI LLMs to make trading decisions for Bitcoin, Ethereum, and Solana on Coinbase. This bot leverages the power of AI to analyze market trends, technical indicators, and historical data to make informed trading decisions.

## Features

### 🤖 AI-Powered Trading
- Connects to Coinbase Advanced Trade API for real-time data and trading
- Uses Google Cloud Vertex AI for sophisticated market analysis and trading decisions
- Supports multiple LLM models (Text-Bison, Gemini, PaLM)
- Supports Bitcoin (BTC), Ethereum (ETH), and Solana (SOL) trading with USD pairs
- Collects and analyzes historical market data with customizable timeframes
- Calculates technical indicators (RSI, MACD, Bollinger Bands, etc.)
- **Enhanced Active Trading Strategy** with lowered confidence thresholds for more frequent trades
- **Dynamic Risk Management** using position sizing instead of trade avoidance
- **Weighted Technical Analysis** with MACD (40%), RSI (30%), and Bollinger Bands (30%)
- **Narrowed RSI Ranges** (45-55 neutral zone) for more definitive signals

## Enhanced Trading Strategy Features

### 🎯 Active Trading Configuration
The bot now implements an enhanced trading strategy designed for more frequent and profitable trades:

#### Lowered Confidence Thresholds
- **Buy/Sell Threshold**: Reduced from 80% to 60% confidence for more active trading
- **Trend Alignment Bonus**: +10% confidence when multiple indicators align
- **Counter-Trend Penalty**: -5% confidence for signals against the trend
- **Result**: More trading opportunities while maintaining quality decisions

#### Weighted Technical Analysis
- **MACD (40% weight)**: Primary trend indicator for major market direction
- **RSI (30% weight)**: Momentum indicator with narrowed ranges (45-55 neutral)
- **Bollinger Bands (30% weight)**: Volatility and breakout detection
- **Smart Conflict Resolution**: Clear hierarchy when indicators disagree

#### Dynamic Risk Management
Instead of avoiding trades during high-risk periods, the bot now adjusts position sizes:
- **High Risk**: 50% position size (still trades but smaller amounts)
- **Medium Risk**: 75% position size
- **Low Risk**: 100% position size (full allocation)

#### Enhanced Portfolio Management
- **Target Allocation**: 80% crypto / 20% USD for optimal trading flexibility
- **Automatic Rebalancing**: Maintains target allocation when drift exceeds 5%
- **USD Buffer**: Ensures liquidity for buying opportunities

### 📊 Technical Indicator Improvements

#### RSI Analysis (Narrowed Ranges)
- **Oversold**: RSI < 45 (was 40) - Strong buy signal
- **Overbought**: RSI > 55 (was 60) - Strong sell signal  
- **Neutral Zone**: 45-55 (narrowed from 40-60)
- **Result**: More definitive buy/sell signals

#### MACD Priority System
- **Primary Trend Indicator**: Highest weight in decision making
- **Crossover Detection**: Identifies trend changes early
- **Histogram Analysis**: Confirms momentum strength
- **Trend Alignment**: Boosts confidence when other indicators agree

#### Bollinger Bands Strategy
- **Breakout Detection**: Distinguishes between breakouts and overextensions
- **Volume Confirmation**: Considers momentum for breakout validation
- **Mean Reversion**: Identifies oversold/overbought conditions

### ⚙️ Configuration Options

Add these settings to your `.env` file for enhanced trading:

```env
# Enhanced Trading Strategy Configuration
CONFIDENCE_THRESHOLD_BUY=60
CONFIDENCE_THRESHOLD_SELL=60
CONFIDENCE_BOOST_TREND_ALIGNED=10
CONFIDENCE_PENALTY_COUNTER_TREND=5

# Technical Analysis Settings
RSI_NEUTRAL_MIN=45
RSI_NEUTRAL_MAX=55
MACD_SIGNAL_WEIGHT=0.4
RSI_SIGNAL_WEIGHT=0.3
BOLLINGER_SIGNAL_WEIGHT=0.3

# Risk Management (Position Sizing)
RISK_HIGH_POSITION_MULTIPLIER=0.5
RISK_MEDIUM_POSITION_MULTIPLIER=0.75
RISK_LOW_POSITION_MULTIPLIER=1.0

# Trade Size Limits
MIN_TRADE_USD=10.0
MAX_POSITION_SIZE_USD=1000.0

# Portfolio Rebalancing
REBALANCE_THRESHOLD_PERCENT=5
REBALANCE_CHECK_INTERVAL_MINUTES=180
```

### 🚀 Performance Improvements

The enhanced strategy delivers:
- **More Trading Opportunities**: Lower thresholds mean more signals
- **Better Risk Management**: Position sizing instead of trade avoidance
- **Improved Decision Quality**: Weighted indicator analysis
- **Dynamic Portfolio**: Automatic rebalancing for optimal allocation
- **Consistent Activity**: Trades during all market conditions with appropriate sizing
- **Real-time monitoring** with live portfolio tracking and performance metrics
- **Bot status tracking** with uptime monitoring and operational status
- **Live UTC clock** with consistent timezone display across all timestamps
- **AI decision visualization** showing recent buy/sell/hold decisions with confidence levels
- **Direct Coinbase integration** with quick access links to Advanced Trade platform
- **Comprehensive activity log** with advanced filtering by action, asset, and time period
- **Portfolio allocation charts** with visual representation of asset distribution
- **Market data display** with real-time price updates and percentage changes
- **Responsive design** optimized for desktop and mobile viewing

### 🔍 Advanced Analytics
- Detailed logging and trade history for performance tracking
- Scheduled trading at configurable intervals (default: 60 minutes)
- AI-powered strategy analysis and improvement recommendations
- Backtesting module for strategy evaluation before live trading
- Performance tracking with portfolio value history and return calculations

### ☁️ Cloud Deployment Ready
- Includes automated setup scripts for AWS EC2 and Google Cloud deployment
- Supervisor process management for 24/7 operation
- Nginx web server configuration for dashboard hosting
- Automated data synchronization and backup capabilities

## Project Structure

```
AI-crypto-bot/
├── .env                    # Environment variables (API keys, secrets)
├── requirements.txt        # Python dependencies
├── config.py               # Configuration settings
├── main.py                 # Entry point for the bot
├── coinbase_client.py      # Coinbase API integration
├── llm_analyzer.py         # LLM-based analysis and decision making
├── trading_strategy.py     # Trading strategy implementation
├── data_collector.py       # Market data collection
├── backtesting.py          # Backtesting module for strategy evaluation
├── backtest_cli.py         # Command-line interface for backtesting
├── strategy_analyzer.py    # AI-powered strategy analysis and improvement
├── update_dashboard_links.sh # Dashboard symlink management script
├── reset_bot_data.sh       # Bot data reset utility script
├── data/                   # All persistent data (single source of truth)
│   ├── portfolio/          # Portfolio data and history
│   │   ├── portfolio.json  # Current portfolio state
│   │   ├── portfolio.json  # Current portfolio state
│   │   └── portfolio_history.csv # Historical portfolio values
│   ├── trades/             # Trade history and logs
│   │   └── trade_history.json # Complete trade history
│   ├── market_data/        # Market price snapshots
│   │   ├── BTC_USD_*.json  # Bitcoin price data
│   │   ├── ETH_USD_*.json  # Ethereum price data
│   │   └── SOL_USD_*.json  # Solana price data
│   ├── reports/            # Analysis and performance reports
│   │   └── *.json          # Strategy analysis reports
│   ├── config/             # Dashboard configuration
│   │   └── config.json     # Dashboard settings
│   └── cache/              # Temporary and cache files
│       ├── latest_decisions.json # Recent AI decisions
│       ├── trading_data.json     # Trading performance cache
│       ├── last_updated.txt      # Last update timestamp
│       └── bot_startup.json      # Bot startup time and status
├── dashboard/              # Web dashboard (UI only)
│   ├── static/             # HTML, CSS, JS files
│   │   ├── index.html      # Main dashboard page
│   │   └── analysis.html   # Analysis dashboard
│   └── images/             # Generated charts and visualizations
│       ├── portfolio_allocation.png
│       ├── portfolio_value.png
│       └── allocation_comparison.png
├── aws_setup/              # AWS deployment scripts
│   ├── README.md           # AWS deployment guide
│   └── setup_ec2.sh        # Automated setup script for EC2
├── gcp_setup/              # Google Cloud deployment scripts
│   ├── README.md           # Google Cloud deployment guide
│   └── setup_gce.sh        # Automated setup script for GCE
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── logger.py           # Logging functionality
│   ├── helpers.py          # Helper functions
│   ├── trade_logger.py     # Trade history logging
│   ├── strategy_evaluator.py # Strategy performance evaluation
│   └── dashboard_updater.py # Dashboard visualization updates
└── tests/                  # Unit tests
    ├── __init__.py
    ├── test_coinbase.py
    └── test_strategy.py
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Coinbase account with API access
- Google Cloud account with Vertex AI API enabled
- Google Cloud service account with Vertex AI permissions
- Basic understanding of cryptocurrency trading
- (Optional) Server in Google Cloud or AWS for 24/7 operation

### Installation

#### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/AI-crypto-bot.git
   cd AI-crypto-bot
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Configure Enhanced Trading Strategy**:
   Add these settings to your `.env` file:
   ```env
   # Enhanced Trading Strategy Configuration
   CONFIDENCE_THRESHOLD_BUY=60
   CONFIDENCE_THRESHOLD_SELL=60
   CONFIDENCE_BOOST_TREND_ALIGNED=10
   CONFIDENCE_PENALTY_COUNTER_TREND=5

   # Technical Analysis Settings
   RSI_NEUTRAL_MIN=45
   RSI_NEUTRAL_MAX=55
   MACD_SIGNAL_WEIGHT=0.4
   RSI_SIGNAL_WEIGHT=0.3
   BOLLINGER_SIGNAL_WEIGHT=0.3

   # Risk Management (Position Sizing)
   RISK_HIGH_POSITION_MULTIPLIER=0.5
   RISK_MEDIUM_POSITION_MULTIPLIER=0.75
   RISK_LOW_POSITION_MULTIPLIER=1.0

   # Trade Size Limits
   MIN_TRADE_USD=10.0
   MAX_POSITION_SIZE_USD=1000.0

   # Portfolio Rebalancing
   REBALANCE_THRESHOLD_PERCENT=5
   REBALANCE_CHECK_INTERVAL_MINUTES=180
   ```

6. **Run the bot**:
   ```bash
   python main.py
   ```

7. **Access the Dashboard** (if deployed with web server):
   ```bash
   # Local development
   http://localhost/crypto-bot/
   
   # Cloud deployment
   http://your-server-ip/crypto-bot/
   ```

## Cloud Deployment Options

For production deployment, use the automated setup scripts in the dedicated directories:

- **AWS EC2 Deployment**: [AWS Deployment Guide](aws_setup/README.md)
- **Google Cloud Deployment**: [Google Cloud Deployment Guide](gcp_setup/README.md)

These guides provide detailed instructions for setting up the bot on cloud platforms for 24/7 operation.

## Web Dashboard Features

The bot includes a comprehensive web dashboard that provides real-time monitoring and control capabilities:

### 🖥️ Dashboard Overview
- **Live Portfolio Tracking**: Real-time portfolio value, returns, and asset allocation
- **Bot Status Monitoring**: Uptime tracking, process information, and operational status
- **Market Data Display**: Current prices with 1h, 4h, 1d, and 5d percentage changes
- **AI Decision Insights**: Recent buy/sell/hold decisions with confidence levels and reasoning

### ⏰ Time & Status Features
- **Live UTC Clock**: Real-time clock in the header showing server time
- **Bot Uptime Display**: Shows how long the bot has been running since last restart
- **Consistent Timestamps**: All times displayed in 24-hour UTC format for clarity
- **Next Decision Timer**: Countdown to the next trading decision

### 🔗 Coinbase Integration
- **Direct Trading Links**: Quick access buttons to Coinbase Advanced Trade for each asset
- **Seamless Workflow**: From AI analysis directly to live market data and trading
- **Asset-Specific URLs**: Direct links to BTC-USD, ETH-USD, and SOL-USD pairs

### 📊 Activity Log
- **Complete Trading History**: Comprehensive log of all buy/sell/hold decisions
- **Advanced Filtering**: Filter by action type, asset, or time period
- **Detailed Information**: Timestamps, prices, amounts, confidence levels, and AI reasoning
- **Real-time Updates**: Activity log refreshes automatically with new decisions

### 🎨 User Experience
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Professional Interface**: Clean, modern design optimized for trading workflows
- **Color-coded Actions**: Visual indicators for buy (green), sell (red), and hold (gray) decisions
- **Interactive Elements**: Hover effects, expandable text, and smooth animations

### 📱 Dashboard Access
Once deployed, access your dashboard at:
- **Local Development**: `http://localhost/crypto-bot/`
- **Cloud Deployment**: `http://your-server-ip/crypto-bot/`

## Web Server Sync Configuration

The bot includes a centralized web server sync mechanism that can be enabled or disabled via environment variables.

### Configuration

Add these variables to your `.env` file:

```bash
# Web Server Sync Configuration
WEBSERVER_SYNC_ENABLED=true                    # Enable/disable web server sync
WEBSERVER_SYNC_PATH=/var/www/html/crypto-bot   # Path to web server directory
```

### How It Works

- **Single Sync Point**: All web server synchronization happens in one place in `main.py`
- **Configurable**: Can be completely disabled by setting `WEBSERVER_SYNC_ENABLED=false`
- **Automatic**: Syncs after each trading cycle and every 30 minutes
- **Efficient**: Uses symlinks for data files, copies static files only when needed

### Manual Sync

You can manually sync the dashboard to the web server:

```bash
# Manual sync (respects WEBSERVER_SYNC_ENABLED setting)
python3 sync_webserver.py

# Force sync (ignores WEBSERVER_SYNC_ENABLED setting)
python3 sync_webserver.py  # and choose 'y' when prompted
```

### Sync Behavior

When enabled, the bot will:
1. **After each trading cycle**: Update local data, then sync to web server
2. **Every 30 minutes**: Scheduled sync to ensure web server is up-to-date
3. **On startup**: Initial sync after dashboard initialization

When disabled:
- Only local dashboard data is updated
- No web server operations are performed
- Useful for development or when running without a web server

### Utility Scripts

The bot includes several utility scripts for maintenance and management:

- **`sync_webserver.py`**: Manual web server sync script
- **`reset_bot_data.sh`**: Resets bot data and portfolio state (use with caution)
- **`cleanup_logs.sh`**: Cleans up old log files
- **`cleanup_old_files.sh`**: Removes old market data files

### Strategy Analysis
- **`strategy_analyzer.py`**: Analyzes trading performance and provides AI-powered improvement recommendations
  ```bash
  # Analyze the last 30 days of trading performance
  python strategy_analyzer.py
  
  # Analyze a specific number of days
  python strategy_analyzer.py --days 60
  ```

### Backtesting
- **`backtest_cli.py`**: Command-line interface for backtesting trading strategies
  ```bash
  # Run backtesting with default parameters
  python backtest_cli.py
  ```

## API Key Setup

The bot uses the Coinbase Advanced Trade API, which requires specific API credentials:

1. **Generate API Keys**:
   - Log in to your Coinbase account
   - Go to Settings > API > Advanced Trade API
   - Create a new API key with appropriate permissions (View and Trade)

2. **API Key Format**:
   The Coinbase Advanced Trade API uses a specific format for credentials:
   ```
   # API Key format: organizations/{org_id}/apiKeys/{key_id}
   COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
   
   # API Secret format: EC private key in PEM format
   COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----\nYOUR PRIVATE KEY\n-----END EC PRIVATE KEY-----\n
   ```

3. **Update your .env file** with these credentials

## Portfolio-Based Trading Strategy

The bot implements a sophisticated portfolio-based trading strategy that allows you to start with existing cryptocurrency holdings rather than USD.

### How It Works

1. **Initial Portfolio Setup**:
   - You specify your initial BTC and ETH amounts in the configuration
   - The bot tracks your portfolio value and performance over time
   - All holdings and trades are stored in a persistent portfolio file

2. **Dynamic Trade Sizing**:
   - Trade sizes are proportional to the AI's confidence level
   - Higher confidence leads to larger position sizes
   - The MAX_TRADE_PERCENTAGE setting limits how much of your holdings can be traded at once

3. **Portfolio Rebalancing**:
   - The bot can automatically maintain your target asset allocation (e.g., 40% BTC, 40% ETH, 20% USD)
   - Rebalancing occurs when allocations drift beyond a configurable threshold
   - This ensures your portfolio stays aligned with your investment strategy

4. **Performance Tracking**:
   - The bot tracks your portfolio's total value in USD
   - Performance is measured against your initial holdings
   - Detailed trade history and performance metrics are logged

### Configuration

Configure your portfolio strategy in the `.env` file:

```
# Portfolio settings
INITIAL_BTC_AMOUNT=0.01       # Your starting BTC amount
INITIAL_ETH_AMOUNT=0.15       # Your starting ETH amount
PORTFOLIO_REBALANCE=true      # Enable automatic portfolio rebalancing
MAX_TRADE_PERCENTAGE=25       # Maximum percentage of holdings to trade at once
```

### Benefits

- **Start with existing crypto**: No need to convert to USD first
- **Efficient capital use**: Reinvests proceeds from sales into new opportunities
- **Risk management**: Limits exposure through percentage-based position sizing
- **Automated rebalancing**: Maintains your desired asset allocation
- **Performance tracking**: Monitors your portfolio's growth over time

## Strategy Analysis and Improvement

The bot includes a dedicated strategy analyzer that uses AI to evaluate trading performance and suggest improvements.

### How to Use the Strategy Analyzer

The `strategy_analyzer.py` script feeds historical performance data to the LLM for analysis and recommendations:

```bash
# Analyze the last 30 days of trading performance (default)
python strategy_analyzer.py

# Analyze a specific number of days
python strategy_analyzer.py --days 60
```

### What the Analyzer Provides

The strategy analyzer generates a comprehensive report with:

1. **Performance Analysis**: Detailed evaluation of your trading strategy's effectiveness
2. **Pattern Recognition**: Identification of patterns in successful and unsuccessful trades
3. **Strategic Recommendations**: Specific suggestions to improve your trading strategy
4. **Parameter Adjustments**: Recommended changes to risk levels, trade sizes, etc.
5. **Market Triggers**: Conditions that should prompt strategy adjustments

### Using the Analysis

Analysis reports are saved to the `reports/` directory as JSON files with timestamps. You can:

1. Review the recommendations in the terminal output
2. Examine the detailed analysis in the JSON report
3. Implement suggested parameter adjustments in your `.env` file
4. Modify trading logic based on the AI's recommendations

This creates a feedback loop where your trading strategy continuously improves based on real performance data and AI analysis.
