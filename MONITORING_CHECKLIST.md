# 📊 Bot Monitoring Checklist (Days 1-7)

## 🔍 Daily Monitoring (5 minutes)

### **Quick Health Check**
```bash
# 1. Check bot is running
ps aux | grep "python.*main.py" | grep -v grep

# 2. Check recent activity (last 2 hours)
tail -50 /home/markus/AI-crypto-bot/logs/supervisor.log | grep -E "(Decision:|SELL|BUY|Market regime)"

# 3. Check dashboard
# Visit: http://34.29.9.115/crypto-bot/
```

### **Key Metrics to Track**

**Trading Activity:**
- [ ] Trades per day (target: 3-5, was: <1)
- [ ] Confidence scores (target: 60-80%, was: 33-38%)
- [ ] Market regime detection working
- [ ] Strategy selection logical

**Performance Indicators:**
- [ ] Portfolio value trend
- [ ] EUR balance changes
- [ ] No excessive losses
- [ ] Bot responding to market moves

## 📈 **Expected Improvements Timeline**

### **Day 1 (Today)**
- [x] Bot restarted with adaptive architecture ✅
- [x] 30-minute decision intervals active ✅
- [ ] First adaptive trades executed
- [ ] Market regime detection logs visible

### **Day 2-3**
- [ ] 5-10 trades executed
- [ ] Confidence scores consistently >60%
- [ ] Different strategies leading in different markets
- [ ] EUR balance decreasing (from trades)

### **Day 4-7**
- [ ] Consistent daily trading activity
- [ ] Profitable trading pattern emerging
- [ ] Strategy selection proving effective
- [ ] System running stably

## 🚨 **Warning Signs to Watch**

**Red Flags (Take Action):**
- No trades after 24 hours
- Confidence scores still <50%
- Excessive losses (>5% portfolio value)
- Bot crashes or errors

**Yellow Flags (Monitor Closely):**
- Too many trades (>10/day)
- All trades from same strategy
- Market regime detection seems wrong
- Unusual trading patterns

## 📊 **Daily Monitoring Commands**

### **Check Trading Activity**
```bash
# Recent trades
tail -100 /home/markus/AI-crypto-bot/data/trades/trade_history.json | grep -E '"action": "(BUY|SELL)"' | tail -5

# Recent decisions
tail -20 /home/markus/AI-crypto-bot/data/cache/latest_decisions.json
```

### **Check Performance**
```bash
# Portfolio value
cat /home/markus/AI-crypto-bot/data/portfolio/portfolio.json | grep -E "(portfolio_value|EUR.*amount)"

# Bot logs
tail -30 /home/markus/AI-crypto-bot/logs/supervisor.log
```

### **Check Market Regime Detection**
```bash
# Look for regime detection logs
grep -E "Market regime:|Strategy priority:" /home/markus/AI-crypto-bot/logs/supervisor.log | tail -10
```

## 📈 **Success Metrics**

### **Week 1 Goals**
- [ ] 15-25 total trades (vs <7 previously)
- [ ] Average confidence >65%
- [ ] At least 2 different strategies leading
- [ ] No major system issues

### **Performance Comparison**
| Metric | Old System | Target | Actual |
|--------|------------|--------|--------|
| Trades/day | <1 | 3-5 | ___ |
| Confidence | 33-38% | 60-80% | ___% |
| Market response | Slow | Fast | ___ |
| Strategy diversity | Low | High | ___ |

## 🔧 **Adjustment Guidelines**

### **If Too Few Trades (<2/day)**
- Lower confidence thresholds by 5%
- Check market regime detection
- Verify strategy priorities

### **If Too Many Trades (>8/day)**
- Raise confidence thresholds by 5%
- Add minimum time between trades
- Check for overactive strategies

### **If Poor Performance**
- Review strategy selection logic
- Check market regime accuracy
- Consider reverting to old system

## 📞 **Emergency Procedures**

### **If Major Issues**
```bash
# Stop bot immediately
kill $(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')

# Revert to old system
cp /home/markus/AI-crypto-bot/main.py.backup /home/markus/AI-crypto-bot/main.py
sed -i 's/CONFIDENCE_THRESHOLD_BUY=50/CONFIDENCE_THRESHOLD_BUY=70/' /home/markus/AI-crypto-bot/.env
sed -i 's/CONFIDENCE_THRESHOLD_SELL=50/CONFIDENCE_THRESHOLD_SELL=70/' /home/markus/AI-crypto-bot/.env

# Restart with old system
cd /home/markus/AI-crypto-bot && nohup /home/markus/crypto-bot-env/bin/python main.py > /dev/null 2>&1 &
```

## 📋 **Daily Log Template**

**Date: ___________**

**Trading Activity:**
- Trades executed: ___
- Confidence scores: ___% avg
- Market regimes detected: ___
- Leading strategies: ___

**Performance:**
- Portfolio value: €___
- EUR balance: €___
- Notable trades: ___

**Issues:**
- Problems observed: ___
- Actions taken: ___

**Notes:**
- _______________
