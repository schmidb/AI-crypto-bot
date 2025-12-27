# Configuration Management Steering Document

## Configuration Philosophy & Standards

### Environment-Based Configuration
- **Primary Source**: Environment variables via `.env` file
- **Fallback Values**: Sensible defaults in `config.py`
- **Type Safety**: Explicit type conversion with validation
- **Security**: Never commit sensitive credentials to repository

### Configuration Structure

#### Core Configuration Class
```python
class Config:
    """Centralized configuration management"""
    def __init__(self):
        # Always load from environment with defaults
        self.COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
        self.RISK_LEVEL = os.getenv("RISK_LEVEL", "medium")
        self.SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"
```

#### Environment Variable Standards
- **Naming**: UPPERCASE_WITH_UNDERSCORES
- **Boolean Values**: "true"/"false" strings, converted to bool
- **Numeric Values**: String representation, converted with validation
- **Lists**: Comma-separated strings, split into arrays
- **Sensitive Data**: API keys, secrets, credentials

### Configuration Categories

#### Trading Configuration
```env
# Core Trading Settings
BASE_CURRENCY=EUR                    # Base currency for trading
TRADING_PAIRS=BTC-EUR,ETH-EUR        # Comma-separated trading pairs
DECISION_INTERVAL_MINUTES=60         # Trading decision frequency
RISK_LEVEL=HIGH                      # LOW, MEDIUM, HIGH
SIMULATION_MODE=false                # true for paper trading

# Strategy Thresholds
CONFIDENCE_THRESHOLD_BUY=55          # Minimum confidence for BUY
CONFIDENCE_THRESHOLD_SELL=55         # Minimum confidence for SELL
```

#### API Configuration
```env
# Coinbase Advanced Trade API
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n

# Google Cloud AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
LLM_MODEL=gemini-3-flash-preview
LLM_LOCATION=global
```

#### Risk Management Configuration
```env
# Position Sizing
MIN_TRADE_AMOUNT=5.0                # Minimum trade size (EUR)
MAX_POSITION_SIZE_PERCENT=75        # Max single trade size (% of EUR balance)
TARGET_EUR_ALLOCATION=12            # Target EUR allocation %
MIN_EUR_RESERVE=15.0                # Minimum EUR reserve

# Risk Multipliers
RISK_HIGH_POSITION_MULTIPLIER=0.5   # 50% reduction for high risk
RISK_MEDIUM_POSITION_MULTIPLIER=0.75 # 25% reduction for medium risk
RISK_LOW_POSITION_MULTIPLIER=1.0    # No reduction for low risk
```

### Configuration Validation

#### Type Conversion with Validation
```python
def safe_float_conversion(value: str, default: float, min_val: float = None, max_val: float = None) -> float:
    """Safely convert string to float with validation"""
    try:
        result = float(value)
        if min_val is not None and result < min_val:
            logger.warning(f"Value {result} below minimum {min_val}, using default {default}")
            return default
        if max_val is not None and result > max_val:
            logger.warning(f"Value {result} above maximum {max_val}, using default {default}")
            return default
        return result
    except (ValueError, TypeError):
        logger.warning(f"Invalid float value '{value}', using default {default}")
        return default
```

#### Required vs Optional Settings
```python
# Required settings (must be provided)
required_settings = ['COINBASE_API_KEY', 'COINBASE_API_SECRET', 'GOOGLE_CLOUD_PROJECT']

# Validate required settings
for setting in required_settings:
    if not getattr(config, setting):
        raise ValueError(f"Required setting {setting} is missing")
```

### Environment Management

#### Development Environment (.env.example)
```env
# Copy to .env and fill in your values
COINBASE_API_KEY=your_api_key_here
COINBASE_API_SECRET=your_private_key_here
GOOGLE_CLOUD_PROJECT=your_project_id
SIMULATION_MODE=true                 # Always true for development
NOTIFICATIONS_ENABLED=false          # Disable notifications in dev
```

#### Production Environment
```env
# Production settings
SIMULATION_MODE=false                # Real trading
NOTIFICATIONS_ENABLED=true          # Enable alerts
LOG_LEVEL=INFO                      # Appropriate logging level
WEBSERVER_SYNC_ENABLED=true         # Enable dashboard sync
```

#### Testing Environment
```python
# Automatically set in tests
test_env_vars = {
    'TESTING': 'true',
    'SIMULATION_MODE': 'true',
    'COINBASE_API_KEY': 'test-api-key',
    'NOTIFICATIONS_ENABLED': 'false',
    'WEBSERVER_SYNC_ENABLED': 'false'
}
```

### Security Best Practices

#### Credential Management
- **Never Commit**: API keys, secrets, private keys to repository
- **Environment Variables**: Store sensitive data in environment only
- **Key Rotation**: Support for updating credentials without code changes
- **Validation**: Verify credential format and basic validity

#### API Key Security
```python
def validate_coinbase_credentials(api_key: str, api_secret: str) -> bool:
    """Validate Coinbase API credential format"""
    if not api_key or not api_secret:
        return False
    
    # API key should start with organizations/
    if not api_key.startswith('organizations/'):
        logger.error("Invalid Coinbase API key format")
        return False
    
    # Private key should be PEM format
    if not api_secret.startswith('-----BEGIN EC PRIVATE KEY-----'):
        logger.error("Invalid Coinbase API secret format")
        return False
    
    return True
```

### Configuration Loading Order

#### Priority Hierarchy
1. **Environment Variables**: Highest priority
2. **Config Class Defaults**: Fallback values
3. **System Defaults**: Last resort safe values

#### Loading Process
```python
def load_configuration():
    """Load configuration with proper precedence"""
    # 1. Load .env file
    load_dotenv()
    
    # 2. Initialize config with environment variables
    config = Config()
    
    # 3. Validate required settings
    validate_required_settings(config)
    
    # 4. Log configuration summary (without sensitive data)
    log_configuration_summary(config)
    
    return config
```

### Configuration Monitoring

#### Runtime Configuration Changes
- **Hot Reload**: Support for configuration updates without restart
- **Validation**: Validate changes before applying
- **Rollback**: Ability to revert to previous configuration
- **Audit Trail**: Log all configuration changes

#### Configuration Health Checks
```python
def validate_configuration_health(config: Config) -> Dict[str, bool]:
    """Validate current configuration health"""
    health_checks = {
        'api_credentials_valid': validate_coinbase_credentials(config.COINBASE_API_KEY, config.COINBASE_API_SECRET),
        'trading_pairs_valid': validate_trading_pairs(config.TRADING_PAIRS),
        'risk_settings_valid': validate_risk_settings(config),
        'thresholds_valid': validate_confidence_thresholds(config)
    }
    return health_checks
```

### Backward Compatibility

#### Legacy Support
```python
# Support old environment variable names
self.TARGET_BASE_ALLOCATION = float(os.getenv("TARGET_BASE_ALLOCATION", 
                                              os.getenv("TARGET_USD_ALLOCATION", "20")))
self.MIN_TRADE_AMOUNT = float(os.getenv("MIN_TRADE_AMOUNT", 
                                       os.getenv("MIN_TRADE_USD", "10.0")))
```

#### Migration Warnings
```python
if os.getenv("TARGET_USD_ALLOCATION"):
    logger.warning("TARGET_USD_ALLOCATION is deprecated, use TARGET_BASE_ALLOCATION")
```

### Configuration Documentation

#### Environment Variable Documentation
- **Purpose**: What each variable controls
- **Type**: Expected data type and format
- **Default**: Default value if not specified
- **Examples**: Sample values for different scenarios
- **Dependencies**: Related variables or requirements

#### Configuration Templates
```env
# Trading Configuration Template
# Copy to .env and customize for your setup

# Required: Coinbase API credentials
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END EC PRIVATE KEY-----\n

# Required: Google Cloud settings
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Trading Settings (customize as needed)
TRADING_PAIRS=BTC-EUR,ETH-EUR        # Supported: BTC-EUR, ETH-EUR, SOL-EUR
RISK_LEVEL=MEDIUM                    # Options: LOW, MEDIUM, HIGH
SIMULATION_MODE=true                 # Set to false for live trading
```

### Troubleshooting

#### Common Configuration Issues
1. **Missing Required Variables**: Check .env file exists and contains all required settings
2. **Invalid Format**: Verify API keys, numeric values, boolean strings
3. **Permission Issues**: Ensure service account has necessary permissions
4. **Environment Loading**: Verify .env file is in correct location

#### Configuration Debugging
```python
def debug_configuration():
    """Debug configuration loading issues"""
    logger.info("=== Configuration Debug ===")
    logger.info(f"Environment file exists: {os.path.exists('.env')}")
    logger.info(f"Required variables present: {check_required_variables()}")
    logger.info(f"API credentials format valid: {validate_credential_format()}")
    logger.info(f"Numeric values valid: {validate_numeric_values()}")
```

This configuration management approach ensures consistent, secure, and maintainable settings across all environments.