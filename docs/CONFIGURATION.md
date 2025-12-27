# Configuration Guide

This guide covers all configuration options for the AI crypto trading bot, including environment variables, API setup, and advanced configuration.

## Configuration Overview

The bot uses a hierarchical configuration system:
1. **Environment Variables** (highest priority)
2. **Configuration Class Defaults** (fallback values)
3. **System Defaults** (last resort)

## Environment Setup

### Required Environment File

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
nano .env
```

### Core Configuration

#### Trading API Configuration

```env
# Coinbase Advanced Trade API (Required)
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END EC PRIVATE KEY-----

# Trading pairs (comma-separated)
TRADING_PAIRS=BTC-EUR,ETH-EUR,SOL-EUR

# Base currency for trading
BASE_CURRENCY=EUR
```

**Getting Coinbase API Keys:**
1. Go to [Coinbase Developer Platform](https://www.coinbase.com/cloud)
2. Create a new API key with trading permissions
3. Download the private key file
4. Copy the organization/apiKeys/key-id format for API_KEY
5. Copy the entire private key content for API_SECRET

#### AI/ML Configuration

```env
# Google Cloud AI (Required)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# LLM Configuration
LLM_PROVIDER=google_ai
LLM_MODEL=gemini-3-flash-preview
LLM_FALLBACK_MODEL=gemini-3-pro-preview
LLM_LOCATION=global

# Optional: API key as fallback (not required if using service account)
# GOOGLE_AI_API_KEY=your_api_key_here
```

**Setting up Google Cloud AI:**
1. Create a Google Cloud Project
2. Enable the Vertex AI API
3. Create a service account with "AI Platform User" role
4. Download the service account JSON file
5. Set the path in GOOGLE_APPLICATION_CREDENTIALS

### Trading Configuration

#### Basic Trading Settings

```env
# Trading behavior
SIMULATION_MODE=false              # Set to true for paper trading
DECISION_INTERVAL_MINUTES=60       # How often to make trading decisions
RISK_LEVEL=MEDIUM                  # LOW, MEDIUM, HIGH

# Confidence thresholds (0-100)
CONFIDENCE_THRESHOLD_BUY=55        # Minimum confidence for BUY orders
CONFIDENCE_THRESHOLD_SELL=55       # Minimum confidence for SELL orders
```

#### Position Sizing & Risk Management

```env
# Position sizing
MIN_TRADE_AMOUNT=5.0               # Minimum trade size in EUR
MAX_POSITION_SIZE_PERCENT=75       # Max single trade size (% of EUR balance)
TARGET_EUR_ALLOCATION=12           # Target EUR allocation percentage
MIN_EUR_RESERVE=15.0               # Minimum EUR reserve to maintain

# Risk multipliers by risk level
RISK_HIGH_POSITION_MULTIPLIER=0.5   # 50% reduction for high risk
RISK_MEDIUM_POSITION_MULTIPLIER=0.75 # 25% reduction for medium risk
RISK_LOW_POSITION_MULTIPLIER=1.0    # No reduction for low risk
```

### Strategy Configuration

#### Strategy Weights

```env
# Default strategy weights (will be adjusted dynamically)
TREND_FOLLOWING_WEIGHT=0.4         # 40% weight
MEAN_REVERSION_WEIGHT=0.3          # 30% weight
MOMENTUM_WEIGHT=0.3                # 30% weight
```

#### Trend Following Strategy

```env
# Technical indicator parameters
TREND_STRENGTH_THRESHOLD=60        # Minimum trend strength (0-100)
TREND_RSI_OVERBOUGHT=75           # RSI overbought level
TREND_RSI_OVERSOLD=25             # RSI oversold level
TREND_MACD_FAST_PERIOD=12         # MACD fast EMA period
TREND_MACD_SLOW_PERIOD=26         # MACD slow EMA period
TREND_MACD_SIGNAL_PERIOD=9        # MACD signal line period
```

#### Mean Reversion Strategy

```env
# Mean reversion parameters
MR_RSI_OVERSOLD=30                # RSI oversold threshold
MR_RSI_OVERBOUGHT=70              # RSI overbought threshold
MR_RSI_EXTREME_OVERSOLD=20        # Extreme oversold level
MR_RSI_EXTREME_OVERBOUGHT=80      # Extreme overbought level
MR_BB_PERIOD=20                   # Bollinger Bands period
MR_BB_STD_DEV=2.0                 # Bollinger Bands standard deviation
MR_BB_DEVIATION_THRESHOLD=1.5     # Deviation threshold for signals
```

#### Momentum Strategy

```env
# Momentum parameters
MOMENTUM_PRICE_THRESHOLD=0.02      # Price momentum threshold (2%)
MOMENTUM_VOLUME_THRESHOLD=1.5      # Volume threshold (1.5x average)
MOMENTUM_RSI_PERIOD=14            # RSI period for momentum
MOMENTUM_MACD_HISTOGRAM_THRESHOLD=0.001  # MACD histogram threshold
MOMENTUM_TECHNICAL_THRESHOLD=60    # Technical momentum threshold
```

### Monitoring & Reporting

#### Performance Tracking

```env
# Performance tracking
PERFORMANCE_TRACKING_ENABLED=true
SNAPSHOT_FREQUENCY_MINUTES=60     # Portfolio snapshot frequency
PERFORMANCE_RETENTION_DAYS=365    # How long to keep performance data
BENCHMARK_SYMBOL=BTC-EUR          # Benchmark for comparison
```

#### Web Dashboard

```env
# Dashboard configuration
WEBSERVER_SYNC_ENABLED=true       # Enable dashboard updates
DASHBOARD_UPDATE_INTERVAL=300     # Update interval in seconds (5 minutes)
DASHBOARD_PORT=8080               # Port for local dashboard (if applicable)
```

#### Daily Email Reports

```env
# Email configuration for daily reports
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
REPORT_RECIPIENT=recipient@example.com
DAILY_REPORT_TIME=08:00           # Time to send daily reports (24h format)
```

**Setting up Gmail for Reports:**
1. Enable 2-factor authentication on your Google account
2. Go to Google Account settings > Security > App passwords
3. Generate an app password for "Mail"
4. Use this password in GMAIL_APP_PASSWORD

#### Notifications & Alerts

```env
# Alert thresholds
DAILY_LOSS_ALERT_THRESHOLD=-0.05   # Alert if daily loss > 5%
MAX_DRAWDOWN_ALERT_THRESHOLD=-0.15 # Alert if drawdown > 15%
WIN_RATE_ALERT_THRESHOLD=0.30      # Alert if win rate < 30%
VOLATILITY_ALERT_THRESHOLD=0.50    # Alert if volatility > 50%

# Notification settings
NOTIFICATIONS_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/... # Optional Slack notifications
```

### Advanced Configuration

#### Logging

```env
# Logging configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE_ENABLED=true            # Enable file logging
LOG_FILE_MAX_SIZE=50MB           # Maximum log file size
LOG_FILE_BACKUP_COUNT=10         # Number of backup log files
LOG_FORMAT=detailed              # simple, detailed, json
```

#### System Settings

```env
# System behavior
TESTING=false                    # Set to true in test environment
DEBUG_MODE=false                 # Enable debug features
SUPERVISOR_ENABLED=false         # Set to true when running under supervisor
BOT_RESTART_CONTEXT=normal       # normal, restart, stop (for uptime tracking)

# API rate limiting
COINBASE_RATE_LIMIT=10           # Requests per second
COINBASE_RETRY_ATTEMPTS=3        # Number of retry attempts
COINBASE_RETRY_DELAY=1           # Delay between retries (seconds)

# Data collection
DATA_COLLECTION_INTERVAL=60      # Market data collection interval (seconds)
TECHNICAL_INDICATOR_PERIOD=200   # Number of periods for technical indicators
```

#### Backtesting Configuration

```env
# Backtesting settings (when running backtests)
BACKTEST_START_DATE=2023-01-01
BACKTEST_END_DATE=2024-01-01
BACKTEST_INITIAL_CAPITAL=1000.0
BACKTEST_TRANSACTION_COST=0.001  # 0.1% per trade
BACKTEST_SLIPPAGE=0.0005         # 0.05% slippage
```

## Configuration Validation

### Automatic Validation

The bot automatically validates configuration on startup:

```python
class Config:
    def __init__(self):
        # Load and validate all configuration
        self.validate_required_settings()
        self.validate_api_credentials()
        self.validate_numeric_ranges()
        self.validate_strategy_weights()
    
    def validate_required_settings(self):
        required = [
            'COINBASE_API_KEY',
            'COINBASE_API_SECRET',
            'GOOGLE_CLOUD_PROJECT'
        ]
        
        for setting in required:
            if not getattr(self, setting):
                raise ValueError(f"Required setting {setting} is missing")
    
    def validate_api_credentials(self):
        # Validate Coinbase API key format
        if not self.COINBASE_API_KEY.startswith('organizations/'):
            raise ValueError("Invalid Coinbase API key format")
        
        # Validate private key format
        if not self.COINBASE_API_SECRET.startswith('-----BEGIN EC PRIVATE KEY-----'):
            raise ValueError("Invalid Coinbase API secret format")
```

### Configuration Health Check

```python
def check_configuration_health():
    """Validate current configuration and return health status"""
    
    health_checks = {
        'api_credentials': validate_coinbase_credentials(),
        'google_cloud': validate_google_cloud_setup(),
        'trading_pairs': validate_trading_pairs(),
        'risk_settings': validate_risk_parameters(),
        'strategy_weights': validate_strategy_weights(),
        'thresholds': validate_confidence_thresholds()
    }
    
    all_healthy = all(health_checks.values())
    
    return {
        'overall_health': 'healthy' if all_healthy else 'issues_detected',
        'checks': health_checks,
        'timestamp': datetime.utcnow().isoformat()
    }
```

## Environment-Specific Configuration

### Development Environment

```env
# Development settings
SIMULATION_MODE=true              # Always use simulation in development
NOTIFICATIONS_ENABLED=false      # Disable notifications
LOG_LEVEL=DEBUG                  # Verbose logging
DECISION_INTERVAL_MINUTES=5      # Faster decisions for testing
MIN_TRADE_AMOUNT=1.0             # Lower minimum for testing
```

### Production Environment

```env
# Production settings
SIMULATION_MODE=false            # Real trading
NOTIFICATIONS_ENABLED=true      # Enable all notifications
LOG_LEVEL=INFO                  # Standard logging
DECISION_INTERVAL_MINUTES=60    # Standard interval
PERFORMANCE_TRACKING_ENABLED=true # Full performance tracking
```

### Testing Environment

```env
# Testing settings (automatically set by test framework)
TESTING=true
SIMULATION_MODE=true
COINBASE_API_KEY=test-api-key
NOTIFICATIONS_ENABLED=false
WEBSERVER_SYNC_ENABLED=false
PERFORMANCE_TRACKING_ENABLED=false
```

## Configuration Management

### Loading Configuration

```python
from config import Config

# Load configuration
config = Config()

# Access configuration values
api_key = config.COINBASE_API_KEY
risk_level = config.RISK_LEVEL
trading_pairs = config.TRADING_PAIRS  # Returns list
```

### Runtime Configuration Updates

Some configuration can be updated at runtime:

```python
# Update strategy weights
config.update_strategy_weights({
    'TREND_FOLLOWING_WEIGHT': 0.5,
    'MEAN_REVERSION_WEIGHT': 0.3,
    'MOMENTUM_WEIGHT': 0.2
})

# Update risk parameters
config.update_risk_settings({
    'RISK_LEVEL': 'LOW',
    'MAX_POSITION_SIZE_PERCENT': 50
})
```

### Configuration Backup

```python
def backup_configuration():
    """Create a backup of current configuration"""
    
    config_backup = {
        'timestamp': datetime.utcnow().isoformat(),
        'environment_variables': dict(os.environ),
        'computed_values': {
            'trading_pairs': config.TRADING_PAIRS,
            'strategy_weights': config.get_strategy_weights(),
            'risk_parameters': config.get_risk_parameters()
        }
    }
    
    backup_file = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(f"backups/{backup_file}", 'w') as f:
        json.dump(config_backup, f, indent=2)
    
    return backup_file
```

## Troubleshooting Configuration

### Common Issues

#### 1. API Authentication Errors
```bash
# Check API key format
echo $COINBASE_API_KEY
# Should start with: organizations/

# Check private key format
head -1 <<< "$COINBASE_API_SECRET"
# Should be: -----BEGIN EC PRIVATE KEY-----
```

#### 2. Google Cloud Setup Issues
```bash
# Check service account file
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
gcloud auth application-default print-access-token
```

#### 3. Configuration Validation
```python
# Run configuration health check
python -c "from config import Config; c = Config(); print(c.validate_all())"
```

### Configuration Debugging

```python
def debug_configuration():
    """Debug configuration loading and validation"""
    
    print("=== Configuration Debug ===")
    print(f"Environment file exists: {os.path.exists('.env')}")
    print(f"Required variables present: {check_required_variables()}")
    print(f"API credentials format valid: {validate_credential_format()}")
    print(f"Numeric values valid: {validate_numeric_values()}")
    print(f"Strategy weights sum to 1.0: {sum(get_strategy_weights().values())}")
    
    # Test API connections
    try:
        coinbase_client = CoinbaseClient()
        print("✓ Coinbase API connection successful")
    except Exception as e:
        print(f"✗ Coinbase API connection failed: {e}")
    
    try:
        llm_analyzer = LLMAnalyzer()
        print("✓ Google AI connection successful")
    except Exception as e:
        print(f"✗ Google AI connection failed: {e}")
```

This comprehensive configuration guide ensures proper setup and operation of the AI crypto trading bot across all environments.