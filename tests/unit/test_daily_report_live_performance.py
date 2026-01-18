"""
Unit tests for Daily Report Live Performance Integration

Tests the integration of live performance reporting into daily email reports.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the problematic imports before importing daily_report
sys.modules['google.genai'] = MagicMock()
sys.modules['llm_analyzer'] = MagicMock()

from daily_report import markdown_to_html


class TestDailyReportLivePerformance:
    """Test live performance integration in daily reports"""
    
    @pytest.fixture
    def report_generator(self):
        """Create report generator with mocked dependencies"""
        with patch('daily_report.LLMAnalyzer'), \
             patch('daily_report.Config'):
            from daily_report import DailyReportGenerator
            generator = DailyReportGenerator()
            return generator
    
    def test_get_live_performance_report_success(self, report_generator):
        """Test successful live performance report loading"""
        mock_report = {
            'report_type': 'live_performance',
            'strategy_usage': {
                'total_decisions': 42,
                'action_breakdown': {'BUY': 8, 'SELL': 6, 'HOLD': 28},
                'average_confidence': 72.3
            },
            'trading_performance': {
                'total_trades': 18,
                'buy_trades': 3,
                'sell_trades': 2,
                'trading_frequency': 2.57,
                'net_flow': 12.74
            }
        }
        
        with patch('utils.monitoring.live_performance_tracker.LivePerformanceTracker') as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker.generate_live_performance_report.return_value = mock_report
            mock_tracker_class.return_value = mock_tracker
            
            result = report_generator.get_live_performance_report()
            
            assert result == mock_report
            assert 'error' not in result
    
    def test_get_live_performance_report_error(self, report_generator):
        """Test live performance report with error"""
        with patch('utils.monitoring.live_performance_tracker.LivePerformanceTracker') as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker.generate_live_performance_report.return_value = {
                'error': 'Test error'
            }
            mock_tracker_class.return_value = mock_tracker
            
            result = report_generator.get_live_performance_report()
            
            assert result['status'] == 'error'
    
    def test_get_live_performance_report_exception(self, report_generator):
        """Test live performance report with exception"""
        with patch('utils.monitoring.live_performance_tracker.LivePerformanceTracker') as mock_tracker_class:
            mock_tracker_class.side_effect = Exception("Test exception")
            
            result = report_generator.get_live_performance_report()
            
            assert result['status'] == 'error'
            assert 'Test exception' in result['message']
    
    def test_format_live_performance_html_success(self, report_generator):
        """Test HTML formatting of live performance data"""
        live_performance = {
            'strategy_usage': {
                'total_decisions': 42,
                'action_breakdown': {'BUY': 8, 'SELL': 6, 'HOLD': 28},
                'average_confidence': 72.3
            },
            'trading_performance': {
                'total_trades': 18,
                'buy_trades': 3,
                'sell_trades': 2,
                'trading_frequency': 2.57,
                'net_flow': 12.74
            }
        }
        
        html = report_generator._format_live_performance_html(live_performance)
        
        assert '📊 Live Performance' in html
        assert 'Total Decisions: 42' in html
        assert 'BUY: 8' in html
        assert 'SELL: 6' in html
        assert 'HOLD: 28' in html
        assert 'Avg Confidence: 72.3%' in html
        assert 'Total: 18 trades' in html
        assert 'Frequency: 2.57 trades/day' in html
        assert 'Net Flow: €+12.74' in html
        assert 'ACTUAL bot decisions from real Google Gemini API' in html
    
    def test_format_live_performance_html_negative_flow(self, report_generator):
        """Test HTML formatting with negative net flow"""
        live_performance = {
            'strategy_usage': {
                'total_decisions': 10,
                'action_breakdown': {'BUY': 2, 'SELL': 3, 'HOLD': 5},
                'average_confidence': 65.0
            },
            'trading_performance': {
                'total_trades': 5,
                'buy_trades': 2,
                'sell_trades': 3,
                'trading_frequency': 0.71,
                'net_flow': -25.50
            }
        }
        
        html = report_generator._format_live_performance_html(live_performance)
        
        assert 'Net Flow: €-25.50' in html
        assert '#dc3545' in html  # Red color for negative
    
    def test_format_live_performance_html_error(self, report_generator):
        """Test HTML formatting with malformed data"""
        live_performance = {'invalid': 'data'}
        
        html = report_generator._format_live_performance_html(live_performance)
        
        # Should return HTML with default/zero values, not empty string
        assert isinstance(html, str)
    
    def test_create_html_email_includes_live_performance(self, report_generator):
        """Test that email HTML includes live performance section"""
        live_performance = {
            'strategy_usage': {
                'total_decisions': 10,
                'action_breakdown': {'BUY': 2, 'SELL': 1, 'HOLD': 7},
                'average_confidence': 70.0
            },
            'trading_performance': {
                'total_trades': 3,
                'buy_trades': 2,
                'sell_trades': 1,
                'trading_frequency': 0.43,
                'net_flow': 5.0
            }
        }
        
        portfolio = {
            'EUR': {'amount': 100.0},
            'BTC': {'amount': 0.001, 'last_price_eur': 80000},
            'ETH': {'amount': 0.05, 'last_price_eur': 2800},
            'SOL': {'amount': 0, 'last_price_eur': 150}
        }
        
        value_changes = {
            'current_value': 1000.0,
            'initial_value': 950.0,
            'total_change': 50.0,
            'total_change_pct': 5.26,
            'trading_performance': {'status': 'error'}
        }
        
        html = report_generator._create_html_email(
            total_value=1000.0,
            trades_count=3,
            errors_count=0,
            portfolio=portfolio,
            value_changes=value_changes,
            ai_analysis="<p>Test analysis</p>",
            server_ip="192.168.1.1",
            live_performance=live_performance
        )
        
        assert '📊 Live Performance' in html
        assert 'Total Decisions: 10' in html
        assert 'ACTUAL bot decisions' in html
    
    def test_create_html_email_without_live_performance(self, report_generator):
        """Test email HTML when live performance is not available"""
        portfolio = {
            'EUR': {'amount': 100.0},
            'BTC': {'amount': 0.001, 'last_price_eur': 80000},
            'ETH': {'amount': 0.05, 'last_price_eur': 2800},
            'SOL': {'amount': 0, 'last_price_eur': 150}
        }
        
        value_changes = {
            'current_value': 1000.0,
            'initial_value': 950.0,
            'total_change': 50.0,
            'total_change_pct': 5.26,
            'trading_performance': {'status': 'error'}
        }
        
        html = report_generator._create_html_email(
            total_value=1000.0,
            trades_count=3,
            errors_count=0,
            portfolio=portfolio,
            value_changes=value_changes,
            ai_analysis="<p>Test analysis</p>",
            server_ip="192.168.1.1",
            live_performance=None
        )
        
        # Should not include live performance section
        assert '📊 Live Performance' not in html
        # But should still have other sections
        assert 'Portfolio Value' in html
        assert 'AI Market Analysis' in html


class TestMarkdownToHtmlConversion:
    """Test markdown to HTML conversion for AI analysis"""
    
    def test_markdown_headers(self):
        """Test header conversion"""
        markdown = "### Main Header\n** Sub Header"
        html = markdown_to_html(markdown)
        
        assert '<h3' in html
        assert 'Main Header' in html
        assert '<h4' in html
        assert 'Sub Header' in html
    
    def test_markdown_bold(self):
        """Test bold text conversion"""
        markdown = "This is **bold text** in a sentence"
        html = markdown_to_html(markdown)
        
        assert '<strong>bold text</strong>' in html
    
    def test_markdown_bullets(self):
        """Test bullet point conversion"""
        markdown = "* First item\n* Second item\n* Third item"
        html = markdown_to_html(markdown)
        
        assert '<li' in html
        assert '<ul' in html
        assert 'First item' in html
        assert 'Second item' in html
    
    def test_markdown_paragraphs(self):
        """Test paragraph conversion"""
        markdown = "First paragraph\n\nSecond paragraph"
        html = markdown_to_html(markdown)
        
        assert '<p' in html
        assert 'First paragraph' in html
        assert 'Second paragraph' in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
