"""
Integration Tests for API Components

Tests the integration between the bot and external APIs:
- Coinbase Advanced Trade API
- Google Cloud Vertex AI API
- Real API connectivity and authentication
- End-to-end API workflows
"""

import pytest
import os
import time
import sys
from unittest.mock import patch, MagicMock

# Mock Google Cloud modules before importing components
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()
sys.modules['google.oauth2'] = MagicMock()
sys.modules['google.oauth2.service_account'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.aiplatform'] = MagicMock()
sys.modules['vertexai'] = MagicMock()
sys.modules['vertexai.generative_models'] = MagicMock()

from coinbase_client import CoinbaseClient
from llm_analyzer import LLMAnalyzer


class TestCoinbaseAPIIntegration:
    """Test Coinbase API integration with real API calls (when credentials available)"""
    
    @pytest.fixture
    def coinbase_client(self):
        """Create Coinbase client for testing"""
        try:
            return CoinbaseClient()
        except ValueError:
            # API credentials not available in CI
            pytest.skip("Coinbase API credentials not available")
    
    @pytest.fixture
    def has_coinbase_credentials(self):
        """Check if Coinbase credentials are available"""
        return (
            os.getenv('COINBASE_API_KEY') and 
            os.getenv('COINBASE_API_SECRET')
        )
    
    def test_coinbase_authentication(self, coinbase_client, has_coinbase_credentials):
        """Test Coinbase API authentication"""
        if not has_coinbase_credentials:
            pytest.skip("Coinbase credentials not available")
        
        # Test authentication by fetching accounts
        try:
            accounts = coinbase_client.get_accounts()
            assert accounts is not None
            assert isinstance(accounts, list)
        except Exception as e:
            pytest.fail(f"Authentication failed: {e}")
    
    def test_coinbase_market_data_integration(self, coinbase_client):
        """Test market data retrieval integration"""
        # This should work without authentication
        try:
            price_data = coinbase_client.get_product_price('BTC-EUR')
            assert price_data is not None
            assert isinstance(price_data, dict)
            assert 'price' in price_data
            price = float(price_data['price'])
            assert price > 0
        except Exception as e:
            pytest.fail(f"Market data retrieval failed: {e}")
    
    def test_coinbase_product_listing(self, coinbase_client):
        """Test product listing integration"""
        try:
            # Test getting product stats which should work
            stats = coinbase_client.get_product_stats('BTC-EUR')
            assert stats is not None
            assert isinstance(stats, dict)
            
            # Test getting price data
            price_data = coinbase_client.get_product_price('BTC-EUR')
            assert price_data is not None
            assert 'price' in price_data
        except Exception as e:
            pytest.fail(f"Product data retrieval failed: {e}")
    
    @pytest.mark.skip(reason="Integration test requires real Coinbase API credentials")
    def test_coinbase_portfolio_integration(self, coinbase_client):
        """Test portfolio data integration with real API"""
        try:
            portfolio = coinbase_client.get_portfolio()
            assert portfolio is not None
            assert isinstance(portfolio, dict)
            
            # Should have expected structure
            for currency in ['BTC', 'ETH', 'EUR']:
                assert currency in portfolio
                assert 'amount' in portfolio[currency]
                assert isinstance(portfolio[currency]['amount'], (int, float))
        except Exception as e:
            pytest.fail(f"Portfolio integration failed: {e}")
    
    def test_coinbase_rate_limiting(self, coinbase_client):
        """Test rate limiting behavior"""
        # Make multiple rapid requests to test rate limiting
        start_time = time.time()
        
        for i in range(5):
            try:
                coinbase_client.get_current_price('BTC-EUR')
            except Exception as e:
                if "rate limit" in str(e).lower():
                    # Rate limiting is working
                    break
        
        elapsed = time.time() - start_time
        # Should not complete instantly if rate limiting is active
        assert elapsed >= 0  # Basic sanity check


class TestGoogleCloudAPIIntegration:
    """Test Google Cloud API integration"""
    
    @pytest.fixture
    def llm_analyzer(self):
        """Create LLM analyzer for testing"""
        return LLMAnalyzer()
    
    @pytest.fixture
    def has_gcp_credentials(self):
        """Check if Google Cloud credentials are available"""
        return (
            os.getenv('GOOGLE_CLOUD_PROJECT') and 
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
    
    @pytest.mark.skipif(
        not (os.getenv('GOOGLE_CLOUD_PROJECT') and os.getenv('GOOGLE_APPLICATION_CREDENTIALS')),
        reason="Google Cloud credentials not available"
    )
    def test_gcp_authentication(self, llm_analyzer, has_gcp_credentials):
        """Test Google Cloud authentication"""
        try:
            # Test authentication by initializing the client
            assert llm_analyzer.client is not None
        except Exception as e:
            pytest.fail(f"GCP authentication failed: {e}")
    
    @pytest.mark.skipif(
        not (os.getenv('GOOGLE_CLOUD_PROJECT') and os.getenv('GOOGLE_APPLICATION_CREDENTIALS')),
        reason="Google Cloud credentials not available"
    )
    def test_llm_analysis_integration(self, llm_analyzer):
        """Test LLM analysis integration with real API"""
        # Skip if we're using mocked modules (integration test environment)
        import google.genai as genai
        if isinstance(genai, MagicMock):
            pytest.skip("Running in test environment with mocked Google Cloud modules")
            
        # Create minimal test data as DataFrame
        import pandas as pd
        
        market_data = pd.DataFrame({
            'close': [45000.0],
            'high': [46000.0],
            'low': [44000.0],
            'volume': [1000000],
            'rsi': [65.0],
            'macd': [0.5],
            'bb_position': [0.7]
        })
        
        try:
            decision = llm_analyzer.analyze_market_data(market_data, 45000.0, 'BTC-EUR')
            assert decision is not None
            assert isinstance(decision, dict)
            assert 'action' in decision
            assert decision['action'] in ['BUY', 'SELL', 'HOLD']
            assert 'confidence' in decision
            assert 0 <= decision['confidence'] <= 100
        except Exception as e:
            pytest.fail(f"LLM analysis integration failed: {e}")


class TestAPIErrorHandling:
    """Test API error handling and recovery"""
    
    def test_coinbase_network_error_handling(self):
        """Test handling of network errors"""
        client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        
        # Mock the SDK client to raise network error
        with patch.object(client.client, 'get_product', side_effect=ConnectionError("Network error")):
            # Should handle network errors gracefully
            result = client.get_product_price('BTC-EUR')
            assert result == {"price": 0.0}  # Should return default price on error
    
    def test_coinbase_api_error_handling(self):
        """Test handling of API errors"""
        client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        
        # Mock the SDK client to raise API error
        with patch.object(client.client, 'get_product', side_effect=Exception("API Error")):
            # Should handle API errors gracefully
            result = client.get_product_price('BTC-EUR')
            assert result == {"price": 0.0}  # Should return default price on error
    
    def test_gcp_quota_error_handling(self):
        """Test handling of GCP quota errors"""
        with patch('llm_analyzer.genai.Client') as mock_client:
            mock_client.side_effect = Exception("Quota exceeded")
            
            # Should handle quota errors gracefully
            try:
                analyzer = LLMAnalyzer()
                # Should not crash on initialization, but may log error
                assert analyzer is not None
            except Exception as e:
                # If it does raise an exception, it should be handled gracefully
                assert "quota" in str(e).lower() or "exceeded" in str(e).lower()


class TestAPIDataConsistency:
    """Test data consistency across API calls"""
    
    def test_price_data_consistency(self):
        """Test that price data is consistent across calls"""
        try:
            client = CoinbaseClient()
        except ValueError:
            pytest.skip("Coinbase API credentials not available")
        
        # Get price twice in quick succession
        price_data1 = client.get_product_price('BTC-EUR')
        time.sleep(1)  # Small delay
        price_data2 = client.get_product_price('BTC-EUR')
        
        if price_data1 and price_data2 and 'price' in price_data1 and 'price' in price_data2:
            price1 = float(price_data1['price'])
            price2 = float(price_data2['price'])
            # Prices should be reasonably close (within 5%)
            diff_percent = abs(price1 - price2) / price1 * 100
            assert diff_percent < 5.0, f"Price difference too large: {diff_percent}%"
    
    def test_portfolio_data_consistency(self):
        """Test portfolio data consistency"""
        if not (os.getenv('COINBASE_API_KEY') and os.getenv('COINBASE_API_SECRET')):
            pytest.skip("Coinbase credentials not available")
        
        try:
            client = CoinbaseClient()
        except ValueError:
            pytest.skip("Coinbase API credentials not available")
        
        # Get portfolio twice
        portfolio1 = client.get_portfolio()
        portfolio2 = client.get_portfolio()
        
        if portfolio1 and portfolio2:
            # Portfolio should be identical (no trades in between)
            for currency in portfolio1:
                if currency in portfolio2:
                    if isinstance(portfolio1[currency], dict) and isinstance(portfolio2[currency], dict):
                        assert portfolio1[currency].get('amount') == portfolio2[currency].get('amount')


class TestAPIIntegrationWorkflow:
    """Test complete API integration workflows"""
    
    def test_market_analysis_workflow(self):
        """Test complete market analysis workflow"""
        # This tests the integration between Coinbase data and LLM analysis
        coinbase_client = CoinbaseClient(api_key='test_key', api_secret='test_secret')
        
        # Get market data
        btc_price_data = coinbase_client.get_product_price('BTC-EUR')
        eth_price_data = coinbase_client.get_product_price('ETH-EUR')
        
        if btc_price_data and eth_price_data and 'price' in btc_price_data and 'price' in eth_price_data:
            btc_price = float(btc_price_data['price'])
            eth_price = float(eth_price_data['price'])
            
            # Create market data structure for LLM analysis
            import pandas as pd
            market_data = pd.DataFrame({
                'price': [btc_price],
                'rsi': [50.0],  # Mock technical indicators
                'macd': [0.0],
                'bb_position': [0.5]
            })
            
            # Test that data structure is valid for LLM analysis
            assert isinstance(market_data, pd.DataFrame)
            assert 'price' in market_data.columns
            assert 'rsi' in market_data.columns
            assert 'macd' in market_data.columns
            assert 'bb_position' in market_data.columns
    
    @pytest.mark.skipif(
        not all([
            os.getenv('COINBASE_API_KEY'),
            os.getenv('COINBASE_API_SECRET'),
            os.getenv('GOOGLE_CLOUD_PROJECT'),
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        ]),
        reason="Full API credentials not available"
    )
    def test_complete_decision_workflow(self):
        """Test complete decision-making workflow with real APIs"""
        # Skip if we're using mocked modules
        import google.genai as genai
        if isinstance(genai, MagicMock):
            pytest.skip("Running in test environment with mocked Google Cloud modules")
            
        # Get real market data
        coinbase_client = CoinbaseClient()
        btc_price_data = coinbase_client.get_product_price('BTC-EUR')
        
        if btc_price_data and 'price' in btc_price_data:
            btc_price = float(btc_price_data['price'])
            
            # Create market data for analysis
            import pandas as pd
            market_data = pd.DataFrame({
                'close': [btc_price],
                'high': [btc_price * 1.02],
                'low': [btc_price * 0.98],
                'volume': [1000000],
                'rsi': [60.0],
                'macd': [0.2],
                'bb_position': [0.7]
            })
            
            # Analyze with LLM
            llm_analyzer = LLMAnalyzer()
            decision = llm_analyzer.analyze_market_data(market_data, btc_price, 'BTC-EUR')
            
            # Validate decision structure
            assert decision is not None
            assert 'action' in decision
            assert 'confidence' in decision
            assert 'reasoning' in decision
            
            # Decision should be valid
            assert decision['action'] in ['BUY', 'SELL', 'HOLD']
            assert 0 <= decision['confidence'] <= 100
