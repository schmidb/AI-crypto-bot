# Performance Optimization Guide

## Instance Upgrade: e2-micro → e2-medium

**Status**: Testing e2-medium (January 1, 2026)  
**Previous Issues**: Super slow performance, frequent network outages on e2-micro  
**Expected Improvements**: 4x memory, dedicated CPU, stable network

## Quick Reference Commands

### **Check Current Instance Type**
```bash
gcloud compute instances describe crypto-trading-bot \
    --zone=your-zone \
    --format="value(machineType)" | sed 's|.*/||'
```

### **Upgrade Instance (Requires Stop/Start)**
```bash
# Stop the bot
gcloud compute instances stop crypto-trading-bot --zone=your-zone

# Change machine type
gcloud compute instances set-machine-type crypto-trading-bot \
    --machine-type=e2-medium \
    --zone=your-zone

# Start the bot
gcloud compute instances start crypto-trading-bot --zone=your-zone
```

### **Monitor Performance**
```bash
# Memory usage
free -h

# CPU usage
htop

# Network connectivity test
ping -c 5 api.coinbase.com

# Bot logs
tail -f /home/markus/AI-crypto-bot/logs/trading_bot.log
```

## Performance Monitoring Script

Create a monitoring script to track the improvement:

```bash
#!/bin/bash
# File: scripts/monitor_performance.sh

echo "=== AI Crypto Bot Performance Monitor ==="
echo "Date: $(date)"
echo

# Instance info
echo "Instance Type:"
gcloud compute instances describe crypto-trading-bot \
    --zone=your-zone \
    --format="value(machineType)" | sed 's|.*/||'
echo

# Memory usage
echo "Memory Usage:"
free -h
echo

# CPU load
echo "CPU Load:"
uptime
echo

# Network test
echo "Network Test (Coinbase API):"
ping -c 3 api.coinbase.com | tail -1
echo

# Disk usage
echo "Disk Usage:"
df -h /
echo

# Bot status
echo "Bot Process:"
ps aux | grep python | grep main.py | head -1
echo

# Recent errors
echo "Recent Errors (last 10):"
tail -20 /home/markus/AI-crypto-bot/logs/errors.log | head -10
```

## Expected Performance Improvements

### **Network Stability**
- **Before (e2-micro)**: Frequent network outages
- **After (e2-medium)**: Stable network connectivity
- **Impact**: Reliable API calls, no missed trading opportunities

### **Processing Speed**
- **Before (e2-micro)**: Super slow processing
- **After (e2-medium)**: 4x memory, dedicated CPU
- **Impact**: Faster market data analysis, quicker decisions

### **Memory Capacity**
- **Before (e2-micro)**: 1 GB (insufficient for pandas)
- **After (e2-medium)**: 4 GB (adequate for current needs)
- **Impact**: No memory pressure, stable operations

## Performance Benchmarks

### **Target Performance Metrics (e2-medium)**
- Market data collection: <5 seconds
- Technical indicators: <10 seconds  
- AI analysis: 5-15 seconds (external API)
- Portfolio calculations: <2 seconds
- Dashboard updates: <5 seconds

### **Warning Thresholds**
- Memory usage >80%: Consider upgrade
- CPU usage sustained >80%: Need more cores
- Network timeouts >5%: Infrastructure issue
- Processing time >2x targets: Performance problem

## Code Optimizations for Better Performance

### **Memory Optimization**
```python
# In data_collector.py - optimize DataFrame memory usage
def optimize_dataframe_memory(df):
    """Optimize DataFrame memory usage"""
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')
        elif df[col].dtype == 'int64':
            df[col] = df[col].astype('int32')
    return df
```

### **Efficient Data Loading**
```python
# Load data in chunks for large datasets
def load_data_efficiently(file_path, chunk_size=1000):
    """Load large datasets efficiently"""
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Process chunk
        processed_chunk = process_chunk(chunk)
        chunks.append(processed_chunk)
    return pd.concat(chunks, ignore_index=True)
```

### **Cache Optimization**
```python
# Implement smart caching for repeated calculations
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_indicators_cached(data_hash, trading_style):
    """Cache indicator calculations"""
    # Expensive calculations here
    return indicators
```

## Monitoring Dashboard

### **System Metrics to Track**
1. **Memory Usage**: Track over time to identify trends
2. **CPU Utilization**: Monitor for sustained high usage
3. **Network Latency**: API response times
4. **Bot Performance**: Decision-making speed
5. **Error Rates**: Network failures, processing errors

### **Alert Thresholds**
```bash
# Add to crontab for automated monitoring
# */5 * * * * /home/markus/AI-crypto-bot/scripts/monitor_performance.sh >> /home/markus/performance.log

# Memory alert
if [ $(free | grep Mem | awk '{print ($3/$2) * 100.0}' | cut -d. -f1) -gt 80 ]; then
    echo "WARNING: Memory usage >80%" | mail -s "Bot Alert" your-email@gmail.com
fi
```

## Troubleshooting Guide

### **If Performance is Still Poor on e2-medium**

#### **Check Memory Usage**
```bash
# If memory >90%, consider e2-standard-2
free -h
# Look for swap usage - indicates memory pressure
```

#### **Check CPU Bottlenecks**
```bash
# If CPU consistently >90%, need more cores
htop
# Look for high load average
```

#### **Network Issues**
```bash
# Test API connectivity
curl -w "@curl-format.txt" -s -o /dev/null https://api.coinbase.com/v2/time

# Check for packet loss
ping -c 100 api.coinbase.com | grep "packet loss"
```

### **Escalation Path**
1. **Week 1**: Monitor e2-medium performance
2. **If issues persist**: Upgrade to e2-standard-2
3. **If still problematic**: Review code optimization
4. **Last resort**: Consider different cloud provider

## Cost vs Performance Analysis

### **Current Test: e2-medium**
- **Cost**: $25/month (+$19 from e2-micro)
- **Expected ROI**: Stable trading operations
- **Risk**: Network outages cost more than $19/month in missed opportunities

### **Future Consideration: e2-standard-2**
- **Cost**: $50/month (+$25 from e2-medium)
- **Benefits**: 2x CPU, 2x memory
- **When to upgrade**: Regular backtesting or multiple trading pairs

## Success Criteria for e2-medium

### **Week 1 Goals**
- [ ] Zero network outages during trading hours
- [ ] All operations complete within target times
- [ ] Memory usage stays <70%
- [ ] No bot crashes or restarts
- [ ] Successful completion of all scheduled tasks

### **Week 2-4 Goals**
- [ ] Consistent performance across different market conditions
- [ ] Stable operation during high volatility periods
- [ ] Dashboard remains responsive
- [ ] All trading decisions executed on time
- [ ] Error rate <1%

## Next Steps

1. **Monitor e2-medium for 1 week**
2. **Document performance improvements**
3. **Update this guide with actual metrics**
4. **Plan future optimizations based on results**

---

**Testing Period**: January 1-8, 2026  
**Review Date**: January 8, 2026  
**Decision Point**: Continue with e2-medium or upgrade to e2-standard-2