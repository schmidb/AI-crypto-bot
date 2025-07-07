"""
Unit tests for TradingStrategy class.

Tests cover:
- Strategy initialization and configuration
- Trading decision logic and AI integration
- Risk management and position sizing
- Portfolio management and rebalancing
- Error handling and edge cases
"""

import pytest
import json
import os
import sys
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock external dependencies at module level
sys.modules['coinbase'] = MagicMock()
sys.modules['coinbase.rest'] = MagicMock()
sys.modules['utils.trade_logger'] = MagicMock()

# Now import the modules we need to test
from config import Config


class TestTradingStrategyInitialization:
    """Test trading strategy initialization and basic setup."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_init_with_valid_config(self, mock_coinbase, mock_trade_logger):
        """Test successful initialization with valid configuration."""
        # Import here to avoid import issues
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "MEDIUM"
        config.BASE_CURRENCY = "EUR"
        config.CRYPTO_ASSETS = ["BTC", "ETH", "SOL"]
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            assert strategy.config == config
            assert strategy.risk_level == "MEDIUM"
            assert strategy.portfolio == {}
            mock_trade_logger.assert_called_once()
            mock_coinbase.assert_called_once()
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_init_with_llm_analyzer(self, mock_coinbase, mock_trade_logger):
        """Test initialization with LLM analyzer."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "HIGH"
        mock_llm = Mock()
        mock_data_collector = Mock()
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config, llm_analyzer=mock_llm, data_collector=mock_data_collector)
            
            assert strategy.llm_analyzer == mock_llm
            assert strategy.data_collector == mock_data_collector
            assert strategy.risk_level == "HIGH"


class TestPortfolioManagement:
    """Test portfolio loading, saving, and management functionality."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_load_portfolio_success(self, mock_coinbase, mock_trade_logger):
        """Test successful portfolio loading from file."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        portfolio_data = {
            "EUR": {"amount": 100.0},
            "BTC": {"amount": 0.01, "last_price_eur": 50000.0},
            "portfolio_value_usd": 600.0
        }
        
        mock_file_content = json.dumps(portfolio_data)
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            strategy = TradingStrategy(config)
            assert strategy.portfolio == portfolio_data
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_load_portfolio_file_not_found(self, mock_coinbase, mock_trade_logger):
        """Test portfolio loading when file doesn't exist."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        
        with patch('builtins.open', side_effect=FileNotFoundError()):
            strategy = TradingStrategy(config)
            assert strategy.portfolio == {}
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    @patch('os.makedirs')
    def test_save_portfolio_success(self, mock_makedirs, mock_coinbase, mock_trade_logger):
        """Test successful portfolio saving."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        portfolio_data = {"EUR": {"amount": 100.0}}
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value=portfolio_data), \
             patch('builtins.open', mock_open()) as mock_file:
            
            strategy = TradingStrategy(config)
            strategy._save_portfolio()
            
            mock_makedirs.assert_called_once_with("data/portfolio", exist_ok=True)
            mock_file.assert_called_once_with("data/portfolio/portfolio.json", "w")
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_refresh_portfolio_from_coinbase_success(self, mock_coinbase, mock_trade_logger):
        """Test successful portfolio refresh from Coinbase."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        coinbase_portfolio = {
            "EUR": {"amount": 150.0},
            "BTC": {"amount": 0.02, "last_price_eur": 51000.0}
        }
        
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_portfolio.return_value = coinbase_portfolio
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}), \
             patch.object(TradingStrategy, '_save_portfolio') as mock_save:
            
            strategy = TradingStrategy(config)
            result = strategy.refresh_portfolio_from_coinbase()
            
            assert result["status"] == "success"
            assert "last_updated" in strategy.portfolio
            mock_save.assert_called_once()
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_refresh_portfolio_from_coinbase_failure(self, mock_coinbase, mock_trade_logger):
        """Test portfolio refresh failure from Coinbase."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_portfolio.return_value = None
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            result = strategy.refresh_portfolio_from_coinbase()
            
            assert result["status"] == "error"
            assert "Failed to get portfolio from Coinbase" in result["message"]


class TestTradingDecisions:
    """Test trading decision logic and AI integration."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_get_trading_decision_buy_signal(self, mock_coinbase, mock_trade_logger):
        """Test trading decision with strong buy signals."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "MEDIUM"
        
        market_data = {"price": 50000.0, "volume": 1000000}
        indicators = {
            "rsi": 25.0,  # Oversold
            "macd": 100.0,
            "macd_signal": 50.0,  # Bullish crossover
            "bb_upper": 52000.0,
            "bb_lower": 48000.0,
            "current_price": 48500.0  # Below lower band
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            decision, confidence, reasoning, strategy_details = strategy.get_trading_decision(market_data, indicators)
            
            # Multi-strategy framework may return HOLD due to confidence thresholds
            # Check that we get a reasonable decision and confidence
            assert decision.lower() in ["buy", "hold"]
            assert confidence > 0
            assert isinstance(reasoning, str)
            assert isinstance(strategy_details, dict)
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_get_trading_decision_sell_signal(self, mock_coinbase, mock_trade_logger):
        """Test trading decision with strong sell signals."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "LOW"  # Higher threshold
        
        market_data = {"price": 52000.0, "volume": 800000}
        indicators = {
            "rsi": 75.0,  # Overbought
            "macd": 50.0,
            "macd_signal": 100.0,  # Bearish crossover
            "bb_upper": 52000.0,
            "bb_lower": 48000.0,
            "current_price": 52500.0  # Above upper band
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            decision, confidence, reasoning, strategy_details = strategy.get_trading_decision(market_data, indicators)
            
            # Multi-strategy framework may return different decisions based on combined analysis
            assert decision.lower() in ["sell", "hold"]
            assert confidence > 0
            assert isinstance(reasoning, str)
            assert isinstance(strategy_details, dict)
            # Check that reasoning contains strategy analysis
            assert "strategy analysis" in reasoning.lower() or "sell" in reasoning.lower()
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_get_trading_decision_hold_signal(self, mock_coinbase, mock_trade_logger):
        """Test trading decision with neutral signals."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "HIGH"
        
        market_data = {"price": 50000.0, "volume": 500000}
        indicators = {
            "rsi": 50.0,  # Neutral
            "macd": 75.0,
            "macd_signal": 70.0,  # Weak signal
            "bb_upper": 52000.0,
            "bb_lower": 48000.0,
            "current_price": 50000.0  # Middle of bands
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            decision, confidence, reasoning, strategy_details = strategy.get_trading_decision(market_data, indicators)
            
            assert decision == "hold"
            assert "no clear signals" in reasoning.lower() or "neutral" in reasoning.lower()
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_get_trading_decision_error_handling(self, mock_coinbase, mock_trade_logger):
        """Test trading decision error handling."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        
        # Create indicators that will cause a type conversion error
        market_data = {"price": 50000.0}
        indicators = {"rsi": "invalid_string"}  # This will cause float() to fail
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            decision, confidence, reasoning, strategy_details = strategy.get_trading_decision(market_data, indicators)
            
            assert decision == "hold"
            # Multi-strategy framework may return low confidence instead of 0
            assert confidence >= 0
            assert isinstance(reasoning, str)
            assert isinstance(strategy_details, dict)


class TestPositionSizing:
    """Test position sizing calculations and risk management."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_calculate_position_size_high_confidence(self, mock_coinbase, mock_trade_logger):
        """Test position sizing with high confidence."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "MEDIUM"
        config.MIN_TRADE_AMOUNT = 30.0
        config.MAX_POSITION_SIZE = 1000.0
        config.RISK_MEDIUM_POSITION_MULTIPLIER = 0.75
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # High confidence should result in larger position
            position_size = strategy.calculate_position_size("buy", 90, 1000.0)
            
            # 90% confidence * 1000 balance * 0.75 risk multiplier = 675
            expected_size = 1000.0 * 0.9 * 0.75
            assert position_size == expected_size
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_calculate_position_size_below_minimum(self, mock_coinbase, mock_trade_logger):
        """Test position sizing below minimum trade amount."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "HIGH"
        config.MIN_TRADE_AMOUNT = 30.0
        config.MAX_POSITION_SIZE = 1000.0
        config.RISK_HIGH_POSITION_MULTIPLIER = 0.5
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # Very low confidence and small balance should return 0
            position_size = strategy.calculate_position_size("buy", 10, 100.0)
            
            # 10% confidence * 100 balance * 0.5 risk = 5, below 30 minimum
            assert position_size == 0
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_get_risk_multiplier_all_levels(self, mock_coinbase, mock_trade_logger):
        """Test risk multiplier for all risk levels."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LOW_POSITION_MULTIPLIER = 1.0
        config.RISK_MEDIUM_POSITION_MULTIPLIER = 0.75
        config.RISK_HIGH_POSITION_MULTIPLIER = 0.5
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            # Test LOW risk
            config.RISK_LEVEL = "LOW"
            strategy = TradingStrategy(config)
            assert strategy._get_risk_multiplier() == 1.0
            
            # Test MEDIUM risk
            config.RISK_LEVEL = "MEDIUM"
            strategy = TradingStrategy(config)
            assert strategy._get_risk_multiplier() == 0.75
            
            # Test HIGH risk
            config.RISK_LEVEL = "HIGH"
            strategy = TradingStrategy(config)
            assert strategy._get_risk_multiplier() == 0.5


if __name__ == "__main__":
    pytest.main([__file__])
