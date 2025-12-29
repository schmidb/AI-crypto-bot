# Logging Standards Steering Document

## Logging Philosophy & Standards

### Structured Logging Architecture
- **Primary Goal**: Clean, actionable logs without noise
- **Log Separation**: Different log files for different purposes
- **Automatic Management**: Rotation, compression, and cleanup
- **Intelligent Filtering**: Remove repetitive and non-essential messages

### Log File Structure

#### Core Log Files
```
logs/
├── trading_bot.log          # Main application log (5MB max, 3 backups)
├── trading_decisions.log    # Trading decisions only (2MB max, 5 backups)
├── errors.log              # Errors and warnings only (2MB max, 3 backups)
├── bot_clean_YYYYMMDD.log  # Clean startup logs
└── *.gz                    # Compressed archived logs
```

#### Log File Purposes
- **trading_bot.log**: All application activity with noise filtered
- **trading_decisions.log**: BUY/SELL/HOLD decisions and portfolio updates only
- **errors.log**: WARNING, ERROR, and CRITICAL messages only
- **startup logs**: Individual bot restart sessions

### Logging Configuration Standards

#### Log Levels and Filtering
```python
# Use structured logging functions
from utils.logging_config import log_trading_decision, log_portfolio_update, log_system_health

# Trading decisions
log_trading_decision(asset="BTC", action="BUY", confidence=75.5, reasoning="Strong uptrend")

# Portfolio updates  
log_portfolio_update(portfolio_value=1000.50, change_pct=2.3)

# System health
log_system_health(component="Coinbase API", status="healthy", details="Response time: 150ms")
```

#### Noise Filtering Rules
Automatically filter out:
- File system operations ("Hard link already exists", "Modified and copied HTML file")
- HTTP request details ("HTTP Request: POST", "AFC is enabled")
- Repetitive sync operations ("Synced X files", "Static files synced")
- Data validation confirmations ("Data validation complete")

#### Log Rotation Policy
- **Main Log**: 5MB max, 3 backups
- **Trading Log**: 2MB max, 5 backups (more history for analysis)
- **Error Log**: 2MB max, 3 backups
- **Compression**: Automatic gzip compression of rotated logs
- **Retention**: 30 days for compressed logs, 7 days for startup logs

### Log Monitoring Tools

#### Monitor Scripts
```bash
# View specific log types
./scripts/monitor_logs.sh trading    # Trading decisions only
./scripts/monitor_logs.sh errors     # Errors and warnings only
./scripts/monitor_logs.sh clean      # Filtered main activity
./scripts/monitor_logs.sh live       # Live monitoring (filtered)
./scripts/monitor_logs.sh status     # System status overview
```

#### Cleanup and Maintenance
```bash
# Manual cleanup
./scripts/cleanup_logs.sh

# Restart with clean logging
./scripts/restart_bot_clean.sh
```

### Console Output Standards

#### Colored and Filtered Console
- **Colors**: Different colors for log levels (Green=INFO, Yellow=WARNING, Red=ERROR)
- **Filtering**: Console shows only important messages, files contain everything
- **Formatting**: Timestamp, level, module, message format
- **Emphasis**: Bold formatting for critical trading decisions

#### Third-Party Logger Suppression
```python
# Suppress noisy third-party loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
```

### Automatic Log Management

#### System Integration
- **Logrotate**: Daily rotation via `/etc/logrotate.d/crypto-bot`
- **Compression**: Automatic gzip compression of large files
- **Cleanup**: Automatic removal of files older than retention period
- **Monitoring**: Log size and health monitoring

#### Rotation Configuration
```
/home/markus/AI-crypto-bot/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    maxsize 10M
}
```

### Performance Considerations

#### Log Performance
- **Async Logging**: Non-blocking log writes
- **Efficient Filtering**: Filter at handler level, not message level
- **Compression**: Reduce disk usage with automatic compression
- **Cleanup**: Prevent disk space issues with automatic cleanup

#### Disk Usage Management
- **Size Limits**: Strict limits on individual log files
- **Compression Ratios**: ~90% size reduction with gzip
- **Retention Policies**: Automatic cleanup of old files
- **Monitoring**: Disk usage alerts and reporting

### Troubleshooting and Debugging

#### Log Analysis Workflow
1. **Check Errors**: `./scripts/monitor_logs.sh errors`
2. **Review Trading**: `./scripts/monitor_logs.sh trading`
3. **Monitor Live**: `./scripts/monitor_logs.sh live`
4. **System Status**: `./scripts/monitor_logs.sh status`

#### Common Issues
- **Missing Logs**: Check file permissions and disk space
- **Large Files**: Run cleanup script or check rotation
- **No Output**: Verify logging configuration and handlers
- **Performance**: Check if log filtering is working properly

### Best Practices

#### Development Guidelines
- **Use Structured Functions**: Use `log_trading_decision()` instead of raw `logger.info()`
- **Appropriate Levels**: INFO for normal operations, WARNING for issues, ERROR for failures
- **Context Information**: Include relevant context (asset, amounts, timestamps)
- **Avoid Spam**: Don't log in tight loops or repetitive operations

#### Production Guidelines
- **Monitor Disk Usage**: Regular checks of log directory size
- **Review Error Logs**: Daily review of error log for issues
- **Performance Impact**: Ensure logging doesn't impact trading performance
- **Backup Important Logs**: Consider backing up trading decision logs

#### Security Considerations
- **No Sensitive Data**: Never log API keys, private keys, or credentials
- **Sanitize Inputs**: Remove or mask sensitive information from logs
- **File Permissions**: Appropriate permissions on log files (644)
- **Access Control**: Restrict access to log files containing trading data

This logging framework ensures clean, actionable logs that support effective monitoring and debugging of the AI crypto trading bot.
