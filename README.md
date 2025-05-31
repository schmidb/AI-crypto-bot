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
- Includes automated setup scripts for AWS EC2 and Google Cloud deployment

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
├── aws_setup/              # AWS deployment scripts
│   └── setup_ec2.sh        # Automated setup script for EC2
├── gcp_setup/              # Google Cloud deployment scripts
│   └── setup_gce.sh        # Automated setup script for GCE
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
   source venv/bin/activate  # On Windows: venv\Scripts\activate
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

5. **Run the bot**:
   ```bash
   python main.py
   ```

#### Cloud Deployment

For production deployment, use the automated setup scripts in the dedicated directories:

- **AWS EC2**: Use the setup script in the `aws_setup` directory
- **Google Cloud**: Use the setup script in the `gcp_setup` directory

See the Cloud Deployment Options section below for detailed instructions.

## Cloud Deployment Options

You can deploy this bot on either AWS EC2 or Google Compute Engine for 24/7 operation. For your convenience, we provide automated setup scripts in the `aws_setup` and `gcp_setup` directories.

### Option 1: AWS EC2 Deployment

Run the bot on an AWS EC2 instance as a systemd service using our setup script.

1. **Launch an EC2 instance**:
   - Log in to your AWS Management Console
   - Navigate to EC2 and click "Launch Instance"
   - Choose Amazon Linux 2023 AMI
   - Select an instance type (t2.medium or better recommended for production)
   - Configure security groups to allow SSH access (port 22)
   - Launch the instance and connect to it via SSH

2. **Clone the repository and run the setup script**:
   ```bash
   # Connect to your EC2 instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Clone the repository
   git clone https://github.com/yourusername/AI-crypto-bot.git
   cd AI-crypto-bot
   
   # Run the AWS setup script
   bash aws_setup/setup_ec2.sh
   ```

3. **Configure your API keys**:
   ```bash
   # Edit your .env file with your API keys
   nano .env
   ```
   Note: The setup script creates a template .env file for you, but you need to add your own API keys.

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

### Option 2: Google Compute Engine Deployment

Run the bot on a Google Compute Engine VM instance using our setup script.

1. **Create a VM Instance**:
   - Log in to Google Cloud Console
   - Navigate to Compute Engine > VM instances
   - Click "Create Instance"
   - Choose a name for your instance
   - Select a region and zone (e.g., us-central1-a)
   - Choose machine type (e2-medium recommended)
   - Select Debian or Ubuntu as the boot disk
   - Allow HTTP/HTTPS traffic if you plan to use the dashboard
   - Click "Create"

2. **Connect to your VM**:
   ```bash
   # Connect via SSH from Cloud Console or using gcloud
   gcloud compute ssh crypto-trading-bot --zone=us-central1-a
   ```

3. **Clone the repository and run the setup script**:
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/AI-crypto-bot.git
   cd AI-crypto-bot
   
   # Run the Google Cloud setup script
   bash gcp_setup/setup_gce.sh
   ```

4. **Configure your API keys**:
   ```bash
   # Edit your .env file with your API keys
   nano .env
   ```
   Note: The setup script creates a template .env file for you, but you need to add your own API keys.

5. **Access the dashboard**:
   - The setup script installs Apache and configures a web dashboard
   - Access it at http://YOUR_VM_IP/crypto-bot/
   - Make sure your firewall rules allow HTTP traffic (port 80)

## Backtesting

The bot includes a backtesting module that allows you to test your trading strategies against historical data before risking real capital.

### Features

- Test trading strategies on historical price data
- Calculate performance metrics (returns, win rate, profit factor, etc.)
- Compare performance across different cryptocurrencies
- Save detailed trade history and performance metrics

### Usage

#### Running a Backtest

```bash
# Basic backtest for BTC-USD
python backtest_cli.py backtest --product BTC-USD --start 2023-01-01 --end 2023-12-31

# Specify initial balance and trade size
python backtest_cli.py backtest --product ETH-USD --start 2023-01-01 --end 2023-12-31 --balance 5000 --trade-size 500

# Custom output file
python backtest_cli.py backtest --product BTC-USD --start 2023-01-01 --end 2023-12-31 --output btc_2023_results.json
```

#### Comparing Multiple Assets

```bash
# Compare BTC and ETH performance
python backtest_cli.py compare --products BTC-USD ETH-USD --start 2023-01-01 --end 2023-12-31

# Compare multiple assets with custom output
python backtest_cli.py compare --products BTC-USD ETH-USD SOL-USD --start 2023-01-01 --end 2023-12-31 --output crypto_comparison_2023.json
```

### Interpreting Results

The backtesting module provides comprehensive performance metrics:

- **Total Return**: Overall percentage return for the period
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Trade Statistics**: Number of trades, average profit/loss, etc.

Results are saved as JSON files in the `backtest_results` directory.
## Testing

The project includes a comprehensive test suite to ensure the reliability and correctness of the trading bot components.

### Running Tests

First, make sure you're using a virtual environment to avoid conflicts with system packages:

```bash
# Create a virtual environment if you haven't already
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

To run all tests:

```bash
python -m unittest discover -s tests
```

To run a specific test file:

```bash
python -m unittest tests.test_coinbase
```

To run a specific test case:

```bash
python -m unittest tests.test_coinbase.TestCoinbaseClient.test_get_product_price
```

### Test Coverage

The test suite covers the following components:

#### Coinbase Client Tests
- API authentication and signature generation
- HTTP request handling
- Market data retrieval
- Order placement

#### Trading Strategy Tests
- Strategy initialization
- Decision making for different market conditions (buy, sell, hold)
- Error handling

#### Data Collector Tests
- Historical data retrieval
- Current market data collection
- Technical indicator calculation

#### Backtesting Tests
- Backtest result tracking
- Trade simulation
- Performance metrics calculation

### Adding New Tests

When adding new features to the bot, corresponding tests should be added to maintain code quality and prevent regressions.

1. Create a new test file in the `tests` directory if needed
2. Follow the naming convention: `test_*.py` for files and `test_*` for methods
3. Use the `unittest` framework and appropriate assertions
4. Mock external dependencies to isolate the component being tested
