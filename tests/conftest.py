"""
Shared pytest fixtures and configuration for AI Crypto Trading Bot tests.

This file contains common fixtures, test utilities, and configuration
that can be used across all test modules.
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Test environment setup
os.environ['TESTING'] = 'true'
os.environ['SIMULATION_MODE'] = 'true'


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration settings."""
    return {
        'BASE_CURRENCY': 'EUR',
        'TRADING_PAIRS': ['BTC-EUR', 'ETH-EUR', 'SOL-EUR'],
        'RISK_LEVEL': 'MEDIUM',
        'SIMULATION_MODE': True,
        'CONFIDENCE_THRESHOLD_BUY': 70,
        'CONFIDENCE_THRESHOLD_SELL': 70,
        'MIN_TRADE_AMOUNT': 30.0,
        'MAX_POSITION_SIZE': 1000.0,
        'TARGET_CRYPTO_ALLOCATION': 90,
        'TARGET_BASE_ALLOCATION': 10,
    }


@pytest.fixture
def mock_coinbase_client():
    """Mock Coinbase client for testing."""
    client = Mock()
    
    # Mock account balance
    client.get_accounts.return_value = {
        'accounts': [
            {'currency': 'EUR', 'available_balance': {'value': '100.00'}},
            {'currency': 'BTC', 'available_balance': {'value': '0.01'}},
            {'currency': 'ETH', 'available_balance': {'value': '0.1'}},
            {'currency': 'SOL', 'available_balance': {'value': '1.0'}},
        ]
    }
    
    # Mock product prices
    client.get_product.return_value = {
        'price': '50000.00',
        'quote_currency': 'EUR',
        'base_currency': 'BTC'
    }
    
    # Mock order placement
    client.create_order.return_value = {
        'order_id': 'test-order-123',
        'status': 'FILLED',
        'filled_size': '0.001',
        'filled_value': '50.00'
    }
    
    return client


@pytest.fixture
def mock_llm_analyzer():
    """Mock LLM analyzer for testing."""
    analyzer = Mock()
    
    # Mock analysis result
    analyzer.analyze_market.return_value = {
        'decision': 'BUY',
        'confidence': 75,
        'reasoning': 'Test analysis reasoning',
        'technical_indicators': {
            'rsi': 45.0,
            'macd': 0.5,
            'bollinger_position': 0.3
        },
        'risk_assessment': 'MEDIUM'
    }
    
    return analyzer


@pytest.fixture
def mock_data_collector():
    """Mock data collector for testing."""
    collector = Mock()
    
    # Mock historical data
    collector.get_historical_data.return_value = {
        'timestamps': [datetime.now() - timedelta(hours=i) for i in range(24)],
        'prices': [50000 + i * 100 for i in range(24)],
        'volumes': [1000 + i * 10 for i in range(24)]
    }
    
    # Mock technical indicators
    collector.calculate_rsi.return_value = 45.0
    collector.calculate_macd.return_value = {'macd': 0.5, 'signal': 0.3, 'histogram': 0.2}
    collector.calculate_bollinger_bands.return_value = {
        'upper': 52000, 'middle': 50000, 'lower': 48000
    }
    
    return collector


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return {
        'balances': {
            'EUR': 100.0,
            'BTC': 0.01,
            'ETH': 0.1,
            'SOL': 1.0
        },
        'prices': {
            'BTC-EUR': 50000.0,
            'ETH-EUR': 3000.0,
            'SOL-EUR': 100.0
        },
        'portfolio_value_eur': 1000.0,
        'initial_value_eur': 900.0,
        'last_updated': datetime.now().isoformat()
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return [
        {
            'timestamp': datetime.now().isoformat(),
            'product_id': 'BTC-EUR',
            'action': 'BUY',
            'amount': 0.001,
            'price': 50000.0,
            'trade_amount_eur': 50.0,
            'confidence': 75,
            'status': 'executed',
            'order_id': 'test-order-123'
        },
        {
            'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
            'product_id': 'ETH-EUR',
            'action': 'SELL',
            'amount': 0.01,
            'price': 3000.0,
            'trade_amount_eur': 30.0,
            'confidence': 80,
            'status': 'executed',
            'order_id': 'test-order-124'
        }
    ]


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subdirectories
        os.makedirs(os.path.join(temp_dir, 'portfolio'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'trades'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'cache'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'reports'), exist_ok=True)
        yield temp_dir


@pytest.fixture
def mock_notification_service():
    """Mock notification service for testing."""
    service = Mock()
    service.send_notification.return_value = True
    service.send_trade_notification.return_value = True
    service.send_error_notification.return_value = True
    return service


@pytest.fixture
def mock_dashboard_updater():
    """Mock dashboard updater for testing."""
    updater = Mock()
    updater.update_portfolio_data.return_value = True
    updater.update_trade_history.return_value = True
    updater.update_market_data.return_value = True
    return updater


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    test_env_vars = {
        'TESTING': 'true',
        'SIMULATION_MODE': 'true',
        'COINBASE_API_KEY': 'test-api-key',
        'COINBASE_API_SECRET': 'test-api-secret',
        'GOOGLE_CLOUD_PROJECT': 'test-project',
        'GOOGLE_APPLICATION_CREDENTIALS': 'test-credentials.json',
        'NOTIFICATIONS_ENABLED': 'false',
        'WEBSERVER_SYNC_ENABLED': 'false'
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_time():
    """Mock time-related functions for consistent testing."""
    with pytest.MonkeyPatch.context() as m:
        fixed_time = datetime(2023, 6, 15, 12, 0, 0)
        m.setattr('datetime.datetime.now', lambda: fixed_time)
        yield fixed_time


# Utility functions for tests
def create_test_file(directory: str, filename: str, content: Dict[str, Any]) -> str:
    """Create a test file with JSON content."""
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w') as f:
        json.dump(content, f, indent=2)
    return filepath


def assert_trade_executed(trade_data: Dict[str, Any], expected_action: str):
    """Assert that a trade was executed with expected parameters."""
    assert trade_data['action'] == expected_action
    assert trade_data['status'] == 'executed'
    assert 'order_id' in trade_data
    assert trade_data['confidence'] >= 70


def assert_portfolio_valid(portfolio_data: Dict[str, Any]):
    """Assert that portfolio data is valid."""
    assert 'balances' in portfolio_data
    assert 'prices' in portfolio_data
    assert 'portfolio_value_eur' in portfolio_data
    assert portfolio_data['portfolio_value_eur'] > 0


# Test markers for different test categories
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]
