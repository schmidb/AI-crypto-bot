"""
Unit tests for configuration management.

This module tests the Config class and all configuration-related functionality
to ensure proper loading, validation, and handling of environment variables.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from config import Config


class TestConfigInitialization:
    """Test Config class initialization and basic functionality."""
    
    def test_config_initialization_with_defaults(self):
        """Test Config initialization with default values when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            # Test default values
            assert config.BASE_CURRENCY == "USD"
            assert config.TRADING_PAIRS == ["BTC-USD", "ETH-USD"]
            assert config.DECISION_INTERVAL_MINUTES == 120
            assert config.RISK_LEVEL == "medium"
            assert config.SIMULATION_MODE is False
            assert config.LLM_PROVIDER == "google_ai"  # Default value from config.py
            assert config.LLM_MODEL == "gemini-3-flash-preview"
            assert config.LLM_LOCATION == "global"
    
    def test_config_initialization_with_env_vars(self):
        """Test Config initialization with custom environment variables."""
        test_env = {
            'BASE_CURRENCY': 'EUR',
            'TRADING_PAIRS': 'BTC-EUR,ETH-EUR,SOL-EUR',
            'DECISION_INTERVAL_MINUTES': '30',
            'RISK_LEVEL': 'high',
            'SIMULATION_MODE': 'true',
            'COINBASE_API_KEY': 'test-api-key',
            'COINBASE_API_SECRET': 'test-api-secret',
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'LLM_MODEL': 'gemini-3-flash-preview'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            
            # Test custom values
            assert config.BASE_CURRENCY == "EUR"
            assert config.TRADING_PAIRS == ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
            assert config.DECISION_INTERVAL_MINUTES == 30
            assert config.RISK_LEVEL == "high"
            assert config.SIMULATION_MODE is True
            assert config.COINBASE_API_KEY == "test-api-key"
            assert config.COINBASE_API_SECRET == "test-api-secret"
            assert config.GOOGLE_CLOUD_PROJECT == "test-project"
            assert config.LLM_MODEL == "gemini-3-flash-preview"
    
    def test_config_boolean_parsing(self):
        """Test proper parsing of boolean environment variables."""
        # Test various boolean representations
        boolean_tests = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('1', False),  # Only 'true' should be True
            ('0', False),
            ('yes', False),
            ('', False)
        ]
        
        for env_value, expected in boolean_tests:
            with patch.dict(os.environ, {'SIMULATION_MODE': env_value}, clear=True):
                config = Config()
                assert config.SIMULATION_MODE is expected, f"Failed for value: {env_value}"
    
    def test_config_numeric_parsing(self):
        """Test proper parsing of numeric environment variables."""
        test_env = {
            'DECISION_INTERVAL_MINUTES': '45',
            'MAX_TRADE_PERCENTAGE': '30.5',
            'TARGET_CRYPTO_ALLOCATION': '85.0',
            'TARGET_BASE_ALLOCATION': '15.0',
            'CONFIDENCE_THRESHOLD_BUY': '75.5',
            'MIN_TRADE_AMOUNT': '25.50',
            'MAX_POSITION_SIZE': '2000.00'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            
            assert config.DECISION_INTERVAL_MINUTES == 45
            assert config.MAX_TRADE_PERCENTAGE == 30.5
            assert config.TARGET_CRYPTO_ALLOCATION == 85.0
            assert config.TARGET_BASE_ALLOCATION == 15.0
            assert config.CONFIDENCE_THRESHOLD_BUY == 75.5
            assert config.MIN_TRADE_AMOUNT == 25.50
            assert config.MAX_POSITION_SIZE == 2000.00


class TestTradingPairsParsing:
    """Test trading pairs parsing and crypto asset extraction."""
    
    def test_trading_pairs_single_pair(self):
        """Test parsing single trading pair."""
        with patch.dict(os.environ, {'TRADING_PAIRS': 'BTC-EUR'}, clear=True):
            config = Config()
            
            assert config.TRADING_PAIRS == ["BTC-EUR"]
            assert config.CRYPTO_ASSETS == ["BTC"]
    
    def test_trading_pairs_multiple_pairs(self):
        """Test parsing multiple trading pairs."""
        with patch.dict(os.environ, {'TRADING_PAIRS': 'BTC-EUR,ETH-EUR,SOL-EUR'}, clear=True):
            config = Config()
            
            assert config.TRADING_PAIRS == ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
            assert set(config.CRYPTO_ASSETS) == {"BTC", "ETH", "SOL"}
    
    def test_trading_pairs_with_duplicates(self):
        """Test handling of duplicate crypto assets in trading pairs."""
        with patch.dict(os.environ, {'TRADING_PAIRS': 'BTC-EUR,BTC-USD,ETH-EUR'}, clear=True):
            config = Config()
            
            assert config.TRADING_PAIRS == ["BTC-EUR", "BTC-USD", "ETH-EUR"]
            assert set(config.CRYPTO_ASSETS) == {"BTC", "ETH"}  # Duplicates removed
    
    def test_trading_pairs_whitespace_handling(self):
        """Test handling of whitespace in trading pairs."""
        with patch.dict(os.environ, {'TRADING_PAIRS': ' BTC-EUR , ETH-EUR , SOL-EUR '}, clear=True):
            config = Config()
            
            # Should handle whitespace gracefully
            assert config.TRADING_PAIRS == [" BTC-EUR ", " ETH-EUR ", " SOL-EUR "]
    
    def test_get_trading_pairs_method(self):
        """Test get_trading_pairs() method."""
        with patch.dict(os.environ, {'TRADING_PAIRS': 'BTC-EUR,ETH-EUR'}, clear=True):
            config = Config()
            
            pairs = config.get_trading_pairs()
            assert pairs == ["BTC-EUR", "ETH-EUR"]
            assert isinstance(pairs, list)
    
    def test_get_crypto_assets_method(self):
        """Test get_crypto_assets() method."""
        with patch.dict(os.environ, {'TRADING_PAIRS': 'BTC-EUR,ETH-EUR,SOL-EUR'}, clear=True):
            config = Config()
            
            assets = config.get_crypto_assets()
            assert set(assets) == {"BTC", "ETH", "SOL"}
            assert isinstance(assets, list)


class TestAllocationCalculations:
    """Test target allocation calculations and related functionality."""
    
    def test_individual_crypto_allocation_calculation(self):
        """Test calculation of individual crypto asset allocations."""
        test_cases = [
            # (trading_pairs, crypto_allocation, expected_individual)
            ('BTC-EUR', 80.0, 80.0),  # Single asset gets full allocation
            ('BTC-EUR,ETH-EUR', 80.0, 40.0),  # Two assets split equally
            ('BTC-EUR,ETH-EUR,SOL-EUR', 90.0, 30.0),  # Three assets split equally
            ('BTC-EUR,ETH-EUR,SOL-EUR,ADA-EUR', 80.0, 20.0),  # Four assets
        ]
        
        for pairs, crypto_alloc, expected_individual in test_cases:
            env_vars = {
                'TRADING_PAIRS': pairs,
                'TARGET_CRYPTO_ALLOCATION': str(crypto_alloc)
            }
            
            with patch.dict(os.environ, env_vars, clear=True):
                config = Config()
                
                assert config.INDIVIDUAL_CRYPTO_ALLOCATION == expected_individual
    
    def test_target_allocation_dictionary(self):
        """Test creation of target allocation dictionary."""
        env_vars = {
            'TRADING_PAIRS': 'BTC-EUR,ETH-EUR,SOL-EUR',
            'BASE_CURRENCY': 'EUR',
            'TARGET_CRYPTO_ALLOCATION': '90.0',
            'TARGET_BASE_ALLOCATION': '10.0'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            expected_allocation = {
                'BTC': 30.0,  # 90% / 3 assets
                'ETH': 30.0,
                'SOL': 30.0,
                'EUR': 10.0
            }
            
            assert config.TARGET_ALLOCATION == expected_allocation
    
    def test_get_target_allocation_method(self):
        """Test get_target_allocation() method."""
        env_vars = {
            'TRADING_PAIRS': 'BTC-EUR,ETH-EUR',
            'BASE_CURRENCY': 'EUR',
            'TARGET_CRYPTO_ALLOCATION': '80.0',
            'TARGET_BASE_ALLOCATION': '20.0'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            allocation = config.get_target_allocation()
            expected = {
                'BTC': 40.0,
                'ETH': 40.0,
                'EUR': 20.0
            }
            
            assert allocation == expected
            assert isinstance(allocation, dict)
    
    def test_allocation_with_zero_crypto_assets(self):
        """Test allocation calculation with no crypto assets."""
        with patch.dict(os.environ, {'TRADING_PAIRS': ''}, clear=True):
            config = Config()
            
            assert config.CRYPTO_ASSETS == ['']  # Empty string becomes single element
            assert config.INDIVIDUAL_CRYPTO_ALLOCATION == 80.0  # Default crypto allocation


class TestCurrencyFormatting:
    """Test currency formatting and symbol handling."""
    
    def test_get_base_currency_method(self):
        """Test get_base_currency() method."""
        currencies = ['USD', 'EUR', 'GBP', 'JPY']
        
        for currency in currencies:
            with patch.dict(os.environ, {'BASE_CURRENCY': currency}, clear=True):
                config = Config()
                assert config.get_base_currency() == currency
    
    def test_get_base_currency_symbol(self):
        """Test currency symbol retrieval."""
        symbol_tests = [
            ('USD', '$'),
            ('EUR', '€'),
            ('GBP', '£'),
            ('JPY', '¥'),
            ('CAD', 'C$'),
            ('AUD', 'A$'),
            ('UNKNOWN', 'UNKNOWN')  # Unknown currency returns itself
        ]
        
        for currency, expected_symbol in symbol_tests:
            with patch.dict(os.environ, {'BASE_CURRENCY': currency}, clear=True):
                config = Config()
                assert config.get_base_currency_symbol() == expected_symbol
    
    def test_format_currency(self):
        """Test currency amount formatting."""
        test_cases = [
            ('USD', 100.0, '$100.00'),
            ('EUR', 250.50, '€250.50'),
            ('GBP', 75.99, '£75.99'),
            ('JPY', 1000.0, '¥1000.00'),
            ('UNKNOWN', 50.0, 'UNKNOWN50.00')
        ]
        
        for currency, amount, expected in test_cases:
            with patch.dict(os.environ, {'BASE_CURRENCY': currency}, clear=True):
                config = Config()
                assert config.format_currency(amount) == expected


class TestRiskManagementSettings:
    """Test risk management configuration settings."""
    
    def test_risk_multipliers_defaults(self):
        """Test default risk multiplier values."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.RISK_HIGH_POSITION_MULTIPLIER == 0.5
            assert config.RISK_MEDIUM_POSITION_MULTIPLIER == 0.75
            assert config.RISK_LOW_POSITION_MULTIPLIER == 1.0
    
    def test_risk_multipliers_custom(self):
        """Test custom risk multiplier values."""
        env_vars = {
            'RISK_HIGH_POSITION_MULTIPLIER': '0.3',
            'RISK_MEDIUM_POSITION_MULTIPLIER': '0.6',
            'RISK_LOW_POSITION_MULTIPLIER': '0.9'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            assert config.RISK_HIGH_POSITION_MULTIPLIER == 0.3
            assert config.RISK_MEDIUM_POSITION_MULTIPLIER == 0.6
            assert config.RISK_LOW_POSITION_MULTIPLIER == 0.9
    
    def test_confidence_thresholds(self):
        """Test confidence threshold settings."""
        env_vars = {
            'CONFIDENCE_THRESHOLD_BUY': '75.0',
            'CONFIDENCE_THRESHOLD_SELL': '70.0',
            'CONFIDENCE_BOOST_TREND_ALIGNED': '15.0',
            'CONFIDENCE_PENALTY_COUNTER_TREND': '8.0'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            assert config.CONFIDENCE_THRESHOLD_BUY == 75.0
            assert config.CONFIDENCE_THRESHOLD_SELL == 70.0
            assert config.CONFIDENCE_BOOST_TREND_ALIGNED == 15.0
            assert config.CONFIDENCE_PENALTY_COUNTER_TREND == 8.0
    
    def test_trade_size_limits(self):
        """Test trade size limit settings."""
        env_vars = {
            'MIN_TRADE_AMOUNT': '50.0',
            'MAX_POSITION_SIZE': '5000.0'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            assert config.MIN_TRADE_AMOUNT == 50.0
            assert config.MAX_POSITION_SIZE == 5000.0


class TestTechnicalAnalysisSettings:
    """Test technical analysis configuration settings."""
    
    def test_technical_indicator_weights(self):
        """Test technical indicator weight settings."""
        env_vars = {
            'MACD_SIGNAL_WEIGHT': '0.5',
            'RSI_SIGNAL_WEIGHT': '0.3',
            'BOLLINGER_SIGNAL_WEIGHT': '0.2'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            assert config.MACD_SIGNAL_WEIGHT == 0.5
            assert config.RSI_SIGNAL_WEIGHT == 0.3
            assert config.BOLLINGER_SIGNAL_WEIGHT == 0.2
    
    def test_rsi_neutral_range(self):
        """Test RSI neutral range settings."""
        env_vars = {
            'RSI_NEUTRAL_MIN': '40.0',
            'RSI_NEUTRAL_MAX': '60.0'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            assert config.RSI_NEUTRAL_MIN == 40.0
            assert config.RSI_NEUTRAL_MAX == 60.0


class TestNotificationSettings:
    """Test notification configuration settings."""
    
    def test_notifications_disabled_by_default(self):
        """Test that notifications are disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.NOTIFICATIONS_ENABLED is False
            assert config.PUSHOVER_TOKEN is None
            assert config.PUSHOVER_USER is None
    
    def test_notifications_enabled(self):
        """Test notification settings when enabled."""
        env_vars = {
            'NOTIFICATIONS_ENABLED': 'true',
            'PUSHOVER_TOKEN': 'test-token',
            'PUSHOVER_USER': 'test-user'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            assert config.NOTIFICATIONS_ENABLED is True
            assert config.PUSHOVER_TOKEN == 'test-token'
            assert config.PUSHOVER_USER == 'test-user'


class TestWebServerSyncSettings:
    """Test web server sync configuration settings."""
    
    def test_webserver_sync_defaults(self):
        """Test default web server sync settings."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.WEBSERVER_SYNC_ENABLED is False
            assert config.WEBSERVER_SYNC_PATH == "/var/www/html/crypto-bot"
    
    def test_webserver_sync_enabled(self):
        """Test web server sync when enabled."""
        env_vars = {
            'WEBSERVER_SYNC_ENABLED': 'true',
            'WEBSERVER_SYNC_PATH': '/custom/path/crypto-bot'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            assert config.WEBSERVER_SYNC_ENABLED is True
            assert config.WEBSERVER_SYNC_PATH == '/custom/path/crypto-bot'


class TestBackwardCompatibility:
    """Test backward compatibility with old environment variable names."""
    
    def test_target_usd_allocation_compatibility(self):
        """Test backward compatibility for TARGET_USD_ALLOCATION."""
        # Test with old variable name
        with patch.dict(os.environ, {'TARGET_USD_ALLOCATION': '25.0'}, clear=True):
            config = Config()
            assert config.TARGET_BASE_ALLOCATION == 25.0
        
        # Test that new variable takes precedence
        env_vars = {
            'TARGET_BASE_ALLOCATION': '15.0',
            'TARGET_USD_ALLOCATION': '25.0'
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.TARGET_BASE_ALLOCATION == 15.0
    
    def test_min_trade_usd_compatibility(self):
        """Test backward compatibility for MIN_TRADE_USD."""
        # Test with old variable name
        with patch.dict(os.environ, {'MIN_TRADE_USD': '15.0'}, clear=True):
            config = Config()
            assert config.MIN_TRADE_AMOUNT == 15.0
        
        # Test that new variable takes precedence
        env_vars = {
            'MIN_TRADE_AMOUNT': '20.0',
            'MIN_TRADE_USD': '15.0'
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.MIN_TRADE_AMOUNT == 20.0
    
    def test_max_position_size_usd_compatibility(self):
        """Test backward compatibility for MAX_POSITION_SIZE_USD."""
        # Test with old variable name
        with patch.dict(os.environ, {'MAX_POSITION_SIZE_USD': '2500.0'}, clear=True):
            config = Config()
            assert config.MAX_POSITION_SIZE == 2500.0
        
        # Test that new variable takes precedence
        env_vars = {
            'MAX_POSITION_SIZE': '3000.0',
            'MAX_POSITION_SIZE_USD': '2500.0'
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.MAX_POSITION_SIZE == 3000.0


class TestModuleLevelVariables:
    """Test module-level variables for backward compatibility."""
    
    def test_module_level_config_instance(self):
        """Test that module-level config instance is created."""
        from config import config
        
        assert isinstance(config, Config)
        assert hasattr(config, 'BASE_CURRENCY')
        assert hasattr(config, 'TRADING_PAIRS')
    
    def test_module_level_variables_exist(self):
        """Test that all expected module-level variables exist."""
        import config
        
        # Test that key variables are available at module level
        expected_vars = [
            'COINBASE_API_KEY', 'COINBASE_API_SECRET',
            'GOOGLE_CLOUD_PROJECT', 'GOOGLE_APPLICATION_CREDENTIALS',
            'LLM_PROVIDER', 'LLM_MODEL', 'LLM_LOCATION',
            'TRADING_PAIRS', 'BASE_CURRENCY', 'DECISION_INTERVAL_MINUTES',
            'RISK_LEVEL', 'SIMULATION_MODE', 'MAX_TRADE_PERCENTAGE',
            'TARGET_CRYPTO_ALLOCATION'
        ]
        
        for var_name in expected_vars:
            assert hasattr(config, var_name), f"Missing module-level variable: {var_name}"


class TestConfigValidation:
    """Test configuration validation and error handling."""
    
    def test_invalid_numeric_values(self):
        """Test handling of invalid numeric environment variables."""
        # Test invalid integer
        with patch.dict(os.environ, {'DECISION_INTERVAL_MINUTES': 'invalid'}, clear=True):
            with pytest.raises(ValueError):
                Config()
        
        # Test invalid float
        with patch.dict(os.environ, {'MAX_TRADE_PERCENTAGE': 'not_a_number'}, clear=True):
            with pytest.raises(ValueError):
                Config()
    
    def test_empty_trading_pairs(self):
        """Test handling of empty trading pairs."""
        with patch.dict(os.environ, {'TRADING_PAIRS': ''}, clear=True):
            config = Config()
            
            # Should handle empty string gracefully
            assert config.TRADING_PAIRS == ['']
            assert config.CRYPTO_ASSETS == ['']
    
    def test_missing_required_credentials(self):
        """Test behavior with missing API credentials."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            # Should not raise error, but credentials should be None
            assert config.COINBASE_API_KEY is None
            assert config.COINBASE_API_SECRET is None
            assert config.GOOGLE_CLOUD_PROJECT is None
            assert config.GOOGLE_APPLICATION_CREDENTIALS is None


# Integration test to verify the complete config works together
class TestConfigIntegration:
    """Integration tests for complete configuration functionality."""
    
    def test_complete_config_setup(self):
        """Test complete configuration setup with all settings."""
        complete_env = {
            # API Credentials
            'COINBASE_API_KEY': 'test-coinbase-key',
            'COINBASE_API_SECRET': 'test-coinbase-secret',
            'GOOGLE_CLOUD_PROJECT': 'test-gcp-project',
            'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/credentials.json',
            
            # LLM Settings
            'LLM_PROVIDER': 'vertex',
            'LLM_MODEL': 'gemini-3-flash-preview',
            'LLM_LOCATION': 'global',
            
            # Trading Settings
            'TRADING_PAIRS': 'BTC-EUR,ETH-EUR,SOL-EUR',
            'BASE_CURRENCY': 'EUR',
            'DECISION_INTERVAL_MINUTES': '45',
            'RISK_LEVEL': 'medium',
            'SIMULATION_MODE': 'true',
            
            # Portfolio Settings
            'MAX_TRADE_PERCENTAGE': '20.0',
            'TARGET_CRYPTO_ALLOCATION': '85.0',
            'TARGET_BASE_ALLOCATION': '15.0',
            
            # Risk Management
            'CONFIDENCE_THRESHOLD_BUY': '70.0',
            'CONFIDENCE_THRESHOLD_SELL': '65.0',
            'MIN_TRADE_AMOUNT': '30.0',
            'MAX_POSITION_SIZE': '1500.0',
            
            # Notifications
            'NOTIFICATIONS_ENABLED': 'true',
            'PUSHOVER_TOKEN': 'test-pushover-token',
            'PUSHOVER_USER': 'test-pushover-user',
            
            # Web Server Sync
            'WEBSERVER_SYNC_ENABLED': 'true',
            'WEBSERVER_SYNC_PATH': '/var/www/html/test-bot'
        }
        
        with patch.dict(os.environ, complete_env, clear=True):
            config = Config()
            
            # Verify all settings are loaded correctly
            assert config.COINBASE_API_KEY == 'test-coinbase-key'
            assert config.BASE_CURRENCY == 'EUR'
            assert config.TRADING_PAIRS == ['BTC-EUR', 'ETH-EUR', 'SOL-EUR']
            assert config.SIMULATION_MODE is True
            assert config.CONFIDENCE_THRESHOLD_BUY == 70.0
            assert config.NOTIFICATIONS_ENABLED is True
            assert config.WEBSERVER_SYNC_ENABLED is True
            
            # Verify calculated values
            assert config.INDIVIDUAL_CRYPTO_ALLOCATION == 85.0 / 3  # 28.33...
            assert len(config.TARGET_ALLOCATION) == 4  # 3 cryptos + EUR
            assert config.get_base_currency_symbol() == '€'
            
            # Verify methods work
            assert config.format_currency(100.0) == '€100.00'
            assert set(config.get_crypto_assets()) == {'BTC', 'ETH', 'SOL'}
    
    def test_config_consistency(self):
        """Test that configuration values are consistent and logical."""
        env_vars = {
            'TRADING_PAIRS': 'BTC-EUR,ETH-EUR',
            'TARGET_CRYPTO_ALLOCATION': '80.0',
            'TARGET_BASE_ALLOCATION': '20.0'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            
            # Test allocation consistency
            total_allocation = sum(config.TARGET_ALLOCATION.values())
            assert abs(total_allocation - 100.0) < 0.01  # Should sum to 100%
            
            # Test that crypto assets match trading pairs
            expected_cryptos = {'BTC', 'ETH'}
            actual_cryptos = set(config.get_crypto_assets())
            assert actual_cryptos == expected_cryptos
            
            # Test that individual allocation makes sense
            expected_individual = 80.0 / 2  # 40% each
            assert config.INDIVIDUAL_CRYPTO_ALLOCATION == expected_individual
