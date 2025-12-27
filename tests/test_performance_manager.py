"""
Tests for PerformanceManager class

This module tests the advanced performance management functionality including:
- Performance reset with confirmation
- Performance periods management
- Performance goals and tracking
- Benchmark comparisons
- Data export/import capabilities
- Advanced analytics and reporting
"""

import pytest
import json
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from utils.performance.performance_manager import PerformanceManager


class TestPerformanceManager:
    """Test suite for PerformanceManager class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def performance_manager(self, temp_dir):
        """Create PerformanceManager instance for testing"""
        return PerformanceManager(performance_path=temp_dir)
    
    @pytest.fixture
    def sample_metrics(self):
        """Sample performance metrics for testing"""
        return {
            "periods": {
                "7d": {
                    "total_return": 15.5,
                    "annualized_return": 45.2,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": 8.3,
                    "volatility": 22.1,
                    "sortino_ratio": 2.1
                },
                "30d": {
                    "total_return": 12.3,
                    "annualized_return": 38.7,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": 12.1,
                    "volatility": 25.4,
                    "sortino_ratio": 1.8
                }
            }
        }
    
    # ===== INITIALIZATION TESTS =====
    
    def test_initialization(self, temp_dir):
        """Test PerformanceManager initialization"""
        manager = PerformanceManager(performance_path=temp_dir)
        
        assert manager.performance_path == Path(temp_dir)
        assert manager.tracker is not None
        assert manager.calculator is not None
        
        # Check that required files are created
        assert manager.periods_file.exists()
        assert manager.goals_file.exists()
        assert manager.benchmarks_file.exists()
    
    def test_default_files_creation(self, performance_manager):
        """Test that default configuration files are created correctly"""
        # Check periods file
        with open(performance_manager.periods_file, 'r') as f:
            periods_data = json.load(f)
        
        assert "periods" in periods_data
        assert "active_period" in periods_data
        assert "created_date" in periods_data
        assert periods_data["periods"] == []
        assert periods_data["active_period"] is None
        
        # Check goals file
        with open(performance_manager.goals_file, 'r') as f:
            goals_data = json.load(f)
        
        assert "goals" in goals_data
        assert "active_goals" in goals_data
        assert "created_date" in goals_data
        
        # Check benchmarks file
        with open(performance_manager.benchmarks_file, 'r') as f:
            benchmarks_data = json.load(f)
        
        assert "benchmarks" in benchmarks_data
        assert "btc_eur" in benchmarks_data["benchmarks"]
        assert "eth_eur" in benchmarks_data["benchmarks"]
        assert benchmarks_data["benchmarks"]["btc_eur"]["enabled"] is True
    
    # ===== PERFORMANCE RESET TESTS =====
    
    def test_reset_performance_confirmation_required(self, performance_manager):
        """Test that performance reset requires confirmation"""
        result = performance_manager.reset_performance_with_confirmation()
        
        assert result["status"] == "confirmation_required"
        assert "confirmation_code" in result
        assert len(result["confirmation_code"]) == 8
        assert "warning" in result
        assert "permanently delete" in result["warning"].lower()
    
    @patch('utils.performance.performance_manager.PerformanceTracker')
    def test_reset_performance_with_confirmation(self, mock_tracker_class, performance_manager):
        """Test performance reset with valid confirmation code"""
        # Mock the tracker reset method
        mock_tracker = Mock()
        mock_tracker.reset_performance.return_value = {
            "backup_created": True,
            "backup_file": "backup_20240617.json"
        }
        performance_manager.tracker = mock_tracker
        
        # First get confirmation code
        result1 = performance_manager.reset_performance_with_confirmation()
        confirmation_code = result1["confirmation_code"]
        
        # Then perform reset with confirmation
        result2 = performance_manager.reset_performance_with_confirmation(confirmation_code)
        
        assert result2["status"] == "success"
        assert "reset_date" in result2
        assert result2["backup_created"] is True
        mock_tracker.reset_performance.assert_called_once()
        
        # Check that reset history is saved
        reset_history_file = performance_manager.performance_path / "reset_history.json"
        assert reset_history_file.exists()
        
        with open(reset_history_file, 'r') as f:
            reset_history = json.load(f)
        
        assert len(reset_history) == 1
        assert reset_history[0]["confirmation_code"] == confirmation_code
    
    @patch('utils.performance.performance_manager.PerformanceTracker')
    def test_reset_performance_error_handling(self, mock_tracker_class, performance_manager):
        """Test error handling during performance reset"""
        # Mock the tracker to raise an exception
        mock_tracker = Mock()
        mock_tracker.reset_performance.side_effect = Exception("Reset failed")
        performance_manager.tracker = mock_tracker
        
        result = performance_manager.reset_performance_with_confirmation("TEST1234")
        
        assert result["status"] == "error"
        assert "failed to reset" in result["message"].lower()
    
    # ===== PERFORMANCE PERIODS TESTS =====
    
    def test_create_performance_period(self, performance_manager):
        """Test creating a new performance period"""
        result = performance_manager.create_performance_period(
            name="Q1 2024",
            description="First quarter performance tracking"
        )
        
        assert result["status"] == "success"
        assert "period_id" in result
        
        # Verify period was saved
        periods_data = performance_manager.get_performance_periods()
        assert len(periods_data["periods"]) == 1
        
        period = periods_data["periods"][0]
        assert period["name"] == "Q1 2024"
        assert period["description"] == "First quarter performance tracking"
        assert period["status"] == "active"
        assert periods_data["active_period"] == period["id"]
    
    def test_create_performance_period_with_dates(self, performance_manager):
        """Test creating performance period with specific dates"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31)
        
        result = performance_manager.create_performance_period(
            name="Q1 2024",
            start_date=start_date,
            end_date=end_date
        )
        
        assert result["status"] == "success"
        
        periods_data = performance_manager.get_performance_periods()
        period = periods_data["periods"][0]
        
        assert period["start_date"] == start_date.isoformat()
        assert period["end_date"] == end_date.isoformat()
        assert period["status"] == "planned"
    
    def test_set_active_period(self, performance_manager):
        """Test setting active performance period"""
        # Create two periods
        result1 = performance_manager.create_performance_period("Period 1")
        result2 = performance_manager.create_performance_period("Period 2")
        
        period1_id = result1["period_id"]
        period2_id = result2["period_id"]
        
        # Set first period as active
        result = performance_manager.set_active_period(period1_id)
        
        assert result["status"] == "success"
        
        periods_data = performance_manager.get_performance_periods()
        assert periods_data["active_period"] == period1_id
    
    def test_set_active_period_invalid_id(self, performance_manager):
        """Test setting active period with invalid ID"""
        result = performance_manager.set_active_period("invalid_id")
        
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
    
    # ===== PERFORMANCE GOALS TESTS =====
    
    def test_set_performance_goal(self, performance_manager):
        """Test setting a performance goal"""
        result = performance_manager.set_performance_goal(
            goal_type="total_return",
            target_value=20.0,
            timeframe="monthly",
            description="Target 20% monthly return"
        )
        
        assert result["status"] == "success"
        assert "goal_id" in result
        
        # Verify goal was saved
        with open(performance_manager.goals_file, 'r') as f:
            goals_data = json.load(f)
        
        assert len(goals_data["goals"]) == 1
        assert len(goals_data["active_goals"]) == 1
        
        goal = goals_data["goals"][0]
        assert goal["type"] == "total_return"
        assert goal["target_value"] == 20.0
        assert goal["timeframe"] == "monthly"
        assert goal["status"] == "active"
    
    def test_check_performance_goals_achieved(self, performance_manager, sample_metrics):
        """Test checking performance goals - achieved"""
        # Set a goal that should be achieved
        performance_manager.set_performance_goal(
            goal_type="total_return",
            target_value=10.0,
            timeframe="weekly"
        )
        
        # Check goals with metrics that exceed the target
        result = performance_manager.check_performance_goals(sample_metrics["periods"]["7d"])
        
        assert result["status"] == "success"
        assert result["goals_achieved"] == 1
        assert len(result["goal_results"]) == 1
        
        goal_result = result["goal_results"][0]
        assert goal_result["achieved"] is True
        assert goal_result["current"] == 15.5  # From sample metrics
        assert goal_result["target"] == 10.0
        assert goal_result["progress"] == 100.0  # Should be capped at 100%
    
    def test_check_performance_goals_not_achieved(self, performance_manager, sample_metrics):
        """Test checking performance goals - not achieved"""
        # Set a goal that should not be achieved
        performance_manager.set_performance_goal(
            goal_type="total_return",
            target_value=25.0,
            timeframe="weekly"
        )
        
        result = performance_manager.check_performance_goals(sample_metrics["periods"]["7d"])
        
        assert result["status"] == "success"
        assert result["goals_achieved"] == 0
        
        goal_result = result["goal_results"][0]
        assert goal_result["achieved"] is False
        assert goal_result["progress"] < 100.0
    
    def test_check_performance_goals_drawdown_type(self, performance_manager, sample_metrics):
        """Test checking performance goals for drawdown (lower is better)"""
        # Set a max drawdown goal
        performance_manager.set_performance_goal(
            goal_type="max_drawdown",
            target_value=10.0,
            timeframe="weekly"
        )
        
        result = performance_manager.check_performance_goals(sample_metrics["periods"]["7d"])
        
        goal_result = result["goal_results"][0]
        assert goal_result["achieved"] is True  # 8.3 <= 10.0
        assert goal_result["current"] == 8.3
        assert goal_result["target"] == 10.0
    
    # ===== BENCHMARK COMPARISON TESTS =====
    
    def test_add_benchmark(self, performance_manager):
        """Test adding a new benchmark"""
        result = performance_manager.add_benchmark(
            benchmark_id="sp500",
            name="S&P 500 Index",
            enabled=True
        )
        
        assert result["status"] == "success"
        
        # Verify benchmark was added
        with open(performance_manager.benchmarks_file, 'r') as f:
            benchmarks_data = json.load(f)
        
        assert "sp500" in benchmarks_data["benchmarks"]
        assert benchmarks_data["benchmarks"]["sp500"]["name"] == "S&P 500 Index"
        assert benchmarks_data["benchmarks"]["sp500"]["enabled"] is True
    
    def test_compare_to_benchmarks(self, performance_manager, sample_metrics):
        """Test comparing portfolio performance to benchmarks"""
        result = performance_manager.compare_to_benchmarks(sample_metrics["periods"]["7d"])
        
        assert result["status"] == "success"
        assert "comparisons" in result
        assert result["benchmarks_compared"] >= 2  # At least BTC and ETH
        
        # Check comparison structure
        comparison = result["comparisons"][0]
        assert "benchmark_id" in comparison
        assert "benchmark_name" in comparison
        assert "benchmark_return" in comparison
        assert "portfolio_return" in comparison
        assert "outperformance" in comparison
        assert "outperforming" in comparison
    
    # ===== DATA EXPORT TESTS =====
    
    @patch('utils.performance.performance_manager.PerformanceTracker')
    def test_export_performance_data_json(self, mock_tracker_class, performance_manager):
        """Test exporting performance data as JSON"""
        # Mock tracker methods
        mock_tracker = Mock()
        mock_tracker.get_portfolio_snapshots.return_value = {
            "snapshots": [
                {"timestamp": "2024-06-17T10:00:00", "total_value": 1000.0, "holdings": {"BTC": 0.5}}
            ]
        }
        mock_tracker.get_performance_metrics.return_value = {"periods": {"7d": {"total_return": 10.0}}}
        performance_manager.tracker = mock_tracker
        
        result = performance_manager.export_performance_data(format_type="json")
        
        assert result["status"] == "success"
        assert result["format"] == "json"
        assert "export_file" in result
        
        # Verify export file exists and contains data
        export_file = Path(result["export_file"])
        assert export_file.exists()
        
        with open(export_file, 'r') as f:
            export_data = json.load(f)
        
        assert "export_date" in export_data
        assert "portfolio_snapshots" in export_data
        assert "performance_metrics" in export_data
        assert "performance_periods" in export_data
    
    @patch('utils.performance.performance_manager.PerformanceTracker')
    def test_export_performance_data_csv(self, mock_tracker_class, performance_manager):
        """Test exporting performance data as CSV"""
        # Mock tracker methods
        mock_tracker = Mock()
        mock_tracker.get_portfolio_snapshots.return_value = {
            "snapshots": [
                {"timestamp": "2024-06-17T10:00:00", "total_value": 1000.0, "holdings": {"BTC": 0.5, "ETH": 2.0}}
            ]
        }
        mock_tracker.get_performance_metrics.return_value = {
            "periods": {
                "7d": {"total_return": 10.0, "sharpe_ratio": 1.5, "max_drawdown": 5.0}
            }
        }
        performance_manager.tracker = mock_tracker
        
        result = performance_manager.export_performance_data(format_type="csv")
        
        assert result["status"] == "success"
        assert result["format"] == "csv"
        assert "exported_files" in result
        assert len(result["exported_files"]) >= 1
    
    def test_export_performance_data_invalid_format(self, performance_manager):
        """Test exporting with invalid format"""
        result = performance_manager.export_performance_data(format_type="xml")
        
        assert result["status"] == "error"
        assert "unsupported export format" in result["message"].lower()
    
    # ===== ADVANCED ANALYTICS TESTS =====
    
    @patch('utils.performance.performance_manager.PerformanceTracker')
    def test_generate_performance_report(self, mock_tracker_class, performance_manager, sample_metrics):
        """Test generating comprehensive performance report"""
        # Mock tracker methods
        mock_tracker = Mock()
        mock_tracker.get_performance_metrics.return_value = sample_metrics
        mock_tracker.get_portfolio_snapshots.return_value = {"snapshots": []}
        performance_manager.tracker = mock_tracker
        
        # Add a goal for testing
        performance_manager.set_performance_goal("total_return", 10.0, "weekly")
        
        result = performance_manager.generate_performance_report(period="7d")
        
        assert result["status"] == "success"
        assert "report" in result
        assert "report_file" in result
        
        report = result["report"]
        assert "report_date" in report
        assert "period" in report
        assert "performance_metrics" in report
        assert "goals_status" in report
        assert "benchmark_comparison" in report
        assert "insights" in report
        assert "summary" in report
        
        # Verify report file was created
        report_file = Path(result["report_file"])
        assert report_file.exists()
    
    def test_generate_performance_insights(self, performance_manager, sample_metrics):
        """Test generating performance insights"""
        insights = performance_manager._generate_performance_insights(sample_metrics, "7d")
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # Check that insights contain relevant information
        insights_text = " ".join(insights).lower()
        assert "return" in insights_text
        assert "sharpe" in insights_text or "risk" in insights_text
    
    def test_calculate_performance_grade(self, performance_manager):
        """Test performance grade calculation"""
        # Test excellent performance
        excellent_data = {
            "total_return": 25.0,
            "sharpe_ratio": 2.5,
            "max_drawdown": 3.0,
            "volatility": 8.0
        }
        grade = performance_manager._calculate_performance_grade(excellent_data)
        assert grade in ["A+", "A", "A-"]
        
        # Test poor performance
        poor_data = {
            "total_return": -10.0,
            "sharpe_ratio": -0.5,
            "max_drawdown": 40.0,
            "volatility": 60.0
        }
        grade = performance_manager._calculate_performance_grade(poor_data)
        assert grade in ["D", "F"]
        
        # Test empty data
        grade = performance_manager._calculate_performance_grade({})
        assert grade == "N/A"
    
    # ===== GOAL PROGRESS CALCULATION TESTS =====
    
    def test_calculate_goal_progress_higher_better(self, performance_manager):
        """Test goal progress calculation for metrics where higher is better"""
        # Test return goal
        progress = performance_manager._calculate_goal_progress("total_return", 15.0, 10.0)
        assert progress == 100.0  # Achieved and exceeded
        
        progress = performance_manager._calculate_goal_progress("total_return", 5.0, 10.0)
        assert progress == 50.0  # Half way there
        
        progress = performance_manager._calculate_goal_progress("total_return", 0.0, 10.0)
        assert progress == 0.0  # No progress
    
    def test_calculate_goal_progress_lower_better(self, performance_manager):
        """Test goal progress calculation for metrics where lower is better"""
        # Test drawdown goal (lower is better)
        progress = performance_manager._calculate_goal_progress("max_drawdown", 5.0, 10.0)
        assert progress == 100.0  # Achieved (5 <= 10)
        
        progress = performance_manager._calculate_goal_progress("max_drawdown", 15.0, 10.0)
        assert progress == 50.0  # 50% worse than target
        
        progress = performance_manager._calculate_goal_progress("max_drawdown", 20.0, 10.0)
        assert progress == 0.0  # Much worse than target
    
    def test_calculate_goal_progress_zero_target(self, performance_manager):
        """Test goal progress calculation with zero target"""
        progress = performance_manager._calculate_goal_progress("total_return", 5.0, 0.0)
        assert progress == 100.0  # Any positive value achieves zero target
        
        progress = performance_manager._calculate_goal_progress("total_return", -5.0, 0.0)
        assert progress == 0.0  # Negative value doesn't achieve zero target
    
    # ===== ERROR HANDLING TESTS =====
    
    def test_error_handling_file_operations(self, performance_manager):
        """Test error handling for file operations"""
        # Remove a required file to trigger error
        os.remove(performance_manager.goals_file)
        
        # This should handle the missing file gracefully
        result = performance_manager.check_performance_goals({"total_return": 10.0})
        
        # Should return error status but not crash
        assert result["status"] == "error"
    
    @patch('utils.performance.performance_manager.json.dump')
    def test_error_handling_json_operations(self, mock_json_dump, performance_manager):
        """Test error handling for JSON operations"""
        # Mock json.dump to raise an exception
        mock_json_dump.side_effect = Exception("JSON write failed")
        
        result = performance_manager.set_performance_goal("total_return", 10.0, "weekly")
        
        assert result["status"] == "error"
        assert "failed to set performance goal" in result["message"].lower()
    
    # ===== INTEGRATION TESTS =====
    
    def test_full_workflow_integration(self, performance_manager, sample_metrics):
        """Test complete workflow integration"""
        # 1. Create performance period
        period_result = performance_manager.create_performance_period("Test Period")
        assert period_result["status"] == "success"
        
        # 2. Set performance goals
        goal_result = performance_manager.set_performance_goal("total_return", 15.0, "weekly")
        assert goal_result["status"] == "success"
        
        # 3. Add custom benchmark
        benchmark_result = performance_manager.add_benchmark("custom", "Custom Benchmark")
        assert benchmark_result["status"] == "success"
        
        # 4. Check goals
        goals_check = performance_manager.check_performance_goals(sample_metrics["periods"]["7d"])
        assert goals_check["status"] == "success"
        
        # 5. Compare to benchmarks
        benchmark_comparison = performance_manager.compare_to_benchmarks(sample_metrics["periods"]["7d"])
        assert benchmark_comparison["status"] == "success"
        
        # 6. Export data
        with patch('utils.performance.performance_manager.PerformanceTracker') as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker.get_portfolio_snapshots.return_value = {"snapshots": []}
            mock_tracker.get_performance_metrics.return_value = sample_metrics
            performance_manager.tracker = mock_tracker
            
            export_result = performance_manager.export_performance_data("json")
            assert export_result["status"] == "success"
        
        # 7. Generate report
        with patch('utils.performance.performance_manager.PerformanceTracker') as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker.get_portfolio_snapshots.return_value = {"snapshots": []}
            mock_tracker.get_performance_metrics.return_value = sample_metrics
            performance_manager.tracker = mock_tracker
            
            report_result = performance_manager.generate_performance_report("7d")
            assert report_result["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__])
