"""
Tests for portfolio-aware LLM prompt generation
Tests the changes made on 2026-01-23 to address LLM BUY bias
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestPortfolioAwareLLMPrompt:
    """Test that LLM prompt includes portfolio context"""
    
    def test_prompt_includes_portfolio_when_provided(self):
        """Test that portfolio data is included in prompt when available"""
        # Mock the necessary modules
        with patch('llm_analyzer.genai'):
            with patch('llm_analyzer.config') as mock_config:
                mock_config.TARGET_EUR_ALLOCATION = 25
                
                from llm_analyzer import LLMAnalyzer
                
                # Create mock analyzer
                analyzer = Mock(spec=LLMAnalyzer)
                analyzer._create_analysis_prompt = LLMAnalyzer._create_analysis_prompt.__get__(analyzer)
                
                # Test data with portfolio
                market_summary = {
                    'current_price': 75000,
                    'price_change_24h': -1.2,
                    'price_change_7d': -3.5,
                    'moving_average_50': 76000,
                    'moving_average_200': 78000,
                    'volatility': 2.5
                }
                
                additional_context = {
                    'portfolio': {
                        'EUR': {'amount': 49.77},
                        'portfolio_value_eur': {'amount': 339.42}
                    }
                }
                
                # Generate prompt
                prompt = analyzer._create_analysis_prompt(
                    market_summary, 
                    'BTC-EUR', 
                    additional_context
                )
                
                # Verify portfolio context is in prompt
                assert 'PORTFOLIO BALANCE CONTEXT' in prompt
                assert 'EUR Available: €49.77' in prompt
                assert 'EUR Allocation: 14.7%' in prompt
                assert 'Target: 25%' in prompt
    
    def test_prompt_shows_warning_when_eur_below_target(self):
        """Test that prompt includes warning when EUR is below target"""
        with patch('llm_analyzer.genai'):
            with patch('llm_analyzer.config') as mock_config:
                mock_config.TARGET_EUR_ALLOCATION = 25
                
                from llm_analyzer import LLMAnalyzer
                
                analyzer = Mock(spec=LLMAnalyzer)
                analyzer._create_analysis_prompt = LLMAnalyzer._create_analysis_prompt.__get__(analyzer)
                
                market_summary = {
                    'current_price': 75000,
                    'price_change_24h': -1.2,
                    'price_change_7d': -3.5,
                    'moving_average_50': 76000,
                    'moving_average_200': 78000,
                    'volatility': 2.5
                }
                
                # EUR below target (14.7% vs 25%)
                additional_context = {
                    'portfolio': {
                        'EUR': {'amount': 49.77},
                        'portfolio_value_eur': {'amount': 339.42}
                    }
                }
                
                prompt = analyzer._create_analysis_prompt(
                    market_summary, 
                    'BTC-EUR', 
                    additional_context
                )
                
                # Should show warning and prefer SELL
                assert '⚠️ WARNING' in prompt
                assert 'below target' in prompt
                assert 'PREFER SELL' in prompt
                assert 'Be cautious with BUY' in prompt
    
    def test_prompt_shows_critical_warning_when_eur_very_low(self):
        """Test critical warning when EUR < 60% of target"""
        with patch('llm_analyzer.genai'):
            with patch('llm_analyzer.config') as mock_config:
                mock_config.TARGET_EUR_ALLOCATION = 25
                
                from llm_analyzer import LLMAnalyzer
                
                analyzer = Mock(spec=LLMAnalyzer)
                analyzer._create_analysis_prompt = LLMAnalyzer._create_analysis_prompt.__get__(analyzer)
                
                market_summary = {
                    'current_price': 75000,
                    'price_change_24h': -1.2,
                    'price_change_7d': -3.5,
                    'moving_average_50': 76000,
                    'moving_average_200': 78000,
                    'volatility': 2.5
                }
                
                # EUR critically low (10% vs 25% target = 40% of target)
                additional_context = {
                    'portfolio': {
                        'EUR': {'amount': 33.94},
                        'portfolio_value_eur': {'amount': 339.42}
                    }
                }
                
                prompt = analyzer._create_analysis_prompt(
                    market_summary, 
                    'BTC-EUR', 
                    additional_context
                )
                
                # Should show critical warning
                assert '⚠️ CRITICAL' in prompt
                assert 'VERY LOW' in prompt
                assert 'STRONGLY PREFER SELL' in prompt
                assert 'Avoid BUY signals unless extremely compelling' in prompt
    
    def test_prompt_encourages_buy_when_eur_high(self):
        """Test that prompt encourages BUY when EUR > 150% of target"""
        with patch('llm_analyzer.genai'):
            with patch('llm_analyzer.config') as mock_config:
                mock_config.TARGET_EUR_ALLOCATION = 25
                
                from llm_analyzer import LLMAnalyzer
                
                analyzer = Mock(spec=LLMAnalyzer)
                analyzer._create_analysis_prompt = LLMAnalyzer._create_analysis_prompt.__get__(analyzer)
                
                market_summary = {
                    'current_price': 75000,
                    'price_change_24h': -1.2,
                    'price_change_7d': -3.5,
                    'moving_average_50': 76000,
                    'moving_average_200': 78000,
                    'volatility': 2.5
                }
                
                # EUR high (40% vs 25% target = 160% of target)
                additional_context = {
                    'portfolio': {
                        'EUR': {'amount': 135.77},
                        'portfolio_value_eur': {'amount': 339.42}
                    }
                }
                
                prompt = analyzer._create_analysis_prompt(
                    market_summary, 
                    'BTC-EUR', 
                    additional_context
                )
                
                # Should encourage BUY
                assert '✅ EUR balance is HIGH' in prompt
                assert 'Good opportunity for BUY' in prompt
                assert 'Consider deploying excess capital' in prompt
    
    def test_prompt_works_without_portfolio(self):
        """Test that prompt generation works when portfolio is not provided"""
        with patch('llm_analyzer.genai'):
            from llm_analyzer import LLMAnalyzer
            
            analyzer = Mock(spec=LLMAnalyzer)
            analyzer._create_analysis_prompt = LLMAnalyzer._create_analysis_prompt.__get__(analyzer)
            
            market_summary = {
                'current_price': 75000,
                'price_change_24h': -1.2,
                'price_change_7d': -3.5,
                'moving_average_50': 76000,
                'moving_average_200': 78000,
                'volatility': 2.5
            }
            
            # No portfolio in context
            additional_context = {
                'indicators': {'rsi': 45}
            }
            
            prompt = analyzer._create_analysis_prompt(
                market_summary, 
                'BTC-EUR', 
                additional_context
            )
            
            # Should not crash, portfolio section should not be present
            assert 'PORTFOLIO BALANCE CONTEXT' not in prompt
            assert prompt is not None
            assert len(prompt) > 0


class TestPortfolioDataFlow:
    """Test that portfolio data flows through to LLM analyzer"""
    
    def test_analyze_market_passes_portfolio_to_context(self):
        """Test that analyze_market includes portfolio in additional_context"""
        with patch('llm_analyzer.genai'):
            with patch('llm_analyzer.pd'):
                from llm_analyzer import LLMAnalyzer
                
                # Create mock analyzer
                analyzer = Mock(spec=LLMAnalyzer)
                analyzer.analyze_market = LLMAnalyzer.analyze_market.__get__(analyzer)
                analyzer.analyze_market_data = Mock(return_value={'decision': 'HOLD', 'confidence': 50})
                
                # Test data with portfolio
                data = {
                    'product_id': 'BTC-EUR',
                    'current_price': 75000,
                    'historical_data': [],
                    'indicators': {'rsi': 45},
                    'market_data': {'price': 75000},
                    'portfolio': {
                        'EUR': {'amount': 49.77},
                        'portfolio_value_eur': {'amount': 339.42}
                    }
                }
                
                # Call analyze_market
                result = analyzer.analyze_market(data)
                
                # Verify analyze_market_data was called with portfolio in additional_context
                analyzer.analyze_market_data.assert_called_once()
                call_args = analyzer.analyze_market_data.call_args
                additional_context = call_args[1]['additional_context']
                
                assert 'portfolio' in additional_context
                assert additional_context['portfolio']['EUR']['amount'] == 49.77


class TestConfidenceThresholds:
    """Test that new confidence thresholds are properly configured"""
    
    def test_buy_threshold_is_70(self):
        """Test that BUY threshold is set to 70"""
        from config import config
        assert config.CONFIDENCE_THRESHOLD_BUY == 70.0
    
    def test_sell_threshold_is_55(self):
        """Test that SELL threshold is set to 55"""
        from config import config
        assert config.CONFIDENCE_THRESHOLD_SELL == 55.0
    
    def test_buy_threshold_higher_than_sell(self):
        """Test that BUY threshold is higher than SELL (encourages SELL)"""
        from config import config
        assert config.CONFIDENCE_THRESHOLD_BUY > config.CONFIDENCE_THRESHOLD_SELL
        assert config.CONFIDENCE_THRESHOLD_BUY - config.CONFIDENCE_THRESHOLD_SELL == 15.0
    
    def test_eur_allocation_target_is_25(self):
        """Test that EUR allocation target is 25%"""
        from config import config
        assert config.TARGET_EUR_ALLOCATION == 25.0
    
    def test_min_eur_reserve_is_25(self):
        """Test that minimum EUR reserve is 25"""
        from config import config
        assert config.MIN_EUR_RESERVE == 25.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
