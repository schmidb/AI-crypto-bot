#!/bin/bash

# AI Crypto Bot - Clean Reset Script
# This script removes all historical data and resets the bot for a fresh start

echo "🔄 Starting AI Crypto Bot data reset..."

# Stop the bot if it's running (check for common process names)
echo "🛑 Stopping any running bot processes..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "crypto.*bot" 2>/dev/null || true

# Remove all historical market data files
echo "📊 Removing historical market data..."
if [ -d "data" ]; then
    # Keep the directory but remove all JSON files except portfolio.json (we'll reset it)
    find data/ -name "*.json" -not -name "portfolio.json" -delete
    echo "   ✅ Removed market data files"
else
    echo "   ℹ️  No data directory found"
fi

# Reset portfolio data
echo "💰 Resetting portfolio data..."
if [ -f "data/portfolio.json" ]; then
    rm data/portfolio.json
    echo "   ✅ Removed existing portfolio data"
fi

# Reset trade history
echo "📈 Resetting trade history..."
if [ -f "data/trade_history.json" ]; then
    rm data/trade_history.json
    echo "   ✅ Removed trade history"
fi

# Clean up log files
echo "📝 Cleaning up log files..."
if [ -d "logs" ]; then
    # Keep the directory structure but clear the logs
    > logs/supervisor.log 2>/dev/null || true
    rm -f logs/crypto_bot.log* 2>/dev/null || true
    rm -f logs/trade_history.csv 2>/dev/null || true
    rm -f logs/strategy_performance.csv 2>/dev/null || true
    echo "   ✅ Cleared log files"
fi

# Clean up reports
echo "📊 Cleaning up analysis reports..."
if [ -d "reports" ]; then
    rm -f reports/*.json 2>/dev/null || true
    echo "   ✅ Cleared analysis reports"
fi

# Clean up Python cache
echo "🧹 Cleaning up Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "   ✅ Cleared Python cache"

# Create fresh data directory structure if needed
echo "📁 Ensuring directory structure..."
mkdir -p data logs reports
echo "   ✅ Directory structure ready"

echo ""
echo "✅ Bot data reset complete!"
echo ""
echo "📋 Summary of what was cleaned:"
echo "   • All historical market data files"
echo "   • Portfolio tracking data"
echo "   • Trade history and logs"
echo "   • Strategy analysis reports"
echo "   • Python cache files"
echo ""
echo "🚀 Your bot is now ready for a fresh start!"
echo "   Run 'python main.py' to begin with clean data from Coinbase"
echo ""
