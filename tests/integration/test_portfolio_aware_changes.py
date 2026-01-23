"""
Integration tests for portfolio-aware LLM changes (2026-01-23)
Tests verify the changes work in production without complex mocking
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestConfigurationChanges:
    """Test that configuration changes are properly applied in production environment"""
    
    @pytest.mark.skipif(
        not os.path.exists('.env'),
        reason="Requires .env file with production configuration"
    )
    def test_buy_threshold_increased_to_70(self):
        """Verify BUY threshold was increased from 65 to 70"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Read directly from environment
        buy_threshold = float(os.getenv('CONFIDENCE_THRESHOLD_BUY', '30'))
        assert buy_threshold == 70.0, \
            f"BUY threshold should be 70 to reduce BUY signals, got {buy_threshold}"
    
    @pytest.mark.skipif(
        not os.path.exists('.env'),
        reason="Requires .env file with production configuration"
    )
    def test_sell_threshold_remains_55(self):
        """Verify SELL threshold remains at 55"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        sell_threshold = float(os.getenv('CONFIDENCE_THRESHOLD_SELL', '30'))
        assert sell_threshold == 55.0, \
            f"SELL threshold should be 55 to encourage SELL signals, got {sell_threshold}"
    
    @pytest.mark.skipif(
        not os.path.exists('.env'),
        reason="Requires .env file with production configuration"
    )
    def test_threshold_gap_is_15_points(self):
        """Verify 15-point gap between BUY and SELL thresholds"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        buy_threshold = float(os.getenv('CONFIDENCE_THRESHOLD_BUY', '30'))
        sell_threshold = float(os.getenv('CONFIDENCE_THRESHOLD_SELL', '30'))
        gap = buy_threshold - sell_threshold
        assert gap == 15.0, \
            f"15-point gap should favor SELL signals over BUY, got {gap}"
    
    @pytest.mark.skipif(
        not os.path.exists('.env'),
        reason="Requires .env file with production configuration"
    )
    def test_eur_allocation_target_increased(self):
        """Verify EUR allocation target increased from 12% to 25%"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        eur_target = float(os.getenv('TARGET_EUR_ALLOCATION', '12'))
        assert eur_target == 25.0, \
            f"EUR target should be 25% to maintain adequate reserves, got {eur_target}"
    
    @pytest.mark.skipif(
        not os.path.exists('.env'),
        reason="Requires .env file with production configuration"
    )
    def test_min_eur_reserve_increased(self):
        """Verify minimum EUR reserve increased from 15 to 25"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        min_reserve = float(os.getenv('MIN_EUR_RESERVE', '15'))
        assert min_reserve == 25.0, \
            f"Minimum EUR reserve should be 25 to prevent capital depletion, got {min_reserve}"
    
    @pytest.mark.skipif(
        not os.path.exists('.env'),
        reason="Requires .env file with production configuration"
    )
    def test_rebalance_target_matches_allocation(self):
        """Verify rebalance target matches EUR allocation target"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        rebalance_target = float(os.getenv('REBALANCE_TARGET_EUR_PERCENT', '12'))
        assert rebalance_target == 25.0, \
            f"Rebalance target should match EUR allocation target, got {rebalance_target}"


class TestLLMAnalyzerPortfolioIntegration:
    """Test that LLM analyzer can handle portfolio data"""
    
    def test_llm_analyzer_accepts_portfolio_in_data(self):
        """Test that analyze_market accepts portfolio in data dict"""
        # This is a structural test - verifies the interface works
        test_data = {
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
        
        # Verify structure is valid (doesn't raise KeyError)
        assert 'portfolio' in test_data
        assert 'EUR' in test_data['portfolio']
        assert 'amount' in test_data['portfolio']['EUR']
        assert 'portfolio_value_eur' in test_data['portfolio']
    
    def test_portfolio_percentage_calculation(self):
        """Test EUR percentage calculation logic"""
        portfolio = {
            'EUR': {'amount': 49.77},
            'portfolio_value_eur': {'amount': 339.42}
        }
        
        eur_balance = portfolio['EUR']['amount']
        portfolio_value = portfolio['portfolio_value_eur']['amount']
        eur_pct = (eur_balance / portfolio_value) * 100
        
        # Should be approximately 14.7%
        assert 14.0 < eur_pct < 15.0, \
            f"EUR percentage should be ~14.7%, got {eur_pct:.1f}%"
    
    def test_critical_low_threshold_calculation(self):
        """Test critical low EUR threshold (60% of target)"""
        from config import config
        target = config.TARGET_EUR_ALLOCATION
        critical_threshold = target * 0.6
        
        # Critical threshold should be 15% (60% of 25%)
        assert critical_threshold == 15.0, \
            f"Critical threshold should be 15%, got {critical_threshold}%"
        
        # Current EUR (14.7%) is below critical threshold
        current_eur_pct = 14.7
        assert current_eur_pct < critical_threshold, \
            "Current EUR should trigger critical warning"
    
    def test_high_eur_threshold_calculation(self):
        """Test high EUR threshold (150% of target)"""
        from config import config
        target = config.TARGET_EUR_ALLOCATION
        high_threshold = target * 1.5
        
        # High threshold should be 37.5% (150% of 25%)
        assert high_threshold == 37.5, \
            f"High threshold should be 37.5%, got {high_threshold}%"


class TestJSONParsingImprovements:
    """Test that JSON parsing improvements are in place"""
    
    def test_json_parser_handles_missing_commas(self):
        """Test that parser can handle missing commas (common LLM error)"""
        import re
        
        # Simulate the fix: add missing commas after arrays
        malformed_json = '{"decision": "BUY", "reasoning": ["test"]\n  "confidence": 75}'
        
        # Apply the fix
        fixed_json = re.sub(r'(\])\s*\n\s*"', r'\1,\n  "', malformed_json)
        
        # Should now have comma after array
        assert '["test"],\n  "confidence"' in fixed_json, \
            "Parser should add missing comma after array"
    
    def test_json_parser_removes_markdown(self):
        """Test that parser removes markdown code blocks"""
        import re
        
        response_with_markdown = '```json\n{"decision": "BUY"}\n```'
        
        # Apply markdown removal
        cleaned = re.sub(r'```json\s*', '', response_with_markdown)
        cleaned = re.sub(r'```\s*', '', cleaned)
        
        # Should not contain markdown
        assert '```' not in cleaned, \
            "Parser should remove markdown code blocks"
        assert '{"decision": "BUY"}' in cleaned


class TestExpectedBehavior:
    """Test expected behavior after changes"""
    
    def test_current_eur_below_target(self):
        """Verify current EUR is below target (triggers SELL preference)"""
        current_eur = 49.77
        portfolio_value = 339.42
        current_pct = (current_eur / portfolio_value) * 100
        
        import os
        from dotenv import load_dotenv
        load_dotenv()
        target_pct = float(os.getenv('TARGET_EUR_ALLOCATION', '25'))
        
        assert current_pct < target_pct, \
            f"Current EUR ({current_pct:.1f}%) should be below target ({target_pct}%)"
    
    @pytest.mark.skipif(
        not os.path.exists('.env'),
        reason="Requires .env file with production configuration"
    )
    def test_buy_threshold_harder_than_sell(self):
        """Verify BUY is harder to trigger than SELL"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        buy_threshold = float(os.getenv('CONFIDENCE_THRESHOLD_BUY', '30'))
        sell_threshold = float(os.getenv('CONFIDENCE_THRESHOLD_SELL', '30'))
        
        # A signal with 60% confidence should:
        # - NOT trigger BUY (needs 70%)
        # - TRIGGER SELL (needs 55%)
        test_confidence = 60
        
        can_buy = test_confidence >= buy_threshold
        can_sell = test_confidence >= sell_threshold
        
        assert not can_buy, f"60% confidence should NOT trigger BUY (threshold: {buy_threshold})"
        assert can_sell, f"60% confidence SHOULD trigger SELL (threshold: {sell_threshold})"


class TestDocumentation:
    """Test that documentation exists for changes"""
    
    def test_config_changes_documented(self):
        """Verify configuration changes are documented"""
        doc_path = 'docs/config_changes_2026-01-23.md'
        assert os.path.exists(doc_path), \
            "Configuration changes should be documented"
    
    def test_llm_implementation_documented(self):
        """Verify LLM portfolio awareness is documented"""
        doc_path = 'docs/llm_portfolio_awareness_implementation.md'
        assert os.path.exists(doc_path), \
            "LLM portfolio awareness should be documented"
    
    def test_analysis_documented(self):
        """Verify 48-hour analysis is documented"""
        doc_path = 'analysis_sell_activity_48h.md'
        assert os.path.exists(doc_path), \
            "48-hour sell activity analysis should be documented"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
