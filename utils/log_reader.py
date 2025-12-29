#!/usr/bin/env python3
"""
Log Reader Utility for AI Crypto Bot Dashboard
Reads and formats log files for the web dashboard
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class LogReader:
    """Utility class to read and format bot logs for dashboard display"""
    
    def __init__(self, log_file_path: str = None):
        """
        Initialize LogReader
        
        Args:
            log_file_path: Path to the log file. If None, uses new structured logs
        """
        if log_file_path:
            self.log_file_path = Path(log_file_path)
        else:
            # Use new structured log files - prioritize main trading bot log
            self.log_file_path = Path("logs/trading_bot.log")
            
            # Fallback to supervisor.log if new logs don't exist
            if not self.log_file_path.exists():
                self.log_file_path = Path("logs/supervisor.log")
        
        # Store additional log files for comprehensive view
        self.trading_decisions_log = Path("logs/trading_decisions.log")
        self.errors_log = Path("logs/errors.log")
        
        # Ensure log file exists
        if not self.log_file_path.exists():
            logger.warning(f"Log file not found: {self.log_file_path}")
    
    def get_recent_logs(self, num_lines: int = 30) -> List[str]:
        """
        Get the most recent log lines
        
        Args:
            num_lines: Number of recent lines to return
            
        Returns:
            List of log lines (strings)
        """
        try:
            if not self.log_file_path.exists():
                return []
            
            # Read the last N lines efficiently
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                # Read all lines and get the last N
                lines = file.readlines()
                recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines
                
                # Clean up lines (remove newlines and empty lines)
                cleaned_lines = []
                for line in recent_lines:
                    line = line.strip()
                    if line:  # Skip empty lines
                        cleaned_lines.append(line)
                
                return cleaned_lines
                
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return []
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the log file
        
        Returns:
            Dictionary with log file statistics
        """
        try:
            if not self.log_file_path.exists():
                return {
                    "exists": False,
                    "size": 0,
                    "lines": 0,
                    "last_modified": None
                }
            
            stat = self.log_file_path.stat()
            
            # Count lines
            line_count = 0
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                line_count = sum(1 for _ in file)
            
            return {
                "exists": True,
                "size": stat.st_size,
                "lines": line_count,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(self.log_file_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting log stats: {e}")
            return {
                "exists": False,
                "error": str(e)
            }
    
    def parse_log_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a log line into components
        
        Args:
            line: Raw log line
            
        Returns:
            Dictionary with parsed components
        """
        try:
            # Expected format: "YYYY-MM-DD HH:MM:SS,mmm - logger_name - LEVEL - message"
            parts = line.split(' - ', 3)
            
            if len(parts) >= 4:
                timestamp_str = parts[0]
                logger_name = parts[1]
                level = parts[2]
                message = parts[3]
                
                return {
                    "timestamp": timestamp_str,
                    "logger": logger_name,
                    "level": level,
                    "message": message,
                    "raw": line
                }
            else:
                # Fallback for non-standard format
                return {
                    "timestamp": "",
                    "logger": "",
                    "level": "INFO",
                    "message": line,
                    "raw": line
                }
                
        except Exception as e:
            logger.error(f"Error parsing log line: {e}")
            return {
                "timestamp": "",
                "logger": "",
                "level": "ERROR",
                "message": f"Error parsing log: {line}",
                "raw": line
            }
    
    def get_formatted_logs(self, num_lines: int = 30) -> Dict[str, Any]:
        """
        Get formatted logs for dashboard display using new structured logs
        """
        try:
            recent_logs = []
            
            # Get clean logs from main log file only (avoid mixing formats)
            main_logs = self.get_recent_logs(num_lines)
            
            # Clean and format each log entry
            for log in main_logs:
                # Skip empty lines
                if not log.strip():
                    continue
                    
                # Clean up the log format for consistent display
                cleaned_log = self._clean_log_entry(log)
                if cleaned_log:
                    recent_logs.append(cleaned_log)
            
            log_stats = self.get_log_stats()
            
            # Parse each log line
            parsed_logs = []
            for line in recent_logs:
                parsed_log = self.parse_log_line(line)
                parsed_logs.append(parsed_log)
            
            return {
                "logs": recent_logs,
                "parsed_logs": parsed_logs,
                "stats": log_stats,
                "count": len(recent_logs),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting formatted logs: {e}")
            return {
                "logs": [],
                "parsed_logs": [],
                "stats": {"exists": False, "error": str(e)},
                "count": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def _clean_log_entry(self, log_entry: str) -> str:
        """Clean and format a log entry for consistent display"""
        try:
            # Remove ANSI color codes
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            cleaned = ansi_escape.sub('', log_entry)
            
            # Add appropriate emoji based on content
            if any(word in cleaned.lower() for word in ['error', 'critical', 'failed', 'exception']):
                return f"🔴 {cleaned}"
            elif any(word in cleaned.lower() for word in ['trade', 'buy', 'sell', 'order', 'portfolio']):
                return f"💰 {cleaned}"
            elif any(word in cleaned.lower() for word in ['warning', 'warn']):
                return f"⚠️ {cleaned}"
            else:
                return f"📊 {cleaned}"
                
        except Exception:
            return log_entry
    
    def _get_recent_logs_from_file(self, file_path: Path, num_lines: int) -> List[str]:
        """Get recent logs from a specific file, handling multi-line entries"""
        try:
            if not file_path.exists():
                return []
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Split by timestamp pattern to handle multi-line entries
            import re
            
            # Pattern for log entries starting with timestamp
            timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}'
            
            # Split content by timestamp pattern but keep the timestamps
            entries = re.split(f'({timestamp_pattern})', content)
            
            # Reconstruct complete log entries
            complete_entries = []
            for i in range(1, len(entries), 2):  # Skip empty first element, take timestamp + content pairs
                if i + 1 < len(entries):
                    timestamp = entries[i]
                    content_part = entries[i + 1]
                    
                    # Clean up the content (remove extra newlines, keep structure)
                    content_part = content_part.strip()
                    if content_part:
                        # For multi-line entries, just take the first meaningful line
                        first_line = content_part.split('\n')[0]
                        if first_line.strip():
                            complete_entry = timestamp + first_line
                            complete_entries.append(complete_entry.strip())
            
            # Take the most recent entries
            recent_entries = complete_entries[-num_lines:] if len(complete_entries) > num_lines else complete_entries
            
            return recent_entries
                
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")
            return []
    
    def export_logs_json(self, output_path: str, num_lines: int = 30) -> bool:
        """
        Export logs to JSON file for dashboard consumption
        
        Args:
            output_path: Path to output JSON file
            num_lines: Number of recent lines to export
            
        Returns:
            True if successful, False otherwise
        """
        try:
            formatted_logs = self.get_formatted_logs(num_lines)
            
            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON file
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(formatted_logs, file, indent=2, ensure_ascii=False)
            
            logger.debug(f"Exported {len(formatted_logs['logs'])} log lines to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting logs to JSON: {e}")
            return False

def main():
    """CLI interface for testing log reader"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Crypto Bot Log Reader")
    parser.add_argument("--lines", "-n", type=int, default=30, help="Number of recent lines to show")
    parser.add_argument("--export", "-e", type=str, help="Export to JSON file")
    parser.add_argument("--log-file", "-f", type=str, help="Path to log file")
    parser.add_argument("--stats", "-s", action="store_true", help="Show log file statistics")
    
    args = parser.parse_args()
    
    # Initialize log reader
    log_reader = LogReader(args.log_file)
    
    if args.stats:
        # Show statistics
        stats = log_reader.get_log_stats()
        print("Log File Statistics:")
        print(json.dumps(stats, indent=2))
        return
    
    if args.export:
        # Export to JSON
        success = log_reader.export_logs_json(args.export, args.lines)
        if success:
            print(f"Successfully exported {args.lines} log lines to {args.export}")
        else:
            print(f"Failed to export logs to {args.export}")
        return
    
    # Show recent logs
    logs = log_reader.get_recent_logs(args.lines)
    print(f"Recent {len(logs)} log lines:")
    print("-" * 80)
    for log in logs:
        print(log)

if __name__ == "__main__":
    main()
