#!/bin/bash
# Script to clean up old large log files and implement daily rotation

echo "Cleaning up old log files..."

# Navigate to the project directory
cd /home/markus/AI-crypto-bot

# Create logs directory if it doesn't exist
mkdir -p logs

# Check current supervisor.log size
if [ -f "logs/supervisor.log" ]; then
    size=$(du -h logs/supervisor.log | cut -f1)
    echo "Current supervisor.log size: $size"
    
    # If the file is large, archive it with timestamp
    if [ $(stat -f%z logs/supervisor.log 2>/dev/null || stat -c%s logs/supervisor.log) -gt 10485760 ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        echo "Archiving large supervisor.log as supervisor_archive_$timestamp.log"
        mv logs/supervisor.log logs/supervisor_archive_$timestamp.log
        
        # Compress the archived file to save space
        gzip logs/supervisor_archive_$timestamp.log
        echo "Archived and compressed old log file"
    fi
fi

# Remove log files older than 30 days
echo "Removing log files older than 30 days..."
find logs/ -name "*.log*" -type f -mtime +30 -delete 2>/dev/null || true
find logs/ -name "*.gz" -type f -mtime +30 -delete 2>/dev/null || true

echo "Log cleanup completed!"

# Show current log directory status
echo "Current logs directory:"
ls -lah logs/ | head -20
