"""
Performance Tracker - Core performance tracking functionality

This module provides comprehensive performance tracking that survives bot restarts
and maintains historical portfolio performance data.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Core performance tracking functionality
    
    Tracks portfolio performance across bot restarts, maintains historical data,
    and provides comprehensive performance metrics calculation.
    """
    
    def __init__(self, config_path: str = "data/performance/"):
        """
        Initialize the performance tracker
        
        Args:
            config_path: Path to performance data directory
        """
        self.config_path = Path(config_path)
        self.config_file = self.config_path / "performance_config.json"
        self.snapshots_file = self.config_path / "portfolio_snapshots.json"
        self.metrics_file = self.config_path / "performance_metrics.json"
        self.periods_file = self.config_path / "performance_periods.json"
        
        # Create directory structure
        self._ensure_directory_structure()
        
        # Load or initialize configuration
        self.config = self._load_or_create_config()
        
        logger.info(f"Performance tracker initialized with config path: {config_path}")
    
    def _ensure_directory_structure(self) -> None:
        """Create necessary directory structure for performance data"""
        try:
            self.config_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Performance directory structure created: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create performance directory structure: {e}")
            raise
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load existing configuration or create default configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info("Loaded existing performance configuration")
                return config
            else:
                # Create default configuration
                default_config = {
                    "tracking_start_date": None,
                    "initial_portfolio_value": None,
                    "initial_portfolio_composition": {},
                    "performance_reset_history": [],
                    "snapshot_frequency": "daily",
                    "last_snapshot_date": None,
                    "tracking_enabled": True,
                    "created_date": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
                
                self._save_config(default_config)
                logger.info("Created default performance configuration")
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading/creating performance configuration: {e}")
            # Return minimal default config to prevent crashes
            return {
                "tracking_enabled": False,
                "error": str(e)
            }
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.debug("Performance configuration saved")
        except Exception as e:
            logger.error(f"Failed to save performance configuration: {e}")
            raise
    
    def initialize_tracking(self, initial_portfolio_value: float, 
                          initial_portfolio_composition: Dict[str, Any],
                          start_date: Optional[str] = None) -> bool:
        """
        Initialize performance tracking with initial portfolio state
        
        Args:
            initial_portfolio_value: Initial total portfolio value in EUR
            initial_portfolio_composition: Initial portfolio composition
            start_date: Optional start date (ISO format), defaults to now
            
        Returns:
            bool: True if initialization successful
        """
        try:
            if start_date is None:
                start_date = datetime.utcnow().isoformat()
            
            # Update configuration
            self.config.update({
                "tracking_start_date": start_date,
                "initial_portfolio_value": initial_portfolio_value,
                "initial_portfolio_composition": initial_portfolio_composition,
                "tracking_enabled": True,
                "last_updated": datetime.utcnow().isoformat()
            })
            
            # Add to reset history
            reset_entry = {
                "date": start_date,
                "reason": "initial_setup",
                "portfolio_value": initial_portfolio_value,
                "portfolio_composition": initial_portfolio_composition
            }
            
            if "performance_reset_history" not in self.config:
                self.config["performance_reset_history"] = []
            
            self.config["performance_reset_history"].append(reset_entry)
            
            # Save configuration
            self._save_config(self.config)
            
            # Take initial snapshot
            self.take_portfolio_snapshot({
                "total_value_eur": initial_portfolio_value,
                "portfolio_composition": initial_portfolio_composition,
                "snapshot_type": "initial_setup"
            })
            
            logger.info(f"Performance tracking initialized with €{initial_portfolio_value:.2f} starting value")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize performance tracking: {e}")
            return False
    
    def take_portfolio_snapshot(self, portfolio_data: Dict[str, Any]) -> bool:
        """
        Take a portfolio snapshot for performance tracking
        
        Args:
            portfolio_data: Current portfolio data including total value and composition
            
        Returns:
            bool: True if snapshot taken successfully
        """
        try:
            if not self.config.get("tracking_enabled", False):
                logger.debug("Performance tracking disabled, skipping snapshot")
                return False
            
            current_time = datetime.utcnow().isoformat()
            
            # Check if we should take a snapshot based on frequency
            if not self._should_take_snapshot():
                logger.debug("Snapshot not needed based on frequency settings")
                return False
            
            # Create snapshot entry
            # Handle both dict and float formats for total_value_eur
            total_value_eur_raw = portfolio_data.get("total_value_eur", 0.0)
            if isinstance(total_value_eur_raw, dict):
                total_value_eur = float(total_value_eur_raw.get("amount", 0))
            else:
                total_value_eur = float(total_value_eur_raw) if total_value_eur_raw else 0
            
            snapshot = {
                "timestamp": current_time,
                "total_value_eur": total_value_eur,
                "portfolio_composition": portfolio_data.get("portfolio_composition", {}),
                "asset_prices": portfolio_data.get("asset_prices", {}),
                "snapshot_type": portfolio_data.get("snapshot_type", "scheduled"),
                "trading_session_id": portfolio_data.get("trading_session_id", "unknown")
            }
            
            # Load existing snapshots
            snapshots = self._load_snapshots()
            
            # Add new snapshot
            snapshots.append(snapshot)
            
            # Keep only recent snapshots (configurable retention)
            retention_days = self.config.get("retention_days", 365)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            snapshots = [s for s in snapshots if datetime.fromisoformat(s["timestamp"]) > cutoff_date]
            
            # Save snapshots
            self._save_snapshots(snapshots)
            
            # Update last snapshot date in config
            self.config["last_snapshot_date"] = current_time
            self._save_config(self.config)
            
            logger.info(f"Portfolio snapshot taken: €{snapshot['total_value_eur']:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to take portfolio snapshot: {e}")
            return False
    
    def _should_take_snapshot(self) -> bool:
        """Determine if a snapshot should be taken based on frequency settings"""
        try:
            frequency = self.config.get("snapshot_frequency", "daily")
            last_snapshot = self.config.get("last_snapshot_date")
            
            if last_snapshot is None:
                return True  # First snapshot
            
            last_snapshot_time = datetime.fromisoformat(last_snapshot)
            current_time = datetime.utcnow()
            time_diff = current_time - last_snapshot_time
            
            if frequency == "hourly":
                return time_diff >= timedelta(hours=1)
            elif frequency == "daily":
                return time_diff >= timedelta(days=1)
            elif frequency == "on_restart":
                return True  # Always take snapshot on restart
            elif frequency == "manual":
                return True  # Always allow manual snapshots
            else:
                logger.warning(f"Unknown snapshot frequency: {frequency}, defaulting to daily")
                return time_diff >= timedelta(days=1)
                
        except Exception as e:
            logger.error(f"Error checking snapshot frequency: {e}")
            return True  # Default to taking snapshot on error
    
    def _load_snapshots(self) -> List[Dict[str, Any]]:
        """Load portfolio snapshots from file"""
        try:
            if self.snapshots_file.exists():
                with open(self.snapshots_file, 'r') as f:
                    snapshots = json.load(f)
                return snapshots if isinstance(snapshots, list) else []
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading portfolio snapshots: {e}")
            return []
    
    def _save_snapshots(self, snapshots: List[Dict[str, Any]]) -> None:
        """Save portfolio snapshots to file"""
        try:
            with open(self.snapshots_file, 'w') as f:
                json.dump(snapshots, f, indent=2)
            logger.debug(f"Saved {len(snapshots)} portfolio snapshots")
        except Exception as e:
            logger.error(f"Failed to save portfolio snapshots: {e}")
            raise
    
    def reset_performance_tracking(self, current_portfolio_value: float,
                                 current_portfolio_composition: Dict[str, Any],
                                 reason: str = "user_request") -> bool:
        """
        Reset performance tracking to current portfolio state
        
        Args:
            current_portfolio_value: Current total portfolio value
            current_portfolio_composition: Current portfolio composition
            reason: Reason for reset
            
        Returns:
            bool: True if reset successful
        """
        try:
            reset_date = datetime.utcnow().isoformat()
            
            # Add to reset history
            reset_entry = {
                "date": reset_date,
                "reason": reason,
                "portfolio_value": current_portfolio_value,
                "portfolio_composition": current_portfolio_composition,
                "previous_start_date": self.config.get("tracking_start_date"),
                "previous_initial_value": self.config.get("initial_portfolio_value")
            }
            
            if "performance_reset_history" not in self.config:
                self.config["performance_reset_history"] = []
            
            self.config["performance_reset_history"].append(reset_entry)
            
            # Update tracking configuration
            self.config.update({
                "tracking_start_date": reset_date,
                "initial_portfolio_value": current_portfolio_value,
                "initial_portfolio_composition": current_portfolio_composition,
                "last_updated": reset_date
            })
            
            # Save configuration
            self._save_config(self.config)
            
            # Take reset snapshot
            self.take_portfolio_snapshot({
                "total_value_eur": current_portfolio_value,
                "portfolio_composition": current_portfolio_composition,
                "snapshot_type": "performance_reset"
            })
            
            logger.info(f"Performance tracking reset: €{current_portfolio_value:.2f} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset performance tracking: {e}")
            return False
    
    def get_performance_summary(self, period: str = "30d") -> Dict[str, Any]:
        """
        Get performance summary for specified period
        
        Args:
            period: Time period ("7d", "30d", "90d", "1y", "all")
            
        Returns:
            Dict containing performance summary
        """
        try:
            if not self.config.get("tracking_enabled", False):
                return {"error": "Performance tracking not enabled"}
            
            snapshots = self._load_snapshots()
            if len(snapshots) < 2:
                return {"error": "Insufficient data for performance calculation"}
            
            # Filter snapshots by period
            filtered_snapshots = self._filter_snapshots_by_period(snapshots, period)
            
            if len(filtered_snapshots) < 2:
                return {"error": f"Insufficient data for {period} period"}
            
            # Calculate basic performance metrics
            initial_value_raw = filtered_snapshots[0]["total_value_eur"]
            current_value_raw = filtered_snapshots[-1]["total_value_eur"]
            
            # Handle both dict and float formats for total_value_eur
            if isinstance(initial_value_raw, dict):
                initial_value = float(initial_value_raw.get("amount", 0))
            else:
                initial_value = float(initial_value_raw) if initial_value_raw else 0
                
            if isinstance(current_value_raw, dict):
                current_value = float(current_value_raw.get("amount", 0))
            else:
                current_value = float(current_value_raw) if current_value_raw else 0
            
            total_return = ((current_value - initial_value) / initial_value) * 100 if initial_value > 0 else 0
            
            summary = {
                "period": period,
                "start_date": filtered_snapshots[0]["timestamp"],
                "end_date": filtered_snapshots[-1]["timestamp"],
                "initial_value": initial_value,
                "current_value": current_value,
                "absolute_change": current_value - initial_value,
                "total_return_percent": total_return,
                "snapshots_count": len(filtered_snapshots),
                "tracking_enabled": True
            }
            
            logger.debug(f"Generated performance summary for {period}: {total_return:.2f}%")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"error": str(e)}
    
    def _filter_snapshots_by_period(self, snapshots: List[Dict[str, Any]], period: str) -> List[Dict[str, Any]]:
        """Filter snapshots by time period"""
        try:
            if period == "all":
                return snapshots
            
            # Parse period
            if period.endswith('d'):
                days = int(period[:-1])
                cutoff_date = datetime.utcnow() - timedelta(days=days)
            elif period.endswith('y'):
                years = int(period[:-1])
                cutoff_date = datetime.utcnow() - timedelta(days=years * 365)
            else:
                logger.warning(f"Unknown period format: {period}, using all data")
                return snapshots
            
            # Filter snapshots
            filtered = [s for s in snapshots if datetime.fromisoformat(s["timestamp"]) >= cutoff_date]
            
            # Sort by timestamp
            filtered.sort(key=lambda x: x["timestamp"])
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtering snapshots by period {period}: {e}")
            return snapshots
    
    def is_tracking_enabled(self) -> bool:
        """Check if performance tracking is enabled"""
        return self.config.get("tracking_enabled", False)
    
    def get_tracking_info(self) -> Dict[str, Any]:
        """Get current tracking information"""
        return {
            "tracking_enabled": self.config.get("tracking_enabled", False),
            "tracking_start_date": self.config.get("tracking_start_date"),
            "initial_portfolio_value": self.config.get("initial_portfolio_value"),
            "last_snapshot_date": self.config.get("last_snapshot_date"),
            "snapshot_frequency": self.config.get("snapshot_frequency", "daily"),
            "reset_count": len(self.config.get("performance_reset_history", [])),
            "config_path": str(self.config_path)
        }
    
    def get_snapshots_count(self) -> int:
        """Get total number of snapshots"""
        try:
            snapshots = self._load_snapshots()
            return len(snapshots)
        except Exception as e:
            logger.error(f"Error getting snapshots count: {e}")
            return 0
