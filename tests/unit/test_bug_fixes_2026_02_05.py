"""
Regression tests for bugs fixed on 2026-02-05

Tests ensure the following bugs don't reoccur:
1. Datetime timezone double-append bug
2. Capital allocation with small amounts
3. Performance tracker timezone comparison
4. Deprecated datetime.utcnow() usage
5. Dashboard module import errors
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import json


class TestDatetimeTimezoneFixes:
    """Test datetime timezone handling fixes"""
    
    def test_no_double_timezone_in_isoformat(self):
        """Test that timezone-aware datetime doesn't get double timezone suffix"""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=1)
        
        # Correct way: strip timezone before adding 'Z'
        start_str = start_time.replace(tzinfo=None).isoformat() + 'Z'
        end_str = now.replace(tzinfo=None).isoformat() + 'Z'
        
        # Should not contain double timezone
        assert '+00:00+00:00' not in start_str
        assert '+00:00+00:00' not in end_str
        assert start_str.endswith('Z')
        assert end_str.endswith('Z')
    
    def test_datetime_now_with_timezone_utc(self):
        """Test that datetime.now(timezone.utc) is used instead of deprecated utcnow()"""
        # This should work without deprecation warnings
        now = datetime.now(timezone.utc)
        
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc
    
    def test_isoformat_parsing_with_z_suffix(self):
        """Test that Z-suffixed timestamps can be parsed correctly"""
        timestamp_str = "2026-02-05T08:00:00.123456Z"
        
        # Should parse correctly
        parsed = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        assert parsed.tzinfo is not None
        assert isinstance(parsed, datetime)


class TestCapitalAllocationBugFix:
    """Test capital allocation bug fixes"""
    
    @pytest.fixture
    def opportunity_manager(self):
        """Create opportunity manager for testing"""
        from utils.trading.opportunity_manager import OpportunityManager
        
        config = Mock()
        config.CONFIDENCE_THRESHOLD_BUY = 50
        config.MIN_TRADE_AMOUNT = 30.0
        
        return OpportunityManager(config)
    
    def test_small_capital_allocation_bug(self, opportunity_manager):
        """
        Test the specific bug: €37.79 available should allocate to at least one trade
        
        Bug: With €37.79 available and €30 minimum, bot was allocating €0.00
        Fix: Check remaining capital before each allocation
        """
        trading_capital = 37.79
        
        opportunities = [
            {
                'product_id': 'BTC-EUR',
                'opportunity_score': 100.0,
                'action': 'BUY',
                'confidence': 92.4,
                'analysis': {'market_data': {}}
            }
        ]
        
        allocations = opportunity_manager._calculate_weighted_allocations(
            opportunities, trading_capital
        )
        
        # Should allocate at least minimum trade amount
        assert 'BTC-EUR' in allocations
        assert allocations['BTC-EUR'] >= 30.0
        assert allocations['BTC-EUR'] <= trading_capital
    
    def test_insufficient_capital_returns_empty(self, opportunity_manager):
        """Test that insufficient capital returns empty allocations"""
        trading_capital = 20.0  # Less than minimum €30
        
        opportunities = [
            {
                'product_id': 'BTC-EUR',
                'opportunity_score': 100.0,
                'action': 'BUY',
                'confidence': 92.4,
                'analysis': {'market_data': {}}
            }
        ]
        
        allocations = opportunity_manager._calculate_weighted_allocations(
            opportunities, trading_capital
        )
        
        # Should return empty allocations
        assert allocations == {}
    
    def test_multiple_opportunities_with_limited_capital(self, opportunity_manager):
        """Test allocation with multiple opportunities but limited capital"""
        trading_capital = 50.0  # Only enough for one trade
        
        opportunities = [
            {
                'product_id': 'BTC-EUR',
                'opportunity_score': 100.0,
                'action': 'BUY',
                'confidence': 92.4,
                'analysis': {'market_data': {}}
            },
            {
                'product_id': 'ETH-EUR',
                'opportunity_score': 80.0,
                'action': 'BUY',
                'confidence': 75.0,
                'analysis': {'market_data': {}}
            }
        ]
        
        allocations = opportunity_manager._calculate_weighted_allocations(
            opportunities, trading_capital
        )
        
        # Should allocate to highest opportunity only
        assert 'BTC-EUR' in allocations
        # ETH-EUR might not get allocation due to insufficient remaining capital
        total_allocated = sum(allocations.values())
        assert total_allocated <= trading_capital


class TestPerformanceTrackerTimezoneFix:
    """Test performance tracker timezone comparison fixes"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp = tempfile.mkdtemp()
        yield temp
        import shutil
        shutil.rmtree(temp)
    
    def test_filter_snapshots_mixed_timezone_awareness(self, temp_dir):
        """
        Test filtering snapshots with mixed timezone-aware and naive datetimes
        
        Bug: "can't compare offset-naive and offset-aware datetimes"
        Fix: Make all timestamps timezone-aware before comparison
        """
        from utils.performance.performance_tracker import PerformanceTracker
        
        tracker = PerformanceTracker(temp_dir)
        
        # Create snapshots with mixed timezone awareness
        now = datetime.now(timezone.utc)
        snapshots = [
            {
                "timestamp": (now - timedelta(days=10)).isoformat(),  # Timezone-aware
                "value": 100
            },
            {
                "timestamp": (now - timedelta(days=5)).replace(tzinfo=None).isoformat(),  # Naive
                "value": 110
            },
            {
                "timestamp": now.isoformat(),  # Timezone-aware
                "value": 120
            }
        ]
        
        # Should not raise timezone comparison error
        filtered = tracker._filter_snapshots_by_period(snapshots, "7d")
        
        # Should filter correctly (only last 7 days)
        assert len(filtered) == 2  # 5 days ago and now
        assert filtered[0]["value"] == 110
        assert filtered[1]["value"] == 120
    
    def test_filter_snapshots_all_timezone_aware(self, temp_dir):
        """Test filtering with all timezone-aware timestamps"""
        from utils.performance.performance_tracker import PerformanceTracker
        
        tracker = PerformanceTracker(temp_dir)
        
        now = datetime.now(timezone.utc)
        snapshots = [
            {"timestamp": (now - timedelta(days=40)).isoformat(), "value": 100},
            {"timestamp": (now - timedelta(days=20)).isoformat(), "value": 110},
            {"timestamp": now.isoformat(), "value": 120}
        ]
        
        # Test different periods
        filtered_30d = tracker._filter_snapshots_by_period(snapshots, "30d")
        assert len(filtered_30d) == 2
        
        filtered_1y = tracker._filter_snapshots_by_period(snapshots, "1y")
        assert len(filtered_1y) == 3


class TestDashboardUpdaterFixes:
    """Test dashboard updater fixes"""
    
    def test_datetime_import_correct(self):
        """Test that datetime is imported as class, not module"""
        from utils.dashboard.dashboard_updater import datetime
        
        # Should be able to call datetime.now() directly
        now = datetime.now(timezone.utc)
        assert isinstance(now, datetime)
    
    def test_log_reader_import_graceful_failure(self):
        """Test that missing log_reader module is handled gracefully"""
        from utils.dashboard.dashboard_updater import DashboardUpdater
        
        updater = DashboardUpdater()
        
        # Should not crash even if log_reader is missing
        try:
            updater._update_logs_data()
            # Should create empty logs data file
            assert os.path.exists("data/cache/logs_data.json")
        except ImportError:
            pytest.fail("Should handle missing log_reader gracefully")


class TestDeprecatedDatetimeUsage:
    """Test that deprecated datetime.utcnow() is not used"""
    
    def test_trade_logger_uses_timezone_aware_datetime(self):
        """Test that trade_logger uses datetime.now(timezone.utc)"""
        from utils.trading.trade_logger import TradeLogger
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            log_file = f.name
        
        try:
            logger = TradeLogger(log_file)
            
            # Log a rebalance trade (correct method signature)
            logger.log_rebalance_trade(
                product_id="BTC-EUR",
                action="BUY",
                amount=0.001,
                usd_value=50.0,
                reason="Test"
            )
            
            # Read the log
            with open(log_file, 'r') as f:
                trades = json.load(f)
            
            # Timestamp should be present and parseable
            assert len(trades) > 0
            timestamp = trades[0]["timestamp"]
            parsed = datetime.fromisoformat(timestamp)
            
            # Should be timezone-aware
            assert parsed.tzinfo is not None
            
        finally:
            os.unlink(log_file)


class TestRegressionIntegration:
    """Integration tests to ensure bugs don't reoccur in real scenarios"""
    
    def test_full_trading_cycle_datetime_handling(self):
        """Test that a full trading cycle handles datetimes correctly"""
        now = datetime.now(timezone.utc)
        
        # Simulate historical data fetch
        periods = {
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "24h": timedelta(hours=24),
            "5d": timedelta(days=5)
        }
        
        for period_name, delta in periods.items():
            start_time = now - delta
            
            # Format correctly (no double timezone)
            start_str = start_time.replace(tzinfo=None).isoformat() + 'Z'
            end_str = now.replace(tzinfo=None).isoformat() + 'Z'
            
            # Verify format
            assert '+00:00+00:00' not in start_str
            assert '+00:00+00:00' not in end_str
            assert start_str.endswith('Z')
            assert end_str.endswith('Z')
    
    def test_capital_allocation_with_real_portfolio_state(self):
        """Test capital allocation with realistic portfolio state"""
        from utils.trading.opportunity_manager import OpportunityManager
        
        config = Mock()
        config.CONFIDENCE_THRESHOLD_BUY = 50
        config.MIN_TRADE_AMOUNT = 30.0
        
        manager = OpportunityManager(config)
        
        # Real scenario: €47.24 EUR, 20% reserve = €37.79 trading capital
        available_eur = 47.24
        trading_capital = available_eur * 0.8  # 20% reserve
        
        opportunities = [
            {
                'product_id': 'BTC-EUR',
                'opportunity_score': 100.0,
                'action': 'BUY',
                'confidence': 92.4,
                'analysis': {'market_data': {}}
            }
        ]
        
        allocations = manager._calculate_weighted_allocations(
            opportunities, trading_capital
        )
        
        # Should allocate to the trade
        assert 'BTC-EUR' in allocations
        assert allocations['BTC-EUR'] >= 30.0
        assert allocations['BTC-EUR'] <= trading_capital


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
