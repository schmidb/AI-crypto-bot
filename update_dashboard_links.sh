#!/bin/bash

# Script to update dashboard symlinks to latest market data files
DATA_DIR="/home/markus/AI-crypto-bot/data"
WEB_DATA_DIR="/var/www/html/crypto-bot/data"

# Update BTC latest file
BTC_LATEST=$(ls -t $DATA_DIR/BTC_USD_*.json 2>/dev/null | head -1)
if [ -n "$BTC_LATEST" ]; then
    ln -sf "$BTC_LATEST" "$WEB_DATA_DIR/btc_latest.json"
fi

# Update ETH latest file
ETH_LATEST=$(ls -t $DATA_DIR/ETH_USD_*.json 2>/dev/null | head -1)
if [ -n "$ETH_LATEST" ]; then
    ln -sf "$ETH_LATEST" "$WEB_DATA_DIR/eth_latest.json"
fi

# Update SOL latest file
SOL_LATEST=$(ls -t $DATA_DIR/SOL_USD_*.json 2>/dev/null | head -1)
if [ -n "$SOL_LATEST" ]; then
    ln -sf "$SOL_LATEST" "$WEB_DATA_DIR/sol_latest.json"
fi

# Update bot startup file
if [ -f "$DATA_DIR/cache/bot_startup.json" ]; then
    ln -sf "$DATA_DIR/cache/bot_startup.json" "$WEB_DATA_DIR/bot_startup.json"
fi

echo "Dashboard links updated at $(date)"
