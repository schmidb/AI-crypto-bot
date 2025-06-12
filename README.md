# 🤖 AI Crypto Trading Bot

An intelligent cryptocurrency trading bot that uses AI analysis to make data-driven trading decisions on Coinbase Advanced Trade.

## 🎯 **Core Philosophy: AI-First Trading**

This bot prioritizes **AI-driven market analysis** over rigid portfolio rebalancing, allowing for:
- **Market-responsive trading** based on technical indicators and trends
- **Dynamic position sizing** that adapts to confidence levels and market conditions  
- **Smart safety limits** that protect your portfolio without blocking profitable trades
- **Momentum-based strategies** that can ride winners and cut losers

## ✨ **Key Features**

### 🧠 **AI-Powered Decision Making**
- **Advanced LLM Analysis**: Uses Google's Gemini 2.5 Pro for market analysis
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Market Sentiment**: Analyzes price trends, volume, and volatility
- **Confidence Scoring**: 0-100% confidence levels for each trading decision

### 📊 **Smart Trading Strategy**
- **AI Priority**: Market analysis drives all trading decisions
- **Dynamic Position Sizing**: Trade sizes adapt to confidence (10-25% of balance)
- **Safety Limits**: Minimum €50 EUR balance, 3% minimum crypto allocation
- **No Trade Blocking**: Doesn't sacrifice profitable trades for rigid allocation targets

### 🛡️ **Risk Management**
- **Confidence Thresholds**: 70% minimum confidence for BUY/SELL decisions
- **Position Limits**: €30-€1000 trade size range
- **Balance Protection**: Maintains minimum balances for continued trading
- **Diversification**: Prevents over-concentration in any single asset

### 📱 **Professional Dashboard**
- **Real-time Portfolio Tracking**: Live EUR values and allocations
- **Comprehensive AI Analysis**: Detailed reasoning for each trade decision with 4 analysis sections
- **Performance Metrics**: P&L tracking, win rates, portfolio growth
- **Market Overview**: Current prices, trends, and technical indicators

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

## ⚙️ **Configuration**

### **Core Settings** (`.env`)

```env
# Trading Configuration
BASE_CURRENCY=EUR                    # Base currency for trading
TRADING_PAIRS=BTC-EUR,ETH-EUR,SOL-EUR  # Trading pairs
RISK_LEVEL=HIGH                      # LOW, MEDIUM, HIGH
SIMULATION_MODE=False                # Set to True for paper trading

# AI Decision Thresholds
CONFIDENCE_THRESHOLD_BUY=70          # Minimum confidence for BUY orders
CONFIDENCE_THRESHOLD_SELL=70         # Minimum confidence for SELL orders

# Trade Size Limits
MIN_TRADE_AMOUNT=30.0               # Minimum trade size (EUR)
MAX_POSITION_SIZE=1000.0            # Maximum single trade size (EUR)

# Portfolio Strategy
PORTFOLIO_REBALANCE=false           # Disabled - AI decisions prioritized
TARGET_CRYPTO_ALLOCATION=90         # Target crypto allocation %
TARGET_BASE_ALLOCATION=10           # Target EUR allocation %
```

### **API Configuration**

```env
# Coinbase Advanced Trade
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_private_key

# Google Cloud (for AI analysis)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
LLM_MODEL=gemini-2.5-pro-preview-05-06
```

## 🎛️ **Trading Strategy Details**

### **AI-First Approach**
Unlike traditional rebalancing bots that force rigid allocation percentages, this bot:

1. **Analyzes Market Conditions** using AI and technical indicators
2. **Makes Trading Decisions** based on market opportunities
3. **Applies Smart Safety Limits** to protect your portfolio
4. **Sizes Positions Dynamically** based on confidence and allocation

### **Smart Safety Limits**
- **Minimum EUR Balance**: €50 (ensures ability to make BUY orders)
- **Maximum EUR Allocation**: 35% (prevents holding too much cash)
- **Minimum Crypto Allocation**: 3% per asset (maintains diversification)
- **Trade Size Scaling**: Higher confidence = larger positions (up to 1.5x)

### **Decision Process**
```
Market Data → AI Analysis → Confidence Score → Safety Check → Position Sizing → Execute Trade
```

## 📊 **Dashboard Features**

### **Portfolio Overview**
- **Total Value**: Real-time EUR portfolio value
- **Asset Allocation**: Current vs target percentages
- **AI-First Strategy Status**: Smart safety limits and trading capability
- **Performance Metrics**: P&L, returns, win rates

### **Enhanced AI Analysis**
- **Comprehensive Trade Details**: 4-section analysis for each trade
  - **AI Reasoning**: Detailed bullet-point market analysis
  - **Technical Analysis**: RSI, MACD, Bollinger Bands with color coding
  - **Bot Decision Process**: Confidence checks and risk management
  - **Market Context**: Price trends, conditions, and analysis quality
- **Recent Decisions**: Latest BUY/SELL/HOLD recommendations
- **Confidence Levels**: AI confidence scores (0-100%)

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
├── trading_strategy.py    # Trading strategy implementation
├── data_collector.py      # Market data collection
├── utils/                 # Utility modules
│   ├── dashboard_updater.py
│   ├── webserver_sync.py
│   ├── logger.py
│   ├── portfolio.py
│   └── ...
├── dashboard/             # Web dashboard
│   ├── static/
│   └── images/
├── data/                  # Runtime data
├── logs/                  # Application logs
├── .env                   # Environment variables
└── requirements.txt       # Dependencies
```

## 🔧 **Advanced Configuration**

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
- **Medium Confidence (70-79%)**: Standard position sizes
- **Low Confidence (<70%)**: No trade execution (HOLD)

### **Dynamic Position Sizing**
- **Over-allocated assets**: Smaller SELL positions to maintain balance
- **Under-allocated assets**: Larger BUY positions when EUR is available
- **High EUR allocation**: Larger BUY positions to deploy cash
- **Low EUR allocation**: Smaller BUY positions to preserve liquidity

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
- **Insufficient Balance**: Stops BUY orders if EUR < €50
- **API Failures**: Graceful degradation with error logging
- **Invalid Decisions**: Defaults to HOLD on analysis errors

### **Portfolio Protection**
- **Minimum Holdings**: Prevents selling below 3% allocation
- **Maximum Cash**: Limits EUR allocation to 35%
- **Trade Size Limits**: €30 minimum, €1000 maximum per trade

## 🔄 **Deployment**

### **Systemd Service**
```bash
# Copy service file
sudo cp crypto-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot
```

### **Dashboard Deployment**
```bash
# Deploy dashboard to web server
python3 deploy_dashboard.py
```

## 📞 **Support & Troubleshooting**

### **Common Issues**

**Bot not trading:**
- Check EUR balance (minimum €50 required)
- Verify AI confidence meets 70% threshold
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
