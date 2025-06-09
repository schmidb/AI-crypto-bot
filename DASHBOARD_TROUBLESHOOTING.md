# Dashboard Troubleshooting Guide

## Quick Fix for "Failed to load data" Error

The dashboard has been updated to work with your bot's actual data format. Here's how to get it working:

### 1. Update Market Data Links
```bash
cd /home/markus/AI-crypto-bot
./update_dashboard_links.sh
```

### 2. Start the Dashboard Server
```bash
python3 start_dashboard.py
```

### 3. Access the Dashboard
Open your browser and go to: `http://localhost:8080`

## Data File Verification

Run this command to check if all data files are accessible:
```bash
python3 test_dashboard_data.py
```

## Common Issues and Solutions

### Issue: "Failed to load portfolio data"
**Cause**: Portfolio data format mismatch
**Solution**: The dashboard now reads from `portfolio_data.json` with the correct field names:
- `portfolio_value_usd` (instead of `total_value`)
- `initial_value_usd` (for calculating returns)
- Asset amounts from `BTC.amount`, `ETH.amount`, etc.

### Issue: "Failed to load market data"
**Cause**: Market data symlinks not updated
**Solution**: 
```bash
./update_dashboard_links.sh
```
This creates symlinks like `BTC_USD_latest.json` pointing to the most recent price files.

### Issue: "No recent decisions available"
**Cause**: `latest_decisions.json` is empty
**Solution**: The dashboard now reads from `trade_history.json` instead, showing the last 3 trading decisions.

### Issue: Charts not displaying
**Cause**: Chart images don't exist or paths are wrong
**Solution**: 
1. Make sure your bot generates chart images in `dashboard/images/`
2. Check that the image files exist:
   - `portfolio_value.png`
   - `portfolio_allocation.png` 
   - `allocation_comparison.png`

### Issue: Server won't start
**Cause**: Port 8080 already in use
**Solution**: 
1. Kill any existing servers: `pkill -f "python.*start_dashboard"`
2. Or change the port in `start_dashboard.py`

## Data File Locations

The dashboard expects these files:
```
data/
├── portfolio/
│   └── portfolio_data.json     # Portfolio overview
├── market_data/
│   ├── BTC_USD_latest.json     # Latest BTC price (symlink)
│   ├── ETH_USD_latest.json     # Latest ETH price (symlink)
│   └── SOL_USD_latest.json     # Latest SOL price (symlink)
├── trades/
│   └── trade_history.json      # All trading decisions
├── cache/
│   ├── bot_startup.json        # Bot startup info
│   └── trading_data.json       # Performance data
└── config/
    └── config.json             # Dashboard config
```

## Testing Commands

```bash
# Test all data files
python3 test_dashboard_data.py

# Test server (if you have requests module)
python3 test_dashboard_server.py

# Update symlinks
./update_dashboard_links.sh

# Start dashboard
python3 start_dashboard.py
```

## Browser Console Debugging

If the dashboard still shows "Failed to load data":

1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for error messages like:
   - `Failed to load ../data/portfolio/portfolio_data.json`
   - `404 Not Found` errors
4. Check Network tab to see which requests are failing

## Manual Data Check

You can manually verify data files:
```bash
# Check portfolio data
cat data/portfolio/portfolio_data.json

# Check latest market data
cat data/market_data/BTC_USD_latest.json

# Check trade history
tail -20 data/trades/trade_history.json
```

## Web Server Alternative

If the Python server doesn't work, you can use any web server:
```bash
# Using Python's built-in server
cd dashboard/static
python3 -m http.server 8080

# Using Node.js (if installed)
cd dashboard/static
npx http-server -p 8080

# Using PHP (if installed)
cd dashboard/static
php -S localhost:8080
```

## Success Indicators

When working correctly, you should see:
- ✅ Portfolio value and return percentage
- ✅ Current BTC, ETH, SOL prices with 24h changes
- ✅ Recent AI trading decisions with confidence levels
- ✅ Bot uptime and decision count
- ✅ Trading activity log with timestamps
- ✅ Live UTC clock in the header

## Still Having Issues?

1. Make sure your bot is running and generating data
2. Check file permissions: `ls -la data/`
3. Verify symlinks: `ls -la data/market_data/`
4. Check browser console for JavaScript errors
5. Try accessing data files directly in browser: `http://localhost:8080/../data/portfolio/portfolio_data.json`
