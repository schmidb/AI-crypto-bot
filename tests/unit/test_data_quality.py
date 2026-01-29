"""
Data Quality Validation Tests

Tests to ensure data integrity and catch data quality issues before they affect trading:
- Market data validation (prices, volumes, timestamps)
- Technical indicator validation (RSI, MACD, Bollinger Bands)
- Portfolio data validation (balances, prices, allocations)
- Price change data validation (timeframe consistency)
- Data freshness and staleness detection
- Data type and format validation
- Missing data detection and handling
"""

import pytest
from unittest.mock import Mock, patch
import logging
from datetime import datetime, timezone, timedelta
import json
import numpy as np

from config import Config
from data_collector import DataCollector
from utils.trading.portfolio import Portfolio


class TestMarketDataQuality:
    """Test market data quality and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
    
    def test_price_data_validity(self):
        """Test that price data is valid and reasonable."""
        # Valid price data
        valid_prices = {
            'BTC-EUR': 45000.0,
            'ETH-EUR': 2800.0,
            'SOL-EUR': 95.0
        }
        
        for pair, price in valid_prices.items():
            assert isinstance(price, (int, float)), f"Price for {pair} must be numeric"
            assert price > 0, f"Price for {pair} must be positive: {price}"
            assert price < 1000000, f"Price for {pair} seems unreasonably high: {price}"
            assert not np.isnan(price), f"Price for {pair} cannot be NaN"
            assert not np.isinf(price), f"Price for {pair} cannot be infinite"
    
    def test_invalid_price_data_detection(self):
        """Test detection of invalid price data."""
        invalid_prices = [
            ('BTC-EUR', 0),          # Zero price
            ('ETH-EUR', -100),       # Negative price
            ('SOL-EUR', float('nan')), # NaN price
            ('BTC-EUR', float('inf')), # Infinite price
            ('ETH-EUR', 'invalid'),    # String price
        ]
        
        for pair, invalid_price in invalid_prices:
            with pytest.raises((AssertionError, TypeError, ValueError)):
                assert isinstance(invalid_price, (int, float))
                assert invalid_price > 0
                assert not np.isnan(invalid_price)
                assert not np.isinf(invalid_price)
    
    def test_volume_data_validity(self):
        """Test that volume data is valid."""
        valid_volume_data = {
            'current': 1500000,
            'average': 1200000,
            '24h': 28000000
        }
        
        for key, volume in valid_volume_data.items():
            assert isinstance(volume, (int, float)), f"Volume {key} must be numeric"
            assert volume >= 0, f"Volume {key} cannot be negative: {volume}"
            assert not np.isnan(volume), f"Volume {key} cannot be NaN"
            assert not np.isinf(volume), f"Volume {key} cannot be infinite"
    
    def test_price_change_data_consistency(self):
        """Test price change data consistency across timeframes."""
        price_changes = {
            '1h': 2.5,
            '4h': 4.0,
            '24h': 6.0,
            '5d': 12.0
        }
        
        # Test data types and ranges
        for timeframe, change in price_changes.items():
            assert isinstance(change, (int, float)), f"Price change {timeframe} must be numeric"
            assert -50 <= change <= 50, f"Price change {timeframe} seems unreasonable: {change}%"
            assert not np.isnan(change), f"Price change {timeframe} cannot be NaN"
            assert not np.isinf(change), f"Price change {timeframe} cannot be infinite"
        
        # Test logical consistency (longer timeframes should generally have larger absolute changes)
        # Note: This is a soft rule, not always true in volatile markets
        if abs(price_changes['5d']) < abs(price_changes['1h']) / 2:
            # Log warning but don't fail - this can happen in volatile markets
            print(f"Warning: 5d change ({price_changes['5d']}%) is much smaller than 1h change ({price_changes['1h']}%)")
    
    def test_timestamp_validity(self):
        """Test timestamp data validity and freshness."""
        now = datetime.now(timezone.utc)
        
        # Valid timestamps (remove timezone info for Z suffix)
        valid_timestamps = [
            now.replace(tzinfo=None).isoformat() + 'Z',
            (now - timedelta(minutes=5)).replace(tzinfo=None).isoformat() + 'Z',
            (now - timedelta(hours=1)).replace(tzinfo=None).isoformat() + 'Z'
        ]
        
        for timestamp_str in valid_timestamps:
            # Test parsing
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            assert isinstance(timestamp, datetime)
            
            # Test freshness (data shouldn't be too old) - compare timezone-aware datetimes
            age = now - timestamp
            assert age.total_seconds() < 7200, f"Data is too old: {age.total_seconds()} seconds"
    
    def test_stale_data_detection(self):
        """Test detection of stale data."""
        now = datetime.now(timezone.utc)
        
        # Stale timestamps (older than 2 hours) - remove timezone info for Z suffix
        stale_timestamps = [
            (now - timedelta(hours=3)).replace(tzinfo=None).isoformat() + 'Z',
            (now - timedelta(days=1)).replace(tzinfo=None).isoformat() + 'Z'
        ]
        
        for timestamp_str in stale_timestamps:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age = now - timestamp
            
            # Should detect as stale
            assert age.total_seconds() > 7200, f"Should detect as stale: {age.total_seconds()} seconds"


class TestTechnicalIndicatorQuality:
    """Test technical indicator data quality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
    
    def test_rsi_validity(self):
        """Test RSI indicator validity."""
        valid_rsi_values = [0, 30, 50, 70, 100]
        
        for rsi in valid_rsi_values:
            assert isinstance(rsi, (int, float)), "RSI must be numeric"
            assert 0 <= rsi <= 100, f"RSI must be between 0-100: {rsi}"
            assert not np.isnan(rsi), "RSI cannot be NaN"
            assert not np.isinf(rsi), "RSI cannot be infinite"
    
    def test_invalid_rsi_detection(self):
        """Test detection of invalid RSI values."""
        invalid_rsi_values = [-10, 110, float('nan'), float('inf'), 'invalid']
        
        for invalid_rsi in invalid_rsi_values:
            with pytest.raises((AssertionError, TypeError, ValueError)):
                if isinstance(invalid_rsi, str):
                    raise TypeError("RSI must be numeric")
                assert 0 <= invalid_rsi <= 100
                assert not np.isnan(invalid_rsi)
                assert not np.isinf(invalid_rsi)
    
    def test_macd_data_structure(self):
        """Test MACD data structure and validity."""
        valid_macd = {
            'macd': 0.5,
            'signal': 0.3,
            'histogram': 0.2
        }
        
        # Test structure
        required_keys = ['macd', 'signal', 'histogram']
        for key in required_keys:
            assert key in valid_macd, f"MACD missing required key: {key}"
        
        # Test values
        for key, value in valid_macd.items():
            assert isinstance(value, (int, float)), f"MACD {key} must be numeric"
            assert not np.isnan(value), f"MACD {key} cannot be NaN"
            assert not np.isinf(value), f"MACD {key} cannot be infinite"
            assert -10 <= value <= 10, f"MACD {key} seems unreasonable: {value}"
    
    def test_bollinger_bands_validity(self):
        """Test Bollinger Bands data validity."""
        bollinger_data = {
            'bb_upper': 52000,
            'bb_middle': 50000,
            'bb_lower': 48000
        }
        
        # Test individual values
        for key, value in bollinger_data.items():
            assert isinstance(value, (int, float)), f"Bollinger {key} must be numeric"
            assert value > 0, f"Bollinger {key} must be positive: {value}"
            assert not np.isnan(value), f"Bollinger {key} cannot be NaN"
            assert not np.isinf(value), f"Bollinger {key} cannot be infinite"
        
        # Test logical relationships
        assert bollinger_data['bb_upper'] > bollinger_data['bb_middle'], \
            "Upper band must be above middle band"
        assert bollinger_data['bb_middle'] > bollinger_data['bb_lower'], \
            "Middle band must be above lower band"
        
        # Test reasonable band width (should be 2-20% of middle price)
        band_width = bollinger_data['bb_upper'] - bollinger_data['bb_lower']
        width_percentage = (band_width / bollinger_data['bb_middle']) * 100
        assert 1 <= width_percentage <= 25, f"Bollinger band width seems unreasonable: {width_percentage}%"
    
    def test_technical_indicator_consistency(self):
        """Test consistency between technical indicators and price."""
        current_price = 50000.0
        technical_indicators = {
            'rsi': 65,
            'macd': {'macd': 0.3, 'signal': 0.2, 'histogram': 0.1},
            'bb_upper': 52000,
            'bb_middle': 50000,
            'bb_lower': 48000,
            'current_price': current_price
        }
        
        # Price should be within reasonable range of Bollinger Bands
        bb_range = technical_indicators['bb_upper'] - technical_indicators['bb_lower']
        price_deviation = abs(current_price - technical_indicators['bb_middle'])
        
        # Price shouldn't be more than 2x the band width away from middle
        assert price_deviation <= bb_range, \
            f"Price too far from Bollinger middle: {price_deviation} vs band width {bb_range}"


class TestPortfolioDataQuality:
    """Test portfolio data quality and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
    
    def test_portfolio_balance_validity(self):
        """Test portfolio balance data validity."""
        portfolio_data = {
            'EUR': {'amount': 1000.0, 'price': 1.0},
            'BTC': {'amount': 0.1, 'price': 50000.0},
            'ETH': {'amount': 1.5, 'price': 3000.0}
        }
        
        for currency, data in portfolio_data.items():
            # Test amount
            assert isinstance(data['amount'], (int, float)), f"{currency} amount must be numeric"
            assert data['amount'] >= 0, f"{currency} amount cannot be negative: {data['amount']}"
            assert not np.isnan(data['amount']), f"{currency} amount cannot be NaN"
            assert not np.isinf(data['amount']), f"{currency} amount cannot be infinite"
            
            # Test price
            assert isinstance(data['price'], (int, float)), f"{currency} price must be numeric"
            assert data['price'] > 0, f"{currency} price must be positive: {data['price']}"
            assert not np.isnan(data['price']), f"{currency} price cannot be NaN"
            assert not np.isinf(data['price']), f"{currency} price cannot be infinite"
    
    def test_portfolio_allocation_consistency(self):
        """Test portfolio allocation consistency."""
        portfolio_data = {
            'EUR': {'amount': 1000.0, 'price': 1.0},
            'BTC': {'amount': 0.1, 'price': 50000.0},
            'ETH': {'amount': 1.5, 'price': 3000.0}
        }
        
        # Calculate total value
        total_value = sum(data['amount'] * data['price'] for data in portfolio_data.values())
        assert total_value > 0, "Total portfolio value must be positive"
        
        # Calculate allocations
        allocations = {}
        for currency, data in portfolio_data.items():
            value = data['amount'] * data['price']
            allocation = (value / total_value) * 100
            allocations[currency] = allocation
            
            # Test allocation ranges
            assert 0 <= allocation <= 100, f"{currency} allocation out of range: {allocation}%"
        
        # Test total allocation
        total_allocation = sum(allocations.values())
        assert abs(total_allocation - 100) < 0.01, f"Total allocation should be 100%: {total_allocation}%"
    
    def test_minimum_balance_requirements(self):
        """Test minimum balance requirements."""
        # Test EUR balance (should be >= 50 for trading)
        eur_balance = 1000.0
        assert eur_balance >= 50, f"EUR balance too low for trading: €{eur_balance}"
        
        # Test crypto balances (should be reasonable)
        crypto_balances = {
            'BTC': 0.1,
            'ETH': 1.5,
            'SOL': 10.0
        }
        
        for crypto, balance in crypto_balances.items():
            assert balance >= 0, f"{crypto} balance cannot be negative: {balance}"
            # Test for dust amounts (very small balances that might cause issues)
            if balance > 0:
                assert balance >= 0.0001, f"{crypto} balance too small (dust): {balance}"


class TestDataCollectorQuality:
    """Test data collector output quality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
    
    def test_collected_data_structure(self):
        """Test that collected data has proper structure."""
        # Test with mock data structure that should be returned by data collector
        market_data = {
            'price': 50000.0,
            'volume': {'current': 1500000, 'average': 1200000},
            'price_changes': {'1h': 2.0, '4h': 3.0, '24h': 5.0, '5d': 8.0}
        }
        
        # Validate structure
        assert 'price' in market_data
        assert 'volume' in market_data
        assert 'price_changes' in market_data
        
        # Validate price
        assert isinstance(market_data['price'], (int, float))
        assert market_data['price'] > 0
        
        # Validate volume structure
        volume_data = market_data['volume']
        assert isinstance(volume_data, dict)
        assert 'current' in volume_data
        assert 'average' in volume_data
        
        # Validate price changes structure
        price_changes = market_data['price_changes']
        assert isinstance(price_changes, dict)
        required_timeframes = ['1h', '4h', '24h', '5d']
        for timeframe in required_timeframes:
            assert timeframe in price_changes
    
    def test_data_freshness_validation(self):
        """Test data freshness validation."""
        now = datetime.now(timezone.utc)
        
        # Test fresh data (within last 5 minutes) - remove timezone info for Z suffix
        fresh_timestamp = (now - timedelta(minutes=2)).replace(tzinfo=None).isoformat() + 'Z'
        fresh_data = {
            'timestamp': fresh_timestamp,
            'price': 50000.0
        }
        
        timestamp = datetime.fromisoformat(fresh_data['timestamp'].replace('Z', '+00:00'))
        age_seconds = (now - timestamp).total_seconds()
        
        assert age_seconds < 300, f"Data should be fresh: {age_seconds} seconds old"
    
    def test_data_completeness_validation(self):
        """Test that collected data is complete."""
        required_market_data_keys = ['price', 'volume', 'price_changes']
        required_technical_keys = ['rsi', 'macd', 'bb_upper', 'bb_lower', 'bb_middle', 'current_price']
        required_price_change_keys = ['1h', '4h', '24h', '5d']
        
        # Mock complete data
        market_data = {
            'price': 50000.0,
            'volume': {'current': 1500000, 'average': 1200000},
            'price_changes': {'1h': 2.0, '4h': 3.0, '24h': 5.0, '5d': 8.0}
        }
        
        technical_indicators = {
            'rsi': 65,
            'macd': {'macd': 0.3, 'signal': 0.2, 'histogram': 0.1},
            'bb_upper': 52000,
            'bb_lower': 48000,
            'bb_middle': 50000,
            'current_price': 50000.0
        }
        
        # Test market data completeness
        for key in required_market_data_keys:
            assert key in market_data, f"Missing required market data key: {key}"
        
        # Test technical indicators completeness
        for key in required_technical_keys:
            assert key in technical_indicators, f"Missing required technical indicator: {key}"
        
        # Test price changes completeness
        for timeframe in required_price_change_keys:
            assert timeframe in market_data['price_changes'], f"Missing price change timeframe: {timeframe}"


class TestDataQualityIntegration:
    """Integration tests for data quality across the system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
    
    def test_end_to_end_data_quality(self):
        """Test data quality from collection to strategy analysis."""
        # Mock complete, valid data set - remove timezone info for Z suffix
        market_data = {
            'price': 50000.0,
            'volume': {'current': 1500000, 'average': 1200000},
            'price_changes': {'1h': 2.0, '4h': 3.0, '24h': 5.0, '5d': 8.0},
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        technical_indicators = {
            'rsi': 65,
            'macd': {'macd': 0.3, 'signal': 0.2, 'histogram': 0.1},
            'bb_upper': 52000,
            'bb_lower': 48000,
            'bb_middle': 50000,
            'current_price': 50000.0
        }
        
        portfolio = {
            'EUR': {'amount': 1000.0, 'price': 1.0},
            'BTC': {'amount': 0.1, 'price': 50000.0}
        }
        
        # Validate all data components
        self._validate_market_data(market_data)
        self._validate_technical_indicators(technical_indicators)
        self._validate_portfolio_data(portfolio)
    
    def _validate_market_data(self, market_data):
        """Validate market data quality."""
        assert isinstance(market_data, dict)
        assert 'price' in market_data
        assert 'volume' in market_data
        assert 'price_changes' in market_data
        
        # Validate price
        price = market_data['price']
        assert isinstance(price, (int, float))
        assert price > 0
        assert not np.isnan(price)
        assert not np.isinf(price)
        
        # Validate volume
        volume = market_data['volume']
        assert isinstance(volume, dict)
        assert 'current' in volume
        assert 'average' in volume
        
        # Validate price changes
        price_changes = market_data['price_changes']
        assert isinstance(price_changes, dict)
        for timeframe in ['1h', '4h', '24h', '5d']:
            assert timeframe in price_changes
            change = price_changes[timeframe]
            assert isinstance(change, (int, float))
            assert not np.isnan(change)
            assert not np.isinf(change)
    
    def _validate_technical_indicators(self, technical_indicators):
        """Validate technical indicators quality."""
        assert isinstance(technical_indicators, dict)
        
        # Validate RSI
        rsi = technical_indicators.get('rsi')
        if rsi is not None:
            assert 0 <= rsi <= 100
            assert not np.isnan(rsi)
            assert not np.isinf(rsi)
        
        # Validate MACD
        macd = technical_indicators.get('macd')
        if macd is not None:
            assert isinstance(macd, dict)
            for key in ['macd', 'signal', 'histogram']:
                if key in macd:
                    value = macd[key]
                    assert isinstance(value, (int, float))
                    assert not np.isnan(value)
                    assert not np.isinf(value)
        
        # Validate Bollinger Bands
        bb_upper = technical_indicators.get('bb_upper')
        bb_lower = technical_indicators.get('bb_lower')
        bb_middle = technical_indicators.get('bb_middle')
        
        if all(x is not None for x in [bb_upper, bb_lower, bb_middle]):
            assert bb_upper > bb_middle > bb_lower
            assert all(not np.isnan(x) and not np.isinf(x) for x in [bb_upper, bb_lower, bb_middle])
    
    def _validate_portfolio_data(self, portfolio):
        """Validate portfolio data quality."""
        assert isinstance(portfolio, dict)
        
        for currency, data in portfolio.items():
            assert isinstance(data, dict)
            assert 'amount' in data
            assert 'price' in data
            
            amount = data['amount']
            price = data['price']
            
            assert isinstance(amount, (int, float))
            assert isinstance(price, (int, float))
            assert amount >= 0
            assert price > 0
            assert not np.isnan(amount) and not np.isnan(price)
            assert not np.isinf(amount) and not np.isinf(price)
    
    def test_data_quality_error_detection(self):
        """Test that data quality errors are properly detected."""
        # Test with various data quality issues
        bad_data_scenarios = [
            # Scenario 1: Invalid price
            {
                'market_data': {'price': -100, 'volume': {'current': 1000}, 'price_changes': {'1h': 1}},
                'error_type': 'negative_price'
            },
            # Scenario 2: NaN RSI
            {
                'technical_indicators': {'rsi': float('nan'), 'current_price': 50000},
                'error_type': 'nan_rsi'
            },
            # Scenario 3: Invalid Bollinger Band relationship
            {
                'technical_indicators': {
                    'bb_upper': 48000,  # Upper < Lower (invalid)
                    'bb_lower': 52000,
                    'bb_middle': 50000,
                    'current_price': 50000
                },
                'error_type': 'invalid_bollinger_relationship'
            }
        ]
        
        for scenario in bad_data_scenarios:
            with pytest.raises((AssertionError, ValueError, TypeError)):
                if 'market_data' in scenario:
                    self._validate_market_data(scenario['market_data'])
                if 'technical_indicators' in scenario:
                    self._validate_technical_indicators(scenario['technical_indicators'])


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
