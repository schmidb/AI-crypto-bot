#!/bin/bash
# Script to set up automatic daily log rotation and cleanup

echo "Setting up automatic log rotation and cleanup..."

# Add cron job for daily log cleanup (runs at 2 AM daily)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/markus/AI-crypto-bot/cleanup_logs.sh >> /home/markus/AI-crypto-bot/logs/cleanup.log 2>&1") | crontab -

echo "Cron job added for daily log cleanup at 2 AM"

# Run initial cleanup
echo "Running initial log cleanup..."
./cleanup_logs.sh

echo "Log rotation setup completed!"
echo ""
echo "Summary of changes:"
echo "1. Updated logger.py with daily rotating handlers"
echo "2. Updated main.py to use daily rotating logger"
echo "3. Created cleanup script for old log files"
echo "4. Added daily cron job for automatic cleanup"
echo ""
echo "Your logs will now:"
echo "- Rotate daily at midnight"
echo "- Keep 30 days of history"
echo "- Automatically clean up files older than 30 days"
echo "- Use format: supervisor_YYYYMMDD.log"
echo ""
echo "To apply supervisor changes, run: ./update_supervisor_logging.sh"
