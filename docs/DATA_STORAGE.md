# Data Storage Documentation

This document provides comprehensive information about how the AI crypto trading bot stores, manages, and persists data across all system components.

## Overview

The AI crypto trading bot uses a **file-based storage architecture** with JSON files as the primary persistence mechanism. This approach provides simplicity, transparency, and reliability while maintaining the ability to inspect and recover data manually when needed.

## Storage Architecture

### Design Principles

1. **Transparency**: All data stored in human-readable formats (JSON, text)
2. **Atomicity**: All critical writes are atomic to prevent corruption
3. **Recoverability**: Multiple fallback mechanisms for data recovery
4. **Performance**: Efficient storage formats for large datasets (Parquet)
5. **Security**: Sensitive data never persisted to disk

### Directory Structure

```
AI-crypto-bot/
├── data/                           # Primary data storage
│   ├── portfolio.json              # Current portfolio state (CRITICAL)
│   ├── performance/                # Performance tracking
│   │   ├── performance_config.json     # Tracking configuration
│   │   ├── portfolio_snapshots.json    # Historical snapshots
│   │   ├── performance_metrics.json    # Calculated metrics
│   │   └── performance_periods.json    # Performance periods
│   ├── cache/                      # Session and temporary data
│   │   ├── bot_startup.json           # Bot startup metadata
│   │   └── latest_decisions.json      # Recent trading decisions
│   ├── historical/                 # Market data (Parquet)
│   │   ├── BTC-EUR_hour_180d.parquet   # Bitcoin hourly data
│   │   ├── ETH-EUR_hour_30d.parquet    # Ethereum hourly data
│   │   └── SOL-EUR_daily_90d.parquet   # Solana daily data
│   └── backtest_results/           # Backtesting outputs
│       └── performance_report.md
├── logs/                           # Application logs
│   ├── supervisor.log              # Main application logs
│   ├── daily_report.log           # Report generation logs
│   └── daily_report_20241228.txt  # Generated daily reports
├── reports/                        # Analysis reports
│   ├── interval_optimization/      # Trading interval analysis
│   ├── daily_health/              # Daily health checks
│   └── weekly_validation/         # Weekly validation reports
└── dashboard/data/backtest_results/ # Dashboard data
    ├── latest_backtest.json       # Latest backtest for web UI
    ├── data_summary.json          # Market data summary
    ├── strategy_comparison.json   # Strategy performance
    └── update_status.json         # Dashboard sync status
```

## Core Data Components

### 1. Portfolio State (`data/portfolio.json`)

**Purpose**: Stores the current state of the trading portfolio including asset balances, prices, and metadata.

**Critical Importance**: This is the most important file in the system. Portfolio corruption can lead to trading errors.

**Structure**:
```json
{
  "trades_executed": 42,
  "portfolio_value_eur": {
    "amount": 1250.75,
    "last_price_eur": 1.0
  },
  "initial_value_eur": {
    "amount": 1000.0,
    "last_price_eur": 1.0
  },
  "last_updated": "2024-12-28T10:30:45.123456",
  "EUR": {
    "amount": 150.25,
    "initial_amount": 200.0
  },
  "BTC": {
    "amount": 0.02456789,
    "initial_amount": 0.02000000,
    "last_price_eur": 42500.50
  },
  "ETH": {
    "amount": 0.45678901,
    "initial_amount": 0.40000000,
    "last_price_eur": 2850.75
  }
}
```

**Key Fields**:
- `trades_executed`: Total number of trades executed
- `portfolio_value_eur`: Current total portfolio value in EUR
- `initial_value_eur`: Initial portfolio value for performance calculation
- `last_updated`: Timestamp of last portfolio update
- Asset entries: Each supported asset (EUR, BTC, ETH, SOL) with amounts and prices

**Update Frequency**: Every portfolio change (trades, price updates, exchange sync)

**Backup Strategy**: 
- Automatic `.bak` file creation before each write
- Fallback to exchange data if file is corrupted
- Cloud backup sync (optional)

### 2. Performance Tracking (`data/performance/`)

**Purpose**: Maintains historical performance data that survives bot restarts and provides comprehensive performance analytics.

#### Performance Configuration (`performance_config.json`)
```json
{
  "tracking_start_date": "2024-01-01T00:00:00.000000",
  "initial_portfolio_value": 1000.0,
  "initial_portfolio_composition": {
    "EUR": {"amount": 200.0},
    "BTC": {"amount": 0.02, "last_price_eur": 40000.0}
  },
  "performance_reset_history": [
    {
      "date": "2024-01-01T00:00:00.000000",
      "reason": "initial_setup",
      "portfolio_value": 1000.0,
      "portfolio_composition": {...}
    }
  ],
  "snapshot_frequency": "daily",
  "last_snapshot_date": "2024-12-28T00:00:00.000000",
  "tracking_enabled": true,
  "created_date": "2024-01-01T00:00:00.000000",
  "version": "1.0"
}
```

#### Portfolio Snapshots (`portfolio_snapshots.json`)
```json
[
  {
    "timestamp": "2024-12-28T00:00:00.000000",
    "total_value_eur": 1250.75,
    "portfolio_composition": {
      "EUR": {"amount": 150.25},
      "BTC": {"amount": 0.02456789, "last_price_eur": 42500.50}
    },
    "asset_prices": {
      "BTC": 42500.50,
      "ETH": 2850.75
    },
    "snapshot_type": "scheduled",
    "trading_session_id": "session_20241228_001"
  }
]
```

**Snapshot Types**:
- `scheduled`: Regular automated snapshots
- `initial_setup`: First snapshot when tracking starts
- `performance_reset`: Snapshot taken during performance reset
- `manual`: Manually triggered snapshots

**Retention Policy**: Configurable (default: 365 days)

### 3. Historical Market Data (`data/historical/`)

**Purpose**: Stores historical price and volume data for backtesting and analysis.

**Format**: Apache Parquet for efficient storage and fast loading

**File Naming Convention**: `{ASSET}-{BASE}_{granularity}_{period}.parquet`

**Examples**:
- `BTC-EUR_hour_180d.parquet`: Bitcoin hourly data for 180 days
- `ETH-EUR_daily_30d.parquet`: Ethereum daily data for 30 days
- `SOL-EUR_minute_7d.parquet`: Solana minute data for 7 days

**Data Schema**:
```
timestamp: datetime64[ns]
open: float64
high: float64
low: float64
close: float64
volume: float64
```

**Compression**: Snappy compression for optimal performance

**Sync Strategy**: Optional backup to Google Cloud Storage

### 4. Cache Data (`data/cache/`)

**Purpose**: Temporary and session data that doesn't need long-term persistence.

#### Bot Startup Metadata (`bot_startup.json`)
```json
{
  "pid": 12345,
  "startup_time": "2024-12-28T08:00:00.000000",
  "session_id": "session_20241228_001",
  "restart_context": "normal",
  "config_hash": "abc123def456"
}
```

#### Latest Trading Decisions (`latest_decisions.json`)
```json
[
  {
    "timestamp": "2024-12-28T10:30:00.000000",
    "product_id": "BTC-EUR",
    "decision": "BUY",
    "confidence": 75,
    "reasoning": "Strong upward trend with high volume",
    "strategies": {
      "trend_following": {"signal": "BUY", "confidence": 80},
      "mean_reversion": {"signal": "HOLD", "confidence": 60},
      "momentum": {"signal": "BUY", "confidence": 85}
    }
  }
]
```

### 5. Logs (`logs/`)

**Purpose**: Application logs for debugging, monitoring, and audit trails.

#### Main Application Log (`supervisor.log`)
- Rotating log file with configurable size limits
- Contains all application events, errors, and debug information
- Sanitized to remove sensitive data (API keys, private keys)

#### Daily Report Log (`daily_report.log`)
- Specific to daily report generation process
- Includes AI analysis requests and responses
- Performance metrics and email delivery status

#### Generated Reports (`daily_report_*.txt`)
- AI-generated daily trading reports
- Timestamped files for historical reference
- Human-readable format for easy review

### 6. Analysis Reports (`reports/`)

**Purpose**: Results from various analysis and optimization processes.

#### Interval Optimization (`interval_optimization/`)
```json
{
  "analysis_date": "2024-12-28T12:00:00.000000",
  "intervals_tested": [15, 30, 60, 120, 240],
  "best_interval": 60,
  "results": {
    "15": {"total_return": 5.2, "sharpe_ratio": 0.8, "max_drawdown": -8.5},
    "60": {"total_return": 12.8, "sharpe_ratio": 1.4, "max_drawdown": -6.2}
  },
  "recommendation": "Continue using 60-minute intervals"
}
```

#### Daily Health Checks (`daily_health/`)
```json
{
  "check_date": "2024-12-28",
  "overall_health": "healthy",
  "strategy_performance": {
    "trend_following": {"status": "good", "recent_accuracy": 0.72},
    "mean_reversion": {"status": "warning", "recent_accuracy": 0.58}
  },
  "system_metrics": {
    "api_response_time": 245,
    "data_freshness": "current",
    "error_rate": 0.02
  }
}
```

### 7. Dashboard Data (`dashboard/data/backtest_results/`)

**Purpose**: Processed data optimized for web dashboard consumption.

#### Latest Backtest Results (`latest_backtest.json`)
```json
{
  "backtest_date": "2024-12-28T12:00:00.000000",
  "period": "30d",
  "strategies": {
    "trend_following": {
      "total_return": 8.5,
      "sharpe_ratio": 1.2,
      "max_drawdown": -5.8,
      "win_rate": 0.68
    }
  },
  "portfolio_evolution": [
    {"date": "2024-12-01", "value": 1000.0},
    {"date": "2024-12-28", "value": 1085.0}
  ]
}
```

## Data Operations

### File I/O Patterns

#### Atomic Write Operations
All critical data writes use atomic operations to prevent corruption:

```python
def save_portfolio_atomically(portfolio_data: dict):
    """Save portfolio data with atomic write operation"""
    import tempfile
    import os
    import json
    
    portfolio_file = "data/portfolio.json"
    
    # Create temporary file in same directory
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', 
        dir=os.path.dirname(portfolio_file),
        delete=False,
        suffix='.tmp'
    )
    
    try:
        # Write data to temporary file
        json.dump(portfolio_data, temp_file, indent=2, default=str)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        
        # Create backup of current file
        if os.path.exists(portfolio_file):
            os.replace(portfolio_file, f"{portfolio_file}.bak")
        
        # Atomic move to final location
        os.replace(temp_file.name, portfolio_file)
        
        logger.info("Portfolio saved successfully")
        
    except Exception as e:
        # Cleanup on failure
        try:
            os.unlink(temp_file.name)
        except:
            pass
        raise e
```

#### Data Validation and Recovery
All data loading includes validation and recovery mechanisms:

```python
def load_portfolio_with_recovery():
    """Load portfolio with validation and recovery"""
    portfolio_file = "data/portfolio.json"
    backup_file = f"{portfolio_file}.bak"
    
    # Try to load primary file
    portfolio_data = validate_and_load_json(portfolio_file, validate_portfolio_schema)
    if portfolio_data is not None:
        return portfolio_data
    
    logger.warning("Primary portfolio file corrupted, trying backup")
    
    # Try backup file
    if os.path.exists(backup_file):
        portfolio_data = validate_and_load_json(backup_file, validate_portfolio_schema)
        if portfolio_data is not None:
            logger.info("Recovered portfolio from backup file")
            # Restore backup as primary
            os.replace(backup_file, portfolio_file)
            return portfolio_data
    
    logger.error("Both portfolio files corrupted, fetching from exchange")
    
    # Last resort: fetch from exchange
    try:
        client = CoinbaseClient()
        exchange_portfolio = client.get_portfolio()
        if exchange_portfolio:
            logger.info("Portfolio recovered from exchange")
            return exchange_portfolio
    except Exception as e:
        logger.error(f"Failed to recover from exchange: {e}")
    
    # Create default portfolio
    logger.warning("Creating default portfolio")
    return create_default_portfolio()
```

### Performance Optimization

#### Caching Strategy
Frequently accessed data is cached in memory with TTL:

```python
class DataCache:
    """In-memory cache for frequently accessed data"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str, loader_func: callable):
        """Get data from cache or load fresh"""
        now = time.time()
        
        # Check if cached data is still valid
        if (key in self.cache and 
            key in self.timestamps and
            now - self.timestamps[key] < self.ttl):
            return self.cache[key]
        
        # Load fresh data
        data = loader_func()
        self.cache[key] = data
        self.timestamps[key] = now
        
        return data
    
    def invalidate(self, key: str):
        """Invalidate cached data"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
```

#### Batch Operations
Multiple related operations are batched when possible:

```python
def update_portfolio_batch(updates: List[Dict]):
    """Batch multiple portfolio updates"""
    portfolio = load_portfolio()
    
    for update in updates:
        if update['type'] == 'price_update':
            portfolio[update['asset']]['last_price_eur'] = update['price']
        elif update['type'] == 'amount_update':
            portfolio[update['asset']]['amount'] = update['amount']
    
    # Recalculate portfolio value once
    calculate_portfolio_value(portfolio)
    
    # Single atomic save
    save_portfolio_atomically(portfolio)
```

### Cloud Storage Integration

#### Google Cloud Storage Sync
Critical data is optionally synced to Google Cloud Storage for backup:

```python
def sync_to_gcs(local_files: List[str], gcs_bucket: str):
    """Sync local files to Google Cloud Storage"""
    from google.cloud import storage
    
    client = storage.Client()
    bucket = client.bucket(gcs_bucket)
    
    for local_file in local_files:
        try:
            # Create blob with metadata
            blob_name = f"backup/{datetime.now().strftime('%Y/%m/%d')}/{os.path.basename(local_file)}"
            blob = bucket.blob(blob_name)
            
            # Add metadata
            blob.metadata = {
                'source': 'ai-crypto-bot',
                'backup_date': datetime.now().isoformat(),
                'file_type': 'portfolio_data' if 'portfolio' in local_file else 'performance_data'
            }
            
            # Upload file
            blob.upload_from_filename(local_file)
            logger.info(f"Synced {local_file} to gs://{gcs_bucket}/{blob_name}")
            
        except Exception as e:
            logger.error(f"Failed to sync {local_file}: {e}")
```

## Data Security

### Sensitive Data Handling

**Never Stored**:
- API keys and secrets
- Private keys
- Authentication tokens
- User credentials

**Sanitization**: All logs are sanitized to remove sensitive information:

```python
def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive data before logging"""
    sensitive_patterns = [
        'api_key', 'api_secret', 'private_key', 'password',
        'token', 'credential', 'auth', 'secret'
    ]
    
    sanitized = {}
    for key, value in data.items():
        if any(pattern in key.lower() for pattern in sensitive_patterns):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_log_data(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized
```

### File Permissions

**Recommended Permissions**:
- Data directory: `750` (owner: rwx, group: r-x, other: ---)
- JSON files: `640` (owner: rw-, group: r--, other: ---)
- Log files: `644` (owner: rw-, group: r--, other: r--)
- Backup files: `600` (owner: rw-, group: ---, other: ---)

## Monitoring and Health Checks

### Storage Health Monitoring

```python
def get_storage_health_status() -> dict:
    """Comprehensive storage health check"""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'healthy'
    }
    
    # Check critical files
    critical_files = [
        'data/portfolio.json',
        'data/performance/performance_config.json'
    ]
    
    for file_path in critical_files:
        file_status = {
            'exists': os.path.exists(file_path),
            'size_bytes': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat() if os.path.exists(file_path) else None,
            'readable': os.access(file_path, os.R_OK) if os.path.exists(file_path) else False,
            'writable': os.access(file_path, os.W_OK) if os.path.exists(file_path) else False
        }
        
        health_status[f'file_{os.path.basename(file_path)}'] = file_status
        
        if not file_status['exists'] or not file_status['readable']:
            health_status['overall_status'] = 'critical'
    
    # Check disk usage
    disk_usage = shutil.disk_usage('data/')
    health_status['disk_usage'] = {
        'total_gb': disk_usage.total / (1024**3),
        'used_gb': disk_usage.used / (1024**3),
        'free_gb': disk_usage.free / (1024**3),
        'usage_percent': (disk_usage.used / disk_usage.total) * 100
    }
    
    if health_status['disk_usage']['usage_percent'] > 90:
        health_status['overall_status'] = 'warning'
    
    # Check data freshness
    portfolio_file = 'data/portfolio.json'
    if os.path.exists(portfolio_file):
        last_modified = datetime.fromtimestamp(os.path.getmtime(portfolio_file))
        age_minutes = (datetime.now() - last_modified).total_seconds() / 60
        
        health_status['data_freshness'] = {
            'portfolio_age_minutes': age_minutes,
            'is_stale': age_minutes > 120  # Consider stale if older than 2 hours
        }
        
        if health_status['data_freshness']['is_stale']:
            health_status['overall_status'] = 'warning'
    
    return health_status
```

### Automated Alerts

```python
def check_and_alert_storage_issues():
    """Check storage health and send alerts if needed"""
    health_status = get_storage_health_status()
    
    if health_status['overall_status'] in ['warning', 'critical']:
        alert_message = f"Storage health status: {health_status['overall_status']}\n"
        
        # Add specific issues
        for key, value in health_status.items():
            if isinstance(value, dict) and 'exists' in value and not value['exists']:
                alert_message += f"- Missing file: {key}\n"
            elif key == 'disk_usage' and value['usage_percent'] > 90:
                alert_message += f"- High disk usage: {value['usage_percent']:.1f}%\n"
            elif key == 'data_freshness' and value.get('is_stale'):
                alert_message += f"- Stale data: Portfolio not updated for {value['portfolio_age_minutes']:.0f} minutes\n"
        
        # Send alert (implementation depends on notification system)
        send_storage_alert(alert_message, health_status['overall_status'])
```

## Backup and Recovery

### Backup Strategy

#### Local Backups
- **Automatic**: `.bak` files created before each critical file update
- **Retention**: Keep last 5 backup versions
- **Validation**: Backup files validated before original is overwritten

#### Cloud Backups
- **Frequency**: Daily sync to Google Cloud Storage
- **Retention**: 30 days for daily backups, 12 months for monthly backups
- **Encryption**: Data encrypted in transit and at rest

#### Backup Verification
```python
def verify_backup_integrity():
    """Verify backup file integrity"""
    backup_files = [
        'data/portfolio.json.bak',
        'data/performance/performance_config.json.bak'
    ]
    
    verification_results = {}
    
    for backup_file in backup_files:
        if not os.path.exists(backup_file):
            verification_results[backup_file] = {'status': 'missing'}
            continue
        
        try:
            # Try to load and validate backup
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            # Basic validation
            if isinstance(data, dict) and len(data) > 0:
                verification_results[backup_file] = {
                    'status': 'valid',
                    'size_bytes': os.path.getsize(backup_file),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(backup_file)).isoformat()
                }
            else:
                verification_results[backup_file] = {'status': 'invalid_content'}
                
        except Exception as e:
            verification_results[backup_file] = {
                'status': 'corrupted',
                'error': str(e)
            }
    
    return verification_results
```

### Recovery Procedures

#### Portfolio Recovery
1. **Automatic Recovery**: System automatically tries backup files if primary is corrupted
2. **Exchange Recovery**: Fetch current state from Coinbase if local files fail
3. **Manual Recovery**: Restore from cloud backups if needed

#### Performance Data Recovery
1. **Reinitialize Tracking**: Start fresh tracking from current portfolio state
2. **Partial Recovery**: Recover what's possible from backup files
3. **Historical Reconstruction**: Rebuild from trade logs if available

#### Complete System Recovery
```bash
# Recovery script example
#!/bin/bash

echo "Starting AI Crypto Bot data recovery..."

# Create backup of current state
mkdir -p recovery_backup
cp -r data/ recovery_backup/ 2>/dev/null || true

# Download latest backups from GCS
gsutil -m cp -r gs://your-backup-bucket/backup/latest/ data/

# Verify recovered data
python -c "
from utils.trading.portfolio import Portfolio
from utils.performance.performance_tracker import PerformanceTracker

try:
    portfolio = Portfolio()
    print('✓ Portfolio data recovered successfully')
except Exception as e:
    print(f'✗ Portfolio recovery failed: {e}')

try:
    tracker = PerformanceTracker()
    print('✓ Performance data recovered successfully')
except Exception as e:
    print(f'✗ Performance recovery failed: {e}')
"

echo "Recovery complete. Check logs for any issues."
```

## Best Practices

### Development Guidelines

1. **Always Use Atomic Writes**: Never write directly to critical files
2. **Validate All Data**: Check structure and content on every load
3. **Handle Corruption Gracefully**: Implement fallback mechanisms
4. **Log All Operations**: Track all data operations for debugging
5. **Test Recovery Procedures**: Regularly test backup and recovery

### Production Guidelines

1. **Monitor Storage Health**: Implement automated health checks
2. **Regular Backups**: Ensure backup systems are working
3. **Disk Space Management**: Monitor and clean up old data
4. **Performance Monitoring**: Track file I/O performance
5. **Security Auditing**: Regular security reviews of data handling

### Testing Requirements

1. **Mock File Operations**: Use temporary files in tests
2. **Test Corruption Scenarios**: Simulate file corruption and recovery
3. **Validate Backup Procedures**: Test backup creation and restoration
4. **Performance Testing**: Test with large datasets
5. **Security Testing**: Verify sensitive data is never persisted

## Troubleshooting

### Common Issues

#### Portfolio File Corruption
**Symptoms**: JSON parsing errors, missing fields, invalid data types
**Solutions**:
1. Check `.bak` file and restore if valid
2. Fetch fresh data from exchange
3. Create new portfolio with current exchange state

#### Performance Data Loss
**Symptoms**: Missing snapshots, tracking disabled, calculation errors
**Solutions**:
1. Reinitialize performance tracking from current state
2. Restore from cloud backups if available
3. Rebuild from trade history logs

#### Disk Space Issues
**Symptoms**: Write failures, slow performance, system alerts
**Solutions**:
1. Clean up old log files and reports
2. Archive historical data to cloud storage
3. Implement automated cleanup policies

#### Permission Problems
**Symptoms**: Access denied errors, unable to write files
**Solutions**:
1. Check file and directory permissions
2. Ensure bot process has correct ownership
3. Fix permissions with appropriate chmod commands

### Diagnostic Commands

```bash
# Check data directory structure
find data/ -type f -name "*.json" -exec ls -la {} \;

# Validate JSON files
find data/ -name "*.json" -exec python -m json.tool {} \; > /dev/null

# Check disk usage
du -sh data/ logs/ reports/

# Monitor file changes
inotifywait -m -r data/ --format '%w%f %e %T' --timefmt '%Y-%m-%d %H:%M:%S'

# Test portfolio loading
python -c "from utils.trading.portfolio import Portfolio; p = Portfolio(); print('Portfolio loaded successfully')"
```

This comprehensive data storage system ensures reliable, secure, and maintainable data persistence for the AI crypto trading bot across all operational environments.