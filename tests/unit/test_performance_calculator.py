"""
Unit tests for PerformanceCalculator class

Tests the performance calculation functionality including return calculations,
risk metrics, and trading performance analysis.
"""

import pytest
import math
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from utils.performance.performance_calculator import PerformanceCalculator


class TestPerformanceCalculatorInitialization:
    """Test PerformanceCalculator initialization"""
    
    def test_performance_calculator_initialization(self):
        """Test basic PerformanceCalculator initialization"""
        calculator = PerformanceCalculator()
        assert calculator is not None


class TestReturnCalculations:
    """Test return calculation functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.calculator = PerformanceCalculator()
        
        # Create test snapshots
        base_time = datetime.utcnow()
        self.test_snapshots = [
            {
                "timestamp": (base_time - timedelta(days=30)).isoformat(),
                "total_value_eur": 1000.0
            },
            {
                "timestamp": (base_time - timedelta(days=15)).isoformat(),
                "total_value_eur": 1050.0
            },
            {
                "timestamp": base_time.isoformat(),
                "total_value_eur": 1100.0
            }
        ]
    
    def test_total_return_calculation_positive_returns(self):
        """Test total return calculation with positive returns"""
        result = self.calculator.calculate_total_return(self.test_snapshots)
        
        assert "error" not in result
        assert result["initial_value"] == 1000.0
        assert result["final_value"] == 1100.0
        assert result["absolute_return"] == 100.0
        assert result["percentage_return"] == 10.0  # (1100-1000)/1000 * 100
        assert result["days_elapsed"] == 30
        assert "annualized_return" in result
    
    def test_total_return_calculation_negative_returns(self):
        """Test total return calculation with negative returns"""
        negative_snapshots = [
            {
                "timestamp": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "total_value_eur": 1000.0
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "total_value_eur": 900.0
            }
        ]
        
        result = self.calculator.calculate_total_return(negative_snapshots)
        
        assert "error" not in result
        assert result["absolute_return"] == -100.0
        assert result["percentage_return"] == -10.0  # (900-1000)/1000 * 100
    
    def test_total_return_calculation_with_insufficient_data(self):
        """Test total return calculation with insufficient data"""
        single_snapshot = [{"timestamp": datetime.utcnow().isoformat(), "total_value_eur": 1000.0}]
        
        result = self.calculator.calculate_total_return(single_snapshot)
        
        assert "error" in result
        assert "Insufficient data" in result["error"]
    
    def test_annualized_return_calculation(self):
        """Test annualized return calculation"""
        # Create snapshots spanning exactly 1 year with 20% total return
        base_time = datetime.utcnow()
        yearly_snapshots = [
            {
                "timestamp": (base_time - timedelta(days=365)).isoformat(),
                "total_value_eur": 1000.0
            },
            {
                "timestamp": base_time.isoformat(),
                "total_value_eur": 1200.0
            }
        ]
        
        result = self.calculator.calculate_total_return(yearly_snapshots)
        
        assert "error" not in result
        assert result["percentage_return"] == 20.0
        # Annualized return should be approximately 20% for 1-year period
        assert abs(result["annualized_return"] - 20.0) < 1.0
    
    def test_compound_annual_growth_rate(self):
        """Test CAGR calculation for multi-year periods"""
        # Create snapshots spanning 2 years
        base_time = datetime.utcnow()
        multi_year_snapshots = [
            {
                "timestamp": (base_time - timedelta(days=730)).isoformat(),  # 2 years ago
                "total_value_eur": 1000.0
            },
            {
                "timestamp": base_time.isoformat(),
                "total_value_eur": 1440.0  # 44% total return over 2 years
            }
        ]
        
        result = self.calculator.calculate_total_return(multi_year_snapshots)
        
        assert "error" not in result
        # CAGR should be approximately 20% ((1440/1000)^(1/2) - 1)
        expected_cagr = ((1440/1000) ** (1/2) - 1) * 100
        assert abs(result["annualized_return"] - expected_cagr) < 1.0
    
    def test_return_calculation_edge_cases(self):
        """Test return calculation edge cases"""
        # Test with zero initial value
        zero_initial_snapshots = [
            {"timestamp": datetime.utcnow().isoformat(), "total_value_eur": 0.0},
            {"timestamp": (datetime.utcnow() + timedelta(days=1)).isoformat(), "total_value_eur": 100.0}
        ]
        
        result = self.calculator.calculate_total_return(zero_initial_snapshots)
        assert "error" in result
        assert "Invalid initial" in result["error"]


class TestTradingPerformanceCalculations:
    """Test trading performance calculation functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.calculator = PerformanceCalculator()
        
        # Create test trade history
        base_time = datetime.utcnow()
        self.test_trades = [
            {
                "timestamp": (base_time - timedelta(days=10)).isoformat(),
                "action": "BUY",
                "crypto_amount": 0.001,
                "price": 50000.0,
                "total_fees": 0.30,
                "trade_amount_usd": 50.0
            },
            {
                "timestamp": (base_time - timedelta(days=5)).isoformat(),
                "action": "SELL",
                "crypto_amount": 0.0005,
                "price": 52000.0,
                "total_fees": 0.15,
                "trade_amount_usd": 26.0
            },
            {
                "timestamp": (base_time - timedelta(days=2)).isoformat(),
                "action": "BUY",
                "crypto_amount": 0.0008,
                "price": 48000.0,
                "total_fees": 0.20,
                "trade_amount_usd": 38.4
            }
        ]
    
    def test_trading_performance_basic_calculation(self):
        """Test basic trading performance calculation"""
        result = self.calculator.calculate_trading_performance(self.test_trades)
        
        assert "error" not in result
        assert result["total_trades"] == 3
        assert abs(result["total_fees"] - 0.65) < 0.001  # Handle floating point precision
        assert "win_rate" in result
        assert "net_profit" in result
    
    def test_trading_performance_with_period_filter(self):
        """Test trading performance with period filtering"""
        # Filter to last 7 days
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        result = self.calculator.calculate_trading_performance(
            self.test_trades, period_start=period_start
        )
        
        assert "error" not in result
        # Should only include trades from last 7 days (2 trades)
        assert result["total_trades"] == 2
    
    def test_trading_performance_with_no_trades(self):
        """Test trading performance with empty trade history"""
        result = self.calculator.calculate_trading_performance([])
        
        assert "error" in result
        assert "No trade history" in result["error"]
    
    def test_win_rate_calculation(self):
        """Test win rate calculation"""
        # Mock trade P&L calculation to return known values
        with patch.object(self.calculator, '_calculate_trade_pnl') as mock_pnl:
            # First trade: profit, second: loss, third: profit
            mock_pnl.side_effect = [10.0, -5.0, 8.0]
            
            result = self.calculator.calculate_trading_performance(self.test_trades)
            
            assert "error" not in result
            assert result["winning_trades"] == 2
            assert result["losing_trades"] == 1
            assert result["win_rate"] == (2/3) * 100  # 66.67%
    
    def test_profit_factor_calculation(self):
        """Test profit factor calculation"""
        with patch.object(self.calculator, '_calculate_trade_pnl') as mock_pnl:
            # Total profit: 15.0, Total loss: 8.0
            mock_pnl.side_effect = [10.0, -8.0, 5.0]
            
            result = self.calculator.calculate_trading_performance(self.test_trades)
            
            assert "error" not in result
            assert result["total_profit"] == 15.0
            assert result["total_loss"] == 8.0
            assert result["profit_factor"] == 15.0 / 8.0  # 1.875


class TestRiskMetrics:
    """Test risk metrics calculation functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.calculator = PerformanceCalculator()
        
        # Create test snapshots with varying values for risk calculation
        base_time = datetime.utcnow()
        self.risk_snapshots = []
        
        # Create daily snapshots with some volatility
        values = [1000, 1020, 980, 1050, 990, 1030, 1010, 1070, 950, 1100]
        for i, value in enumerate(values):
            snapshot = {
                "timestamp": (base_time - timedelta(days=len(values)-i-1)).isoformat(),
                "total_value_eur": float(value)
            }
            self.risk_snapshots.append(snapshot)
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation"""
        result = self.calculator.calculate_risk_metrics(self.risk_snapshots)
        
        assert "error" not in result
        assert "sharpe_ratio" in result
        assert "volatility_annualized" in result
        assert result["return_samples"] > 0
    
    def test_maximum_drawdown_calculation(self):
        """Test maximum drawdown calculation"""
        result = self.calculator.calculate_risk_metrics(self.risk_snapshots)
        
        assert "error" not in result
        assert "max_drawdown" in result
        assert result["max_drawdown"] >= 0  # Drawdown should be positive percentage
    
    def test_volatility_calculation(self):
        """Test volatility calculation"""
        result = self.calculator.calculate_risk_metrics(self.risk_snapshots)
        
        assert "error" not in result
        assert "volatility_daily" in result
        assert "volatility_annualized" in result
        assert result["volatility_daily"] >= 0
        assert result["volatility_annualized"] >= 0
    
    def test_sortino_ratio_calculation(self):
        """Test Sortino ratio calculation"""
        result = self.calculator.calculate_risk_metrics(self.risk_snapshots)
        
        assert "error" not in result
        assert "sortino_ratio" in result
        assert "downside_deviation" in result
    
    def test_risk_metrics_with_insufficient_data(self):
        """Test risk metrics with insufficient data"""
        insufficient_snapshots = [
            {"timestamp": datetime.utcnow().isoformat(), "total_value_eur": 1000.0}
        ]
        
        result = self.calculator.calculate_risk_metrics(insufficient_snapshots)
        
        assert "error" in result
        assert "Insufficient data" in result["error"]


class TestMarketPerformanceCalculations:
    """Test market performance calculation functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.calculator = PerformanceCalculator()
        
        # Create test data
        base_time = datetime.utcnow()
        self.market_snapshots = [
            {
                "timestamp": (base_time - timedelta(days=30)).isoformat(),
                "total_value_eur": 1000.0
            },
            {
                "timestamp": base_time.isoformat(),
                "total_value_eur": 1200.0
            }
        ]
        
        self.market_trades = [
            {
                "timestamp": (base_time - timedelta(days=15)).isoformat(),
                "action": "BUY",
                "total_fees": 0.50
            }
        ]
    
    def test_market_vs_trading_performance_separation(self):
        """Test separation of market vs trading performance"""
        with patch.object(self.calculator, 'calculate_total_return') as mock_total:
            with patch.object(self.calculator, 'calculate_trading_performance') as mock_trading:
                # Mock total return of 20%
                mock_total.return_value = {
                    "percentage_return": 20.0,
                    "initial_value": 1000.0
                }
                
                # Mock trading return of 5% (€50 profit on €1000 initial)
                mock_trading.return_value = {
                    "net_profit": 50.0
                }
                
                result = self.calculator.calculate_market_performance(
                    self.market_snapshots, self.market_trades
                )
                
                assert "error" not in result
                assert result["total_return"] == 20.0
                assert result["trading_return"] == 5.0  # 50/1000 * 100
                assert result["market_return"] == 15.0  # 20 - 5
    
    def test_market_performance_with_no_trading(self):
        """Test market performance calculation with no trading activity"""
        result = self.calculator.calculate_market_performance(self.market_snapshots, [])
        
        assert "error" not in result
        assert "total_return" in result
        assert "market_return" in result
    
    def test_market_performance_contribution_calculation(self):
        """Test market performance contribution percentage"""
        with patch.object(self.calculator, 'calculate_total_return') as mock_total:
            with patch.object(self.calculator, 'calculate_trading_performance') as mock_trading:
                mock_total.return_value = {"percentage_return": 10.0, "initial_value": 1000.0}
                mock_trading.return_value = {"net_profit": 30.0}  # 3% trading return
                
                result = self.calculator.calculate_market_performance(
                    self.market_snapshots, self.market_trades
                )
                
                assert "error" not in result
                assert "market_contribution" in result
                assert "trading_contribution" in result
                # Market: 7%, Trading: 3%, so contributions should be 70% and 30%
                assert abs(result["market_contribution"] - 70.0) < 1.0
                assert abs(result["trading_contribution"] - 30.0) < 1.0


class TestPerformanceCalculatorUtilities:
    """Test utility functions in PerformanceCalculator"""
    
    def setup_method(self):
        """Set up test environment"""
        self.calculator = PerformanceCalculator()
    
    def test_max_drawdown_calculation_utility(self):
        """Test maximum drawdown calculation utility function"""
        # Test snapshots with known drawdown
        test_snapshots = [
            {"total_value_eur": 1000.0},  # Peak
            {"total_value_eur": 1100.0},  # New peak
            {"total_value_eur": 900.0},   # Drawdown: (1100-900)/1100 = 18.18%
            {"total_value_eur": 950.0},   # Recovery
            {"total_value_eur": 1200.0}   # New peak
        ]
        
        max_drawdown = self.calculator._calculate_max_drawdown(test_snapshots)
        
        # Should be approximately 18.18%
        expected_drawdown = ((1100 - 900) / 1100) * 100
        assert abs(max_drawdown - expected_drawdown) < 0.1
    
    def test_trade_pnl_calculation_utility(self):
        """Test trade P&L calculation utility function"""
        test_trade = {
            "action": "BUY",
            "crypto_amount": 0.001,
            "price": 50000.0
        }
        
        # Currently returns 0 as placeholder - test that it doesn't crash
        pnl = self.calculator._calculate_trade_pnl(test_trade)
        assert isinstance(pnl, float)
    
    def test_trade_filtering_by_period(self):
        """Test trade filtering by date period"""
        base_time = datetime.utcnow()
        test_trades = [
            {"timestamp": (base_time - timedelta(days=5)).isoformat()},
            {"timestamp": (base_time - timedelta(days=15)).isoformat()},
            {"timestamp": (base_time - timedelta(days=25)).isoformat()}
        ]
        
        # Filter to last 10 days
        start_date = (base_time - timedelta(days=10)).isoformat()
        
        filtered = self.calculator._filter_trades_by_period(test_trades, start_date, None)
        
        # Should only include the first trade (5 days ago)
        assert len(filtered) == 1
        assert filtered[0]["timestamp"] == test_trades[0]["timestamp"]
    
    def test_annualized_return_utility(self):
        """Test annualized return utility function"""
        test_snapshots = [
            {
                "timestamp": (datetime.utcnow() - timedelta(days=365)).isoformat(),
                "total_value_eur": 1000.0
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "total_value_eur": 1200.0
            }
        ]
        
        annualized_return = self.calculator.calculate_annualized_return(test_snapshots)
        
        # Should be approximately 20% for 20% return over 1 year
        assert abs(annualized_return - 20.0) < 1.0
    
    def test_win_rate_utility(self):
        """Test win rate utility function"""
        test_trades = [
            {"action": "BUY", "timestamp": datetime.utcnow().isoformat()}
        ]
        
        # Mock the trading performance calculation
        with patch.object(self.calculator, 'calculate_trading_performance') as mock_trading:
            mock_trading.return_value = {"win_rate": 75.0}
            
            win_rate = self.calculator.calculate_win_rate(test_trades)
            assert win_rate == 75.0


if __name__ == '__main__':
    pytest.main([__file__])
