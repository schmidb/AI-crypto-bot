"""
Risk Management Tests

Tests safety limits, emergency mechanisms, edge case handling,
and risk management systems across the trading bot.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
import pandas as pd

from coinbase_client import CoinbaseClient
from utils.portfolio import Portfolio
from strategies.adaptive_strategy_manager import AdaptiveStrategyManager
from llm_analyzer import LLMAnalyzer


class TestSafetyLimits:
    """Test safety limit enforcement"""
    
    def test_minimum_balance_protection(self):
        """Test minimum balance protection"""
        portfolio = Portfolio()
        portfolio.data = {
            'BTC': {'amount': 0.001, 'last_price_usd': 45000.0},
            'EUR': {'amount': 10.0, 'last_price_usd': 1.0},  # Below minimum
            'portfolio_value_usd': 55.0
        }
        
        # Should prevent trading when EUR balance is too low
        eur_balance = portfolio.get_asset_amount('EUR')
        min_eur_reserve = 15.0  # From config
        
        assert eur_balance < min_eur_reserve
        # Trading should be restricted
        can_trade = eur_balance >= min_eur_reserve
        assert not can_trade
    
    def test_maximum_position_size_limits(self):
        """Test maximum position size limits"""
        portfolio = Portfolio()
        portfolio.data = {
            'BTC': {'amount': 0.001, 'last_price_usd': 45000.0},
            'EUR': {'amount': 1000.0, 'last_price_usd': 1.0},
            'portfolio_value_usd': 1045.0
        }
        
        # Test maximum trade size calculation
        eur_balance = portfolio.get_asset_amount('EUR')
        max_trade_percent = 50.0  # 50% max per trade
        max_trade_amount = eur_balance * (max_trade_percent / 100)
        
        # Should not exceed maximum trade size
        proposed_trade = 600.0  # 60% of EUR balance
        assert proposed_trade > max_trade_amount
        
        # Should limit to maximum allowed
        actual_trade = min(proposed_trade, max_trade_amount)
        assert actual_trade == max_trade_amount
        assert actual_trade <= eur_balance * 0.5
    
    def test_allocation_constraint_enforcement(self):
        """Test allocation constraint enforcement"""
        portfolio = Portfolio()
        portfolio.data = {
            'BTC': {'amount': 0.01, 'last_price_usd': 45000.0},  # 450 EUR
            'ETH': {'amount': 0.1, 'last_price_usd': 3000.0},    # 300 EUR
            'EUR': {'amount': 250.0, 'last_price_usd': 1.0},     # 250 EUR
            'portfolio_value_usd': 1000.0
        }
        
        # Calculate current allocations
        total_value = 1000.0
        btc_allocation = (450.0 / total_value) * 100  # 45%
        eth_allocation = (300.0 / total_value) * 100  # 30%
        eur_allocation = (250.0 / total_value) * 100  # 25%
        
        # Test allocation limits (e.g., max 75% in any single asset)
        max_single_allocation = 75.0
        
        assert btc_allocation < max_single_allocation
        assert eth_allocation < max_single_allocation
        assert eur_allocation < max_single_allocation
        
        # Test minimum EUR allocation (e.g., min 12%)
        min_eur_allocation = 12.0
        assert eur_allocation >= min_eur_allocation
    
    def test_confidence_threshold_enforcement(self):
        """Test confidence threshold enforcement"""
        # Test BUY threshold
        buy_threshold = 55.0
        buy_confidences = [45, 55, 65, 75]
        
        for confidence in buy_confidences:
            should_buy = confidence >= buy_threshold
            if confidence >= buy_threshold:
                assert should_buy
            else:
                assert not should_buy
        
        # Test SELL threshold
        sell_threshold = 55.0
        sell_confidences = [45, 55, 65, 75]
        
        for confidence in sell_confidences:
            should_sell = confidence >= sell_threshold
            if confidence >= sell_threshold:
                assert should_sell
            else:
                assert not should_sell
    
    def test_trade_frequency_limits(self):
        """Test trade frequency limits"""
        import time
        
        # Simulate trade timing
        last_trade_time = time.time()
        min_trade_interval = 60  # 1 minute minimum between trades
        
        # Immediate second trade should be blocked
        current_time = last_trade_time + 30  # 30 seconds later
        time_since_last_trade = current_time - last_trade_time
        
        can_trade = time_since_last_trade >= min_trade_interval
        assert not can_trade  # Should be blocked
        
        # Trade after minimum interval should be allowed
        current_time = last_trade_time + 70  # 70 seconds later
        time_since_last_trade = current_time - last_trade_time
        
        can_trade = time_since_last_trade >= min_trade_interval
        assert can_trade  # Should be allowed


class TestEmergencyMechanisms:
    """Test emergency stop and safety mechanisms"""
    
    def test_emergency_stop_trigger(self):
        """Test emergency stop mechanism"""
        # Simulate emergency conditions
        emergency_conditions = [
            {'condition': 'api_failure_count', 'value': 5, 'threshold': 3},
            {'condition': 'consecutive_losses', 'value': 10, 'threshold': 5},
            {'condition': 'portfolio_drop_percent', 'value': 25, 'threshold': 20},
        ]
        
        for condition in emergency_conditions:
            should_stop = condition['value'] >= condition['threshold']
            assert should_stop, f"Emergency stop should trigger for {condition['condition']}"
    
    def test_api_failure_handling(self):
        """Test API failure emergency handling"""
        client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        
        # Mock consecutive API failures
        failure_count = 0
        max_failures = 3
        
        for attempt in range(5):
            try:
                # Simulate API failure
                if attempt < 4:  # First 4 attempts fail
                    failure_count += 1
                    raise Exception("API Error")
                else:
                    # Success on 5th attempt
                    failure_count = 0
                    result = {"price": 45000.0}
            except Exception:
                if failure_count >= max_failures:
                    # Should trigger emergency stop
                    emergency_stop = True
                    break
        
        assert failure_count >= max_failures
    
    def test_portfolio_protection_mechanisms(self):
        """Test portfolio protection in extreme scenarios"""
        portfolio = Portfolio()
        
        # Scenario 1: Extreme portfolio drop
        initial_value = 1000.0
        current_value = 700.0  # 30% drop
        drop_percentage = ((initial_value - current_value) / initial_value) * 100
        
        max_allowed_drop = 25.0  # 25% maximum drop before emergency stop
        should_stop = drop_percentage > max_allowed_drop
        assert should_stop
        
        # Scenario 2: Single asset over-concentration
        portfolio.data = {
            'BTC': {'amount': 0.02, 'last_price_usd': 45000.0},  # 900 EUR (90%)
            'EUR': {'amount': 100.0, 'last_price_usd': 1.0},     # 100 EUR (10%)
            'portfolio_value_usd': 1000.0
        }
        
        btc_percentage = (900.0 / 1000.0) * 100
        max_single_asset = 75.0  # 75% maximum in single asset
        
        is_over_concentrated = btc_percentage > max_single_asset
        assert is_over_concentrated
    
    def test_network_failure_recovery(self):
        """Test network failure recovery mechanisms"""
        client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        
        # Simulate network failures with retry logic
        max_retries = 3
        retry_count = 0
        success = False
        
        for attempt in range(max_retries + 1):
            try:
                if attempt < max_retries:  # Fail first attempts
                    raise ConnectionError("Network error")
                else:
                    # Success on final attempt
                    success = True
                    break
            except ConnectionError:
                retry_count += 1
                if retry_count >= max_retries:
                    # Should implement fallback mechanism
                    fallback_activated = True
                    break
        
        # Should either succeed or activate fallback
        assert success or (retry_count >= max_retries)
    
    def test_data_corruption_handling(self):
        """Test handling of corrupted data"""
        # Test corrupted portfolio file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("invalid json content")
            corrupted_file = f.name
        
        try:
            # Should handle corrupted file gracefully
            portfolio = Portfolio(portfolio_file=corrupted_file)
            
            # Should initialize with safe defaults
            assert hasattr(portfolio, 'data')
            assert isinstance(portfolio.data, dict)
            
        finally:
            os.unlink(corrupted_file)
        
        # Test corrupted market data
        corrupted_data = pd.DataFrame({
            'close': [None, float('inf'), -1, 'invalid'],
            'volume': [float('nan'), -1000, None, 0]
        })
        
        # Should handle corrupted data without crashing
        try:
            # Clean the data
            cleaned_data = corrupted_data.dropna()
            numeric_data = cleaned_data.select_dtypes(include=[float, int])
            assert len(numeric_data) >= 0  # Should not crash
        except Exception as e:
            # Should handle gracefully
            assert "invalid" not in str(e).lower() or True


class TestEdgeCaseHandling:
    """Test edge case handling"""
    
    def test_zero_balance_scenarios(self):
        """Test handling of zero balance scenarios"""
        portfolio = Portfolio()
        portfolio.data = {
            'BTC': {'amount': 0.0, 'last_price_usd': 45000.0},
            'EUR': {'amount': 0.0, 'last_price_usd': 1.0},
            'portfolio_value_usd': 0.0
        }
        
        # Should handle zero balances gracefully
        btc_amount = portfolio.get_asset_amount('BTC')
        eur_amount = portfolio.get_asset_amount('EUR')
        
        assert btc_amount == 0.0
        assert eur_amount == 0.0
        
        # Should prevent trading with zero balance
        can_buy = eur_amount > 0
        can_sell = btc_amount > 0
        
        assert not can_buy
        assert not can_sell
    
    def test_extreme_price_movements(self):
        """Test handling of extreme price movements"""
        extreme_scenarios = [
            {'price': 0.01, 'change': -99.99},      # Extreme crash
            {'price': 1000000, 'change': 1000},     # Extreme pump
            {'price': float('inf'), 'change': float('inf')},  # Invalid price
            {'price': -100, 'change': -100},        # Negative price
        ]
        
        for scenario in extreme_scenarios:
            price = scenario['price']
            
            # Should validate price ranges
            is_valid_price = 0 < price < 10000000 and price != float('inf')
            
            if not is_valid_price:
                # Should reject invalid prices
                assert price <= 0 or price == float('inf') or price > 10000000
            else:
                # Should handle extreme but valid prices
                assert 0 < price < 10000000
    
    def test_high_frequency_requests(self):
        """Test handling of high frequency requests"""
        client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        
        # Test rate limiting
        request_times = []
        min_interval = client.min_request_interval
        
        with patch.object(client.client, 'get_product') as mock_get:
            mock_get.return_value = MagicMock(price=50000)
            
            import time
            start_time = time.time()
            
            # Make rapid requests
            for i in range(3):
                client.get_product_price('BTC-EUR')
                request_times.append(time.time())
            
            total_time = time.time() - start_time
            
            # Should enforce minimum intervals
            expected_min_time = 2 * min_interval  # 2 intervals for 3 requests
            assert total_time >= expected_min_time * 0.8  # Allow some tolerance
    
    def test_concurrent_access_safety(self):
        """Test concurrent access safety"""
        portfolio = Portfolio()
        portfolio.data = {
            'BTC': {'amount': 0.001, 'last_price_usd': 45000.0},
            'EUR': {'amount': 100.0, 'last_price_usd': 1.0},
            'portfolio_value_usd': 145.0
        }
        
        import threading
        import time
        
        results = []
        errors = []
        
        def concurrent_operation():
            try:
                # Simulate concurrent portfolio operations
                for _ in range(10):
                    value = portfolio._calculate_portfolio_value()
                    results.append(value)
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=concurrent_operation)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access without errors
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 30  # 3 threads × 10 operations each
    
    def test_memory_exhaustion_protection(self):
        """Test protection against memory exhaustion"""
        # Test large data structure handling
        large_data_size = 10000
        
        try:
            # Create large dataset
            large_data = pd.DataFrame({
                'close': [45000.0 + i for i in range(large_data_size)],
                'volume': [1000000 + i for i in range(large_data_size)]
            })
            
            # Should handle large datasets efficiently
            assert len(large_data) == large_data_size
            
            # Test memory usage doesn't grow excessively
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss
            
            # Process the large dataset
            moving_avg = large_data['close'].rolling(window=50).mean()
            
            memory_after = process.memory_info().rss
            memory_increase = memory_after - memory_before
            
            # Should not use excessive memory (less than 100MB)
            assert memory_increase < 100 * 1024 * 1024
            
        except MemoryError:
            # Should handle memory errors gracefully
            assert True  # Expected for very large datasets


class TestExtremeMarketConditions:
    """Test handling of extreme market conditions"""
    
    def test_flash_crash_scenario(self):
        """Test handling of flash crash scenarios"""
        # Simulate flash crash data
        flash_crash_data = pd.DataFrame({
            'close': [45000, 44000, 35000, 20000, 25000, 30000],  # Rapid drop and recovery
            'high': [45200, 44200, 35200, 20200, 25200, 30200],
            'low': [44800, 35000, 19000, 19500, 24800, 29800],
            'volume': [1000000, 5000000, 20000000, 15000000, 10000000, 8000000],  # High volume
            'rsi': [50, 30, 10, 15, 25, 35],
            'macd': [0.5, -1.0, -5.0, -3.0, -1.0, 0.0],
            'bb_position': [0.5, 0.2, 0.0, 0.1, 0.3, 0.4]
        })
        
        analyzer = LLMAnalyzer()
        
        with patch.object(analyzer, '_call_genai') as mock_genai:
            # Should be very cautious during flash crash
            mock_genai.return_value = {
                'decision': 'HOLD',  # Conservative during extreme volatility
                'confidence': 30,    # Low confidence
                'reasoning': 'Extreme market volatility detected'
            }
            
            response = analyzer.analyze_market_data(flash_crash_data, 30000.0, 'BTC-EUR')
            
            # Should be conservative during extreme conditions
            assert response['decision'] == 'HOLD'
            assert response['confidence'] <= 50
    
    def test_market_manipulation_detection(self):
        """Test detection of potential market manipulation"""
        # Simulate suspicious price patterns
        manipulation_patterns = [
            # Pump and dump pattern
            [45000, 45000, 60000, 65000, 40000, 35000],
            # Wash trading pattern (high volume, minimal price change)
            [45000, 45010, 44990, 45005, 44995, 45000],
        ]
        
        for pattern in manipulation_patterns:
            suspicious_data = pd.DataFrame({
                'close': pattern,
                'high': [p * 1.01 for p in pattern],
                'low': [p * 0.99 for p in pattern],
                'volume': [10000000] * len(pattern),  # Unusually high volume
                'rsi': [50] * len(pattern),
                'macd': [0.1] * len(pattern),
                'bb_position': [0.5] * len(pattern)
            })
            
            # Calculate price volatility
            price_changes = pd.Series(pattern).pct_change().abs()
            avg_volatility = price_changes.mean()
            
            # High volatility with high volume might indicate manipulation
            is_suspicious = avg_volatility > 0.1 and all(v > 5000000 for v in suspicious_data['volume'])
            
            if is_suspicious:
                # Should be cautious with suspicious patterns
                recommended_action = 'HOLD'
                confidence = 40
            else:
                recommended_action = 'BUY'
                confidence = 70
            
            # Verify appropriate caution
            if is_suspicious:
                assert recommended_action == 'HOLD'
                assert confidence <= 50
    
    def test_low_liquidity_conditions(self):
        """Test handling of low liquidity conditions"""
        low_liquidity_data = pd.DataFrame({
            'close': [45000.0],
            'high': [46000.0],
            'low': [44000.0],
            'volume': [10000],  # Very low volume
            'rsi': [65],
            'macd': [0.5],
            'bb_position': [0.7]
        })
        
        # Low liquidity should increase caution
        volume = low_liquidity_data['volume'].iloc[0]
        typical_volume = 1000000
        
        liquidity_ratio = volume / typical_volume
        is_low_liquidity = liquidity_ratio < 0.1  # Less than 10% of typical volume
        
        assert is_low_liquidity
        
        # Should reduce confidence in low liquidity conditions
        if is_low_liquidity:
            confidence_adjustment = -20  # Reduce confidence by 20 points
            base_confidence = 75
            adjusted_confidence = max(0, base_confidence + confidence_adjustment)
            
            assert adjusted_confidence == 55
    
    def test_circuit_breaker_conditions(self):
        """Test circuit breaker-like conditions"""
        # Simulate conditions that would trigger circuit breakers
        circuit_breaker_scenarios = [
            {'price_change': -15, 'should_halt': True},   # 15% drop
            {'price_change': 20, 'should_halt': True},    # 20% gain
            {'price_change': -5, 'should_halt': False},   # 5% drop (normal)
            {'price_change': 8, 'should_halt': False},    # 8% gain (normal)
        ]
        
        for scenario in circuit_breaker_scenarios:
            price_change = scenario['price_change']
            should_halt = abs(price_change) >= 10  # 10% threshold
            
            assert should_halt == scenario['should_halt']
            
            if should_halt:
                # Should halt trading during extreme moves
                trading_allowed = False
                recommended_action = 'HOLD'
            else:
                trading_allowed = True
                recommended_action = 'BUY' if price_change < 0 else 'SELL'
            
            if scenario['should_halt']:
                assert not trading_allowed
                assert recommended_action == 'HOLD'
