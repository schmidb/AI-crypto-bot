# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the AI crypto trading bot.

## Quick Diagnostics

### Health Check Script

Run this script to quickly diagnose common issues:

```bash
python -c "
import os
import sys
from pathlib import Path

print('=== AI Crypto Trading Bot Health Check ===')
print(f'Python version: {sys.version}')
print(f'Working directory: {os.getcwd()}')
print(f'Virtual environment: {sys.prefix}')

# Check critical files
critical_files = ['.env', 'main.py', 'config.py', 'requirements.txt']
for file in critical_files:
    exists = Path(file).exists()
    print(f'{file}: {\"✓\" if exists else \"✗ MISSING\"}')

# Check environment variables
env_vars = ['COINBASE_API_KEY', 'GOOGLE_CLOUD_PROJECT', 'SIMULATION_MODE']
for var in env_vars:
    value = os.getenv(var)
    print(f'{var}: {\"✓ SET\" if value else \"✗ NOT SET\"}')

print('\\n=== Testing Imports ===')
try:
    from config import Config
    print('Config: ✓')
except Exception as e:
    print(f'Config: ✗ {e}')

try:
    from coinbase_client import CoinbaseClient
    print('CoinbaseClient: ✓')
except Exception as e:
    print(f'CoinbaseClient: ✗ {e}')

try:
    from llm_analyzer import LLMAnalyzer
    print('LLMAnalyzer: ✓')
except Exception as e:
    print(f'LLMAnalyzer: ✗ {e}')
"
```

## Common Issues

### 1. Bot Won't Start

#### Symptoms
- Bot exits immediately
- Import errors
- Configuration errors

#### Diagnosis
```bash
# Check Python version
python --version

# Check virtual environment
which python
pip list | grep -E "(coinbase|google-genai)"

# Test configuration loading
python -c "from config import Config; Config()"

# Check logs
tail -f logs/supervisor.log
```

#### Solutions

**Missing Dependencies:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check for conflicting packages
pip check
```

**Configuration Issues:**
```bash
# Verify .env file exists and has correct format
cat .env | head -5

# Check environment variable loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('SIMULATION_MODE:', os.getenv('SIMULATION_MODE'))
"
```

**Permission Issues:**
```bash
# Fix file permissions
chmod 600 .env
chmod 755 main.py
```

### 2. API Connection Failures

#### Coinbase API Issues

**Symptoms:**
- "Invalid API key" errors
- Connection timeouts
- Authentication failures

**Diagnosis:**
```bash
# Test API key format
python -c "
import os
api_key = os.getenv('COINBASE_API_KEY')
print('API Key format:', 'VALID' if api_key and api_key.startswith('organizations/') else 'INVALID')
"

# Test API connectivity
curl -H "Content-Type: application/json" https://api.coinbase.com/api/v3/brokerage/time
```

**Solutions:**

**Invalid API Key Format:**
```bash
# Correct format should be:
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id

# NOT:
COINBASE_API_KEY=your-key-id
```

**Invalid Private Key:**
```bash
# Private key should start and end with:
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----
...key content...
-----END EC PRIVATE KEY-----
```

**Rate Limiting:**
```python
# Check if you're hitting rate limits
# Coinbase allows 10 requests per second
# The bot includes rate limiting, but check logs for rate limit errors
```

#### Google Cloud AI Issues

**Symptoms:**
- "Authentication failed" errors
- "Project not found" errors
- "Model not available" errors

**Diagnosis:**
```bash
# Test Google Cloud authentication
gcloud auth application-default print-access-token

# Check service account permissions
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT

# Test AI API access
python -c "
from llm_analyzer import LLMAnalyzer
analyzer = LLMAnalyzer()
print('Google AI connection: SUCCESS')
"
```

**Solutions:**

**Authentication Issues:**
```bash
# Set correct service account path
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Verify service account has correct permissions
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:your-sa@project.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

**Model Access Issues:**
```bash
# Ensure using correct models and location
LLM_MODEL=gemini-3-flash-preview
LLM_LOCATION=global

# NOT:
LLM_MODEL=gemini-pro  # Old model
LLM_LOCATION=us-central1  # Wrong location for preview models
```

### 3. Trading Issues

#### No Trades Being Executed

**Symptoms:**
- Bot runs but never places trades
- All signals are "HOLD"
- Low confidence scores

**Diagnosis:**
```bash
# Check confidence thresholds
python -c "
from config import Config
c = Config()
print(f'Buy threshold: {c.CONFIDENCE_THRESHOLD_BUY}')
print(f'Sell threshold: {c.CONFIDENCE_THRESHOLD_SELL}')
"

# Check simulation mode
python -c "
import os
print('Simulation mode:', os.getenv('SIMULATION_MODE'))
"

# Check recent signals
tail -f logs/supervisor.log | grep -i "signal\|confidence"
```

**Solutions:**

**High Confidence Thresholds:**
```bash
# Lower confidence thresholds for more trades
CONFIDENCE_THRESHOLD_BUY=45
CONFIDENCE_THRESHOLD_SELL=45
```

**Market Conditions:**
```bash
# Check if market is in sideways/low volatility period
# Bot may naturally trade less in stable markets
```

**Insufficient Balance:**
```bash
# Check minimum trade amounts
MIN_TRADE_AMOUNT=5.0  # Lower if needed
MIN_EUR_RESERVE=10.0  # Ensure sufficient reserves
```

#### Trades Failing

**Symptoms:**
- "Insufficient funds" errors
- "Order rejected" errors
- Trades not appearing on exchange

**Diagnosis:**
```bash
# Check account balances
python -c "
from coinbase_client import CoinbaseClient
client = CoinbaseClient()
accounts = client.get_accounts()
for account in accounts:
    print(f'{account[\"currency\"]}: {account[\"available_balance\"][\"value\"]}')
"

# Check order history
python -c "
from coinbase_client import CoinbaseClient
client = CoinbaseClient()
orders = client.list_orders()
for order in orders[-5:]:
    print(f'{order[\"side\"]} {order[\"product_id\"]} - {order[\"status\"]}')
"
```

**Solutions:**

**Insufficient Funds:**
```bash
# Ensure adequate EUR balance
# Check MIN_EUR_RESERVE setting
# Verify position sizing calculations
```

**Order Size Issues:**
```bash
# Check minimum order sizes for each trading pair
# BTC-EUR: Usually €5-10 minimum
# ETH-EUR: Usually €5-10 minimum
```

### 4. Performance Issues

#### High CPU Usage

**Symptoms:**
- System becomes slow
- High CPU usage by Python process
- Frequent timeouts

**Diagnosis:**
```bash
# Monitor CPU usage
top -p $(pgrep -f main.py)

# Check for infinite loops in logs
tail -f logs/supervisor.log | grep -E "ERROR|Exception"

# Profile the application
pip install py-spy
py-spy top --pid $(pgrep -f main.py)
```

**Solutions:**

**Reduce Decision Frequency:**
```bash
# Increase decision interval
DECISION_INTERVAL_MINUTES=120  # Instead of 60
```

**Optimize Data Collection:**
```bash
# Reduce technical indicator periods
TECHNICAL_INDICATOR_PERIOD=100  # Instead of 200
```

#### High Memory Usage

**Symptoms:**
- Memory usage keeps growing
- System runs out of memory
- Process gets killed

**Diagnosis:**
```bash
# Monitor memory usage
ps aux | grep python
free -h

# Check for memory leaks
pip install memory-profiler
python -m memory_profiler main.py
```

**Solutions:**

**Limit Data Retention:**
```bash
# Reduce performance data retention
PERFORMANCE_RETENTION_DAYS=30  # Instead of 365

# Clean up old log files
find logs/ -name "*.log" -mtime +7 -delete
```

### 5. Dashboard Issues

#### Dashboard Not Loading

**Symptoms:**
- HTTP 404 errors
- Dashboard shows old data
- Can't access dashboard URL

**Diagnosis:**
```bash
# Check Apache status
sudo systemctl status apache2

# Check dashboard files
ls -la /var/www/html/crypto-bot/

# Check firewall
sudo ufw status
```

**Solutions:**

**Apache Not Running:**
```bash
sudo systemctl start apache2
sudo systemctl enable apache2
```

**Missing Dashboard Files:**
```bash
# Ensure dashboard sync is enabled
WEBSERVER_SYNC_ENABLED=true

# Check dashboard update process
python -c "
from deploy_dashboard import sync_dashboard
sync_dashboard()
"
```

**Firewall Issues:**
```bash
# Allow HTTP traffic
sudo ufw allow 80
sudo ufw allow 443
```

### 6. Email Report Issues

#### Daily Reports Not Sent

**Symptoms:**
- No daily emails received
- Email errors in logs
- SMTP authentication failures

**Diagnosis:**
```bash
# Check cron job
crontab -l | grep daily_report

# Test email configuration
python -c "
import smtplib
from email.mime.text import MIMEText
import os

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
    print('Email configuration: SUCCESS')
    server.quit()
except Exception as e:
    print(f'Email configuration: FAILED - {e}')
"

# Check daily report logs
tail -f logs/daily_report.log
```

**Solutions:**

**Gmail Authentication:**
```bash
# Ensure 2FA is enabled on Gmail account
# Use App Password, not regular password
# Format: GMAIL_APP_PASSWORD=abcd efgh ijkl mnop (16 characters)
```

**Cron Job Issues:**
```bash
# Check cron service
sudo systemctl status cron

# Test manual execution
cd ~/AI-crypto-bot && python daily_report.py
```

### 7. Data Quality Issues

#### Stale or Missing Data

**Symptoms:**
- Old timestamps in market data
- Missing technical indicators
- "No data available" errors

**Diagnosis:**
```bash
# Check data collection
python -c "
from data_collector import DataCollector
collector = DataCollector()
data = collector.collect_all_data()
print('Market data timestamp:', data.get('timestamp'))
print('Available indicators:', list(data.get('technical_indicators', {}).keys()))
"

# Check API connectivity
curl -I https://api.coinbase.com/api/v3/brokerage/products/BTC-EUR/ticker
```

**Solutions:**

**API Rate Limiting:**
```bash
# Increase data collection interval
DATA_COLLECTION_INTERVAL=120  # 2 minutes instead of 1
```

**Network Issues:**
```bash
# Check DNS resolution
nslookup api.coinbase.com
nslookup googleapis.com

# Check proxy settings if applicable
```

## Advanced Troubleshooting

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment variables
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG

# Run with debug output
python main.py 2>&1 | tee debug.log
```

### Performance Profiling

```bash
# Install profiling tools
pip install py-spy line-profiler memory-profiler

# CPU profiling
py-spy record -o profile.svg -- python main.py

# Memory profiling
python -m memory_profiler main.py

# Line-by-line profiling (add @profile decorator to functions)
kernprof -l -v main.py
```

### Database Debugging

```bash
# Check portfolio state
python -c "
import json
from portfolio import Portfolio
portfolio = Portfolio()
print(json.dumps(portfolio.to_dict(), indent=2))
"

# Check performance data
python -c "
from utils.performance_tracker import PerformanceTracker
tracker = PerformanceTracker()
summary = tracker.get_performance_summary()
print(json.dumps(summary, indent=2))
"
```

### Network Debugging

```bash
# Test external connectivity
ping -c 4 api.coinbase.com
ping -c 4 googleapis.com

# Check SSL certificates
openssl s_client -connect api.coinbase.com:443 -servername api.coinbase.com

# Monitor network traffic
sudo tcpdump -i any host api.coinbase.com
```

## Log Analysis

### Important Log Patterns

**Successful Operation:**
```
INFO - Portfolio updated: €1000.00 total value
INFO - Market analysis completed: BUY signal with 75% confidence
INFO - Trade executed: BUY 0.002 BTC-EUR at €45000.00
```

**Warning Signs:**
```
WARNING - Low confidence signal: 35% (threshold: 55%)
WARNING - High volatility detected: 45%
WARNING - API rate limit approaching
```

**Error Patterns:**
```
ERROR - Failed to connect to Coinbase API: Connection timeout
ERROR - Google AI API error: Authentication failed
ERROR - Insufficient balance for trade: €5.00 required, €3.50 available
```

### Log File Locations

```bash
# Main application logs
tail -f logs/supervisor.log

# Daily report logs
tail -f logs/daily_report.log

# System logs (if using systemd)
sudo journalctl -u crypto-bot -f

# Apache logs (for dashboard)
sudo tail -f /var/log/apache2/access.log
sudo tail -f /var/log/apache2/error.log
```

## Getting Help

### Information to Collect

When seeking help, collect this information:

```bash
# System information
uname -a
python --version
pip list | grep -E "(coinbase|google)"

# Configuration (sanitized)
python -c "
from config import Config
import os
c = Config()
print('Simulation mode:', c.SIMULATION_MODE)
print('Risk level:', c.RISK_LEVEL)
print('Trading pairs:', c.TRADING_PAIRS)
print('Python path:', os.sys.path[0])
"

# Recent logs (last 50 lines)
tail -50 logs/supervisor.log

# Error details
python -c "
import traceback
try:
    from main import main
    main()
except Exception as e:
    traceback.print_exc()
"
```

### Support Channels

1. **GitHub Issues**: For bugs and feature requests
2. **Documentation**: Check all documentation files
3. **Community**: Discord/Telegram groups (if available)
4. **Logs**: Always include relevant log excerpts

### Before Reporting Issues

1. **Check this troubleshooting guide**
2. **Search existing GitHub issues**
3. **Test with minimal configuration**
4. **Verify it's not a known limitation**
5. **Collect all relevant information**

This troubleshooting guide should resolve most common issues with the AI crypto trading bot. For persistent problems, follow the information collection guidelines and seek help through appropriate channels.