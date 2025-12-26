# 🤖 AI Crypto Trading Bot

An advanced multi-strategy cryptocurrency trading bot that combines AI analysis with traditional technical indicators for intelligent trading decisions on Coinbase Advanced Trade.

## 🎯 **Core Philosophy: Adaptive Multi-Strategy Trading**

This bot uses a sophisticated **multi-strategy framework** that adapts to market conditions:
- **4 Parallel Strategies**: LLM AI analysis, trend following, mean reversion, and momentum trading
- **Market Regime Detection**: Automatically identifies trending, ranging, or volatile market conditions
- **Adaptive Strategy Prioritization**: Different strategies take priority based on current market regime
- **Phase 3 Enhancements**: News sentiment analysis and volatility assessment integration

## ✨ **Key Features**

### 🧠 **Multi-Strategy Decision Making**
- **Adaptive Strategy Manager**: Hierarchical decision making with 4 parallel strategies
- **Market Regime Detection**: Automatically identifies trending, ranging, or volatile conditions
- **Strategy Prioritization**: Different strategies take priority based on market regime:
  - **Trending Markets**: Trend following → Momentum → LLM → Mean reversion
  - **Ranging Markets**: Mean reversion → LLM → Momentum → Trend following  
  - **Volatile Markets**: LLM → Mean reversion → Trend following → Momentum
- **Confidence Thresholds**: Adaptive thresholds based on market conditions and strategy type

### 📊 **Phase 3 Enhanced Analysis**
- **News Sentiment Integration**: Real-time cryptocurrency news sentiment analysis
- **Volatility Assessment**: Market volatility analysis affecting strategy weights
- **Advanced LLM Analysis**: Google's Gemini 3.0 Flash for comprehensive market analysis
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Performance Tracking**: Historical strategy performance with 64,650+ decisions tracked

### 🎯 **Intelligent Trading Strategy**
- **Hierarchical Decision Making**: First strategy to meet confidence threshold executes
- **Dynamic Position Sizing**: Trade sizes adapt to confidence and market conditions
- **Capital Management**: Sophisticated EUR reserve management (12% target allocation)
- **Safety Limits**: Minimum €15 EUR balance, maximum 50% EUR usage per trade

### 📱 **Push Notifications**
- **Real-time Trade Alerts**: Instant notifications for BUY/SELL executions
- **Error Notifications**: Critical error alerts with context
- **Portfolio Summaries**: Daily portfolio performance updates
- **Bot Status Updates**: Startup, shutdown, and status notifications

### 🛡️ **Risk Management**
- **Dual-Layer System**: Static risk configuration + dynamic market assessment
- **Confidence Thresholds**: 55% minimum confidence for BUY/SELL decisions
- **Position Sizing**: Risk-adjusted trade sizes (HIGH=50% reduction, MEDIUM=25%, LOW=0%)
- **Market Volatility**: Real-time assessment (high/medium/low) affects trading decisions
- **Balance Protection**: Maintains minimum balances for continued trading
- **Diversification**: Prevents over-concentration in any single asset

📚 **[Complete Risk Management Guide →](RISK_MANAGEMENT.md)**

### 📱 **Professional Dashboard**
- **Real-time Portfolio Tracking**: Live EUR values and allocations
- **Comprehensive AI Analysis**: Detailed reasoning for each trade decision with 4 analysis sections
- **Performance Metrics**: P&L tracking, win rates, portfolio growth
- **Market Overview**: Current prices, trends, and technical indicators

## 🧪 **Test Coverage & Quality Assurance**

### **📊 Test Implementation Progress**

```
Phase 1 (Critical Components):     ████████████████████ 100% (5/5)
Phase 2 (Core Functionality):     ████████░░░░░░░░░░░░  20% (1/5)
Phase 3 (Integration & E2E):      ░░░░░░░░░░░░░░░░░░░░  0% (0/5)
Phase 4 (Specialized Testing):    ░░░░░░░░░░░░░░░░░░░░  0% (0/7)

Overall Test Suite Progress:       ████████████░░░░░░░░ 31.8% (7/22)
```

### **✅ Completed Tests**
- **✅ Configuration Management** (`test_config.py`) - **100% coverage** - 37 tests
  - Environment variable parsing and validation
  - Trading pairs and allocation calculations
  - Risk management settings
  - Backward compatibility

- **✅ Coinbase Client** (`test_coinbase_client.py`) - **53% coverage** - 38 tests
  - Client initialization and credential validation
  - Rate limiting and error handling
  - Account operations and balance retrieval
  - Market data operations and price fetching
  - Trading operations and order placement
  - Precision handling for different trading pairs
  - Notification integration and error recovery

- **✅ Trading Strategy** (`test_trading_strategy.py`) - **Core functionality** - 14 tests
  - Strategy initialization and configuration
  - Trading decision logic with technical indicators
  - Risk management and confidence thresholds
  - Position sizing calculations
  - Portfolio management operations
  - Error handling and edge cases

- **✅ Risk Management** (`test_risk_management.py`) - **Comprehensive coverage** - 32 tests
  - Risk level configuration and multipliers
  - Confidence threshold enforcement
  - Balance and safety checks
  - Smart trading limits and portfolio protection
  - Position sizing with risk management
  - Confidence adjustments based on technical indicators
  - Integrated risk scenarios and error handling

- **✅ Portfolio Management** (`test_portfolio.py`) - **Complete coverage** - 41 tests
  - Portfolio initialization and loading from multiple sources
  - Portfolio validation and data structure integrity
  - Portfolio saving and persistence across instances
  - Portfolio value calculations and price updates
  - Asset allocation calculations and performance metrics
  - Trade execution and portfolio updates
  - Exchange data synchronization and integration
  - Portfolio rebalancing calculations and actions
  - Error handling and edge case management
  - Large number precision and concurrent access safety
  - Rate limiting and error handling
  - Account operations and balance retrieval
  - Market data operations and price fetching
  - Trading operations and order placement
  - Precision handling for different trading pairs
  - Notification integration and error recovery

- **✅ LLM Analyzer** (`test_llm_analyzer.py`) - **100% coverage** - 26 tests
  - Initialization and Google Cloud authentication
  - Vertex AI provider integration and API calls
  - Market data analysis and decision generation
  - Technical indicator processing and prompt creation
  - Response parsing and JSON handling
  - Trading decision making (BUY/SELL/HOLD signals)
  - Error handling and edge cases
  - Configuration validation and parameter handling

### **🎉 Phase 1 Complete!**
All critical components now have comprehensive test coverage.

### **🎉 LLM Analyzer Complete!**
First Phase 2 component with 100% test coverage and 26 comprehensive tests.

### **📋 Next Priority Tests (Phase 2)**
- **📋 Data Collector** (`test_data_collector.py`)
- **📋 Dashboard Updater** (`test_dashboard_updater.py`)
- **📋 Notification Service** (`test_notification_service.py`)
- **📋 Trade Logger** (`test_trade_logger.py`)

### **🎯 Quality Metrics**
- **Code Coverage Target**: 90%+ for unit tests
- **Current Coverage**: 100% (config), 53% (coinbase_client), 100% (llm_analyzer), Comprehensive (core modules)
- **Test Execution Time**: <1 second per module
- **Test Categories**: Unit, Integration, E2E, Performance, Security

📚 **[Complete Test Documentation →](tests/README.md)**

## 📊 **Current Status**

### **Active Trading Pairs**
- **BTC-EUR**: Bitcoin trading against Euro
- **ETH-EUR**: Ethereum trading against Euro
- **SOL**: Held but not actively traded (legacy position)

### **Portfolio Composition** (as of latest run)
- **BTC**: 0.00215666 (~€162.50)
- **ETH**: 0.01527914 (~€38.50)
- **SOL**: 0.042109793 (~€8.00) - *Legacy holding*
- **EUR**: €15.38 (6.9% allocation)
- **Total Value**: €224.37

### **Strategy Performance**
- **64,650+ Trading Decisions** tracked and analyzed
- **Multi-Strategy Framework** with adaptive market regime detection
- **Live Trading Mode** with real-time portfolio synchronization

## 🚀 **Quick Start**

### Prerequisites
- Python 3.8+
- Coinbase Advanced Trade account
- Google Cloud account (for AI analysis)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-crypto-bot
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. **Deploy dashboard** (optional)
   ```bash
   python3 deploy_dashboard.py
   ```

6. **Run the bot**
   ```bash
   python3 main.py
   ```

### ☁️ **Cloud Deployment**
For production deployment on cloud platforms, use the automated setup scripts:
- **AWS EC2**: See [`aws_setup/README.md`](aws_setup/README.md) for complete AWS deployment guide
- **Google Cloud**: See [`gcp_setup/README.md`](gcp_setup/README.md) for complete GCP deployment guide

Both include automated scripts for dependencies, web server setup, and service configuration.

## ⚙️ **Configuration**

### **Core Settings** (`.env`)

```env
# Trading Configuration
BASE_CURRENCY=EUR                    # Base currency for trading
TRADING_PAIRS=BTC-EUR,ETH-EUR        # Trading pairs (SOL removed from active trading)
RISK_LEVEL=HIGH                      # LOW, MEDIUM, HIGH
SIMULATION_MODE=False                # Set to True for paper trading

# Multi-Strategy Thresholds
CONFIDENCE_THRESHOLD_BUY=55          # Minimum confidence for BUY orders
CONFIDENCE_THRESHOLD_SELL=55         # Minimum confidence for SELL orders

# Trade Size Limits
MIN_TRADE_AMOUNT=5.0                # Minimum trade size (EUR)
MAX_POSITION_SIZE_PERCENT=75        # Maximum single trade size (% of EUR balance)

# Capital Management Strategy
TARGET_EUR_ALLOCATION=12            # Target EUR allocation %
MIN_EUR_RESERVE=15.0                # Minimum EUR reserve
MAX_EUR_USAGE_PER_TRADE=50.0        # Maximum EUR usage per trade %
```

### **API Configuration**

```env
# Coinbase Advanced Trade
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_private_key

# Google Cloud (for AI analysis)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
LLM_MODEL=gemini-3-flash-preview

# Push Notifications (Pushover)
NOTIFICATIONS_ENABLED=true
PUSHOVER_TOKEN=your_pushover_app_token
PUSHOVER_USER=your_pushover_user_key
```

### **Push Notification Setup**

1. **Download Pushover App**
   - iOS: [App Store](https://apps.apple.com/app/pushover-notifications/id506088175)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=net.superblock.pushover)

2. **Create Pushover Account**
   - Sign up at [pushover.net](https://pushover.net)
   - Note your User Key from the dashboard

3. **Create Application**
   - Go to [Create Application](https://pushover.net/apps/build)
   - Name: "AI Crypto Bot" (or your preference)
   - Copy the API Token/Key

4. **Configure Environment**
   ```env
   NOTIFICATIONS_ENABLED=true
   PUSHOVER_TOKEN=your_app_api_token_here
   PUSHOVER_USER=your_user_key_here
   ```

5. **Test Notifications**
   ```bash
   python3 test_notifications.py
   ```

## 🎛️ **Trading Strategy Details**

### **Multi-Strategy Framework**
Unlike traditional single-strategy bots, this bot employs a sophisticated multi-strategy approach:

1. **Market Regime Detection**: Analyzes 24h price changes and Bollinger Band width to classify markets as:
   - **Trending**: Strong directional movement (>2% daily change)
   - **Ranging**: Sideways movement with low volatility
   - **Volatile**: High volatility with uncertain direction

2. **Strategy Hierarchy**: Based on market regime, strategies are prioritized:
   - **Trend Following**: Momentum-based signals for trending markets
   - **Mean Reversion**: Counter-trend signals for ranging markets  
   - **Momentum**: Short-term momentum indicators
   - **LLM Strategy**: AI-powered analysis with news sentiment integration

3. **Adaptive Confidence Thresholds**: Each strategy has different confidence requirements based on market conditions:
   - Lower thresholds for favored strategies in their optimal market regime
   - Higher thresholds for strategies working against market conditions

### **Decision Process**
```
Market Data → Regime Detection → Strategy Prioritization → Confidence Check → Position Sizing → Execute Trade
```

### **Capital Management**
- **Target EUR Allocation**: 12% (€15+ minimum reserve)
- **Maximum Trade Size**: 50% of available EUR balance
- **Position Sizing**: Scales with strategy confidence and market conditions
- **Risk Management**: Integrated position multipliers based on market volatility

## 📊 **Dashboard Features**

### **Portfolio Overview**
- **Total Value**: Real-time EUR portfolio value
- **Asset Allocation**: Current vs target percentages
- **Multi-Strategy Status**: Current market regime and active strategy priorities
- **Performance Metrics**: P&L, returns, win rates

### **Enhanced AI Analysis**
- **Comprehensive Trade Details**: 4-section analysis for each trade
  - **AI Reasoning**: Detailed bullet-point market analysis
  - **Technical Analysis**: RSI, MACD, Bollinger Bands with color coding
  - **Bot Decision Process**: Confidence checks and risk management
  - **Market Context**: Price trends, conditions, and analysis quality
- **Recent Decisions**: Latest BUY/SELL/HOLD recommendations
- **Confidence Levels**: AI confidence scores (0-100%)
- **Strategy Performance**: Individual strategy success rates and performance metrics

### **Live Logs Dashboard**
- **Real-time Log Monitoring**: Last 30 lines of bot activity
- **Auto-refresh**: Updates every 5 seconds automatically
- **Color-coded Log Levels**: ERROR (red), WARNING (yellow), INFO (blue), DEBUG (gray)
- **Live Status Indicators**: Bot operational status and last update time
- **Interactive Controls**: Manual refresh, auto-scroll toggle, clear logs

### **Market Data**
- **Live Prices**: Real-time cryptocurrency prices
- **Price Changes**: 1h, 4h, 24h, 5d percentage changes
- **Trading Status**: Current bot status and next decision time

## 🏗️ **Project Structure**

```
AI-crypto-bot/
├── main.py                 # Main bot entry point
├── config.py              # Configuration management
├── coinbase_client.py     # Coinbase API client
├── llm_analyzer.py        # AI analysis engine
├── data_collector.py      # Market data collection
├── strategies/            # Multi-strategy framework
│   ├── adaptive_strategy_manager.py
│   ├── llm_strategy.py
│   ├── trend_following.py
│   ├── mean_reversion.py
│   ├── momentum.py
│   └── base_strategy.py
├── utils/                 # Utility modules
│   ├── dashboard_updater.py
│   ├── webserver_sync.py
│   ├── logger.py
│   ├── portfolio.py
│   ├── capital_manager.py
│   ├── news_sentiment.py
│   ├── volatility_analyzer.py
│   └── ...
├── dashboard/             # Web dashboard
│   ├── static/
│   └── images/
├── aws_setup/             # AWS deployment scripts
│   ├── setup_ec2.sh
│   ├── iam_policy.json
│   ├── cloudwatch_setup.sh
│   └── create_secrets.sh
├── gcp_setup/             # Google Cloud deployment scripts
│   ├── setup_gce.sh
│   └── README.md
├── data/                  # Runtime data
├── logs/                  # Application logs
├── .env                   # Environment variables
└── requirements.txt       # Dependencies
```

## 🕒 **Persistent Uptime Tracking**

The bot features intelligent uptime management that distinguishes between restarts and stops:

### **Uptime Behavior**
- **Restarts**: Configuration changes, updates, or service restarts **preserve uptime**
- **Explicit Stops**: Manual stops or `systemctl stop` **reset uptime**
- **Crash Recovery**: Automatic restarts after crashes **preserve uptime**

### **Bot Management**
Use the included bot manager for proper uptime handling:

```bash
# Start the bot
python3 bot_manager.py start

# Restart (preserves uptime) - for config changes, updates
python3 bot_manager.py restart

# Stop (resets uptime) - for maintenance, shutdown
python3 bot_manager.py stop

# Check status and total uptime
python3 bot_manager.py status
```

### **Dashboard Display**
- **Total Uptime**: Cumulative uptime across all sessions
- **Restart Count**: Number of restarts since original start
- **Professional Metrics**: True operational uptime tracking

## 🔧 **Advanced Configuration**

### **Multi-Strategy Settings**
```env
# Strategy Confidence Thresholds (per market regime)
# Trending Markets
TREND_FOLLOWING_BUY_THRESHOLD=55
MOMENTUM_BUY_THRESHOLD=60
LLM_STRATEGY_BUY_THRESHOLD=65
MEAN_REVERSION_BUY_THRESHOLD=75

# Ranging Markets  
MEAN_REVERSION_BUY_THRESHOLD=60
LLM_STRATEGY_BUY_THRESHOLD=65
MOMENTUM_BUY_THRESHOLD=70
TREND_FOLLOWING_BUY_THRESHOLD=75

# Volatile Markets
LLM_STRATEGY_BUY_THRESHOLD=70
MEAN_REVERSION_BUY_THRESHOLD=75
TREND_FOLLOWING_BUY_THRESHOLD=80
MOMENTUM_BUY_THRESHOLD=80
```

### **Risk Management**
```env
# Position Sizing Multipliers
RISK_HIGH_POSITION_MULTIPLIER=0.5    # 50% position reduction for high risk
RISK_MEDIUM_POSITION_MULTIPLIER=0.75 # 25% position reduction for medium risk
RISK_LOW_POSITION_MULTIPLIER=1.0     # No reduction for low risk

# Technical Analysis Weights
RSI_SIGNAL_WEIGHT=0.3               # RSI indicator weight
MACD_SIGNAL_WEIGHT=0.4              # MACD indicator weight
BOLLINGER_SIGNAL_WEIGHT=0.3         # Bollinger Bands weight
```

### **Dashboard Customization**
```env
# Web Interface
WEBSERVER_SYNC_ENABLED=true         # Enable web dashboard
WEBSERVER_SYNC_PATH=/var/www/html/crypto-bot  # Dashboard path
DASHBOARD_TRADE_HISTORY_LIMIT=10    # Number of recent trades to show
```

## 📈 **Performance Optimization**

### **Confidence-Based Trading**
- **High Confidence (80%+)**: Larger position sizes, immediate execution
- **Medium Confidence (60-79%)**: Standard position sizes
- **Low Confidence (<60%)**: No trade execution (HOLD)

### **Dynamic Position Sizing**
- **Over-allocated assets**: Smaller SELL positions to maintain balance
- **Under-allocated assets**: Larger BUY positions when EUR is available
- **High EUR allocation**: Larger BUY positions to deploy cash
- **Low EUR allocation**: Smaller BUY positions to preserve liquidity

### **Strategy Performance Tracking**
- **64,650+ Decisions Tracked**: Comprehensive historical performance data
- **Individual Strategy Metrics**: Success rates and performance per strategy
- **Market Regime Analysis**: Strategy effectiveness in different market conditions
- **Adaptive Learning**: Strategy weights adjust based on historical performance

## 🛠️ **Maintenance & Monitoring**

### **Log Files**
- **Main Log**: `logs/crypto_bot.log` - General bot activity
- **Trade Log**: `data/trades/trade_history.json` - All executed trades
- **Decision Log**: `data/cache/latest_decisions.json` - Recent AI decisions

### **Data Files**
- **Portfolio**: `data/portfolio/portfolio.json` - Current holdings
- **Market Data**: `data/*_EUR_*.json` - Historical price and analysis data
- **Configuration**: `data/config/` - Runtime configuration snapshots

### **Health Checks**
- **Dashboard Status**: Green badge indicates healthy operation
- **EUR Balance**: Warning if below €50 minimum
- **API Connectivity**: Automatic retry on connection issues
- **AI Analysis**: Fallback to HOLD if analysis fails

## 🚨 **Safety Features**

### **Simulation Mode**
Test strategies without real money:
```env
SIMULATION_MODE=True
```

### **Emergency Stops**
- **Insufficient Balance**: Stops BUY orders if EUR < €15
- **API Failures**: Graceful degradation with error logging
- **Invalid Decisions**: Defaults to HOLD on analysis errors

### **Portfolio Protection**
- **Minimum Holdings**: Prevents selling below minimum thresholds
- **Maximum Cash**: Limits EUR allocation based on target settings
- **Trade Size Limits**: €5 minimum, maximum 50% EUR usage per trade

## 🔄 **Deployment**

### **Local Deployment**

#### **Systemd Service**
```bash
# Copy service file
sudo cp crypto-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot
```

#### **Dashboard Deployment**
```bash
# Deploy dashboard to web server
python3 deploy_dashboard.py
```

### **☁️ Cloud Deployment**

#### **🚀 AWS EC2 Deployment**

**1. Launch EC2 Instance**
- Choose Amazon Linux 2023 AMI
- Select t2.medium or better for production
- Configure security groups:
  - SSH access (port 22)
  - HTTP access (port 80) for dashboard

**2. Connect and Setup**
```bash
# Connect to instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Clone repository
git clone https://github.com/schmidb/AI-crypto-bot.git
cd AI-crypto-bot

# Run setup script
bash aws_setup/setup_ec2.sh
```

**3. Configure and Start**
```bash
# Edit configuration
nano .env

# Start service
sudo systemctl start crypto-bot
sudo systemctl enable crypto-bot

# Check status
sudo systemctl status crypto-bot
sudo journalctl -u crypto-bot -f
```

**4. Access Dashboard**
```
http://your-ec2-ip/crypto-bot/
```

#### **🌐 Google Cloud Deployment**

**1. Create VM Instance**
- Navigate to Compute Engine > VM instances
- Choose e2-medium or better
- Select Debian/Ubuntu boot disk
- Allow HTTP/HTTPS traffic
- Add firewall rule for port 80

**2. Connect and Setup**
```bash
# Connect via SSH
gcloud compute ssh your-instance-name --zone=your-zone

# Clone repository
git clone https://github.com/schmidb/AI-crypto-bot.git
cd AI-crypto-bot

# Run setup script
bash gcp_setup/setup_gce.sh
```

**3. Configure and Start**
```bash
# Edit configuration
nano .env

# Check service status
sudo supervisorctl status crypto-bot

# View logs
tail -f /var/log/crypto-bot/crypto-bot.log

# Restart if needed
sudo supervisorctl restart crypto-bot
```

**4. Access Dashboard**
```
http://your-vm-ip/crypto-bot/
```

#### **🔐 Security Configuration**

**AWS IAM Policy** (for CloudWatch integration):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

**GCP Firewall Rules**:
```bash
# Allow HTTP traffic for dashboard
gcloud compute firewall-rules create allow-http-crypto-bot \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP access to crypto bot dashboard"
```

## 📞 **Support & Troubleshooting**

### **Common Issues**

**Bot not trading:**
- Check EUR balance (minimum €15 required)
- Verify AI confidence meets 55% threshold
- Confirm API keys are valid

**Dashboard not updating:**
- Check webserver sync settings
- Verify file permissions
- Restart bot if needed

**Low performance:**
- Review confidence thresholds
- Check market conditions
- Analyze recent AI decisions in dashboard

### **Getting Help**
1. Check log files for error messages
2. Review dashboard for status indicators
3. Verify configuration settings
4. Test in simulation mode first

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ **Disclaimer**

This software is for educational and research purposes. Cryptocurrency trading involves substantial risk of loss. Past performance does not guarantee future results. Use at your own risk and never invest more than you can afford to lose.

---

**Built with ❤️ for intelligent cryptocurrency trading**
