# Data Storage Steering Document

## Data Storage Philosophy & Standards

### File-Based Storage Architecture
- **Primary Storage**: JSON files for structured data persistence
- **Historical Data**: Parquet format for efficient time-series storage
- **Atomic Operations**: All file writes must be atomic to prevent corruption
- **Graceful Degradation**: Fallback mechanisms for data recovery

### Storage Directory Structure

#### Core Data Directories
```
data/
├── portfolio.json              # Current portfolio state (CRITICAL)
├── performance/                # Performance tracking data
│   ├── performance_config.json     # Tracking configuration
│   ├── portfolio_snapshots.json    # Historical snapshots
│   ├── performance_metrics.json    # Calculated metrics
│   └── performance_periods.json    # Performance periods
├── cache/                      # Temporary and session data
│   ├── bot_startup.json           # Bot startup metadata
│   └── latest_decisions.json      # Recent trading decisions
├── historical/                 # Market data (Parquet format)
│   ├── {ASSET}-{BASE}_{granularity}_{period}.parquet
│   └── ...
└── backtest_results/          # Backtesting outputs
    └── performance_report.md

logs/                          # Application logs
├── supervisor.log             # Main application logs
├── daily_report.log          # Report generation logs
└── daily_report_*.txt        # Generated reports

reports/                       # Analysis reports
├── interval_optimization/     # Optimization results
├── daily_health/             # Health check results
└── weekly_validation/        # Validation results

dashboard/data/backtest_results/  # Dashboard data
├── latest_backtest.json      # Latest backtest for web UI
├── data_summary.json         # Market data summary
└── ...
```

### File Naming Conventions

#### JSON Data Files
- **Portfolio**: `portfolio.json` (singular, critical system file)
- **Performance**: `performance_{type}.json` (descriptive type)
- **Cache**: `{purpose}_{context}.json` (purpose-driven naming)
- **Reports**: `{analysis_type}_{timestamp}.json` (timestamped results)

#### Historical Data Files
- **Format**: `{ASSET}-{BASE}_{granularity}_{period}.parquet`
- **Examples**: 
  - `BTC-EUR_hour_180d.parquet`
  - `ETH-EUR_daily_30d.parquet`
  - `SOL-EUR_minute_7d.parquet`

#### Log Files
- **Application**: `{component}.log` (rotating logs)
- **Reports**: `{report_type}_{timestamp}.txt` (timestamped outputs)

### JSON Schema Standards

#### Portfolio Schema
```json
{
  "trades_executed": 0,
  "portfolio_value_eur": {"amount": 1000.0, "last_price_eur": 1.0},
  "initial_value_eur": {"amount": 1000.0, "last_price_eur": 1.0},
  "last_updated": "2024-01-01T00:00:00.000000",
  "EUR": {
    "amount": 100.0,
    "initial_amount": 100.0
  },
  "BTC": {
    "amount": 0.01,
    "initial_amount": 0.01,
    "last_price_eur": 45000.0
  }
}
```

#### Performance Snapshot Schema
```json
{
  "timestamp": "2024-01-01T00:00:00.000000",
  "total_value_eur": 1000.0,
  "portfolio_composition": {...},
  "asset_prices": {...},
  "snapshot_type": "scheduled|initial_setup|performance_reset",
  "trading_session_id": "session_id"
}
```

#### Configuration Schema
```json
{
  "tracking_start_date": "2024-01-01T00:00:00.000000",
  "initial_portfolio_value": 1000.0,
  "initial_portfolio_composition": {...},
  "performance_reset_history": [...],
  "snapshot_frequency": "daily|hourly|on_restart|manual",
  "last_snapshot_date": "2024-01-01T00:00:00.000000",
  "tracking_enabled": true,
  "created_date": "2024-01-01T00:00:00.000000",
  "version": "1.0"
}
```

### File Operation Standards

#### Atomic Write Pattern
```python
def save_data_atomically(file_path: str, data: dict):
    """Standard atomic write pattern for all JSON files"""
    import tempfile
    import os
    import json
    
    # Create temporary file in same directory
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', 
        dir=os.path.dirname(file_path),
        delete=False,
        suffix='.tmp'
    )
    
    try:
        # Write data to temporary file
        json.dump(data, temp_file, indent=2, default=str)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        
        # Atomic move to final location
        os.replace(temp_file.name, file_path)
        
    except Exception as e:
        # Cleanup on failure
        try:
            os.unlink(temp_file.name)
        except:
            pass
        raise e
```

#### Data Validation Pattern
```python
def validate_and_load_json(file_path: str, schema_validator: callable) -> dict:
    """Standard validation pattern for loading JSON files"""
    try:
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Validate structure
        validated_data = schema_validator(data)
        return validated_data
        
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None
```

### Data Persistence Strategies

#### Portfolio State Management
- **Frequency**: Save on every portfolio change
- **Backup**: Keep previous version as `.bak` file
- **Recovery**: Fallback to exchange data if corrupted
- **Validation**: Structure validation on every load

#### Performance Tracking
- **Snapshots**: Configurable frequency (hourly/daily)
- **Retention**: Configurable retention period (default: 365 days)
- **Cleanup**: Automatic old data removal
- **Reset Capability**: Maintain reset history for auditing

#### Historical Data
- **Format**: Parquet for efficient storage and fast loading
- **Compression**: Use snappy compression for Parquet files
- **Partitioning**: By asset and time period
- **Sync**: Optional cloud storage backup

### Error Handling & Recovery

#### File Corruption Recovery
```python
def load_with_recovery(primary_file: str, backup_file: str, default_factory: callable):
    """Standard recovery pattern for critical files"""
    # Try primary file
    data = validate_and_load_json(primary_file, validate_schema)
    if data is not None:
        return data
    
    # Try backup file
    if os.path.exists(backup_file):
        data = validate_and_load_json(backup_file, validate_schema)
        if data is not None:
            logger.warning(f"Recovered from backup: {backup_file}")
            return data
    
    # Create default data
    logger.error(f"Creating default data for {primary_file}")
    return default_factory()
```

#### Data Migration Pattern
```python
def migrate_data_version(data: dict, current_version: str) -> dict:
    """Handle data format migrations"""
    data_version = data.get("version", "1.0")
    
    if data_version != current_version:
        logger.info(f"Migrating data from {data_version} to {current_version}")
        
        # Apply migration transformations
        migrated_data = apply_migrations(data, data_version, current_version)
        migrated_data["version"] = current_version
        
        return migrated_data
    
    return data
```

### Performance Optimization

#### File I/O Best Practices
- **Batch Operations**: Group multiple writes when possible
- **Lazy Loading**: Load data only when needed
- **Caching**: Cache frequently accessed data in memory
- **Compression**: Use appropriate compression for large files

#### Memory Management
```python
class DataManager:
    """Standard data manager pattern"""
    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_data(self, key: str, loader: callable):
        """Get data with caching"""
        now = time.time()
        
        # Check cache validity
        if (key in self._cache and 
            key in self._cache_timestamps and
            now - self._cache_timestamps[key] < self.cache_ttl):
            return self._cache[key]
        
        # Load fresh data
        data = loader()
        self._cache[key] = data
        self._cache_timestamps[key] = now
        
        return data
```

### Cloud Storage Integration

#### Google Cloud Storage Sync
- **Purpose**: Backup critical data and share dashboard data
- **Files**: Performance data, backtest results, historical data
- **Frequency**: Configurable sync intervals
- **Security**: Use service account with minimal permissions

#### Sync Strategy
```python
def sync_to_cloud(local_path: str, gcs_path: str, metadata: dict = None):
    """Standard cloud sync pattern"""
    try:
        # Upload with metadata
        blob = bucket.blob(gcs_path)
        if metadata:
            blob.metadata = metadata
        
        blob.upload_from_filename(local_path)
        logger.info(f"Synced {local_path} to gs://{bucket_name}/{gcs_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync {local_path}: {e}")
        return False
```

### Security & Access Control

#### File Permissions
- **Data Directory**: 750 (owner: rwx, group: r-x, other: ---)
- **JSON Files**: 640 (owner: rw-, group: r--, other: ---)
- **Log Files**: 644 (owner: rw-, group: r--, other: r--)
- **Sensitive Files**: 600 (owner: rw-, group: ---, other: ---)

#### Data Sanitization
```python
def sanitize_for_logging(data: dict) -> dict:
    """Remove sensitive data before logging"""
    sensitive_keys = {
        'api_key', 'api_secret', 'private_key', 'password', 
        'token', 'credential', 'auth'
    }
    
    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_logging(value)
        else:
            sanitized[key] = value
    
    return sanitized
```

### Monitoring & Alerting

#### Data Health Checks
- **File Existence**: Verify critical files exist
- **Data Integrity**: Validate JSON structure and content
- **Size Monitoring**: Alert on unexpected file size changes
- **Age Monitoring**: Alert on stale data

#### Storage Metrics
```python
def get_storage_health() -> dict:
    """Standard storage health check"""
    return {
        'portfolio_file_exists': os.path.exists('data/portfolio.json'),
        'portfolio_file_size': get_file_size('data/portfolio.json'),
        'portfolio_last_modified': get_file_mtime('data/portfolio.json'),
        'performance_snapshots_count': count_snapshots(),
        'disk_usage_mb': get_directory_size('data/'),
        'oldest_snapshot_age_days': get_oldest_snapshot_age(),
        'backup_status': check_backup_status()
    }
```

### Backup & Disaster Recovery

#### Backup Strategy
- **Local Backups**: `.bak` files for critical data
- **Cloud Backups**: Regular sync to Google Cloud Storage
- **Retention**: Keep backups for configurable periods
- **Testing**: Regular backup restoration testing

#### Recovery Procedures
1. **Portfolio Corruption**: Restore from `.bak` file or exchange data
2. **Performance Data Loss**: Reinitialize tracking from current state
3. **Historical Data Loss**: Re-download from exchange APIs
4. **Complete Data Loss**: Restore from cloud backups

### Best Practices

#### Development Guidelines
- **Always use atomic writes** for critical data files
- **Validate data structure** on every load operation
- **Implement graceful degradation** for missing or corrupted files
- **Use consistent naming conventions** across all storage operations
- **Log all data operations** with appropriate detail level

#### Production Guidelines
- **Monitor disk usage** and implement cleanup policies
- **Regular backup verification** to ensure recovery capability
- **Performance monitoring** of file I/O operations
- **Security auditing** of file permissions and access patterns

#### Testing Requirements
- **Mock file operations** in unit tests
- **Test data corruption scenarios** and recovery procedures
- **Validate backup and restore procedures** regularly
- **Performance testing** of large data operations

This data storage framework ensures reliable, secure, and maintainable data persistence for the AI crypto trading bot across all operational environments.