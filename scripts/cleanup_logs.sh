#!/bin/bash

# Log cleanup and rotation script for AI crypto trading bot
# This script manages log files to prevent disk space issues

LOG_DIR="/home/markus/AI-crypto-bot/logs"
MAX_LOG_SIZE_MB=10
MAX_AGE_DAYS=30

echo "🧹 Starting log cleanup process..."

# Function to rotate large log files
rotate_large_logs() {
    echo "📋 Checking for oversized log files..."
    
    find "$LOG_DIR" -name "*.log" -size +${MAX_LOG_SIZE_MB}M | while read -r logfile; do
        echo "📦 Rotating large log file: $(basename "$logfile")"
        
        # Create timestamped backup
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_name="${logfile}.${timestamp}"
        
        # Move current log to backup
        mv "$logfile" "$backup_name"
        
        # Compress the backup
        gzip "$backup_name"
        
        # Create new empty log file with correct permissions
        touch "$logfile"
        chown markus:markus "$logfile"
        chmod 644 "$logfile"
        
        echo "✅ Rotated: $(basename "$logfile") -> $(basename "$backup_name").gz"
    done
}

# Function to clean old log files
clean_old_logs() {
    echo "🗑️  Removing log files older than $MAX_AGE_DAYS days..."
    
    # Remove old compressed logs
    find "$LOG_DIR" -name "*.log.*.gz" -mtime +$MAX_AGE_DAYS -delete
    
    # Remove old bot restart logs
    find "$LOG_DIR" -name "bot_restart_*.log" -mtime +7 -delete
    
    # Remove old daily report files
    find "$LOG_DIR" -name "daily_report_*.txt" -mtime +14 -delete
    
    echo "✅ Old log cleanup completed"
}

# Function to compress current large logs
compress_logs() {
    echo "🗜️  Compressing large log files..."
    
    # Compress logs larger than 5MB that aren't the current supervisor log
    find "$LOG_DIR" -name "*.log" -size +5M ! -name "supervisor.log" | while read -r logfile; do
        if [[ ! "$logfile" =~ \.gz$ ]]; then
            echo "🗜️  Compressing: $(basename "$logfile")"
            gzip "$logfile"
        fi
    done
}

# Function to show log directory summary
show_summary() {
    echo ""
    echo "📊 Log Directory Summary:"
    echo "========================"
    
    total_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
    file_count=$(find "$LOG_DIR" -type f | wc -l)
    
    echo "Total size: $total_size"
    echo "File count: $file_count"
    echo ""
    
    echo "Largest files:"
    find "$LOG_DIR" -type f -exec ls -lh {} \; | sort -k5 -hr | head -5 | awk '{print $5 " " $9}'
    echo ""
    
    echo "Recent activity:"
    find "$LOG_DIR" -name "*.log" -mtime -1 | head -5 | while read -r file; do
        size=$(ls -lh "$file" | awk '{print $5}')
        echo "  $(basename "$file"): $size"
    done
}

# Main execution
cd "$(dirname "$0")/.." || exit 1

# Check if log directory exists
if [[ ! -d "$LOG_DIR" ]]; then
    echo "❌ Log directory not found: $LOG_DIR"
    exit 1
fi

# Show initial state
echo "📍 Current log directory: $LOG_DIR"
show_summary

# Perform cleanup operations
rotate_large_logs
clean_old_logs
compress_logs

# Show final state
echo ""
echo "🎉 Log cleanup completed!"
show_summary

# Create a simple log rotation config for logrotate (optional)
cat > /tmp/crypto-bot-logrotate << 'EOF'
/home/markus/AI-crypto-bot/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    maxsize 10M
}
EOF

echo ""
echo "💡 To enable automatic log rotation, run:"
echo "   sudo cp /tmp/crypto-bot-logrotate /etc/logrotate.d/crypto-bot"
echo ""
echo "🔄 To run this cleanup manually: ./scripts/cleanup_logs.sh"
