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
            log_file_path: Path to the log file. If None, uses default supervisor log
        """
        if log_file_path:
            self.log_file_path = Path(log_file_path)
        else:
            # Default to supervisor log file
            self.log_file_path = Path("logs/supervisor.log")
        
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
        Get formatted logs for dashboard display
        
        Args:
            num_lines: Number of recent lines to return
            
        Returns:
            Dictionary with logs and metadata
        """
        try:
            recent_logs = self.get_recent_logs(num_lines)
            log_stats = self.get_log_stats()
            
            # Parse each log line
            parsed_logs = []
            for line in recent_logs:
                parsed_log = self.parse_log_line(line)
                parsed_logs.append(parsed_log)
            
            return {
                "logs": recent_logs,  # Raw log lines for simple display
                "parsed_logs": parsed_logs,  # Parsed log objects
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
