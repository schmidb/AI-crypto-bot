#!/usr/bin/env python3
"""
Data and log cleanup manager for the crypto trading bot.
Automatically removes old files based on retention policies.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import glob

logger = logging.getLogger(__name__)

class CleanupManager:
    """Manages cleanup of old logs and data files"""
    
    def __init__(self, base_path: str = "/home/markus/AI-crypto-bot"):
        self.base_path = Path(base_path)
        
        # Retention policies (in days)
        self.retention_policies = {
            'analysis_files': 42,      # 6 weeks - AI analysis JSON files
            'logs': 28,                # 4 weeks - application logs
            'cache': 14,               # 2 weeks - temporary cache files
            'performance_details': 84, # 12 weeks - detailed performance data
            'volatility': 28,          # 4 weeks - volatility data
        }
    
    def cleanup_analysis_files(self) -> int:
        """Clean up old analysis JSON files (BTC_EUR_*, ETH_EUR_*, etc.)"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_policies['analysis_files'])
        deleted_count = 0
        
        data_path = self.base_path / "data"
        if not data_path.exists():
            return 0
            
        # Pattern for analysis files: SYMBOL_EUR_YYYYMMDD_HHMMSS.json
        patterns = ["*_EUR_*.json", "*_USD_*.json"]
        
        for pattern in patterns:
            for file_path in data_path.glob(pattern):
                try:
                    # Skip latest files and portfolio.json
                    if file_path.name.endswith('_latest.json') or file_path.name == 'portfolio.json':
                        continue
                        
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old analysis file: {file_path.name}")
                        
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
        
        return deleted_count
    
    def cleanup_logs(self) -> int:
        """Clean up old log files"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_policies['logs'])
        deleted_count = 0
        
        logs_path = self.base_path / "logs"
        if not logs_path.exists():
            return 0
            
        for log_file in logs_path.glob("*.log*"):
            try:
                # Skip current active logs
                if log_file.name in ['supervisor.log', 'crypto_bot.log']:
                    continue
                    
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old log file: {log_file.name}")
                    
            except Exception as e:
                logger.warning(f"Failed to delete {log_file}: {e}")
        
        return deleted_count
    
    def cleanup_cache(self) -> int:
        """Clean up old cache files"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_policies['cache'])
        deleted_count = 0
        
        cache_path = self.base_path / "data" / "cache"
        if not cache_path.exists():
            return 0
            
        for cache_file in cache_path.glob("*"):
            try:
                if cache_file.is_file():
                    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        cache_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old cache file: {cache_file.name}")
                        
            except Exception as e:
                logger.warning(f"Failed to delete {cache_file}: {e}")
        
        return deleted_count
    
    def cleanup_performance_details(self) -> int:
        """Clean up old detailed performance files, keep summaries"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_policies['performance_details'])
        deleted_count = 0
        
        perf_path = self.base_path / "data" / "performance"
        if not perf_path.exists():
            return 0
            
        for perf_file in perf_path.glob("*.json"):
            try:
                # Keep daily/monthly summaries, clean detailed files
                if any(x in perf_file.name.lower() for x in ['summary', 'daily', 'monthly']):
                    continue
                    
                file_time = datetime.fromtimestamp(perf_file.stat().st_mtime)
                if file_time < cutoff_date:
                    perf_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old performance file: {perf_file.name}")
                    
            except Exception as e:
                logger.warning(f"Failed to delete {perf_file}: {e}")
        
        return deleted_count
    
    def cleanup_volatility_data(self) -> int:
        """Clean up old volatility data"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_policies['volatility'])
        deleted_count = 0
        
        vol_path = self.base_path / "data" / "volatility"
        if not vol_path.exists():
            return 0
            
        for vol_file in vol_path.glob("*.json"):
            try:
                file_time = datetime.fromtimestamp(vol_file.stat().st_mtime)
                if file_time < cutoff_date:
                    vol_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old volatility file: {vol_file.name}")
                    
            except Exception as e:
                logger.warning(f"Failed to delete {vol_file}: {e}")
        
        return deleted_count
    
    def get_disk_usage(self) -> dict:
        """Get current disk usage for bot directories"""
        usage = {}
        
        directories = ['data', 'logs', 'data/cache', 'data/performance', 'data/volatility']
        
        for dir_name in directories:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                usage[dir_name] = total_size / (1024 * 1024)  # MB
            else:
                usage[dir_name] = 0
                
        return usage
    
    def run_cleanup(self) -> dict:
        """Run all cleanup operations and return summary"""
        logger.info("🧹 Starting daily cleanup...")
        
        # Get disk usage before cleanup
        usage_before = self.get_disk_usage()
        
        # Run cleanup operations
        results = {
            'analysis_files': self.cleanup_analysis_files(),
            'logs': self.cleanup_logs(),
            'cache': self.cleanup_cache(),
            'performance_details': self.cleanup_performance_details(),
            'volatility_data': self.cleanup_volatility_data(),
        }
        
        # Get disk usage after cleanup
        usage_after = self.get_disk_usage()
        
        # Calculate space saved
        total_saved = sum(usage_before.values()) - sum(usage_after.values())
        
        # Log summary
        total_files = sum(results.values())
        logger.info(f"🧹 Cleanup completed: {total_files} files deleted, {total_saved:.1f}MB freed")
        
        for category, count in results.items():
            if count > 0:
                logger.info(f"  - {category}: {count} files")
        
        return {
            'files_deleted': results,
            'total_files': total_files,
            'space_saved_mb': total_saved,
            'usage_before': usage_before,
            'usage_after': usage_after
        }

if __name__ == "__main__":
    # For testing
    cleanup = CleanupManager()
    result = cleanup.run_cleanup()
    print(f"Cleanup completed: {result}")
