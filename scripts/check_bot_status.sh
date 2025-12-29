#!/bin/bash
# Check if crypto bot is running

echo "🔍 Checking for running crypto bot instances..."

# Check supervisor status
echo ""
echo "📊 Supervisor status:"
sudo supervisorctl status crypto-bot 2>/dev/null || echo "Supervisor not configured or not running"

# Check for Python processes
echo ""
echo "🐍 Python processes:"
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Found running bot processes:"
    pgrep -f "python.*main.py" | while read pid; do
        echo "  PID: $pid - $(ps -p $pid -o cmd --no-headers)"
    done
else
    echo "❌ No bot processes found"
fi

# Check lock file
echo ""
echo "🔒 Lock file status:"
if [ -f "/tmp/crypto-bot.lock" ]; then
    echo "✅ Lock file exists:"
    echo "  PID: $(cat /tmp/crypto-bot.lock 2>/dev/null || echo 'Could not read PID')"
    echo "  File: /tmp/crypto-bot.lock"
else
    echo "❌ No lock file found"
fi

# Check if PID in lock file is actually running
if [ -f "/tmp/crypto-bot.lock" ]; then
    lock_pid=$(cat /tmp/crypto-bot.lock 2>/dev/null)
    if [ ! -z "$lock_pid" ]; then
        if kill -0 "$lock_pid" 2>/dev/null; then
            echo "✅ Process $lock_pid is running"
        else
            echo "⚠️  Process $lock_pid is not running (stale lock file)"
        fi
    fi
fi

echo ""
echo "💡 To start the bot safely, use: sudo supervisorctl start crypto-bot"
echo "💡 To stop the bot safely, use: sudo supervisorctl stop crypto-bot"
