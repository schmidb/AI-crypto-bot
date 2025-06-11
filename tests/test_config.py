#!/usr/bin/env python3
"""
Unit tests for configuration management
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestConfiguration(unittest.TestCase):
    """Test cases for configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original environment variables
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Clean up test environment"""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)
    
    @patch.dict(os.environ, {
        'COINBASE_API_KEY': 'test_api_key',
        'COINBASE_API_SECRET': 'test_api_secret',
        'GOOGLE_PROJECT_ID': 'test_project',
        'GOOGLE_LOCATION': 'us-central1',
        'SIMULATION_MODE': 'true',
        'RISK_LEVEL': 'medium',
        'DECISION_INTERVAL_MINUTES': '60'
    })
    def test_config_loading_from_env(self):
        """Test configuration loading from environment variables"""
        # Import config after setting environment variables
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Verify configuration values
        self.assertEqual(config.COINBASE_API_KEY, 'test_api_key')
        self.assertEqual(config.COINBASE_API_SECRET, 'test_api_secret')
        self.assertEqual(config.GOOGLE_PROJECT_ID, 'test_project')
        self.assertEqual(config.GOOGLE_LOCATION, 'us-central1')
        self.assertTrue(config.SIMULATION_MODE)
        self.assertEqual(config.RISK_LEVEL, 'medium')
        self.assertEqual(config.DECISION_INTERVAL_MINUTES, 60)
    
    @patch.dict(os.environ, {
        'SIMULATION_MODE': 'false',
        'WEBSERVER_SYNC_ENABLED': 'true',
        'CONFIDENCE_THRESHOLD_BUY': '70',
        'CONFIDENCE_THRESHOLD_SELL': '75'
    })
    def test_boolean_and_numeric_config(self):
        """Test boolean and numeric configuration parsing"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Test boolean parsing
        self.assertFalse(config.SIMULATION_MODE)
        self.assertTrue(config.WEBSERVER_SYNC_ENABLED)
        
        # Test numeric parsing
        self.assertEqual(config.CONFIDENCE_THRESHOLD_BUY, 70)
        self.assertEqual(config.CONFIDENCE_THRESHOLD_SELL, 75)
    
    @patch.dict(os.environ, {
        'TRADING_PAIRS': 'BTC-USD,ETH-USD,SOL-USD',
        'SUPPORTED_ASSETS': 'BTC,ETH,SOL'
    })
    def test_list_config_parsing(self):
        """Test parsing of comma-separated list configurations"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Test list parsing
        expected_pairs = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        expected_assets = ['BTC', 'ETH', 'SOL']
        
        self.assertEqual(config.TRADING_PAIRS, expected_pairs)
        self.assertEqual(config.SUPPORTED_ASSETS, expected_assets)
    
    def test_config_defaults(self):
        """Test default configuration values when env vars are not set"""
        # Clear relevant environment variables
        env_vars_to_clear = [
            'SIMULATION_MODE', 'RISK_LEVEL', 'DECISION_INTERVAL_MINUTES',
            'WEBSERVER_SYNC_ENABLED', 'CONFIDENCE_THRESHOLD_BUY'
        ]
        
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
        
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Test default values (these should be defined in config.py)
        self.assertIsInstance(config.SIMULATION_MODE, bool)
        self.assertIn(config.RISK_LEVEL, ['low', 'medium', 'high'])
        self.assertIsInstance(config.DECISION_INTERVAL_MINUTES, int)
        self.assertGreater(config.DECISION_INTERVAL_MINUTES, 0)
    
    @patch.dict(os.environ, {
        'MIN_TRADE_USD': '10.50',
        'MAX_POSITION_SIZE_USD': '1000.00',
        'REBALANCE_THRESHOLD_PERCENT': '5.0'
    })
    def test_float_config_parsing(self):
        """Test parsing of float configuration values"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Test float parsing
        self.assertEqual(config.MIN_TRADE_USD, 10.50)
        self.assertEqual(config.MAX_POSITION_SIZE_USD, 1000.00)
        self.assertEqual(config.REBALANCE_THRESHOLD_PERCENT, 5.0)
    
    def test_config_validation(self):
        """Test configuration validation"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Test that required configurations exist
        required_configs = [
            'TRADING_PAIRS',
            'SIMULATION_MODE',
            'RISK_LEVEL',
            'DECISION_INTERVAL_MINUTES'
        ]
        
        for config_name in required_configs:
            self.assertTrue(hasattr(config, config_name), 
                          f"Required configuration {config_name} is missing")
    
    @patch.dict(os.environ, {
        'RISK_LEVEL': 'invalid_risk_level'
    })
    def test_invalid_config_handling(self):
        """Test handling of invalid configuration values"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        # This should either use a default value or raise an appropriate error
        try:
            import config
            # If it doesn't raise an error, it should use a valid default
            self.assertIn(config.RISK_LEVEL, ['low', 'medium', 'high'])
        except (ValueError, KeyError):
            # It's acceptable to raise an error for invalid config
            pass
    
    def test_config_class_initialization(self):
        """Test Config class initialization if it exists"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Test Config class if it exists
        if hasattr(config, 'Config'):
            config_instance = config.Config()
            
            # Verify Config class has required attributes
            required_attributes = [
                'SIMULATION_MODE',
                'RISK_LEVEL',
                'TRADING_PAIRS'
            ]
            
            for attr in required_attributes:
                self.assertTrue(hasattr(config_instance, attr),
                              f"Config class missing attribute {attr}")

class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration with other components"""
    
    @patch.dict(os.environ, {
        'SIMULATION_MODE': 'true',
        'TRADING_PAIRS': 'BTC-USD,ETH-USD',
        'RISK_LEVEL': 'low'
    })
    def test_config_integration_with_trading_strategy(self):
        """Test configuration integration with trading strategy"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Verify configuration values that would be used by trading strategy
        self.assertTrue(config.SIMULATION_MODE)
        self.assertEqual(len(config.TRADING_PAIRS), 2)
        self.assertEqual(config.RISK_LEVEL, 'low')
        
        # Test that configuration is suitable for trading strategy
        for pair in config.TRADING_PAIRS:
            self.assertIn('-', pair)  # Should be in format 'ASSET-USD'
            self.assertTrue(pair.endswith('USD'))  # Should be USD pairs
    
    @patch.dict(os.environ, {
        'WEBSERVER_SYNC_ENABLED': 'true',
        'WEBSERVER_SYNC_PATH': '/var/www/html/crypto-bot'
    })
    def test_config_integration_with_webserver(self):
        """Test configuration integration with web server sync"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Verify web server configuration
        self.assertTrue(config.WEBSERVER_SYNC_ENABLED)
        self.assertTrue(config.WEBSERVER_SYNC_PATH.startswith('/'))
        self.assertIn('crypto-bot', config.WEBSERVER_SYNC_PATH)
    
    @patch.dict(os.environ, {
        'GOOGLE_PROJECT_ID': 'test-project-123',
        'GOOGLE_LOCATION': 'us-central1',
        'LLM_MODEL': 'text-bison'
    })
    def test_config_integration_with_llm(self):
        """Test configuration integration with LLM analyzer"""
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Verify LLM configuration
        self.assertIsInstance(config.GOOGLE_PROJECT_ID, str)
        self.assertIsInstance(config.GOOGLE_LOCATION, str)
        self.assertIsInstance(config.LLM_MODEL, str)
        
        # Verify format
        self.assertNotEqual(config.GOOGLE_PROJECT_ID, '')
        self.assertIn('us-', config.GOOGLE_LOCATION)

if __name__ == '__main__':
    unittest.main()
