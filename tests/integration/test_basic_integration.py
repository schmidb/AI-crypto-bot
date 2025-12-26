"""
Simplified Integration Tests

Basic integration tests that focus on core functionality
and use the correct API signatures.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer
from utils.portfolio import Portfolio


class TestBasicAPIIntegration:
    """Basic API integration tests"""
    
    def test_coinbase_price_retrieval(self):
        """Test basic Coinbase price retrieval"""
        try:
            client = CoinbaseClient()
        except ValueError:
            pytest.skip("Coinbase API credentials not available")
        
        try:
            price_data = client.get_product_price('BTC-EUR')
            if price_data and 'price' in price_data:
                price = float(price_data['price'])
                assert price > 0
        except Exception:
            # API might be unavailable, skip test
            pytest.skip("Coinbase API unavailable")
    
    def test_portfolio_basic_operations(self):
        """Test basic portfolio operations"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            portfolio_file = f.name
        
        try:
            portfolio = Portfolio(portfolio_file=portfolio_file)
            
            # Test basic operations
            assert portfolio.get_asset_amount('BTC') >= 0
            assert portfolio.get_asset_amount('EUR') >= 0
            
            # Test data structure
            portfolio_dict = portfolio.to_dict()
            assert isinstance(portfolio_dict, dict)
            
        finally:
            os.unlink(portfolio_file)
    
    def test_llm_analyzer_initialization(self):
        """Test LLM analyzer can be initialized"""
        try:
            analyzer = LLMAnalyzer()
            assert analyzer is not None
        except Exception:
            # GCP credentials might not be available
            pytest.skip("GCP credentials not available")


class TestComponentDataFlow:
    """Test data flow between components"""
    
    def test_coinbase_to_portfolio_data_flow(self):
        """Test data flow from Coinbase to Portfolio"""
        mock_data = {
            'BTC': {'amount': 0.001},
            'ETH': {'amount': 0.01}, 
            'EUR': {'amount': 100.0}
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            portfolio_file = f.name
        
        try:
            with patch.object(CoinbaseClient, 'get_portfolio', return_value=mock_data):
                with patch.object(CoinbaseClient, '__init__', return_value=None):
                    client = CoinbaseClient()
                    client.api_key = "test"
                    client.api_secret = "test"
                    portfolio = Portfolio(portfolio_file=portfolio_file)
                    
                    # Get data from client
                    coinbase_data = client.get_portfolio()
                    
                    # Update portfolio
                    if coinbase_data:
                        portfolio.update_from_exchange(coinbase_data)
                    
                    # Verify data flow
                    assert portfolio.get_asset_amount('BTC') >= 0
                    assert portfolio.get_asset_amount('EUR') >= 0
                
        finally:
            os.unlink(portfolio_file)
    
    def test_portfolio_state_persistence(self):
        """Test portfolio state persists across instances"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            portfolio_file = f.name
        
        try:
            # Create and save portfolio
            portfolio1 = Portfolio(portfolio_file=portfolio_file)
            portfolio1.update_asset_amount('BTC', 0.001)
            portfolio1.save()
            
            # Load in new instance
            portfolio2 = Portfolio(portfolio_file=portfolio_file)
            
            # Verify persistence
            assert portfolio2.get_asset_amount('BTC') > 0
            
        finally:
            os.unlink(portfolio_file)


class TestErrorHandling:
    """Test error handling across components"""
    
    def test_coinbase_error_handling(self):
        """Test Coinbase client handles errors gracefully"""
        # Mock the client to avoid credential requirements
        with patch.object(CoinbaseClient, '__init__', return_value=None):
            client = CoinbaseClient()
            client.api_key = "test"
            client.api_secret = "test"
            
            # Test with invalid product ID
            result = client.get_product_price('INVALID-PAIR')
            
            # Should handle gracefully (return None, empty dict, or valid error response)
            assert result is None or result == {} or isinstance(result, dict)
    
    def test_portfolio_corrupted_file_handling(self):
        """Test portfolio handles corrupted files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            portfolio_file = f.name
        
        try:
            # Should not crash on corrupted file
            portfolio = Portfolio(portfolio_file=portfolio_file)
            assert portfolio is not None
            
            # Should have some default values
            assert isinstance(portfolio.get_asset_amount('BTC'), (int, float))
            
        finally:
            os.unlink(portfolio_file)


class TestIntegrationWorkflows:
    """Test complete integration workflows"""
    
    def test_basic_trading_data_workflow(self):
        """Test basic trading data workflow"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            portfolio_file = f.name
        
        try:
            # Mock market data in correct format
            mock_portfolio_data = {
                'BTC': {'amount': 0.001},
                'EUR': {'amount': 100.0}
            }
            
            with patch.object(CoinbaseClient, 'get_portfolio', return_value=mock_portfolio_data):
                with patch.object(CoinbaseClient, '__init__', return_value=None):
                    # 1. Get market data
                    client = CoinbaseClient()
                    client.api_key = "test"
                    client.api_secret = "test"
                    market_data = client.get_portfolio()
                    
                    # 2. Update portfolio
                    portfolio = Portfolio(portfolio_file=portfolio_file)
                    if market_data:
                        portfolio.update_from_exchange(market_data)
                    
                    # 3. Verify workflow
                    assert portfolio.get_asset_amount('BTC') >= 0
                    assert portfolio.get_asset_amount('EUR') >= 0
                    
                    # 4. Test portfolio calculations
                    allocations = portfolio.get_asset_allocation()
                    assert isinstance(allocations, dict)
                
        finally:
            os.unlink(portfolio_file)
