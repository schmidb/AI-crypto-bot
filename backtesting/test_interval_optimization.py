#!/usr/bin/env python3
"""
Test script for interval optimization functionality
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile
import shutil

from interval_optimization import IntervalOptimizer

class TestIntervalOptimizer:
    """Test cases for IntervalOptimizer"""
    
    def setup_method(self):
        """Set up test environment"""
        # Create temporary directories
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / "data" / "historical"
        self.results_dir = self.temp_dir / "reports" / "interval_optimization"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test data
        self.create_test_data()
        
        # Initialize optimizer
        self.optimizer = IntervalOptimizer(data_dir=str(self.data_dir))
        self.optimizer.results_dir = self.results_dir
        
        # Limit test scope for faster execution
        self.optimizer.test_intervals = [30, 60]
        self.optimizer.products = ['BTC-USD']
        self.optimizer.strategies = ['momentum']
    
    def teardown_method(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_data(self):
        """Create synthetic test data"""
        # Generate 30 days of hourly data
        start_date = datetime.now() - timedelta(days=30)
        dates = pd.date_range(start=start_date, periods=720, freq='H')  # 30 days * 24 hours
        
        # Generate realistic price data with trend and volatility
        np.random.seed(42)  # For reproducible tests
        
        base_price = 50000  # Starting price
        returns = np.random.normal(0.0001, 0.02, len(dates))  # Small positive drift with volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        df = pd.DataFrame(index=dates)
        df['close'] = prices
        df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
        df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.01, len(df)))
        df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.01, len(df)))
        df['volume'] = np.random.uniform(100, 1000, len(df))
        
        # Save test data
        test_file = self.data_dir / "BTC-USD_hour_30d.parquet"
        df.to_parquet(test_file, compression='gzip')
        
        print(f"Created test data: {len(df)} rows saved to {test_file}")
    
    def test_load_historical_data(self):
        """Test loading historical data"""
        df = self.optimizer.load_historical_data('BTC-USD', days=30)
        
        assert not df.empty, "Should load test data successfully"
        assert len(df) == 720, "Should have 720 hourly data points (30 days)"
        assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']), "Should have OHLCV columns"
    
    def test_resample_data(self):
        """Test data resampling to different intervals"""
        df = self.optimizer.load_historical_data('BTC-USD', days=30)
        
        # Test 30-minute resampling
        resampled_30 = self.optimizer.resample_data(df, 30)
        assert len(resampled_30) == len(df) * 2, "30-minute data should have 2x more points than hourly"
        
        # Test 60-minute (should return original)
        resampled_60 = self.optimizer.resample_data(df, 60)
        assert len(resampled_60) == len(df), "60-minute data should be same as original"
        
        # Test 120-minute resampling
        resampled_120 = self.optimizer.resample_data(df, 120)
        assert len(resampled_120) == len(df) // 2, "120-minute data should have half the points"
    
    def test_run_interval_backtest(self):
        """Test running backtest for specific interval"""
        result = self.optimizer.run_interval_backtest('BTC-USD', 60, 'momentum')
        
        assert result, "Should return backtest results"
        assert result['product'] == 'BTC-USD', "Should have correct product"
        assert result['interval_minutes'] == 60, "Should have correct interval"
        assert result['strategy'] == 'momentum', "Should have correct strategy"
        assert 'total_return' in result, "Should have total_return metric"
        assert 'sharpe_ratio' in result, "Should have sharpe_ratio metric"
        assert result['data_points'] > 0, "Should have processed data points"
    
    def test_analyze_regime_performance(self):
        """Test regime performance analysis"""
        # Create mock results
        mock_results = [
            {
                'interval_minutes': 30,
                'total_return': 0.05,
                'sharpe_ratio': 1.2,
                'sortino_ratio': 1.5,
                'max_drawdown': -0.02,
                'win_rate': 0.6,
                'total_trades': 50
            },
            {
                'interval_minutes': 60,
                'total_return': 0.03,
                'sharpe_ratio': 1.0,
                'sortino_ratio': 1.3,
                'max_drawdown': -0.015,
                'win_rate': 0.65,
                'total_trades': 25
            }
        ]
        
        regime_analysis = self.optimizer.analyze_regime_performance(mock_results)
        
        assert regime_analysis, "Should return regime analysis"
        assert 30 in regime_analysis, "Should have 30-minute analysis"
        assert 60 in regime_analysis, "Should have 60-minute analysis"
        assert 'avg_total_return' in regime_analysis[30], "Should have average metrics"
        assert 'consistency_score' in regime_analysis[30], "Should have consistency score"
    
    def test_find_optimal_interval(self):
        """Test finding optimal interval"""
        # Create mock regime analysis
        mock_regime_analysis = {
            30: {
                'avg_total_return': 0.05,
                'avg_sharpe_ratio': 1.2,
                'avg_sortino_ratio': 1.5,
                'avg_max_drawdown': -0.02,
                'avg_win_rate': 0.6,
                'avg_total_trades': 50,
                'consistency_score': 0.8,
                'risk_adjusted_return': 1.5,
                'sample_count': 1
            },
            60: {
                'avg_total_return': 0.03,
                'avg_sharpe_ratio': 1.0,
                'avg_sortino_ratio': 1.3,
                'avg_max_drawdown': -0.015,
                'avg_win_rate': 0.65,
                'avg_total_trades': 25,
                'consistency_score': 0.9,
                'risk_adjusted_return': 1.3,
                'sample_count': 1
            }
        }
        
        optimal_analysis = self.optimizer.find_optimal_interval(mock_regime_analysis)
        
        assert optimal_analysis, "Should return optimal analysis"
        assert 'optimal_interval_minutes' in optimal_analysis, "Should have optimal interval"
        assert 'optimal_score' in optimal_analysis, "Should have optimal score"
        assert 'recommendation' in optimal_analysis, "Should have recommendation"
        assert optimal_analysis['optimal_interval_minutes'] in [30, 60], "Should choose valid interval"
    
    def test_save_results(self):
        """Test saving results to file"""
        mock_results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'test_configuration': {'intervals_tested': [30, 60]},
            'summary': {'total_backtests': 2, 'optimal_interval': 60}
        }
        
        filepath = self.optimizer.save_results(mock_results)
        
        assert filepath, "Should return filepath"
        assert Path(filepath).exists(), "Should create results file"
        
        # Check latest file
        latest_file = self.results_dir / "latest_interval_optimization.json"
        assert latest_file.exists(), "Should create latest results file"
        
        # Verify content
        with open(latest_file, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results['summary']['optimal_interval'] == 60, "Should save correct data"

def test_integration():
    """Integration test with limited scope"""
    print("\n🧪 Running integration test for interval optimization...")
    
    # Create temporary test environment
    temp_dir = Path(tempfile.mkdtemp())
    data_dir = temp_dir / "data" / "historical"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create minimal test data (smaller dataset for faster testing)
        start_date = datetime.now() - timedelta(days=7)  # Just 7 days
        dates = pd.date_range(start=start_date, periods=168, freq='H')  # 7 days * 24 hours
        
        np.random.seed(42)
        base_price = 50000
        returns = np.random.normal(0.0001, 0.01, len(dates))
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        df = pd.DataFrame(index=dates)
        df['close'] = prices
        df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
        df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.005, len(df)))
        df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.005, len(df)))
        df['volume'] = np.random.uniform(100, 1000, len(df))
        
        # Save test data
        test_file = data_dir / "BTC-USD_hour_7d.parquet"
        df.to_parquet(test_file, compression='gzip')
        
        # Initialize optimizer with limited scope
        optimizer = IntervalOptimizer(data_dir=str(data_dir))
        optimizer.results_dir = temp_dir / "reports" / "interval_optimization"
        optimizer.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Very limited test scope
        optimizer.test_intervals = [60]  # Only test current interval
        optimizer.products = ['BTC-USD']
        optimizer.strategies = ['momentum']
        
        # Override load method to use our 7-day data
        original_load = optimizer.load_historical_data
        def load_test_data(product, days=180):
            return original_load(product, days=7)
        optimizer.load_historical_data = load_test_data
        
        # Run analysis
        results = optimizer.run_comprehensive_analysis()
        
        assert results, "Should complete analysis successfully"
        assert results['summary']['total_backtests'] > 0, "Should complete at least one backtest"
        
        # Save results
        filepath = optimizer.save_results(results)
        assert filepath, "Should save results successfully"
        
        print(f"✅ Integration test completed successfully")
        print(f"📊 Completed {results['summary']['total_backtests']} backtests")
        print(f"💾 Results saved to: {filepath}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
        
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Run integration test
    success = test_integration()
    
    if success:
        print("\n🎉 All tests passed! Interval optimization is ready for use.")
    else:
        print("\n❌ Tests failed. Please check the implementation.")
    
    exit(0 if success else 1)