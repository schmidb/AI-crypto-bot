# Google Cloud Instance Sizing Guide for AI Crypto Bot

## Current Status: Upgrading from e2-micro to e2-medium

**Date**: January 1, 2026  
**Previous Instance**: e2-micro (experiencing performance issues)  
**New Instance**: e2-medium (testing phase)  
**Reason for Upgrade**: Severe performance issues and network outages on e2-micro

## Instance Performance Analysis

### e2-micro Issues (Current Problems)
- **Performance**: Super slow processing
- **Network**: Very frequent network outages
- **Memory**: 1 GB insufficient for pandas DataFrames
- **CPU**: 2 shared vCPUs with limited burst capacity
- **Cost**: ~$6/month (free tier eligible)
- **Verdict**: ❌ **NOT SUITABLE** for production trading

### e2-medium (Testing Now)
- **vCPUs**: 1 dedicated
- **Memory**: 4 GB
- **Network**: Better network performance and stability
- **Cost**: ~$25/month
- **Expected Benefits**:
  - Stable network connectivity (critical for trading)
  - Sufficient memory for market data processing
  - Dedicated CPU for consistent performance
- **Verdict**: ✅ **RECOMMENDED** for current usage

## Comprehensive Instance Comparison

| Instance Type | vCPUs | Memory | Network | Cost/Month | Use Case | Recommendation |
|---------------|-------|---------|---------|------------|----------|----------------|
| **e2-micro** | 2 shared | 1 GB | Limited | ~$6 | Development only | ❌ Avoid for production |
| **e2-small** | 2 shared | 2 GB | Standard | ~$12 | Light production | ⚠️ Minimal viable |
| **e2-medium** | 1 dedicated | 4 GB | Standard | ~$25 | **Current production** | ✅ **RECOMMENDED** |
| **e2-standard-2** | 2 dedicated | 8 GB | Standard | ~$50 | Heavy backtesting | 🎯 Future upgrade |
| **e2-standard-4** | 4 dedicated | 16 GB | Standard | ~$100 | Multiple bots | 💰 Overkill |

## Resource Requirements Analysis

### AI Crypto Bot Workloads

#### **Regular Operations (Every 60-120 minutes)**
- Market data collection via Coinbase API
- Technical indicator calculations (RSI, MACD, Bollinger Bands)
- AI analysis via external Gemini-3 API
- Portfolio value calculations
- Trading decision execution

**Resource Needs**: Low to moderate CPU, 2-4 GB RAM

#### **Data Processing**
- Pandas DataFrames for 7-180 days of historical data
- Technical analysis calculations
- Portfolio performance tracking
- Dashboard data updates

**Resource Needs**: Moderate CPU, 4-8 GB RAM

#### **Backtesting (Infrequent)**
- Vectorbt portfolio simulations
- Large dataset processing
- Strategy optimization
- Performance analysis

**Resource Needs**: High CPU, 8+ GB RAM

## Sizing Recommendations by Usage Pattern

### **Current Usage: Production Trading (No Regular Backtesting)**

#### ✅ **Primary Recommendation: e2-medium**
- **Specs**: 1 vCPU, 4 GB RAM
- **Cost**: $25/month
- **Benefits**:
  - Stable network connectivity (fixes outage issues)
  - Sufficient memory for market data processing
  - Dedicated CPU for consistent performance
  - Cost-effective for regular operations
- **Limitations**:
  - Slower backtesting when needed
  - Single CPU limits parallel processing

#### 💡 **Budget Alternative: e2-small**
- **Specs**: 2 vCPU (shared), 2 GB RAM
- **Cost**: $12/month
- **Trade-offs**: More CPU cores but less memory
- **Risk**: May still experience memory pressure

### **Future Usage: Regular Backtesting**

#### 🎯 **Upgrade Target: e2-standard-2**
- **Specs**: 2 vCPU, 8 GB RAM
- **Cost**: $50/month
- **When to Upgrade**:
  - Running backtests weekly or more
  - Adding more trading pairs
  - Memory usage consistently >80%
  - Need faster technical analysis

## Cost Optimization Strategies

### **1. Temporary Scaling for Backtesting**
```bash
# Scale up for backtesting
gcloud compute instances stop crypto-trading-bot --zone=your-zone
gcloud compute instances set-machine-type crypto-trading-bot \
    --machine-type=e2-standard-2 --zone=your-zone
gcloud compute instances start crypto-trading-bot --zone=your-zone

# Run backtests
./backtesting/run_comprehensive_backtest.py

# Scale back down
gcloud compute instances stop crypto-trading-bot --zone=your-zone
gcloud compute instances set-machine-type crypto-trading-bot \
    --machine-type=e2-medium --zone=your-zone
gcloud compute instances start crypto-trading-bot --zone=your-zone
```

### **2. Preemptible Instances for Development**
- **Cost**: ~80% cheaper
- **Use Case**: Testing, development, one-off backtests
- **Limitation**: Can be terminated with 30-second notice

### **3. Scheduled Scaling**
```bash
# Morning scale-up (if needed for market hours)
gcloud compute instances set-machine-type crypto-trading-bot \
    --machine-type=e2-standard-2 --zone=your-zone

# Evening scale-down
gcloud compute instances set-machine-type crypto-trading-bot \
    --machine-type=e2-medium --zone=your-zone
```

## Performance Monitoring

### **Key Metrics to Monitor**

#### **Memory Usage**
```bash
# Check memory usage
free -h
htop

# Alert thresholds:
# - >70% = Monitor closely
# - >80% = Consider upgrade
# - >90% = Immediate action needed
```

#### **CPU Usage**
```bash
# Check CPU usage
top
htop

# Alert thresholds:
# - Sustained >80% = Consider upgrade
# - Frequent 100% spikes = Need more CPU
```

#### **Network Stability**
```bash
# Monitor network connectivity
ping -c 10 api.coinbase.com
curl -w "@curl-format.txt" -s -o /dev/null https://api.coinbase.com/v2/time

# Log network issues for pattern analysis
```

### **Performance Benchmarks**

#### **Expected Performance on e2-medium**
- Market data collection: <5 seconds
- Technical indicator calculation: <10 seconds
- AI analysis response: 5-15 seconds (external API)
- Portfolio update: <2 seconds
- Dashboard refresh: <5 seconds

#### **Warning Signs for Upgrade**
- Market data collection >15 seconds
- Frequent memory warnings in logs
- Network timeouts during trading hours
- Dashboard becomes unresponsive
- Bot misses trading opportunities due to slow processing

## Migration Checklist

### **From e2-micro to e2-medium**
- [ ] Stop the bot gracefully
- [ ] Create instance snapshot (backup)
- [ ] Change machine type to e2-medium
- [ ] Start instance
- [ ] Verify bot startup
- [ ] Monitor performance for 24-48 hours
- [ ] Check network stability
- [ ] Validate trading operations
- [ ] Update documentation

### **Rollback Plan**
If e2-medium doesn't solve issues:
- [ ] Stop instance
- [ ] Revert to e2-small (compromise option)
- [ ] Or upgrade to e2-standard-2 (if budget allows)

## Cost Analysis

### **Monthly Cost Comparison**
- **e2-micro**: $6/month (current, problematic)
- **e2-medium**: $25/month (+$19, testing now)
- **e2-standard-2**: $50/month (+$44, future option)

### **Cost vs. Performance Trade-offs**
- **$19/month increase**: Likely to solve network and performance issues
- **ROI**: Stable trading operations worth much more than $19/month
- **Risk**: Network outages could cause missed trading opportunities

## Recommendations Summary

### **Immediate Action (Current)**
1. ✅ **Upgrade to e2-medium** (in progress)
2. Monitor performance for 1 week
3. Document any remaining issues
4. Verify network stability improvements

### **Short-term (1-3 months)**
1. Collect performance metrics on e2-medium
2. Optimize code for memory efficiency if needed
3. Consider e2-standard-2 if adding more features

### **Long-term (3-6 months)**
1. Evaluate usage patterns
2. Consider scheduled scaling for cost optimization
3. Plan for growth (more trading pairs, regular backtesting)

## Troubleshooting Common Issues

### **Network Outages**
- **Cause**: e2-micro has limited network performance
- **Solution**: e2-medium provides better network stability
- **Monitoring**: Log network latency and failures

### **Memory Issues**
- **Symptoms**: Bot crashes, slow pandas operations
- **Solution**: e2-medium's 4GB should resolve most issues
- **Monitoring**: Track memory usage patterns

### **CPU Bottlenecks**
- **Symptoms**: Slow technical analysis, delayed decisions
- **Solution**: e2-medium's dedicated CPU should improve consistency
- **Future**: Consider e2-standard-2 for parallel processing

---

**Last Updated**: January 1, 2026  
**Next Review**: After 1 week of e2-medium testing  
**Contact**: Review performance metrics and update recommendations based on real-world usage