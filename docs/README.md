# AI Crypto Trading Bot - Developer Documentation

This documentation is designed for developers, contributors, and users who want to understand the technical details of the AI crypto trading bot.

## 📚 Documentation Index

### Core Concepts
- **[Trading Strategies](TRADING_STRATEGIES.md)** - Detailed explanation of the three trading strategies
- **[Risk Management](RISK_MANAGEMENT.md)** - Risk controls, position sizing, and safety mechanisms
- **[Architecture](ARCHITECTURE.md)** - System design, components, and data flow
- **[Data Storage](DATA_STORAGE.md)** - Data persistence, storage architecture, and recovery procedures

### Development & Analysis
- **[Backtesting](BACKTESTING.md)** - Backtesting framework, results, and analysis
- **[Comprehensive Testing Strategy](COMPREHENSIVE_TESTING_STRATEGY.md)** - Systematic testing approach for strategy optimization
- **[Performance Analysis](PERFORMANCE_ANALYSIS.md)** - Performance metrics, tracking, and optimization
- **[Configuration](CONFIGURATION.md)** - Comprehensive configuration guide

### Deployment & Operations
- **[Deployment Overview](deployment/)** - All deployment options
  - [GCP Deployment](deployment/gcp-deployment.md)
  - [AWS Deployment](deployment/aws-deployment.md)
  - [Local Development](deployment/local-development.md)
- **[API Reference](API_REFERENCE.md)** - API endpoints and usage
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## 🎯 Quick Navigation

**For New Developers:**
1. Start with [Architecture](ARCHITECTURE.md) to understand the system
2. Read [Trading Strategies](TRADING_STRATEGIES.md) to understand the logic
3. Review [Configuration](CONFIGURATION.md) for setup details

**For Strategy Analysis:**
1. [Trading Strategies](TRADING_STRATEGIES.md) - How strategies work
2. [Backtesting](BACKTESTING.md) - Historical performance analysis
3. [Comprehensive Testing Strategy](COMPREHENSIVE_TESTING_STRATEGY.md) - Systematic testing approach
4. [Risk Management](RISK_MANAGEMENT.md) - Safety mechanisms

**For Deployment:**
1. Choose your platform in [deployment/](deployment/)
2. Follow the specific deployment guide
3. Use [Troubleshooting](TROUBLESHOOTING.md) if needed

## 🔧 Technical Stack

- **Language**: Python 3.11+
- **AI/ML**: Google Gemini (via new `google-genai` library)
- **Trading API**: Coinbase Advanced Trade
- **Technical Analysis**: TA-Lib, pandas, numpy
- **Backtesting**: VectorBT
- **Cloud**: Google Cloud Platform, AWS
- **Monitoring**: Custom performance tracking, daily reports

## 📈 Key Features

- **Multi-Strategy Trading**: Trend Following, Mean Reversion, Momentum
- **AI-Powered Analysis**: Gemini 3 Flash/Pro for market analysis
- **Comprehensive Risk Management**: Position sizing, stop losses, allocation limits
- **Real-time Monitoring**: Web dashboard, daily email reports
- **Backtesting Framework**: Historical performance validation
- **Cloud Deployment**: Automated setup for GCP and AWS

## 🤝 Contributing

This bot is designed for educational and research purposes. When contributing:

1. Follow the existing code structure and patterns
2. Update relevant documentation
3. Add tests for new features
4. Ensure risk management principles are maintained

## ⚠️ Important Notes

- **Educational Purpose**: This bot is for learning and research
- **Risk Warning**: Cryptocurrency trading involves significant risk
- **No Financial Advice**: This software does not provide financial advice
- **Use at Your Own Risk**: Always understand the code before running with real money

## 📞 Support

- Check [Troubleshooting](TROUBLESHOOTING.md) for common issues
- Review the specific deployment guides
- Examine the code and tests for implementation details