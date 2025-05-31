# AI-Powered Crypto Trading Bot

A Python-based cryptocurrency trading bot that uses Google Cloud Vertex AI LLMs to make trading decisions for Bitcoin and Ethereum on Coinbase. This bot leverages the power of AI to analyze market trends, technical indicators, and historical data to make informed trading decisions.

## Features

- Connects to Coinbase Advanced Trade API for real-time data and trading
- Uses Google Cloud Vertex AI for sophisticated market analysis and trading decisions
- Supports multiple LLM models (Text-Bison, Gemini, PaLM)
- Supports Bitcoin (BTC) and Ethereum (ETH) trading with USD pairs
- Collects and analyzes historical market data with customizable timeframes
- Calculates technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Implements risk management strategies based on configurable risk levels
- Provides detailed logging and trade history for performance tracking
- Scheduled trading at configurable intervals

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
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── logger.py           # Logging functionality
│   └── helpers.py          # Helper functions
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

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/AI-crypto-bot.git
cd AI-crypto-bot
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up API keys**

Create a `.env` file in the root directory based on the `.env.example` template:

```
# Coinbase API credentials
COINBASE_API_KEY=your_api_key_here
COINBASE_API_SECRET=your_api_secret_here

# Google Cloud configuration
GOOGLE_CLOUD_PROJECT=your_project_id_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# LLM configuration
LLM_PROVIDER=vertex_ai  # vertex_ai, palm, gemini
LLM_MODEL=text-bison@002  # text-bison@002, gemini-pro, etc.
LLM_LOCATION=us-central1  # Google Cloud region

# Trading parameters
TRADING_PAIRS=BTC-USD,ETH-USD
MAX_INVESTMENT_PER_TRADE_USD=100
RISK_LEVEL=medium  # low, medium, high
SIMULATION_MODE=True  # Set to False for real trading
```

4. **Run the bot**

```bash
python main.py
```

## Getting API Keys

### Coinbase API Keys

1. Log in to your Coinbase account
2. Go to Settings > API > New API Key
3. Enable the necessary permissions (view, trade)
4. Complete the security verification
5. Copy the API key and secret to your `.env` file

### Google Cloud Setup

1. Create a Google Cloud account if you don't have one
2. Create a new project in the Google Cloud Console
3. Enable the Vertex AI API for your project
4. Create a service account with Vertex AI User role
5. Download the service account key JSON file
6. Set the path to this file in your `.env` as `GOOGLE_APPLICATION_CREDENTIALS`

## Configuration

You can modify the trading parameters in the `config.py` file:

- `TRADING_PAIRS`: List of trading pairs to monitor and trade
- `MAX_INVESTMENT_PER_TRADE_USD`: Maximum amount to invest per trade
- `RISK_LEVEL`: Risk tolerance (low, medium, high)
- `LLM_PROVIDER`: LLM provider to use (vertex_ai, palm, gemini)
- `LLM_MODEL`: Model to use for analysis (text-bison@002, gemini-pro, etc.)
- `ANALYSIS_TIMEFRAME`: Timeframe for market analysis
- `DECISION_INTERVAL_MINUTES`: How often to make trading decisions

## How It Works

1. **Data Collection**: The bot collects historical price data and current market information from Coinbase.

2. **Technical Analysis**: It calculates various technical indicators like RSI, MACD, and Bollinger Bands.

3. **LLM Analysis**: The market data and indicators are sent to the LLM (Google Cloud Vertex AI), which analyzes the information and makes a trading recommendation.

4. **Decision Making**: Based on the LLM's analysis and confidence level, the bot decides whether to buy, sell, or hold.

5. **Trade Execution**: If a buy or sell decision is made with sufficient confidence, the bot executes the trade through the Coinbase API.

6. **Logging and Monitoring**: All decisions and trades are logged for review and performance tracking.

## Disclaimer

This trading bot is for educational purposes only. Cryptocurrency trading involves significant risk. Use this software at your own risk. The authors are not responsible for any financial losses incurred from using this bot.

## License

MIT License
## Advanced Usage

### Simulation Mode

Before trading with real money, you can run the bot in simulation mode:

1. Add `SIMULATION_MODE=True` to your `.env` file
2. Run the bot as usual with `python main.py`

### Backtesting

To test your strategy against historical data:

```bash
python backtest.py --pair BTC-USD --start 2023-01-01 --end 2023-12-31
```

### Customizing the LLM Prompt

You can modify the prompt template in `llm_analyzer.py` to adjust how the LLM analyzes market data and makes decisions. Different models may respond better to different prompt structures.

### Adding New Technical Indicators

Extend the `calculate_technical_indicators` method in `data_collector.py` to add new indicators for the LLM to consider.

## Troubleshooting

### Common Issues

- **API Rate Limiting**: If you encounter rate limiting issues, increase the delay between API calls in `main.py`
- **LLM Token Limits**: If your analysis is being cut off, try using a more concise market summary or upgrade to a model with higher token limits
- **Trade Execution Failures**: Check your API permissions and ensure you have sufficient funds in your Coinbase account

### Logs

Check the log files in the `logs/` directory for detailed information about the bot's operation and any errors that occur.
## Deployment on AWS EC2

You can run this bot on an AWS EC2 instance as a systemd service for 24/7 operation.

### Setting up an EC2 Instance

1. **Launch an EC2 instance**:
   - Log in to your AWS Management Console
   - Navigate to EC2 and click "Launch Instance"
   - Choose Amazon Linux 2023 AMI
   - Select an instance type (t2.micro for testing, t2.medium or better for production)
   - Configure security groups to allow SSH access (port 22)
   - Launch the instance and connect to it via SSH

2. **Clone the repository and run the setup script**:
   ```bash
   # Connect to your EC2 instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Clone the repository
   git clone https://github.com/yourusername/AI-crypto-bot.git
   cd AI-crypto-bot
   
   # Make the setup script executable
   chmod +x setup_ec2.sh
   
   # Run the setup script
   ./setup_ec2.sh
   ```

3. **Configure your environment**:
   ```bash
   # Edit the .env file with your API keys and settings
   nano .env
   ```

4. **Start the service**:
   ```bash
   sudo systemctl start crypto-bot
   ```

5. **Check the status**:
   ```bash
   sudo systemctl status crypto-bot
   ```

6. **View logs**:
   ```bash
   sudo journalctl -u crypto-bot -f
   ```

### Managing the Service

- **Start the service**: `sudo systemctl start crypto-bot`
- **Stop the service**: `sudo systemctl stop crypto-bot`
- **Restart the service**: `sudo systemctl restart crypto-bot`
- **Enable at boot**: `sudo systemctl enable crypto-bot`
- **Disable at boot**: `sudo systemctl disable crypto-bot`

### Security Considerations

When running on AWS EC2:

1. Use IAM roles instead of storing AWS credentials on the instance
2. Keep your instance updated with `sudo yum update -y`
3. Use security groups to restrict access to your instance
4. Consider using AWS Secrets Manager for API keys
5. Enable CloudWatch monitoring for your EC2 instance
## Web Dashboard

The bot includes a web-based dashboard for monitoring trading activities:

1. **Real-time monitoring**: View the current status of the bot and recent trading decisions
2. **Trading pair overview**: See performance metrics for each trading pair
3. **Recent trades**: View details of recent buy and sell transactions
4. **Performance metrics**: Track success rates and overall performance

The dashboard is password-protected using Apache's basic authentication and automatically updates after each trading cycle.

### Accessing the Dashboard

After deploying on AWS EC2:
1. Navigate to `http://your-ec2-public-ip/crypto-bot/` in your browser
2. Enter the username and password you configured during setup
3. The dashboard refreshes automatically every 5 minutes
