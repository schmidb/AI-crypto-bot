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

4. **Run in simulation mode**
   ```bash
   python main.py
   ```

## 🎯 Key Features

- **Multi-Strategy Trading**: Combines trend following, mean reversion, and momentum strategies
- **AI-Powered Analysis**: Uses Google Gemini for market analysis and decision making
- **Risk Management**: Comprehensive position sizing and safety mechanisms
- **Real-time Dashboard**: Web-based monitoring and performance tracking
- **Automated Reports**: Daily email summaries with AI-generated insights
- **Cloud Deployment**: Ready-to-deploy on Google Cloud Platform and AWS

## 📊 Supported Assets

- **BTC-EUR**: Bitcoin to Euro
- **ETH-EUR**: Ethereum to Euro  
- **SOL-EUR**: Solana to Euro

## 🛡️ Safety First

- **Simulation Mode**: Test strategies without real money
- **Risk Controls**: Position limits, stop losses, and allocation caps
- **Comprehensive Testing**: Extensive test suite with 90%+ coverage
- **Backtesting**: Historical performance validation

## 📚 Documentation

For detailed information, see the [Developer Documentation](docs/):

- **[Trading Strategies](docs/TRADING_STRATEGIES.md)** - How the bot makes decisions
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete setup instructions
- **[Testing Strategy](docs/COMPREHENSIVE_TESTING_STRATEGY.md)** - Systematic backtesting approach
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