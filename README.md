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

4. **Configure your environment**:
   ```bash
   # Create and edit your .env file
   cp .env.example .env
   nano .env
   ```

5. **Access the dashboard**:
   - The setup script installs Apache and configures a web dashboard
   - Access it at http://YOUR_VM_IP/crypto-bot/
   - Make sure your firewall rules allow HTTP traffic (port 80)
