"""
Tests for HybridPerformanceTracker
Tests decision recording, outcome tracking, and accuracy calculation
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from strategies.performance_tracker import HybridPerformanceTracker, DecisionRecord, StrategyPerformance


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_data_collector():
    """Mock data collector for price fetching"""
    collector = Mock()
    collector.get_current_price = Mock(return_value=50000.0)
    return collector


@pytest.fixture
def tracker(temp_data_dir):
    """Create tracker instance with temp directory"""
    return HybridPerformanceTracker(data_dir=temp_data_dir)


class TestHybridPerformanceTrackerInitialization:
    """Test tracker initialization"""
    
    def test_initialization_creates_directory(self, temp_data_dir):
        """Test that initialization creates data directory"""
        data_dir = os.path.join(temp_data_dir, "new_dir")
        tracker = HybridPerformanceTracker(data_dir=data_dir)
        
        assert os.path.exists(data_dir)
        # Files are created on first save, not on initialization
        assert tracker.performance_file == os.path.join(data_dir, "strategy_performance.json")
        assert tracker.decisions_file == os.path.join(data_dir, "decision_records.json")
    
    def test_initialization_loads_existing_data(self, temp_data_dir):
        """Test that initialization loads existing data"""
        # Create existing data
        performance_file = os.path.join(temp_data_dir, "strategy_performance.json")
        decisions_file = os.path.join(temp_data_dir, "decision_records.json")
        
        existing_performance = {
            "test_strategy": {
                "strategy_name": "test_strategy",
                "total_decisions": 10,
                "correct_decisions": 7,
                "buy_decisions": 5,
                "sell_decisions": 3,
                "hold_decisions": 2,
                "avg_confidence": 75.0,
                "accuracy_rate": 0.7,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        with open(performance_file, 'w') as f:
            json.dump(existing_performance, f)
        
        existing_decisions = [
            {
                "timestamp": datetime.now().isoformat(),
                "product_id": "BTC-EUR",
                "strategy_name": "test_strategy",
                "action": "BUY",
                "confidence": 75.0,
                "price_at_decision": 50000.0,
                "price_after_1h": None,
                "price_after_4h": None,
                "price_after_24h": None,
                "was_correct": None,
                "profit_loss_1h": None,
                "profit_loss_4h": None,
                "profit_loss_24h": None
            }
        ]
        
        with open(decisions_file, 'w') as f:
            json.dump(existing_decisions, f)
        
        # Initialize tracker
        tracker = HybridPerformanceTracker(data_dir=temp_data_dir)
        
        assert len(tracker.strategy_performance) == 1
        assert "test_strategy" in tracker.strategy_performance
        assert tracker.strategy_performance["test_strategy"].total_decisions == 10
        assert len(tracker.decision_records) == 1


class TestDecisionRecording:
    """Test decision recording functionality"""
    
    def test_record_decision_with_dict_signals(self, tracker):
        """Test recording decision with dictionary format signals"""
        strategy_signals = {
            "momentum": {"action": "BUY", "confidence": 75.0},
            "trend_following": {"action": "HOLD", "confidence": 60.0}
        }
        
        final_decision = {"action": "BUY", "confidence": 70.0}
        
        tracker.record_decision(
            product_id="BTC-EUR",
            strategy_signals=strategy_signals,
            final_decision=final_decision,
            current_price=50000.0
        )
        
        # Should have 3 records: 2 strategies + 1 combined
        assert len(tracker.decision_records) == 3
        
        # Check individual strategy records
        momentum_record = [r for r in tracker.decision_records if r.strategy_name == "momentum"][0]
        assert momentum_record.action == "BUY"
        assert momentum_record.confidence == 75.0
        assert momentum_record.price_at_decision == 50000.0
        
        # Check combined record
        combined_record = [r for r in tracker.decision_records if r.strategy_name == "combined_hybrid"][0]
        assert combined_record.action == "BUY"
        assert combined_record.confidence == 70.0
    
    def test_record_decision_updates_strategy_performance(self, tracker):
        """Test that recording updates strategy performance stats"""
        strategy_signals = {
            "momentum": {"action": "BUY", "confidence": 75.0}
        }
        
        final_decision = {"action": "BUY", "confidence": 70.0}
        
        tracker.record_decision(
            product_id="BTC-EUR",
            strategy_signals=strategy_signals,
            final_decision=final_decision,
            current_price=50000.0
        )
        
        assert "momentum" in tracker.strategy_performance
        perf = tracker.strategy_performance["momentum"]
        assert perf.total_decisions == 1
        assert perf.buy_decisions == 1
        assert perf.avg_confidence == 75.0


class TestOutcomeTracking:
    """Test outcome tracking and accuracy calculation"""
    
    def test_update_outcomes_1h(self, tracker, mock_data_collector):
        """Test updating 1h outcomes"""
        # Create decision from 2 hours ago
        decision_time = datetime.now() - timedelta(hours=2)
        record = DecisionRecord(
            timestamp=decision_time.isoformat(),
            product_id="BTC-EUR",
            strategy_name="test_strategy",
            action="BUY",
            confidence=75.0,
            price_at_decision=50000.0
        )
        tracker.decision_records.append(record)
        
        # Mock current price higher (profitable BUY)
        mock_data_collector.get_current_price.return_value = 51000.0
        
        # Update outcomes
        tracker.update_decision_outcomes(data_collector=mock_data_collector)
        
        # Check 1h outcome updated
        assert record.price_after_1h == 51000.0
        assert record.profit_loss_1h == pytest.approx(2.0, rel=0.01)  # 2% profit
    
    def test_update_outcomes_24h_buy_correct(self, tracker, mock_data_collector):
        """Test 24h outcome for correct BUY decision"""
        # Create decision from 25 hours ago
        decision_time = datetime.now() - timedelta(hours=25)
        record = DecisionRecord(
            timestamp=decision_time.isoformat(),
            product_id="BTC-EUR",
            strategy_name="test_strategy",
            action="BUY",
            confidence=75.0,
            price_at_decision=50000.0
        )
        tracker.decision_records.append(record)
        
        # Mock current price higher (profitable BUY)
        mock_data_collector.get_current_price.return_value = 52000.0
        
        # Update outcomes
        tracker.update_decision_outcomes(data_collector=mock_data_collector)
        
        # Check 24h outcome and correctness
        assert record.price_after_24h == 52000.0
        assert record.profit_loss_24h == pytest.approx(4.0, rel=0.01)  # 4% profit
        assert record.was_correct is True  # BUY was correct (price went up)
    
    def test_update_outcomes_24h_buy_incorrect(self, tracker, mock_data_collector):
        """Test 24h outcome for incorrect BUY decision"""
        # Create decision from 25 hours ago
        decision_time = datetime.now() - timedelta(hours=25)
        record = DecisionRecord(
            timestamp=decision_time.isoformat(),
            product_id="BTC-EUR",
            strategy_name="test_strategy",
            action="BUY",
            confidence=75.0,
            price_at_decision=50000.0
        )
        tracker.decision_records.append(record)
        
        # Mock current price lower (unprofitable BUY)
        mock_data_collector.get_current_price.return_value = 48000.0
        
        # Update outcomes
        tracker.update_decision_outcomes(data_collector=mock_data_collector)
        
        # Check correctness
        assert record.was_correct is False  # BUY was incorrect (price went down)
    
    def test_update_outcomes_24h_sell_correct(self, tracker, mock_data_collector):
        """Test 24h outcome for correct SELL decision"""
        decision_time = datetime.now() - timedelta(hours=25)
        record = DecisionRecord(
            timestamp=decision_time.isoformat(),
            product_id="BTC-EUR",
            strategy_name="test_strategy",
            action="SELL",
            confidence=75.0,
            price_at_decision=50000.0
        )
        tracker.decision_records.append(record)
        
        # Mock current price lower (good SELL)
        mock_data_collector.get_current_price.return_value = 48000.0
        
        # Update outcomes
        tracker.update_decision_outcomes(data_collector=mock_data_collector)
        
        # Check correctness
        assert record.was_correct is True  # SELL was correct (price went down)
    
    def test_update_outcomes_24h_hold_correct(self, tracker, mock_data_collector):
        """Test 24h outcome for correct HOLD decision"""
        decision_time = datetime.now() - timedelta(hours=25)
        record = DecisionRecord(
            timestamp=decision_time.isoformat(),
            product_id="BTC-EUR",
            strategy_name="test_strategy",
            action="HOLD",
            confidence=75.0,
            price_at_decision=50000.0
        )
        tracker.decision_records.append(record)
        
        # Mock current price stable (within 2%)
        mock_data_collector.get_current_price.return_value = 50500.0  # 1% change
        
        # Update outcomes
        tracker.update_decision_outcomes(data_collector=mock_data_collector)
        
        # Check correctness
        assert record.was_correct is True  # HOLD was correct (price stable)
    
    def test_update_outcomes_skips_already_evaluated(self, tracker, mock_data_collector):
        """Test that already evaluated decisions are skipped"""
        decision_time = datetime.now() - timedelta(hours=25)
        record = DecisionRecord(
            timestamp=decision_time.isoformat(),
            product_id="BTC-EUR",
            strategy_name="test_strategy",
            action="BUY",
            confidence=75.0,
            price_at_decision=50000.0,
            was_correct=True  # Already evaluated
        )
        tracker.decision_records.append(record)
        
        # Update outcomes
        tracker.update_decision_outcomes(data_collector=mock_data_collector)
        
        # Should not call API for already evaluated decisions
        mock_data_collector.get_current_price.assert_not_called()


class TestAccuracyCalculation:
    """Test accuracy rate calculation"""
    
    def test_recalculate_accuracy_rates(self, tracker):
        """Test accuracy rate recalculation"""
        # Add some evaluated decisions
        for i in range(10):
            record = DecisionRecord(
                timestamp=datetime.now().isoformat(),
                product_id="BTC-EUR",
                strategy_name="test_strategy",
                action="BUY",
                confidence=75.0,
                price_at_decision=50000.0,
                was_correct=(i < 7)  # 7 correct, 3 incorrect
            )
            tracker.decision_records.append(record)
        
        # Initialize strategy performance
        tracker.strategy_performance["test_strategy"] = StrategyPerformance(
            strategy_name="test_strategy",
            total_decisions=10
        )
        
        # Recalculate
        tracker._recalculate_accuracy_rates()
        
        # Check accuracy
        perf = tracker.strategy_performance["test_strategy"]
        assert perf.accuracy_rate == 0.7  # 70% accuracy
        assert perf.correct_decisions == 7


class TestPerformanceSummary:
    """Test performance summary generation"""
    
    def test_get_performance_summary(self, tracker):
        """Test performance summary generation"""
        # Add some data
        tracker.strategy_performance["momentum"] = StrategyPerformance(
            strategy_name="momentum",
            total_decisions=100,
            correct_decisions=60,
            accuracy_rate=0.6,
            avg_confidence=70.0
        )
        
        summary = tracker.get_performance_summary()
        
        assert summary["total_decisions"] == 0  # No decision records yet
        assert "momentum" in summary["strategies"]
        assert summary["strategies"]["momentum"]["accuracy_rate"] == 0.6


class TestDataPersistence:
    """Test data saving and loading"""
    
    def test_save_and_load_decision_records(self, temp_data_dir):
        """Test saving and loading decision records"""
        tracker1 = HybridPerformanceTracker(data_dir=temp_data_dir)
        
        # Add decision
        record = DecisionRecord(
            timestamp=datetime.now().isoformat(),
            product_id="BTC-EUR",
            strategy_name="test_strategy",
            action="BUY",
            confidence=75.0,
            price_at_decision=50000.0
        )
        tracker1.decision_records.append(record)
        tracker1._save_decision_records()
        
        # Load in new tracker
        tracker2 = HybridPerformanceTracker(data_dir=temp_data_dir)
        
        assert len(tracker2.decision_records) == 1
        assert tracker2.decision_records[0].action == "BUY"
    
    def test_save_and_load_performance_data(self, temp_data_dir):
        """Test saving and loading performance data"""
        tracker1 = HybridPerformanceTracker(data_dir=temp_data_dir)
        
        # Add performance data
        tracker1.strategy_performance["test_strategy"] = StrategyPerformance(
            strategy_name="test_strategy",
            total_decisions=100,
            correct_decisions=70,
            accuracy_rate=0.7
        )
        tracker1._save_performance_data()
        
        # Load in new tracker
        tracker2 = HybridPerformanceTracker(data_dir=temp_data_dir)
        
        assert "test_strategy" in tracker2.strategy_performance
        assert tracker2.strategy_performance["test_strategy"].accuracy_rate == 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
