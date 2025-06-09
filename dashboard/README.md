# AI Crypto Bot Dashboard

A clean, modern web dashboard for monitoring your AI-powered cryptocurrency trading bot.

## Features

### 🖥️ Main Dashboard (`index.html`)
- **Real-time Portfolio Tracking**: Live portfolio value, returns, and asset allocation
- **Market Data Display**: Current prices with percentage changes for BTC, ETH, and SOL
- **AI Decision Insights**: Recent buy/sell/hold decisions with confidence levels
- **Bot Status Monitoring**: Uptime tracking and operational status
- **Trading Activity Log**: Complete history of all trading decisions
- **Live UTC Clock**: Real-time server time display
- **Direct Coinbase Links**: Quick access to Advanced Trade platform

### 📊 Analysis Dashboard (`analysis.html`)
- **Portfolio Value Charts**: Historical performance visualization
- **Allocation Charts**: Visual representation of asset distribution
- **Comparison Charts**: Portfolio allocation analysis

## Quick Start

### Option 1: Local Development Server
```bash
# Start the built-in Python server
python start_dashboard.py

# Access dashboard at:
# http://localhost:8080
```

### Option 2: Static File Server
```bash
# Serve the static directory with any web server
cd dashboard/static
python -m http.server 8080

# Access dashboard at:
# http://localhost:8080
```

## File Structure

```
dashboard/
├── README.md           # This file
├── static/             # Web files
│   ├── index.html      # Main dashboard
│   └── analysis.html   # Analysis dashboard
└── images/             # Generated charts
    ├── portfolio_value.png
    ├── portfolio_allocation.png
    └── allocation_comparison.png
```

## Data Sources

The dashboard reads data from the following locations:

- **Portfolio Data**: `../data/portfolio/portfolio_data.json`
- **Market Data**: `../data/market_data/[ASSET]_USD_latest.json`
- **AI Decisions**: `../data/cache/latest_decisions.json`
- **Trading History**: `../data/trades/trade_history.json`
- **Bot Status**: `../data/cache/bot_startup.json`
- **Performance**: `../data/cache/trading_data.json`

## Updating Market Data Links

Run the dashboard links script to update symlinks to the latest market data:

```bash
./update_dashboard_links.sh
```

This creates symlinks in `data/market_data/` pointing to the most recent price data files.

## Customization

### Styling
All CSS is embedded in the HTML files for easy customization. The dashboard uses:
- Modern gradient backgrounds
- Glass-morphism effects with backdrop blur
- Responsive grid layouts
- Color-coded indicators for buy/sell/hold actions

### Auto-refresh
The dashboard automatically refreshes data every 30 seconds. You can modify this interval in the JavaScript section.

### Adding New Features
To add new data displays:
1. Create the HTML structure in the appropriate card
2. Add a JavaScript function to load the data
3. Call the function in the `initDashboard()` function

## Troubleshooting

### Dashboard shows "Failed to load data"
- Ensure the bot is running and generating data files
- Check that file paths in the JavaScript match your data structure
- Run `./update_dashboard_links.sh` to update symlinks

### Charts not displaying
- Verify that chart images exist in the `images/` directory
- Ensure the bot's visualization components are working
- Check browser console for JavaScript errors

### Server won't start
- Make sure port 8080 is available
- Try a different port by modifying `start_dashboard.py`
- Check file permissions on the dashboard directory

## Browser Compatibility

The dashboard is tested and works with:
- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

Modern JavaScript features are used, so older browsers may not be supported.
