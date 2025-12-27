"""
Unit tests for PerformanceTracker class

Tests the core performance tracking functionality including initialization,
snapshot management, and performance calculation.
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

from utils.performance.performance_tracker import PerformanceTracker


class TestPerformanceTrackerInitialization:
    """Test PerformanceTracker initialization and setup"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "performance")
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_performance_tracker_initialization_with_defaults(self):
        """Test PerformanceTracker initialization with default settings"""
        tracker = PerformanceTracker(self.config_path)
        
        assert tracker.config_path == Path(self.config_path)
        assert tracker.config_file == Path(self.config_path) / "performance_config.json"
        assert tracker.snapshots_file == Path(self.config_path) / "portfolio_snapshots.json"
        assert tracker.metrics_file == Path(self.config_path) / "performance_metrics.json"
        assert tracker.periods_file == Path(self.config_path) / "performance_periods.json"
        
        # Check that directory was created
        assert os.path.exists(self.config_path)
        
        # Check that config was created with defaults
        assert tracker.config is not None
        assert "tracking_enabled" in tracker.config
        assert "snapshot_frequency" in tracker.config
        assert tracker.config["snapshot_frequency"] == "daily"
    
    def test_performance_tracker_creates_directory_structure(self):
        """Test that PerformanceTracker creates necessary directory structure"""
        nested_path = os.path.join(self.temp_dir, "data", "performance", "nested")
        
        # Directory should not exist initially
        assert not os.path.exists(nested_path)
        
        # Initialize tracker
        tracker = PerformanceTracker(nested_path)
        
        # Directory should now exist
        assert os.path.exists(nested_path)
        assert os.path.exists(tracker.config_file)
    
    def test_performance_tracker_loads_existing_config(self):
        """Test PerformanceTracker loads existing configuration"""
        # Create directory and config file
        os.makedirs(self.config_path, exist_ok=True)
        config_file = os.path.join(self.config_path, "performance_config.json")
        
        existing_config = {
            "tracking_start_date": "2025-06-01T12:00:00",
            "initial_portfolio_value": 1000.0,
            "tracking_enabled": True,
            "snapshot_frequency": "hourly"
        }
        
        with open(config_file, 'w') as f:
            json.dump(existing_config, f)
        
        # Initialize tracker
        tracker = PerformanceTracker(self.config_path)
        
        # Should load existing config
        assert tracker.config["tracking_start_date"] == "2025-06-01T12:00:00"
        assert tracker.config["initial_portfolio_value"] == 1000.0
        assert tracker.config["tracking_enabled"] is True
        assert tracker.config["snapshot_frequency"] == "hourly"
    
    def test_performance_tracker_handles_corrupted_config(self):
        """Test PerformanceTracker handles corrupted configuration file"""
        # Create directory and corrupted config file
        os.makedirs(self.config_path, exist_ok=True)
        config_file = os.path.join(self.config_path, "performance_config.json")
        
        with open(config_file, 'w') as f:
            f.write("invalid json content")
        
        # Initialize tracker - should handle corruption gracefully
        tracker = PerformanceTracker(self.config_path)
        
        # Should have error handling
        assert tracker.config is not None
        assert "tracking_enabled" in tracker.config
        # Should be disabled due to error
        assert tracker.config["tracking_enabled"] is False


class TestPerformanceInitialization:
    """Test performance tracking initialization"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "performance")
        self.tracker = PerformanceTracker(self.config_path)
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialize_tracking_with_valid_portfolio(self):
        """Test initialize tracking with valid portfolio data"""
        initial_value = 1000.0
        initial_composition = {"EUR": 100.0, "BTC": 0.001, "ETH": 0.5}
        
        result = self.tracker.initialize_tracking(initial_value, initial_composition)
        
        assert result is True
        assert self.tracker.config["tracking_enabled"] is True
        assert self.tracker.config["initial_portfolio_value"] == initial_value
        assert self.tracker.config["initial_portfolio_composition"] == initial_composition
        assert self.tracker.config["tracking_start_date"] is not None
        
        # Check reset history
        assert len(self.tracker.config["performance_reset_history"]) == 1
        reset_entry = self.tracker.config["performance_reset_history"][0]
        assert reset_entry["reason"] == "initial_setup"
        assert reset_entry["portfolio_value"] == initial_value
    
    def test_initialize_tracking_with_custom_start_date(self):
        """Test initialize tracking with custom start date"""
        initial_value = 1500.0
        initial_composition = {"EUR": 200.0, "BTC": 0.002}
        custom_date = "2025-06-01T10:00:00"
        
        result = self.tracker.initialize_tracking(initial_value, initial_composition, custom_date)
        
        assert result is True
        assert self.tracker.config["tracking_start_date"] == custom_date
    
    def test_initialize_tracking_error_handling(self):
        """Test initialize tracking error handling"""
        # Test with invalid data
        with patch.object(self.tracker, '_save_config', side_effect=Exception("Save error")):
            result = self.tracker.initialize_tracking(1000.0, {})
            assert result is False
    
    def test_tracking_state_persistence_across_restarts(self):
        """Test that tracking state persists across tracker restarts"""
        initial_value = 2000.0
        initial_composition = {"EUR": 500.0, "BTC": 0.003}
        
        # Initialize tracking
        self.tracker.initialize_tracking(initial_value, initial_composition)
        
        # Create new tracker instance (simulating restart)
        new_tracker = PerformanceTracker(self.config_path)
        
        # Should load existing configuration
        assert new_tracker.config["tracking_enabled"] is True
        assert new_tracker.config["initial_portfolio_value"] == initial_value
        assert new_tracker.config["initial_portfolio_composition"] == initial_composition


class TestPortfolioSnapshots:
    """Test portfolio snapshot functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "performance")
        self.tracker = PerformanceTracker(self.config_path)
        
        # Initialize tracking
        self.tracker.initialize_tracking(1000.0, {"EUR": 100.0, "BTC": 0.001})
        
        # Set to manual frequency for testing
        self.tracker.config["snapshot_frequency"] = "manual"
        self.tracker._save_config(self.tracker.config)
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_take_portfolio_snapshot_basic_functionality(self):
        """Test basic portfolio snapshot functionality"""
        portfolio_data = {
            "total_value_eur": 1100.0,
            "portfolio_composition": {"EUR": 50.0, "BTC": 0.0012},
            "asset_prices": {"BTC-EUR": 90000.0},
            "snapshot_type": "manual"
        }
        
        result = self.tracker.take_portfolio_snapshot(portfolio_data)
        
        assert result is True
        
        # Check that snapshot was saved
        snapshots = self.tracker._load_snapshots()
        assert len(snapshots) >= 1  # At least initial + this snapshot
        
        # Find our snapshot
        manual_snapshots = [s for s in snapshots if s.get("snapshot_type") == "manual"]
        assert len(manual_snapshots) == 1
        
        snapshot = manual_snapshots[0]
        assert snapshot["total_value_eur"] == 1100.0
        assert snapshot["portfolio_composition"] == {"EUR": 50.0, "BTC": 0.0012}
        assert snapshot["asset_prices"] == {"BTC-EUR": 90000.0}
    
    def test_take_portfolio_snapshot_with_trade_data(self):
        """Test portfolio snapshot with trade data"""
        portfolio_data = {
            "total_value_eur": 1050.0,
            "portfolio_composition": {"EUR": 75.0, "BTC": 0.0011},
            "snapshot_type": "post_trade",
            "trading_session_id": "session_123"
        }
        
        result = self.tracker.take_portfolio_snapshot(portfolio_data)
        
        assert result is True
        
        snapshots = self.tracker._load_snapshots()
        trade_snapshots = [s for s in snapshots if s.get("snapshot_type") == "post_trade"]
        assert len(trade_snapshots) == 1
        
        snapshot = trade_snapshots[0]
        assert snapshot["trading_session_id"] == "session_123"
    
    def test_snapshot_frequency_daily(self):
        """Test daily snapshot frequency logic"""
        # Set last snapshot to yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        self.tracker.config["last_snapshot_date"] = yesterday.isoformat()
        self.tracker.config["snapshot_frequency"] = "daily"
        
        # Should take snapshot (more than 1 day ago)
        assert self.tracker._should_take_snapshot() is True
        
        # Set last snapshot to 1 hour ago
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        self.tracker.config["last_snapshot_date"] = one_hour_ago.isoformat()
        
        # Should not take snapshot (less than 1 day ago)
        assert self.tracker._should_take_snapshot() is False
    
    def test_snapshot_frequency_hourly(self):
        """Test hourly snapshot frequency logic"""
        self.tracker.config["snapshot_frequency"] = "hourly"
        
        # Set last snapshot to 2 hours ago
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        self.tracker.config["last_snapshot_date"] = two_hours_ago.isoformat()
        
        # Should take snapshot
        assert self.tracker._should_take_snapshot() is True
        
        # Set last snapshot to 30 minutes ago
        thirty_min_ago = datetime.utcnow() - timedelta(minutes=30)
        self.tracker.config["last_snapshot_date"] = thirty_min_ago.isoformat()
        
        # Should not take snapshot
        assert self.tracker._should_take_snapshot() is False
    
    def test_snapshot_deduplication_logic(self):
        """Test that snapshots are not duplicated unnecessarily"""
        # Take first snapshot
        portfolio_data = {"total_value_eur": 1000.0, "portfolio_composition": {}}
        
        # Set frequency to daily and last snapshot to now
        self.tracker.config["snapshot_frequency"] = "daily"
        self.tracker.config["last_snapshot_date"] = datetime.utcnow().isoformat()
        
        result = self.tracker.take_portfolio_snapshot(portfolio_data)
        
        # Should not take snapshot due to frequency limit
        assert result is False
    
    def test_snapshot_data_validation_and_integrity(self):
        """Test snapshot data validation and integrity"""
        # Test with missing required fields
        incomplete_data = {"total_value_eur": 1000.0}  # Missing composition
        
        result = self.tracker.take_portfolio_snapshot(incomplete_data)
        
        # Should still work with defaults
        assert result is True
        
        snapshots = self.tracker._load_snapshots()
        latest_snapshot = snapshots[-1]
        assert "portfolio_composition" in latest_snapshot
        assert "timestamp" in latest_snapshot
    
    def test_snapshot_with_disabled_tracking(self):
        """Test snapshot behavior when tracking is disabled"""
        self.tracker.config["tracking_enabled"] = False
        
        portfolio_data = {"total_value_eur": 1000.0, "portfolio_composition": {}}
        result = self.tracker.take_portfolio_snapshot(portfolio_data)
        
        # Should not take snapshot when disabled
        assert result is False


class TestPerformanceReset:
    """Test performance reset functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "performance")
        self.tracker = PerformanceTracker(self.config_path)
        
        # Initialize tracking
        self.tracker.initialize_tracking(1000.0, {"EUR": 100.0, "BTC": 0.001})
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_reset_performance_tracking(self):
        """Test basic performance reset functionality"""
        new_value = 1500.0
        new_composition = {"EUR": 200.0, "BTC": 0.0015}
        
        result = self.tracker.reset_performance_tracking(new_value, new_composition, "test_reset")
        
        assert result is True
        assert self.tracker.config["initial_portfolio_value"] == new_value
        assert self.tracker.config["initial_portfolio_composition"] == new_composition
        
        # Check reset history
        reset_history = self.tracker.config["performance_reset_history"]
        assert len(reset_history) == 2  # Initial + reset
        
        latest_reset = reset_history[-1]
        assert latest_reset["reason"] == "test_reset"
        assert latest_reset["portfolio_value"] == new_value
        assert "previous_start_date" in latest_reset
        assert "previous_initial_value" in latest_reset
    
    def test_reset_preserves_historical_data(self):
        """Test that reset preserves historical data in reset history"""
        original_start_date = self.tracker.config["tracking_start_date"]
        original_value = self.tracker.config["initial_portfolio_value"]
        
        # Reset performance
        self.tracker.reset_performance_tracking(2000.0, {}, "preserve_test")
        
        # Check that previous data is preserved
        reset_history = self.tracker.config["performance_reset_history"]
        latest_reset = reset_history[-1]
        
        assert latest_reset["previous_start_date"] == original_start_date
        assert latest_reset["previous_initial_value"] == original_value
    
    def test_reset_with_custom_reason_logging(self):
        """Test reset with custom reason logging"""
        custom_reason = "quarterly_reset_2025_q2"
        
        result = self.tracker.reset_performance_tracking(1800.0, {}, custom_reason)
        
        assert result is True
        
        reset_history = self.tracker.config["performance_reset_history"]
        latest_reset = reset_history[-1]
        assert latest_reset["reason"] == custom_reason
    
    def test_multiple_reset_periods_handling(self):
        """Test handling of multiple reset periods"""
        # Perform multiple resets
        self.tracker.reset_performance_tracking(1200.0, {}, "reset_1")
        self.tracker.reset_performance_tracking(1400.0, {}, "reset_2")
        self.tracker.reset_performance_tracking(1600.0, {}, "reset_3")
        
        reset_history = self.tracker.config["performance_reset_history"]
        assert len(reset_history) == 4  # Initial + 3 resets
        
        # Check that all resets are recorded
        reasons = [reset["reason"] for reset in reset_history[1:]]  # Skip initial
        assert "reset_1" in reasons
        assert "reset_2" in reasons
        assert "reset_3" in reasons


class TestPerformanceDataRetrieval:
    """Test performance data retrieval functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "performance")
        self.tracker = PerformanceTracker(self.config_path)
        
        # Initialize tracking
        self.tracker.initialize_tracking(1000.0, {"EUR": 100.0, "BTC": 0.001})
        
        # Add some test snapshots
        self._add_test_snapshots()
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _add_test_snapshots(self):
        """Add test snapshots for different time periods"""
        base_time = datetime.utcnow()
        
        # Add snapshots for different periods
        test_snapshots = [
            {"days_ago": 0, "value": 1100.0},    # Today
            {"days_ago": 1, "value": 1080.0},    # 1 day ago
            {"days_ago": 7, "value": 1050.0},    # 1 week ago
            {"days_ago": 30, "value": 1000.0},   # 1 month ago
            {"days_ago": 90, "value": 950.0},    # 3 months ago
        ]
        
        for snapshot_data in test_snapshots:
            snapshot_time = base_time - timedelta(days=snapshot_data["days_ago"])
            portfolio_data = {
                "total_value_eur": snapshot_data["value"],
                "portfolio_composition": {"EUR": 50.0, "BTC": 0.001},
                "snapshot_type": "test_data"
            }
            
            # Manually create snapshot with specific timestamp
            snapshot = {
                "timestamp": snapshot_time.isoformat(),
                "total_value_eur": portfolio_data["total_value_eur"],
                "portfolio_composition": portfolio_data["portfolio_composition"],
                "snapshot_type": portfolio_data["snapshot_type"]
            }
            
            # Load existing snapshots and add new one
            snapshots = self.tracker._load_snapshots()
            snapshots.append(snapshot)
            self.tracker._save_snapshots(snapshots)
    
    def test_get_performance_summary_for_different_periods(self):
        """Test getting performance summary for different time periods"""
        # Test 7-day period
        summary_7d = self.tracker.get_performance_summary("7d")
        assert "error" not in summary_7d
        assert summary_7d["period"] == "7d"
        assert "total_return_percent" in summary_7d
        
        # Test 30-day period
        summary_30d = self.tracker.get_performance_summary("30d")
        assert "error" not in summary_30d
        assert summary_30d["period"] == "30d"
        
        # Test all-time period
        summary_all = self.tracker.get_performance_summary("all")
        assert "error" not in summary_all
        assert summary_all["period"] == "all"
    
    def test_get_performance_summary_with_no_data(self):
        """Test performance summary with no data"""
        # Create new tracker with no snapshots
        empty_tracker = PerformanceTracker(os.path.join(self.temp_dir, "empty"))
        empty_tracker.initialize_tracking(1000.0, {})
        
        # Clear snapshots
        empty_tracker._save_snapshots([])
        
        summary = empty_tracker.get_performance_summary("30d")
        assert "error" in summary
    
    def test_get_performance_summary_with_disabled_tracking(self):
        """Test performance summary when tracking is disabled"""
        self.tracker.config["tracking_enabled"] = False
        
        summary = self.tracker.get_performance_summary("30d")
        assert "error" in summary
        assert "not enabled" in summary["error"]
    
    def test_performance_data_filtering_by_date_ranges(self):
        """Test performance data filtering by date ranges"""
        # Test that 7d period returns fewer snapshots than 30d
        snapshots_7d = self.tracker._filter_snapshots_by_period(
            self.tracker._load_snapshots(), "7d"
        )
        snapshots_30d = self.tracker._filter_snapshots_by_period(
            self.tracker._load_snapshots(), "30d"
        )
        
        assert len(snapshots_7d) <= len(snapshots_30d)
    
    def test_tracking_info_retrieval(self):
        """Test getting tracking information"""
        info = self.tracker.get_tracking_info()
        
        assert info["tracking_enabled"] is True
        assert "tracking_start_date" in info
        assert "initial_portfolio_value" in info
        assert "snapshot_frequency" in info
        assert info["reset_count"] >= 1  # At least initial setup
    
    def test_snapshots_count_retrieval(self):
        """Test getting snapshots count"""
        count = self.tracker.get_snapshots_count()
        assert count > 0  # Should have at least initial + test snapshots


if __name__ == '__main__':
    pytest.main([__file__])
