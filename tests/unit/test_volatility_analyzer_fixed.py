"""
Unit tests for VolatilityAnalyzer - Phase 3 component
"""

import pytest
import os
import numpy as np
import tempfile
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

from utils.performance.volatility_analyzer import VolatilityAnalyzer


class TestVolatilityAnalyzerInitialization:
    """Test VolatilityAnalyzer initialization."""
    
    def test_volatility_analyzer_initialization_default(self):
        """Test VolatilityAnalyzer initializes with default data directory."""
        with patch('os.makedirs'):
            analyzer = VolatilityAnalyzer()
            
            assert hasattr(analyzer, 'logger')
            assert hasattr(analyzer, 'data_dir')
            assert analyzer.data_dir == "data/volatility"
    
    def test_volatility_analyzer_initialization_custom_dir(self):
        """Test VolatilityAnalyzer initializes with custom data directory."""
        custom_dir = "custom/volatility/path"
        
        with patch('os.makedirs'):
            analyzer = VolatilityAnalyzer(custom_dir)
            
            assert analyzer.data_dir == custom_dir


class TestVolatilityAnalysis:
    """Test main volatility analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('os.makedirs'):
            self.analyzer = VolatilityAnalyzer()
        
        # Create sample price data
        np.random.seed(42)  # For reproducible tests
        base_price = 45000
        returns = np.random.normal(0, 0.02, 100)  # 2% volatility
        self.sample_prices = [base_price]
        
        for ret in returns[1:]:
            self.sample_prices.append(self.sample_prices[-1] * (1 + ret))
        
        self.sample_time_periods = {
            '1h': 1.5,
            '24h': -2.3,
            '7d': 5.2
        }
    
    def test_analyze_volatility_basic(self):
        """Test basic volatility analysis."""
        result = self.analyzer.analyze_volatility(
            'BTC-EUR', 
            self.sample_prices, 
            self.sample_time_periods
        )
        
        assert isinstance(result, dict)
        assert 'product_id' in result
        assert 'timestamp' in result
        assert 'metrics' in result
        assert 'regime' in result
        assert 'strategy_adjustments' in result
        
        assert result['product_id'] == 'BTC-EUR'
        assert isinstance(result['metrics'], dict)
        assert isinstance(result['regime'], dict)
        assert isinstance(result['strategy_adjustments'], dict)
    
    def test_analyze_volatility_high_volatility(self):
        """Test analysis with high volatility data."""
        # Create high volatility price data
        high_vol_returns = np.random.normal(0, 0.08, 50)  # 8% volatility
        high_vol_prices = [45000]
        
        for ret in high_vol_returns[1:]:
            high_vol_prices.append(high_vol_prices[-1] * (1 + ret))
        
        result = self.analyzer.analyze_volatility(
            'BTC-EUR', 
            high_vol_prices, 
            {'1h': 8.5, '24h': -12.3}
        )
        
        # Should detect high volatility
        assert result['regime']['category'] in ['high', 'medium']
        assert result['regime']['score'] > 0.4
    
    def test_analyze_volatility_low_volatility(self):
        """Test analysis with low volatility data."""
        # Create low volatility price data
        low_vol_returns = np.random.normal(0, 0.005, 50)  # 0.5% volatility
        low_vol_prices = [45000]
        
        for ret in low_vol_returns[1:]:
            low_vol_prices.append(low_vol_prices[-1] * (1 + ret))
        
        result = self.analyzer.analyze_volatility(
            'BTC-EUR', 
            low_vol_prices, 
            {'1h': 0.2, '24h': -0.5}
        )
        
        # Should detect low volatility
        assert result['regime']['category'] in ['low', 'medium']
        assert result['regime']['score'] < 0.8


class TestVolatilityMetrics:
    """Test volatility metrics calculation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('os.makedirs'):
            self.analyzer = VolatilityAnalyzer()
    
    def test_calculate_volatility_metrics_basic(self):
        """Test basic volatility metrics calculation."""
        prices = [100, 102, 98, 105, 103, 99, 101]
        time_periods = {'1h': 1.0, '24h': -2.0}
        
        metrics = self.analyzer._calculate_volatility_metrics(prices, time_periods)
        
        assert isinstance(metrics, dict)
        assert 'basic_volatility' in metrics
        assert 'annualized_volatility' in metrics
        assert 'price_change_volatility' in metrics
        assert 'average_true_range' in metrics
        assert 'volatility_trend' in metrics
        assert 'data_points' in metrics
        
        assert metrics['data_points'] == len(prices)
        assert isinstance(metrics['basic_volatility'], float)
        assert metrics['basic_volatility'] >= 0
    
    def test_calculate_volatility_metrics_insufficient_data(self):
        """Test metrics calculation with insufficient data."""
        prices = [100]  # Only one price point
        time_periods = {}
        
        metrics = self.analyzer._calculate_volatility_metrics(prices, time_periods)
        
        assert 'error' in metrics
        assert metrics['error'] == 'Insufficient price data'
    
    def test_calculate_volatility_metrics_empty_data(self):
        """Test metrics calculation with empty data."""
        prices = []
        time_periods = {}
        
        metrics = self.analyzer._calculate_volatility_metrics(prices, time_periods)
        
        assert 'error' in metrics


class TestVolatilityRegimeDetection:
    """Test volatility regime detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('os.makedirs'):
            self.analyzer = VolatilityAnalyzer()
    
    def test_determine_volatility_regime_high(self):
        """Test detection of high volatility regime."""
        high_vol_metrics = {
            'basic_volatility': 0.08,  # 8% volatility
            'price_change_volatility': 8.0,
            'average_true_range': 15.0,
            'volatility_trend': 0.2
        }
        
        regime = self.analyzer._determine_volatility_regime(high_vol_metrics)
        
        assert isinstance(regime, dict)
        assert 'category' in regime
        assert 'score' in regime
        assert 'confidence' in regime
        assert 'trend' in regime
        
        assert regime['category'] in ['high', 'medium']
        assert regime['score'] > 0.5
        assert 0 <= regime['confidence'] <= 1
    
    def test_determine_volatility_regime_low(self):
        """Test detection of low volatility regime."""
        low_vol_metrics = {
            'basic_volatility': 0.005,  # 0.5% volatility
            'price_change_volatility': 0.5,
            'average_true_range': 1.0,
            'volatility_trend': -0.05
        }
        
        regime = self.analyzer._determine_volatility_regime(low_vol_metrics)
        
        assert regime['category'] in ['low', 'medium']
        assert regime['score'] < 0.7
    
    def test_determine_volatility_regime_error_handling(self):
        """Test regime detection with error metrics."""
        error_metrics = {'error': 'calculation_failed'}
        
        regime = self.analyzer._determine_volatility_regime(error_metrics)
        
        assert regime['category'] == 'unknown'
        assert regime['score'] == 0.5
        assert regime['confidence'] == 0.3


class TestStrategyAdjustments:
    """Test strategy adjustments based on volatility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('os.makedirs'):
            self.analyzer = VolatilityAnalyzer()
    
    def test_get_volatility_strategy_adjustments_high(self):
        """Test strategy adjustments for high volatility."""
        high_vol_regime = {
            'category': 'high',
            'score': 0.8,
            'confidence': 0.9
        }
        
        adjustments = self.analyzer._get_volatility_strategy_adjustments(high_vol_regime)
        
        assert isinstance(adjustments, dict)
        assert 'trend_following' in adjustments
        assert 'mean_reversion' in adjustments
        assert 'momentum' in adjustments
        assert 'llm_strategy' in adjustments
        assert 'position_size_multiplier' in adjustments
        assert 'confidence_threshold_adjustment' in adjustments
        
        # High volatility should reduce position sizes
        assert adjustments['position_size_multiplier'] < 1.0
        # Should favor mean reversion
        assert adjustments['mean_reversion'] > 0
    
    def test_get_volatility_strategy_adjustments_low(self):
        """Test strategy adjustments for low volatility."""
        low_vol_regime = {
            'category': 'low',
            'score': 0.3,
            'confidence': 0.8
        }
        
        adjustments = self.analyzer._get_volatility_strategy_adjustments(low_vol_regime)
        
        # Low volatility should increase position sizes
        assert adjustments['position_size_multiplier'] > 1.0
        # Should favor trend following
        assert adjustments['trend_following'] > 0
    
    def test_get_volatility_strategy_adjustments_medium(self):
        """Test strategy adjustments for medium volatility."""
        medium_vol_regime = {
            'category': 'medium',
            'score': 0.5,
            'confidence': 0.7
        }
        
        adjustments = self.analyzer._get_volatility_strategy_adjustments(medium_vol_regime)
        
        # Medium volatility should have neutral position sizing
        assert adjustments['position_size_multiplier'] == 1.0
        # Adjustments should be small
        assert abs(adjustments['trend_following']) <= 0.1


class TestMarketVolatilitySummary:
    """Test market volatility summary functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('os.makedirs'):
            self.analyzer = VolatilityAnalyzer()
    
    def test_get_market_volatility_summary_no_data(self):
        """Test summary with no volatility data."""
        summary = self.analyzer.get_market_volatility_summary()
        
        assert isinstance(summary, dict)
        assert summary['status'] == 'no_data'
        assert summary['overall_volatility'] == 'unknown'
    
    def test_get_market_volatility_summary_with_data(self):
        """Test summary with volatility data."""
        # Add some mock data to cache
        self.analyzer.volatility_cache = {
            'BTC-EUR': {
                'regime': {'category': 'high', 'score': 0.8, 'confidence': 0.9}
            },
            'ETH-EUR': {
                'regime': {'category': 'medium', 'score': 0.6, 'confidence': 0.8}
            }
        }
        
        summary = self.analyzer.get_market_volatility_summary()
        
        assert 'overall_volatility' in summary
        assert 'overall_score' in summary
        assert 'asset_count' in summary
        assert 'regime_distribution' in summary
        assert 'last_updated' in summary
        
        assert summary['asset_count'] == 2
        assert isinstance(summary['regime_distribution'], dict)
        assert summary['overall_score'] > 0


class TestVolatilityHistory:
    """Test volatility history management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        with patch('os.makedirs'):
            self.analyzer = VolatilityAnalyzer(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_volatility_history_no_file(self):
        """Test loading history when file doesn't exist."""
        history = self.analyzer._load_volatility_history()
        
        assert isinstance(history, dict)
        assert len(history) == 0
    
    def test_update_volatility_history(self):
        """Test updating volatility history."""
        analysis = {
            'product_id': 'BTC-EUR',
            'timestamp': datetime.now().isoformat(),
            'regime': {'category': 'high', 'score': 0.8}
        }
        
        self.analyzer._update_volatility_history('BTC-EUR', analysis)
        
        assert 'BTC-EUR' in self.analyzer.volatility_history
        assert len(self.analyzer.volatility_history['BTC-EUR']) == 1
        assert self.analyzer.volatility_history['BTC-EUR'][0] == analysis


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('os.makedirs'):
            self.analyzer = VolatilityAnalyzer()
    
    def test_analyze_volatility_with_exception(self):
        """Test volatility analysis when calculation fails."""
        # Mock the _calculate_volatility_metrics to raise an exception
        with patch.object(self.analyzer, '_calculate_volatility_metrics', side_effect=Exception("Test error")):
            result = self.analyzer.analyze_volatility('BTC-EUR', [100, 101, 102], {})
            
            # Should return default analysis
            assert result['regime']['category'] == 'medium'
            assert result['regime']['score'] == 0.5
            assert 'error' in result['metrics']
    
    def test_get_default_volatility_analysis(self):
        """Test default volatility analysis generation."""
        default = self.analyzer._get_default_volatility_analysis('BTC-EUR')
        
        assert isinstance(default, dict)
        assert default['product_id'] == 'BTC-EUR'
        assert 'timestamp' in default
        assert 'metrics' in default
        assert 'regime' in default
        assert 'strategy_adjustments' in default
        
        assert default['regime']['category'] == 'medium'
        assert default['strategy_adjustments']['position_size_multiplier'] == 1.0


class TestIntegrationScenarios:
    """Test integration scenarios with realistic data."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('os.makedirs'):
            self.analyzer = VolatilityAnalyzer()
    
    def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        # Generate realistic price data
        np.random.seed(42)
        prices = [45000]
        for i in range(50):
            change = np.random.normal(0, 0.03)  # 3% volatility
            prices.append(prices[-1] * (1 + change))
        
        time_periods = {
            '1h': 2.5,
            '24h': -1.8,
            '7d': 4.2
        }
        
        # Run full analysis
        result = self.analyzer.analyze_volatility('BTC-EUR', prices, time_periods)
        
        # Verify complete result structure
        assert all(key in result for key in ['product_id', 'timestamp', 'metrics', 'regime', 'strategy_adjustments'])
        
        # Verify metrics are calculated
        metrics = result['metrics']
        assert 'basic_volatility' in metrics
        assert metrics['basic_volatility'] > 0
        
        # Verify regime is determined
        regime = result['regime']
        assert regime['category'] in ['low', 'medium', 'high']
        assert 0 <= regime['score'] <= 1
        
        # Verify strategy adjustments are provided
        adjustments = result['strategy_adjustments']
        assert 'position_size_multiplier' in adjustments
        assert adjustments['position_size_multiplier'] > 0
        
        # Verify data is cached
        assert 'BTC-EUR' in self.analyzer.volatility_cache
    
    def test_multiple_asset_analysis(self):
        """Test analysis of multiple assets."""
        assets = ['BTC-EUR', 'ETH-EUR', 'SOL-EUR']
        
        for asset in assets:
            # Generate different volatility for each asset
            volatility = 0.02 + (hash(asset) % 100) / 10000  # Different volatility per asset
            prices = [45000]
            for i in range(30):
                change = np.random.normal(0, volatility)
                prices.append(prices[-1] * (1 + change))
            
            self.analyzer.analyze_volatility(asset, prices, {'1h': 1.0})
        
        # Check that all assets are analyzed
        assert len(self.analyzer.volatility_cache) == 3
        
        # Get market summary
        summary = self.analyzer.get_market_volatility_summary()
        assert summary['asset_count'] == 3
        assert 'overall_volatility' in summary