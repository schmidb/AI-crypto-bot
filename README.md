# AI Crypto Trading Bot

An intelligent cryptocurrency trading bot that combines technical analysis with AI-powered market insights to make automated trading decisions.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Coinbase Advanced Trade API access
- Google Cloud Platform account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AI-crypto-bot.git
   cd AI-crypto-bot
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure your settings**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and preferences
   ```

4. **Test the new Phase 1 features**
   ```bash
   # Test the opportunity manager
   python test_opportunity_manager.py
   
   # Run the bot (automatically uses new prioritization)
   python main.py
   ```

5. **Run in simulation mode**
   ```bash
   python main.py
   ```

## 🎯 Key Features

### 🚀 **NEW: Phase 1 - Intelligent Multi-Coin Prioritization**
- **Opportunity Scoring**: Analyzes all coins and ranks by trading opportunity strength
- **Dynamic Capital Allocation**: Allocates more capital to stronger signals (up to 60% max)
- **Three-Phase Trading Cycle**: Analyze → Rank → Execute for maximum efficiency
- **Scalable Architecture**: Automatically handles any number of trading pairs

### 🧠 **Core Trading Intelligence**
- **Multi-Strategy Trading**: Combines trend following, mean reversion, and momentum strategies
- **AI-Powered Analysis**: Uses Google Gemini for market analysis and decision making
- **Adaptive Strategy Manager**: Adjusts strategy weights based on market conditions
- **Risk Management**: Comprehensive position sizing and safety mechanisms

### 📊 **Monitoring & Analytics**
- **Real-time Dashboard**: Web-based monitoring and performance tracking
- **Enhanced Logging**: Detailed opportunity scoring and allocation insights
- **Automated Reports**: Daily email summaries with AI-generated insights
- **Performance Tracking**: Historical analysis and strategy optimization

### ☁️ **Deployment Ready**
- **Cloud Deployment**: Ready-to-deploy on Google Cloud Platform and AWS
- **Windows Compatible**: Cross-platform file locking and process management

## 📊 Supported Assets

The bot now intelligently prioritizes trading opportunities across multiple assets:

- **BTC-EUR**: Bitcoin to Euro
- **ETH-EUR**: Ethereum to Euro  
- **SOL-EUR**: Solana to Euro
- **Easily Expandable**: Add more pairs in configuration - the system automatically handles prioritization

### 🎯 **How Multi-Coin Prioritization Works**
1. **Analyze All Pairs**: Simultaneously analyzes all configured trading pairs
2. **Opportunity Scoring**: Ranks opportunities using confidence, momentum, consensus, and market regime
3. **Smart Capital Allocation**: Distributes capital based on signal strength (stronger signals get more)
4. **Priority Execution**: Executes best opportunities first, ensuring optimal capital utilization

## 🛡️ Safety First

- **Simulation Mode**: Test strategies without real money
- **Risk Controls**: Position limits, stop losses, and allocation caps
- **Comprehensive Testing**: Extensive test suite with 90%+ coverage
- **Backtesting**: Historical performance validation

## 📚 Documentation

For detailed information, see the [Developer Documentation](docs/):

### 🆕 **Phase 1 Documentation**
- **[Phase 1 Implementation](docs/PHASE_1_OPPORTUNITY_PRIORITIZATION.md)** - Complete Phase 1 technical details
- **[Opportunity Manager](utils/trading/opportunity_manager.py)** - Core prioritization logic

### ⚠️ **Important: Backtesting Limitations**
- **[Backtesting Analysis](BACKTEST_LLM_ANALYSIS.md)** - Critical information about LLM backtesting limitations
- **Technical strategies** (momentum, mean_reversion, trend_following) can be accurately backtested
- **LLM strategy** uses Google Gemini API and cannot be simulated - backtest results are approximations only
- **Live performance tracking** monitors actual bot decisions from trading logs (not simulated)

### 📖 **Core Documentation**
- **[Trading Strategies](docs/TRADING_STRATEGIES.md)** - How the bot makes decisions
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete setup instructions
- **[Backtesting Strategy](docs/COMPREHENSIVE_BACKTESTING_STRATEGY.md)** - Systematic backtesting approach
- **[Deployment Guides](docs/deployment/)** - Cloud and local deployment
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🚀 Deployment Options

### Local Development
Perfect for testing and development:
```bash
# See docs/deployment/local-development.md
python main.py  # Runs in simulation mode by default
```

### Google Cloud Platform
Automated deployment with monitoring:
```bash
# See docs/deployment/gcp-deployment.md
bash gcp_deployment/setup_gcp.sh
```

### Amazon Web Services
Enterprise deployment with auto-scaling:
```bash
# See docs/deployment/aws-deployment.md
bash aws_setup/setup_ec2.sh
```

## ⚠️ Important Disclaimers

- **Educational Purpose**: This bot is designed for learning and research
- **Financial Risk**: Cryptocurrency trading involves significant financial risk
- **No Guarantees**: Past performance does not guarantee future results
- **Use at Your Own Risk**: Always understand the code before trading with real money
- **Not Financial Advice**: This software does not provide investment advice

## 🤝 Contributing

We welcome contributions! Please see our [development documentation](docs/) for:
- Code structure and architecture
- Testing requirements and standards
- Development setup and workflows

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) folder for comprehensive guides
- **Issues**: Report bugs and request features on GitHub Issues
- **Troubleshooting**: See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

**Remember**: Always start with simulation mode and thoroughly understand the system before considering live trading.