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
## Cloud Deployment Options

You can deploy this bot on either AWS EC2 or Google Compute Engine for 24/7 operation.

### Option 1: AWS EC2 Deployment

Run the bot on an AWS EC2 instance as a systemd service.

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

#### Managing the AWS EC2 Service

- **Start the service**: `sudo systemctl start crypto-bot`
- **Stop the service**: `sudo systemctl stop crypto-bot`
- **Restart the service**: `sudo systemctl restart crypto-bot`
- **Enable at boot**: `sudo systemctl enable crypto-bot`
- **Disable at boot**: `sudo systemctl disable crypto-bot`

#### AWS Security Considerations

1. Use IAM roles instead of storing AWS credentials on the instance
2. Keep your instance updated with `sudo yum update -y`
3. Use security groups to restrict access to your instance
4. Consider using AWS Secrets Manager for API keys
5. Enable CloudWatch monitoring for your EC2 instance

### Option 2: Google Compute Engine Deployment

Run the bot on a Google Compute Engine VM instance.

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

3. **Install dependencies and clone the repository**:
   ```bash
   # Update package lists
   sudo apt-get update
   
   # Install required packages
   sudo apt-get install -y python3-pip python3-venv git supervisor
   
   # Clone the repository
   git clone https://github.com/yourusername/AI-crypto-bot.git
   cd AI-crypto-bot
   
   # Create a virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Configure your environment**:
   ```bash
   # Create and edit your .env file
   cp .env.example .env
   nano .env
   ```

5. **Set up supervisor to manage the bot process**:
   ```bash
   # Create supervisor configuration
   sudo bash -c 'cat > /etc/supervisor/conf.d/crypto-bot.conf << EOL
   [program:crypto-bot]
   command=/home/$USER/AI-crypto-bot/venv/bin/python /home/$USER/AI-crypto-bot/main.py
   directory=/home/$USER/AI-crypto-bot
   autostart=true
   autorestart=true
   startretries=10
   user=$USER
   redirect_stderr=true
   stdout_logfile=/home/$USER/AI-crypto-bot/logs/supervisor.log
   stdout_logfile_maxbytes=50MB
   stdout_logfile_backups=10
   environment=HOME="/home/$USER",USER="$USER"
   EOL'
   
   # Create log directory
   mkdir -p ~/AI-crypto-bot/logs
   
   # Reload supervisor configuration
   sudo supervisorctl reread
   sudo supervisorctl update
   ```

6. **Start and monitor the bot**:
   ```bash
   # Start the bot
   sudo supervisorctl start crypto-bot
   
   # Check status
   sudo supervisorctl status crypto-bot
   
   # View logs
   tail -f ~/AI-crypto-bot/logs/supervisor.log
   ```

#### Managing the Google Compute Engine Service

- **Start the service**: `sudo supervisorctl start crypto-bot`
- **Stop the service**: `sudo supervisorctl stop crypto-bot`
- **Restart the service**: `sudo supervisorctl restart crypto-bot`
- **View logs**: `tail -f ~/AI-crypto-bot/logs/supervisor.log`

#### Google Cloud Security Considerations

1. Use service accounts with minimal permissions
2. Keep your VM updated with `sudo apt-get update && sudo apt-get upgrade`
3. Use firewall rules to restrict access to your VM
4. Consider using Secret Manager for API keys
5. Enable Cloud Monitoring for your VM instance
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

## Trade Logging and Tax Reporting

The bot automatically logs all trading activities to CSV files for record keeping and tax reporting purposes:

1. **Trade History**: All buy and sell activities are logged to `logs/trade_history.csv` with the following information:
   - Timestamp
   - Trade ID
   - Product ID (e.g., BTC-USD)
   - Side (buy or sell)
   - Price
   - Size (amount of cryptocurrency)
   - Value in USD
   - Fee in USD
   - Cost basis in USD
   - Tax year

2. **Automated Tax Reports**: The bot generates daily tax reports in Excel format with:
   - Complete trade history
   - Separate sheets for buys and sells
   - Summary statistics
   - Asset-specific summaries

3. **Manual Report Generation**: You can also generate tax reports on demand:
   ```python
   from utils.tax_report import TaxReportGenerator
   
   # Generate report for specific year
   generator = TaxReportGenerator()
   generator.generate_report("my_tax_report_2024.xlsx", tax_year=2024)
   
   # Generate report for all years
   generator.generate_report("all_trades_report.xlsx")
   ```

All reports are saved in the `reports` directory by default.
## Strategy Evaluation and Performance Tracking

The bot includes comprehensive strategy evaluation and performance tracking features:

1. **Detailed Strategy Logging**: Every trade decision is logged with extensive metrics:
   - Market conditions (volatility, volume, trend)
   - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
   - LLM analysis details (confidence, key factors, reasoning)
   - Trade performance (profit/loss, holding period)

2. **Performance Metrics**: The system tracks key performance indicators:
   - Win/loss ratio
   - Average profit on winning trades
   - Average loss on losing trades
   - Maximum drawdown
   - Profit factor
   - Holding period statistics

3. **Automated Reports**: The bot generates weekly strategy performance reports in Excel format:
   - Overall performance summary
   - Detailed trade analysis
   - Winning and losing trades breakdown
   - Asset-specific performance
   - Correlation analysis between indicators and outcomes

4. **Strategy Optimization**: The detailed logging enables:
   - Identifying which market conditions your strategy performs best in
   - Determining which technical indicators are most predictive
   - Understanding when the LLM's reasoning is most accurate
   - Optimizing risk levels and position sizing

All strategy performance data is saved in `logs/strategy_performance.csv` with detailed logs in `logs/detailed_logs/`. Weekly reports are automatically generated in the `reports` directory.
## Dashboard

The bot includes a web-based dashboard for monitoring trading activities:

1. **Real-time monitoring**: View the current status of the bot and recent trading decisions
2. **Trading pair overview**: See performance metrics for each trading pair
3. **Trade history**: View detailed history of all buy and sell transactions with interactive charts
4. **Performance metrics**: Track success rates, win/loss ratio, profit factor, and other key metrics
5. **Strategy analysis**: Visualize performance across different market conditions
6. **Report access**: Download tax and strategy performance reports directly from the dashboard

The dashboard automatically updates after each trading cycle and refreshes every 5 minutes in your browser.

### Accessing the Dashboard

After deploying on AWS EC2 or Google Compute Engine:
1. Navigate to `http://your-server-ip/crypto-bot/` in your browser
2. The dashboard will display the latest trading information and performance metrics
3. Use the navigation menu to access different sections of the dashboard

### Dashboard Features

- **Overview**: Quick summary of bot status, total trades, win rate, and total profit/loss
- **Trading Pairs**: Current price and latest trading decision for each pair
- **Trade History**: Interactive chart of price history and table of recent trades
- **Performance**: Detailed metrics and visualizations of strategy performance
- **Reports**: Links to download tax and strategy performance reports
