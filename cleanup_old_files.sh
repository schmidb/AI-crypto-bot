#!/bin/bash

# Cleanup script for AI Crypto Trading Bot
# This script removes old files to keep the repository clean

echo "Starting cleanup of old files..."

# Remove Python cache files
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove backup files
echo "Removing backup files..."
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*.backup" -delete 2>/dev/null || true
find . -name "*.orig" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true

# Clean old data files (keep last 7 days)
echo "Cleaning old data files (keeping last 7 days)..."
if [ -d "data" ]; then
    find data/ -name "*.json" -mtime +7 -delete 2>/dev/null || true
fi

# Compress old log files (older than 3 days)
echo "Compressing old log files..."
if [ -d "logs" ]; then
    find logs/ -name "*.log" -mtime +3 ! -name "*.gz" -exec gzip {} \; 2>/dev/null || true
fi

# Remove temporary files
echo "Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true

echo "Cleanup completed!"

# Show disk usage
echo "Current disk usage:"
du -sh . 2>/dev/null || true
