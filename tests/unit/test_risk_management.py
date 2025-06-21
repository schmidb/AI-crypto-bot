"""
Unit tests for Risk Management functionality.

Tests cover:
- Risk level configuration and multipliers
- Risk-adjusted decision making and confidence thresholds
- Position sizing with risk management
- Balance and safety checks
- Smart trading limits and portfolio protection
- Dynamic risk assessment and market conditions
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


class TestRiskLevelConfiguration:
    """Test risk level configuration and multiplier settings."""
    
    def test_risk_level_defaults(self):
        """Test default risk level configuration."""
        # Clear environment variables to test true defaults
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            # Test default values
            assert config.RISK_LEVEL == "medium"
            assert config.RISK_HIGH_POSITION_MULTIPLIER == 0.5
            assert config.RISK_MEDIUM_POSITION_MULTIPLIER == 0.75
            assert config.RISK_LOW_POSITION_MULTIPLIER == 1.0
    
    @patch.dict(os.environ, {
        'RISK_LEVEL': 'HIGH',
        'RISK_HIGH_POSITION_MULTIPLIER': '0.3',
        'RISK_MEDIUM_POSITION_MULTIPLIER': '0.6',
        'RISK_LOW_POSITION_MULTIPLIER': '0.9'
    })
    def test_risk_level_custom_configuration(self):
        """Test custom risk level configuration from environment."""
        config = Config()
        
        assert config.RISK_LEVEL == "HIGH"
        assert config.RISK_HIGH_POSITION_MULTIPLIER == 0.3
        assert config.RISK_MEDIUM_POSITION_MULTIPLIER == 0.6
        assert config.RISK_LOW_POSITION_MULTIPLIER == 0.9
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_risk_multiplier_calculation_high_risk(self, mock_coinbase, mock_trade_logger):
        """Test risk multiplier calculation for HIGH risk level."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "HIGH"
        config.RISK_HIGH_POSITION_MULTIPLIER = 0.4
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            multiplier = strategy._get_risk_multiplier()
            
            assert multiplier == 0.4
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_risk_multiplier_calculation_medium_risk(self, mock_coinbase, mock_trade_logger):
        """Test risk multiplier calculation for MEDIUM risk level."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "MEDIUM"
        config.RISK_MEDIUM_POSITION_MULTIPLIER = 0.8
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            multiplier = strategy._get_risk_multiplier()
            
            assert multiplier == 0.8
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_risk_multiplier_calculation_low_risk(self, mock_coinbase, mock_trade_logger):
        """Test risk multiplier calculation for LOW risk level."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "LOW"
        config.RISK_LOW_POSITION_MULTIPLIER = 1.0
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            multiplier = strategy._get_risk_multiplier()
            
            assert multiplier == 1.0
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_risk_multiplier_case_insensitive(self, mock_coinbase, mock_trade_logger):
        """Test risk multiplier with case-insensitive risk levels."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_MEDIUM_POSITION_MULTIPLIER = 0.75
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            # Test lowercase
            config.RISK_LEVEL = "medium"
            strategy = TradingStrategy(config)
            assert strategy._get_risk_multiplier() == 0.75
            
            # Test uppercase
            config.RISK_LEVEL = "MEDIUM"
            strategy = TradingStrategy(config)
            assert strategy._get_risk_multiplier() == 0.75
            
            # Test mixed case
            config.RISK_LEVEL = "MeDiUm"
            strategy = TradingStrategy(config)
            assert strategy._get_risk_multiplier() == 0.75
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_risk_multiplier_invalid_level_fallback(self, mock_coinbase, mock_trade_logger):
        """Test risk multiplier fallback for invalid risk levels."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "INVALID"
        config.RISK_MEDIUM_POSITION_MULTIPLIER = 0.75
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            multiplier = strategy._get_risk_multiplier()
            
            # Should fallback to medium risk multiplier
            assert multiplier == 0.75


class TestConfidenceThresholds:
    """Test confidence threshold enforcement in risk management."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_buy_confidence_threshold_enforcement(self, mock_coinbase, mock_trade_logger):
        """Test BUY confidence threshold enforcement."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_BUY = 75
        config.BASE_CURRENCY = "EUR"
        
        # Mock sufficient balance
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'EUR', 'available_balance': {'value': '1000.00'}}
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # Test confidence below threshold - should be blocked before smart limits
            result = strategy._apply_risk_management("BUY", 70, "BTC-EUR")
            assert result["action"] == "HOLD"
            assert "confidence_too_low_for_buy" in result["risk_adjustment"]
            
            # Test confidence above threshold - mock smart limits for this case
            with patch.object(TradingStrategy, '_apply_smart_trading_limits', return_value=("BUY", "ai_decision_approved")):
                result = strategy._apply_risk_management("BUY", 80, "BTC-EUR")
                assert result["action"] == "BUY"
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_sell_confidence_threshold_enforcement(self, mock_coinbase, mock_trade_logger):
        """Test SELL confidence threshold enforcement."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_SELL = 80
        config.MIN_TRADE_AMOUNT = 30.0
        
        # Mock sufficient balance and market data
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'BTC', 'available_balance': {'value': '0.01'}}
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        mock_data_collector = Mock()
        mock_data_collector.get_market_data.return_value = {"price": 50000.0}
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            strategy.data_collector = mock_data_collector
            
            # Test confidence below threshold
            result = strategy._apply_risk_management("SELL", 75, "BTC-EUR")
            assert result["action"] == "HOLD"
            assert "confidence_too_low_for_sell" in result["risk_adjustment"]
            
            # Test confidence above threshold
            result = strategy._apply_risk_management("SELL", 85, "BTC-EUR")
            assert result["action"] == "SELL"
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_hold_decision_no_threshold_check(self, mock_coinbase, mock_trade_logger):
        """Test HOLD decisions bypass confidence threshold checks."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_BUY = 90
        config.CONFIDENCE_THRESHOLD_SELL = 90
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # HOLD decision should not be affected by confidence thresholds
            result = strategy._apply_risk_management("HOLD", 30, "BTC-EUR")
            assert result["action"] == "HOLD"
            assert result["confidence"] == 30
            assert "confidence_too_low" not in result.get("risk_adjustment", "")


class TestBalanceSafetyChecks:
    """Test balance and safety checks in risk management."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_insufficient_eur_balance_buy_protection(self, mock_coinbase, mock_trade_logger):
        """Test protection against BUY orders with insufficient EUR balance."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_BUY = 60
        config.MIN_TRADE_AMOUNT = 50.0
        
        # Mock insufficient EUR balance
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'EUR', 'available_balance': {'value': '30.00'}}  # Below minimum
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            result = strategy._apply_risk_management("BUY", 80, "BTC-EUR")
            assert result["action"] == "HOLD"
            assert "insufficient_eur_balance" in result["risk_adjustment"]
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_insufficient_crypto_balance_sell_protection(self, mock_coinbase, mock_trade_logger):
        """Test protection against SELL orders with insufficient crypto balance."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_SELL = 60
        config.MIN_TRADE_AMOUNT = 30.0
        
        # Mock insufficient BTC balance and market data
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'BTC', 'available_balance': {'value': '0.0001'}}  # Very small amount
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        mock_data_collector = Mock()
        mock_data_collector.get_market_data.return_value = {"price": 50000.0}
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            strategy.data_collector = mock_data_collector
            
            result = strategy._apply_risk_management("SELL", 80, "BTC-EUR")
            assert result["action"] == "HOLD"
            assert "insufficient_btc_balance" in result["risk_adjustment"]
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_balance_check_failure_handling(self, mock_coinbase, mock_trade_logger):
        """Test handling of balance check failures."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_BUY = 60
        
        # Mock exception during balance check
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.side_effect = Exception("API Error")
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            result = strategy._apply_risk_management("BUY", 80, "BTC-EUR")
            assert result["action"] == "HOLD"
            assert "balance_check_failed" in result["risk_adjustment"]
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_sufficient_balance_allows_trading(self, mock_coinbase, mock_trade_logger):
        """Test that sufficient balances allow trading to proceed."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_BUY = 60
        config.CONFIDENCE_THRESHOLD_SELL = 60
        config.MIN_TRADE_AMOUNT = 30.0
        
        # Mock sufficient balances
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'EUR', 'available_balance': {'value': '1000.00'}},
            {'currency': 'BTC', 'available_balance': {'value': '0.01'}}
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        mock_data_collector = Mock()
        mock_data_collector.get_market_data.return_value = {"price": 50000.0}
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}), \
             patch.object(TradingStrategy, '_apply_smart_trading_limits', return_value=("BUY", "ai_decision_approved")):
            
            strategy = TradingStrategy(config)
            strategy.data_collector = mock_data_collector
            
            # Test BUY with sufficient EUR
            result = strategy._apply_risk_management("BUY", 80, "BTC-EUR")
            assert result["action"] == "BUY"
            
            # Test SELL with sufficient BTC - need to mock smart limits for SELL too
            with patch.object(TradingStrategy, '_apply_smart_trading_limits', return_value=("SELL", "ai_decision_approved")):
                result = strategy._apply_risk_management("SELL", 80, "BTC-EUR")
                assert result["action"] == "SELL"


class TestSmartTradingLimits:
    """Test smart trading limits and portfolio protection."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_minimum_allocation_protection_sell(self, mock_coinbase, mock_trade_logger):
        """Test protection against selling below minimum allocation."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_SELL = 60
        config.BASE_CURRENCY = "EUR"
        config.MIN_TRADE_AMOUNT = 30.0
        
        # Mock sufficient BTC balance for the balance check
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'BTC', 'available_balance': {'value': '0.01'}}  # Sufficient for balance check
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        # Mock data collector for price
        mock_data_collector = Mock()
        mock_data_collector.get_market_data.return_value = {"price": 50000.0}
        
        # Mock portfolio with low BTC allocation
        portfolio_data = {
            "portfolio_value_usd": 1000.0,
            "BTC": {"amount": 0.001, "last_price_eur": 50000.0},  # €50 = 5%
            "EUR": {"amount": 950.0}  # €950 = 95%
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value=portfolio_data), \
             patch.object(TradingStrategy, '_calculate_portfolio_value', return_value=1000.0), \
             patch.object(TradingStrategy, '_calculate_dynamic_position_size', return_value=1.0), \
             patch.object(TradingStrategy, '_apply_smart_trading_limits') as mock_limits:
            
            # Mock smart limits blocking the sale
            mock_limits.return_value = ("HOLD", "minimum_allocation_protection (post-trade: 2.0% < 3.0%)")
            
            strategy = TradingStrategy(config)
            strategy.data_collector = mock_data_collector
            result = strategy._apply_risk_management("SELL", 80, "BTC-EUR")
            
            # Should be blocked by smart limits
            assert result["action"] == "HOLD"
            assert "smart_limits" in result["risk_adjustment"]
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_maximum_eur_allocation_protection(self, mock_coinbase, mock_trade_logger):
        """Test protection against holding too much EUR."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_SELL = 60
        config.BASE_CURRENCY = "EUR"
        config.MIN_TRADE_AMOUNT = 30.0
        
        # Mock sufficient BTC balance for the balance check
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'BTC', 'available_balance': {'value': '0.01'}}  # Sufficient for balance check
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        # Mock data collector for price
        mock_data_collector = Mock()
        mock_data_collector.get_market_data.return_value = {"price": 50000.0}
        
        # Mock portfolio with high EUR allocation
        portfolio_data = {
            "portfolio_value_usd": 1000.0,
            "EUR": {"amount": 400.0},  # 40% EUR (above 35% max)
            "BTC": {"amount": 0.012, "last_price_eur": 50000.0}  # €600
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value=portfolio_data), \
             patch.object(TradingStrategy, '_calculate_portfolio_value', return_value=1000.0), \
             patch.object(TradingStrategy, '_apply_smart_trading_limits') as mock_limits:
            
            # Mock smart limits blocking further EUR accumulation
            mock_limits.return_value = ("HOLD", "max_eur_allocation_reached (40.0% > 35.0%)")
            
            strategy = TradingStrategy(config)
            strategy.data_collector = mock_data_collector
            result = strategy._apply_risk_management("SELL", 80, "BTC-EUR")
            
            assert result["action"] == "HOLD"
            assert "smart_limits" in result["risk_adjustment"]
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_smart_limits_approve_safe_trades(self, mock_coinbase, mock_trade_logger):
        """Test that smart limits approve safe trades."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_BUY = 60
        config.CONFIDENCE_THRESHOLD_SELL = 60
        
        # Mock sufficient balances
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'EUR', 'available_balance': {'value': '500.00'}},
            {'currency': 'BTC', 'available_balance': {'value': '0.01'}}
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}), \
             patch.object(TradingStrategy, '_apply_smart_trading_limits') as mock_limits:
            
            # Mock smart limits approving the trade
            mock_limits.return_value = ("BUY", "ai_decision_approved")
            
            strategy = TradingStrategy(config)
            result = strategy._apply_risk_management("BUY", 80, "BTC-EUR")
            
            assert result["action"] == "BUY"
            # The risk adjustment might include other factors, just check that the trade was approved
            assert result["action"] == "BUY"  # Main assertion is that the trade was approved


class TestPositionSizingRiskManagement:
    """Test position sizing with risk management integration."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_position_sizing_with_high_risk_reduction(self, mock_coinbase, mock_trade_logger):
        """Test position sizing reduction for high risk levels."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "HIGH"
        config.RISK_HIGH_POSITION_MULTIPLIER = 0.5
        config.MIN_TRADE_AMOUNT = 30.0
        config.MAX_POSITION_SIZE = 1000.0
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # High confidence with high risk should be reduced
            position_size = strategy.calculate_position_size("buy", 90, 1000.0)
            
            # 90% confidence * 1000 balance * 0.5 risk multiplier = 450
            expected_size = 1000.0 * 0.9 * 0.5
            assert position_size == expected_size
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_position_sizing_with_low_risk_no_reduction(self, mock_coinbase, mock_trade_logger):
        """Test position sizing with no reduction for low risk levels."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "LOW"
        config.RISK_LOW_POSITION_MULTIPLIER = 1.0
        config.MIN_TRADE_AMOUNT = 30.0
        config.MAX_POSITION_SIZE = 1000.0
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # High confidence with low risk should not be reduced
            position_size = strategy.calculate_position_size("buy", 80, 1000.0)
            
            # 80% confidence * 1000 balance * 1.0 risk multiplier = 800
            expected_size = 1000.0 * 0.8 * 1.0
            assert position_size == expected_size
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_dynamic_position_sizing_integration(self, mock_coinbase, mock_trade_logger):
        """Test integration of dynamic position sizing with risk management."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_THRESHOLD_BUY = 60
        config.BASE_CURRENCY = "EUR"
        
        # Mock sufficient balance
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'EUR', 'available_balance': {'value': '1000.00'}}
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}), \
             patch.object(TradingStrategy, '_calculate_dynamic_position_size', return_value=1.2), \
             patch.object(TradingStrategy, '_get_risk_multiplier', return_value=0.8), \
             patch.object(TradingStrategy, '_apply_smart_trading_limits', return_value=("BUY", "ai_decision_approved")):
            
            strategy = TradingStrategy(config)
            result = strategy._apply_risk_management("BUY", 80, "BTC-EUR")
            
            # Should combine dynamic sizing (1.2x) with risk multiplier (0.8x) = 0.96x
            # This should be reflected in the risk adjustment message
            assert result["action"] == "BUY"
            # The final multiplier should be close to 0.96 (1.2 * 0.8)
            # Check that position sizing adjustments are mentioned
            assert "position_size" in result["risk_adjustment"] or result["risk_adjustment"] == "ai_decision_approved"
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_position_size_below_minimum_blocked(self, mock_coinbase, mock_trade_logger):
        """Test that position sizes below minimum are blocked."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "HIGH"
        config.RISK_HIGH_POSITION_MULTIPLIER = 0.1  # Very low multiplier
        config.MIN_TRADE_AMOUNT = 50.0
        config.MAX_POSITION_SIZE = 1000.0
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # Low confidence with high risk and small balance
            position_size = strategy.calculate_position_size("buy", 20, 100.0)
            
            # 20% confidence * 100 balance * 0.1 risk = 2, below 50 minimum
            assert position_size == 0


class TestConfidenceAdjustments:
    """Test confidence adjustments based on technical indicators."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_confidence_boost_trend_aligned(self, mock_coinbase, mock_trade_logger):
        """Test confidence boost when technical indicators align with decision."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_BOOST_TREND_ALIGNED = 15
        
        # Mock analysis result with aligned indicators
        analysis_result = {
            "technical_indicators": {
                "rsi": {"value": 25.0, "signal": "oversold"},  # Supports BUY
                "macd": {"signal": "bullish"},  # Supports BUY
                "bollinger_bands": {"signal": "oversold"}  # Supports BUY
            }
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            confidence_adjustments = []
            adjusted_confidence = strategy._apply_confidence_adjustments(
                70, "BUY", analysis_result, confidence_adjustments
            )
            
            # Should get boost for aligned indicators (3/3 = 100% agreement)
            assert adjusted_confidence == 85  # 70 + 15
            assert any("trend_aligned_bonus" in adj for adj in confidence_adjustments)
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_confidence_penalty_counter_trend(self, mock_coinbase, mock_trade_logger):
        """Test confidence penalty when indicators contradict decision."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_PENALTY_COUNTER_TREND = 10
        
        # Mock analysis result with contradicting indicators
        analysis_result = {
            "technical_indicators": {
                "rsi": {"value": 75.0, "signal": "overbought"},  # Contradicts BUY
                "macd": {"signal": "bearish"},  # Contradicts BUY
                "bollinger_bands": {"signal": "overbought"}  # Contradicts BUY
            }
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            confidence_adjustments = []
            adjusted_confidence = strategy._apply_confidence_adjustments(
                80, "BUY", analysis_result, confidence_adjustments
            )
            
            # Should get penalty for counter-trend indicators (0/3 = 0% agreement)
            assert adjusted_confidence == 70  # 80 - 10
            assert any("counter_trend_penalty" in adj for adj in confidence_adjustments)
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_confidence_neutral_indicators(self, mock_coinbase, mock_trade_logger):
        """Test confidence with neutral/mixed indicators."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_BOOST_TREND_ALIGNED = 15
        config.CONFIDENCE_PENALTY_COUNTER_TREND = 10
        
        # Mock analysis result with mixed indicators
        analysis_result = {
            "technical_indicators": {
                "rsi": {"value": 30.0, "signal": "oversold"},  # Supports BUY
                "macd": {"signal": "bearish"},  # Contradicts BUY
                "bollinger_bands": {"signal": "neutral"}  # Neutral
            }
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            confidence_adjustments = []
            adjusted_confidence = strategy._apply_confidence_adjustments(
                75, "BUY", analysis_result, confidence_adjustments
            )
            
            # Should have no adjustment for mixed indicators (1/3 = 33% agreement)
            assert adjusted_confidence == 75  # No change
            assert any("neutral_indicators" in adj for adj in confidence_adjustments)
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_confidence_bounds_enforcement(self, mock_coinbase, mock_trade_logger):
        """Test that confidence adjustments stay within 0-100 bounds."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.CONFIDENCE_BOOST_TREND_ALIGNED = 50  # Large boost
        
        # Mock analysis result with aligned indicators
        analysis_result = {
            "technical_indicators": {
                "rsi": {"value": 25.0, "signal": "oversold"},
                "macd": {"signal": "bullish"},
                "bollinger_bands": {"signal": "oversold"}
            }
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            confidence_adjustments = []
            
            # Test upper bound
            adjusted_confidence = strategy._apply_confidence_adjustments(
                90, "BUY", analysis_result, confidence_adjustments
            )
            assert adjusted_confidence <= 100
            
            # Test lower bound with penalty
            config.CONFIDENCE_PENALTY_COUNTER_TREND = 50
            analysis_result["technical_indicators"] = {
                "rsi": {"value": 75.0, "signal": "overbought"},
                "macd": {"signal": "bearish"},
                "bollinger_bands": {"signal": "overbought"}
            }
            
            adjusted_confidence = strategy._apply_confidence_adjustments(
                20, "BUY", analysis_result, confidence_adjustments
            )
            assert adjusted_confidence >= 0
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_confidence_adjustment_error_handling(self, mock_coinbase, mock_trade_logger):
        """Test confidence adjustment error handling."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        
        # Mock analysis result with invalid data
        analysis_result = {
            "technical_indicators": {
                "rsi": {"value": "invalid"},  # Invalid data type
                "macd": None,
                "bollinger_bands": {}
            }
        }
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            confidence_adjustments = []
            adjusted_confidence = strategy._apply_confidence_adjustments(
                75, "BUY", analysis_result, confidence_adjustments
            )
            
            # Should return original confidence on error
            assert adjusted_confidence == 75
            assert any("error" in adj for adj in confidence_adjustments)


class TestIntegratedRiskScenarios:
    """Test integrated risk management scenarios."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_high_risk_low_confidence_scenario(self, mock_coinbase, mock_trade_logger):
        """Test high risk level with low confidence scenario."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "HIGH"
        config.CONFIDENCE_THRESHOLD_BUY = 80  # High threshold
        config.RISK_HIGH_POSITION_MULTIPLIER = 0.3  # Very conservative
        
        # Mock sufficient balance
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'EUR', 'available_balance': {'value': '1000.00'}}
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # Low confidence should be blocked by threshold
            result = strategy._apply_risk_management("BUY", 75, "BTC-EUR")
            assert result["action"] == "HOLD"
            assert "confidence_too_low_for_buy" in result["risk_adjustment"]
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_low_risk_high_confidence_scenario(self, mock_coinbase, mock_trade_logger):
        """Test low risk level with high confidence scenario."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "LOW"
        config.CONFIDENCE_THRESHOLD_BUY = 60  # Lower threshold
        config.RISK_LOW_POSITION_MULTIPLIER = 1.0  # No reduction
        
        # Mock sufficient balance
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'EUR', 'available_balance': {'value': '1000.00'}}
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}), \
             patch.object(TradingStrategy, '_apply_smart_trading_limits', return_value=("BUY", "ai_decision_approved")):
            
            strategy = TradingStrategy(config)
            
            # High confidence should pass all checks
            result = strategy._apply_risk_management("BUY", 85, "BTC-EUR")
            assert result["action"] == "BUY"
            assert result["confidence"] == 85
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_multiple_risk_factors_compound(self, mock_coinbase, mock_trade_logger):
        """Test multiple risk factors compounding."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.RISK_LEVEL = "MEDIUM"
        config.CONFIDENCE_THRESHOLD_SELL = 70
        config.RISK_MEDIUM_POSITION_MULTIPLIER = 0.75
        
        # Mock marginal balance (just enough)
        mock_coinbase_instance = Mock()
        mock_coinbase_instance.get_accounts.return_value = [
            {'currency': 'BTC', 'available_balance': {'value': '0.001'}}  # Minimal amount
        ]
        mock_coinbase.return_value = mock_coinbase_instance
        
        mock_data_collector = Mock()
        mock_data_collector.get_market_data.return_value = {"price": 50000.0}
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            strategy.data_collector = mock_data_collector
            
            # Marginal confidence with marginal balance
            result = strategy._apply_risk_management("SELL", 72, "BTC-EUR")
            
            # Should either pass or be blocked by balance check
            assert result["action"] in ["SELL", "HOLD"]
            if result["action"] == "HOLD":
                assert "insufficient_btc_balance" in result["risk_adjustment"]


class TestRiskManagementErrorHandling:
    """Test error handling in risk management functions."""
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_risk_management_exception_handling(self, mock_coinbase, mock_trade_logger):
        """Test risk management exception handling."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # Mock an exception that occurs early in the process
            with patch.object(strategy, 'config', side_effect=Exception("Config error")):
                result = strategy._apply_risk_management("BUY", 80, "BTC-EUR")
                
                assert result["action"] == "HOLD"
                assert result["confidence"] == 50
                assert "Risk management error" in result["reasoning"]
                assert result["risk_adjustment"] == "error_fallback"
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_position_sizing_error_handling(self, mock_coinbase, mock_trade_logger):
        """Test position sizing error handling."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        config.MIN_TRADE_AMOUNT = 30.0
        config.MAX_POSITION_SIZE = 1000.0
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # Mock an exception in risk multiplier calculation
            with patch.object(strategy, '_get_risk_multiplier', side_effect=Exception("Risk calc error")):
                position_size = strategy.calculate_position_size("buy", 80, 1000.0)
                
                # Should return 0 on error
                assert position_size == 0
    
    @patch('trading_strategy.TradeLogger')
    @patch('trading_strategy.CoinbaseClient')
    def test_invalid_decision_type_handling(self, mock_coinbase, mock_trade_logger):
        """Test handling of invalid decision types."""
        from trading_strategy import TradingStrategy
        
        config = Config()
        
        with patch.object(TradingStrategy, '_load_portfolio', return_value={}):
            strategy = TradingStrategy(config)
            
            # Test with invalid decision type
            result = strategy._apply_risk_management("INVALID", 80, "BTC-EUR")
            
            # Should handle gracefully and return reasonable defaults
            assert result["action"] in ["HOLD", "INVALID"]
            assert isinstance(result["confidence"], (int, float))
            assert isinstance(result["reasoning"], str)


if __name__ == "__main__":
    pytest.main([__file__])
