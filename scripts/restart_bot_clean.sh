#!/bin/bash

# Restart the trading bot with improved logging
echo "🔄 Restarting AI Crypto Trading Bot with improved logging..."

# Kill existing bot processes
echo "🛑 Stopping existing bot processes..."
pkill -f "python.*main.py" || true
sleep 2

# Clean up any remaining processes
pkill -9 -f "python.*main.py" || true
sleep 1

# Start the bot with new logging
echo "🚀 Starting bot with improved logging..."
cd /home/markus/AI-crypto-bot

# Start in background with new log file
nohup ./venv/bin/python main.py > logs/bot_clean_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Get the PID
BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"

# Wait a moment and check if it's running
sleep 3
if ps -p $BOT_PID > /dev/null; then
    echo "✅ Bot is running successfully with improved logging"
    echo "📋 Monitor logs with: tail -f logs/trading_bot.log"
    echo "🎯 Trading decisions: tail -f logs/trading_decisions.log"
    echo "❌ Errors only: tail -f logs/errors.log"
else
    echo "❌ Bot failed to start, check logs/bot_clean_*.log"
fi
