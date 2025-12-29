#!/bin/bash

# Log monitoring script for AI Crypto Trading Bot
# Provides clean, filtered views of different log types

LOG_DIR="/home/markus/AI-crypto-bot/logs"

show_help() {
    echo "🔍 AI Crypto Bot Log Monitor"
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  trading    - Show trading decisions only"
    echo "  errors     - Show errors and warnings only"
    echo "  clean      - Show filtered main log (no noise)"
    echo "  all        - Show all recent activity"
    echo "  live       - Live tail of clean logs"
    echo "  status     - Show log file status"
    echo ""
}

show_trading() {
    echo "🎯 Recent Trading Decisions:"
    echo "=========================="
    if [[ -f "$LOG_DIR/trading_decisions.log" ]]; then
        tail -20 "$LOG_DIR/trading_decisions.log"
    else
        echo "No trading decisions log found"
    fi
}

show_errors() {
    echo "❌ Recent Errors and Warnings:"
    echo "============================="
    if [[ -f "$LOG_DIR/errors.log" ]]; then
        tail -20 "$LOG_DIR/errors.log"
    else
        echo "No errors log found"
    fi
}

show_clean() {
    echo "📋 Clean Bot Activity (Last 30 lines):"
    echo "======================================"
    if [[ -f "$LOG_DIR/trading_bot.log" ]]; then
        tail -30 "$LOG_DIR/trading_bot.log" | grep -v -E "(Hard link|HTTP Request|AFC is enabled|Synced.*files|Modified and copied|Static files)"
    else
        echo "No main log found"
    fi
}

show_all() {
    echo "📊 All Recent Activity:"
    echo "======================"
    if [[ -f "$LOG_DIR/trading_bot.log" ]]; then
        tail -20 "$LOG_DIR/trading_bot.log"
    else
        echo "No main log found"
    fi
}

show_live() {
    echo "🔴 Live Log Monitor (Ctrl+C to exit):"
    echo "====================================="
    if [[ -f "$LOG_DIR/trading_bot.log" ]]; then
        tail -f "$LOG_DIR/trading_bot.log" | grep -v -E "(Hard link|HTTP Request|AFC is enabled|Synced.*files|Modified and copied|Static files)" --line-buffered
    else
        echo "No main log found"
    fi
}

show_status() {
    echo "📊 Log File Status:"
    echo "=================="
    
    if [[ -d "$LOG_DIR" ]]; then
        echo "Directory: $LOG_DIR"
        echo "Total size: $(du -sh "$LOG_DIR" | cut -f1)"
        echo ""
        
        echo "Log Files:"
        find "$LOG_DIR" -name "*.log" -type f | while read -r file; do
            size=$(ls -lh "$file" | awk '{print $5}')
            modified=$(ls -l "$file" | awk '{print $6, $7, $8}')
            echo "  $(basename "$file"): $size (modified: $modified)"
        done
        
        echo ""
        echo "Compressed Files:"
        find "$LOG_DIR" -name "*.gz" -type f | wc -l | xargs echo "  Count:"
        
        echo ""
        echo "Bot Process Status:"
        if pgrep -f "python.*main.py" > /dev/null; then
            echo "  ✅ Bot is running"
            pgrep -f "python.*main.py" | xargs ps -p | tail -n +2
        else
            echo "  ❌ Bot is not running"
        fi
    else
        echo "❌ Log directory not found: $LOG_DIR"
    fi
}

# Main execution
case "${1:-help}" in
    trading)
        show_trading
        ;;
    errors)
        show_errors
        ;;
    clean)
        show_clean
        ;;
    all)
        show_all
        ;;
    live)
        show_live
        ;;
    status)
        show_status
        ;;
    help|*)
        show_help
        ;;
esac
