"""
Performance Tests

Tests system performance, response times, resource usage,
and scalability of the trading bot components.
"""

import pytest
import time
import psutil
import threading
import tempfile
import os
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer
from utils.trading.portfolio import Portfolio
from utils.performance.performance_tracker import PerformanceTracker
from data_collector import DataCollector


class TestResponseTimes:
    """Test response times for critical operations"""
    
    def test_coinbase_client_response_time(self):
        """Test Coinbase client response time"""
        client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        
        with patch.object(client.client, 'get_product') as mock_get:
            mock_get.return_value = MagicMock(price=50000)
            
            start_time = time.time()
            result = client.get_product_price('BTC-EUR')
            elapsed = time.time() - start_time
            
            # Should respond within 2 seconds (mocked)
            assert elapsed < 2.0
            assert result == {"price": 50000.0}
    
    def test_portfolio_calculation_time(self):
        """Test portfolio calculation performance"""
        portfolio = Portfolio()
        
        # Set up portfolio with test data
        portfolio.data = {
            'BTC': {'amount': 0.001, 'last_price_usd': 45000.0},
            'ETH': {'amount': 0.01, 'last_price_usd': 3000.0},
            'EUR': {'amount': 100.0, 'last_price_usd': 1.0},
            'portfolio_value_usd': 175.0
        }
        
        start_time = time.time()
        value = portfolio._calculate_portfolio_value()
        elapsed = time.time() - start_time
        
        # Should calculate within 0.1 seconds
        assert elapsed < 0.1
        assert isinstance(value, (int, float))
    
    def test_llm_analyzer_response_time(self):
        """Test LLM analyzer response time (mocked)"""
        analyzer = LLMAnalyzer()
        
        # Create test market data
        market_data = pd.DataFrame({
            'close': [45000.0],
            'high': [46000.0],
            'low': [44000.0],
            'volume': [1000000],
            'rsi': [65.0],
            'macd': [0.5],
            'bb_position': [0.7]
        })
        
        with patch.object(analyzer, '_call_genai') as mock_genai:
            mock_genai.return_value = {
                'decision': 'HOLD',
                'confidence': 60,
                'reasoning': 'Market analysis'
            }
            
            start_time = time.time()
            result = analyzer.analyze_market_data(market_data, 45000.0, 'BTC-EUR')
            elapsed = time.time() - start_time
            
            # Should respond within 30 seconds (mocked, much faster)
            assert elapsed < 30.0
            assert result['decision'] in ['BUY', 'SELL', 'HOLD']
    
    def test_data_collector_performance(self):
        """Test data collector performance"""
        client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        collector = DataCollector(client)
        
        # Mock the data collection
        with patch.object(collector, 'get_historical_data') as mock_get:
            mock_data = pd.DataFrame({
                'close': [45000.0, 45100.0, 45200.0],
                'volume': [1000000, 1100000, 1200000]
            })
            mock_get.return_value = mock_data
            
            start_time = time.time()
            result = collector.get_historical_data('BTC-EUR', '1h', 7)
            elapsed = time.time() - start_time
            
            # Should collect data within 5 seconds
            assert elapsed < 5.0
            assert len(result) > 0


class TestResourceUsage:
    """Test resource usage and memory management"""
    
    def test_memory_usage_portfolio(self):
        """Test memory usage of portfolio operations"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create multiple portfolios
        portfolios = []
        for i in range(10):
            portfolio = Portfolio()
            portfolio.data = {
                'BTC': {'amount': 0.001 * i, 'last_price_usd': 45000.0},
                'EUR': {'amount': 100.0 + i, 'last_price_usd': 1.0},
                'portfolio_value_usd': 145.0 + i
            }
            portfolios.append(portfolio)
        
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # Should not use excessive memory (less than 50MB for 10 portfolios)
        assert memory_increase < 50 * 1024 * 1024  # 50MB
        
        # Clean up
        del portfolios
    
    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated operations"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Perform repeated operations
        for i in range(100):
            portfolio = Portfolio()
            portfolio.data = {'BTC': {'amount': 0.001, 'last_price_usd': 45000.0}}
            value = portfolio._calculate_portfolio_value()
            del portfolio
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Should not have significant memory increase (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024  # 10MB
    
    def test_cpu_usage_monitoring(self):
        """Test CPU usage during operations"""
        # Monitor CPU usage during intensive operations
        cpu_percent_before = psutil.cpu_percent(interval=1)
        
        # Perform CPU-intensive operation
        start_time = time.time()
        for i in range(1000):
            portfolio = Portfolio()
            portfolio.data = {'BTC': {'amount': 0.001, 'last_price_usd': 45000.0}}
            portfolio._calculate_portfolio_value()
        elapsed = time.time() - start_time
        
        cpu_percent_after = psutil.cpu_percent(interval=1)
        
        # Should complete within reasonable time
        assert elapsed < 10.0  # 10 seconds for 1000 operations
        
        # CPU usage should be reasonable (this is informational)
        print(f"CPU usage: {cpu_percent_before}% -> {cpu_percent_after}%")
    
    def test_file_handle_management(self):
        """Test that file handles are properly managed"""
        process = psutil.Process()
        initial_files = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        # Create and save multiple portfolios
        temp_files = []
        for i in range(20):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_files.append(f.name)
                portfolio = Portfolio(portfolio_file=f.name)
                portfolio.data = {'BTC': {'amount': 0.001, 'last_price_usd': 45000.0}}
                portfolio.save()
        
        current_files = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        # Clean up
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        
        # Should not have excessive file handle increase
        if initial_files > 0:  # Only test if we can measure file handles
            file_increase = current_files - initial_files
            assert file_increase < 50  # Should not leak file handles


class TestScalability:
    """Test scalability with multiple operations"""
    
    def test_concurrent_portfolio_operations(self):
        """Test concurrent portfolio operations"""
        def portfolio_operation(portfolio_id):
            portfolio = Portfolio()
            portfolio.data = {
                'BTC': {'amount': 0.001 * portfolio_id, 'last_price_usd': 45000.0},
                'EUR': {'amount': 100.0, 'last_price_usd': 1.0},
                'portfolio_value_usd': 145.0
            }
            return portfolio._calculate_portfolio_value()
        
        start_time = time.time()
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(portfolio_operation, i) for i in range(20)]
            results = [future.result() for future in futures]
        
        elapsed = time.time() - start_time
        
        # Should complete within reasonable time
        assert elapsed < 5.0  # 5 seconds for 20 concurrent operations
        assert len(results) == 20
        assert all(isinstance(result, (int, float)) for result in results)
    
    def test_multiple_trading_pairs_performance(self):
        """Test performance with multiple trading pairs"""
        client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        trading_pairs = ['BTC-EUR', 'ETH-EUR', 'ADA-EUR', 'DOT-EUR', 'LINK-EUR']
        
        with patch.object(client.client, 'get_product') as mock_get:
            mock_get.return_value = MagicMock(price=50000)
            
            start_time = time.time()
            
            results = []
            for pair in trading_pairs:
                result = client.get_product_price(pair)
                results.append(result)
            
            elapsed = time.time() - start_time
            
            # Should handle multiple pairs efficiently
            assert elapsed < 2.0  # 2 seconds for 5 pairs
            assert len(results) == 5
            assert all(result['price'] == 50000.0 for result in results)
    
    def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        # Create large market data
        large_data = pd.DataFrame({
            'close': [45000.0 + i for i in range(1000)],
            'high': [46000.0 + i for i in range(1000)],
            'low': [44000.0 + i for i in range(1000)],
            'volume': [1000000 + i * 1000 for i in range(1000)]
        })
        
        start_time = time.time()
        
        # Process the large dataset - simple moving average instead of RSI
        ma_values = []
        for i in range(20, len(large_data)):  # 20-period moving average
            window = large_data['close'].iloc[i-19:i+1]  # 20 periods
            ma = window.mean()
            ma_values.append(ma)
        
        elapsed = time.time() - start_time
        
        # Should process large dataset efficiently
        assert elapsed < 2.0  # 2 seconds for 1000 data points
        assert len(ma_values) > 900  # Should process most of the data (980 expected)


class TestConcurrentOperations:
    """Test concurrent operation performance"""
    
    def test_thread_safety_portfolio(self):
        """Test thread safety of portfolio operations"""
        portfolio = Portfolio()
        portfolio.data = {
            'BTC': {'amount': 0.001, 'last_price_usd': 45000.0},
            'EUR': {'amount': 100.0, 'last_price_usd': 1.0},
            'portfolio_value_usd': 145.0
        }
        
        results = []
        errors = []
        
        def portfolio_read():
            try:
                value = portfolio._calculate_portfolio_value()
                results.append(value)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=portfolio_read)
            threads.append(thread)
        
        start_time = time.time()
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        elapsed = time.time() - start_time
        
        # Should complete without errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert elapsed < 2.0  # Should complete quickly
    
    def test_performance_tracker_concurrency(self):
        """Test performance tracker under concurrent access"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = PerformanceTracker(config_path=temp_dir)
            
            def take_snapshot(snapshot_id):
                portfolio_data = {
                    'BTC': {'amount': 0.001 * snapshot_id, 'last_price_usd': 45000.0},
                    'EUR': {'amount': 100.0, 'last_price_usd': 1.0},
                    'total_value_eur': 145.0 + snapshot_id
                }
                return tracker.take_portfolio_snapshot(portfolio_data)
            
            start_time = time.time()
            
            # Run concurrent snapshot operations
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(take_snapshot, i) for i in range(10)]
                results = [future.result() for future in futures]
            
            elapsed = time.time() - start_time
            
            # Should handle concurrent operations
            assert elapsed < 3.0  # 3 seconds for 10 concurrent snapshots
            assert len(results) == 10


class TestPerformanceBenchmarks:
    """Performance benchmarks for key operations"""
    
    def test_portfolio_value_calculation_benchmark(self):
        """Benchmark portfolio value calculation"""
        portfolio = Portfolio()
        portfolio.data = {
            'BTC': {'amount': 0.001, 'last_price_usd': 45000.0},
            'ETH': {'amount': 0.01, 'last_price_usd': 3000.0},
            'ADA': {'amount': 100, 'last_price_usd': 0.5},
            'DOT': {'amount': 10, 'last_price_usd': 8.0},
            'EUR': {'amount': 100.0, 'last_price_usd': 1.0},
            'portfolio_value_usd': 275.0
        }
        
        # Benchmark multiple calculations
        iterations = 1000
        start_time = time.time()
        
        for _ in range(iterations):
            value = portfolio._calculate_portfolio_value()
        
        elapsed = time.time() - start_time
        avg_time = elapsed / iterations
        
        # Should average less than 1ms per calculation
        assert avg_time < 0.001  # 1 millisecond
        print(f"Portfolio calculation: {avg_time*1000:.2f}ms average")
    
    def test_data_processing_benchmark(self):
        """Benchmark data processing operations"""
        # Create test data
        data_size = 1000
        test_data = pd.DataFrame({
            'close': [45000.0 + i * 10 for i in range(data_size)],
            'volume': [1000000 + i * 1000 for i in range(data_size)]
        })
        
        start_time = time.time()
        
        # Process data (calculate moving averages)
        ma_20 = test_data['close'].rolling(window=20).mean()
        ma_50 = test_data['close'].rolling(window=50).mean()
        volume_ma = test_data['volume'].rolling(window=10).mean()
        
        elapsed = time.time() - start_time
        
        # Should process efficiently
        assert elapsed < 0.1  # 100ms for 1000 data points
        assert len(ma_20) == data_size
        assert len(ma_50) == data_size
        assert len(volume_ma) == data_size
        
        print(f"Data processing: {elapsed*1000:.2f}ms for {data_size} points")
    
    def test_file_io_performance(self):
        """Benchmark file I/O operations"""
        portfolio = Portfolio()
        portfolio.data = {
            'BTC': {'amount': 0.001, 'last_price_usd': 45000.0},
            'EUR': {'amount': 100.0, 'last_price_usd': 1.0},
            'portfolio_value_usd': 145.0
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            # Benchmark save operations
            iterations = 100
            start_time = time.time()
            
            for _ in range(iterations):
                portfolio.portfolio_file = temp_file
                portfolio.save()
            
            elapsed = time.time() - start_time
            avg_save_time = elapsed / iterations
            
            # Should save quickly
            assert avg_save_time < 0.01  # 10ms per save
            print(f"Portfolio save: {avg_save_time*1000:.2f}ms average")
            
            # Benchmark load operations
            start_time = time.time()
            
            for _ in range(iterations):
                new_portfolio = Portfolio(portfolio_file=temp_file)
            
            elapsed = time.time() - start_time
            avg_load_time = elapsed / iterations
            
            # Should load quickly
            assert avg_load_time < 0.01  # 10ms per load
            print(f"Portfolio load: {avg_load_time*1000:.2f}ms average")
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
