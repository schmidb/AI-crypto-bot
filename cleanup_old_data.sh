#!/bin/bash
# Cleanup old data files (keep last 30 days)
# Run this weekly via cron: 0 2 * * 0 /home/markus/AI-crypto-bot/cleanup_old_data.sh

cd /home/markus/AI-crypto-bot

# Delete market data files older than 30 days
find data/ -name "*_EUR_*.json" -mtime +30 -type f -delete

# Keep only last 10000 trades in history
python3 << 'EOF'
import json
try:
    with open('data/trades/trade_history.json', 'r') as f:
        trades = json.load(f)
    if len(trades) > 10000:
        with open('data/trades/trade_history.json', 'w') as f:
            json.dump(trades[-10000:], f, indent=2)
        print(f"Trimmed trade history from {len(trades)} to 10000")
except Exception as e:
    print(f"Error: {e}")
EOF

echo "Cleanup complete: $(date)"
