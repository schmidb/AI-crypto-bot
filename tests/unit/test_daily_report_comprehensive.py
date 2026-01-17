#!/usr/bin/env python3
"""
Comprehensive tests for daily_report.py
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
import json
import os

# Mock the problematic imports before importing daily_report
sys.modules['google.genai'] = Mock()
sys.modules['llm_analyzer'] = Mock()
# Don't mock config globally - use patches in individual tests instead

# Now we can import
from daily_report import markdown_to_html


# Test the standalone markdown_to_html function first (no imports needed)
def test_markdown_to_html_headers():
    """Test markdown header conversion"""
    text = "### Test Header"
    result = markdown_to_html(text)
    assert '<h3 style="color: #333; margin: 15px 0 10px 0; font-size: 16px;">Test Header</h3>' in result

def test_markdown_to_html_bold():
    """Test bold text conversion"""
    text = "This is **bold text** here"
    result = markdown_to_html(text)
    assert '<strong>bold text</strong>' in result


def test_markdown_to_html_bullets():
    """Test bullet point conversion"""
    text = "* First item\n* Second item"
    result = markdown_to_html(text)
    assert '<ul style="margin: 10px 0; padding-left: 20px;">' in result
    assert '<li style="margin: 5px 0;">First item</li>' in result
    assert '<li style="margin: 5px 0;">Second item</li>' in result


def test_markdown_to_html_paragraphs():
    """Test paragraph conversion"""
    text = "First paragraph\n\nSecond paragraph"
    result = markdown_to_html(text)
    assert '<p style="margin: 10px 0; line-height: 1.6;">First paragraph</p>' in result
    assert '<p style="margin: 10px 0; line-height: 1.6;">Second paragraph</p>' in result


def test_markdown_to_html_complex():
    """Test complex markdown with multiple elements"""
    text = """### Daily Report

**Status:** Operational

* Item 1 with **bold**
* Item 2

Regular paragraph here."""
    
    result = markdown_to_html(text)
    assert '<h3' in result
    assert '<strong>Status:</strong>' in result or '<strong>Status</strong>' in result
    assert '<ul' in result
    assert '<li' in result
    # Paragraph may or may not be wrapped depending on context
    assert 'Regular paragraph' in result


@pytest.fixture
def mock_config():
    """Mock Config object"""
    config = Mock()
    config.GMAIL_USER = "test@example.com"
    config.GMAIL_APP_PASSWORD = "test_password"
    return config


@pytest.fixture
def mock_llm_analyzer():
    """Mock LLM analyzer"""
    analyzer = Mock()
    return analyzer


@pytest.fixture
def mock_report_generator():
    """Create a mocked DailyReportGenerator"""
    # Mock the Config and LLMAnalyzer classes at module level
    with patch('daily_report.Config') as mock_config_class, \
         patch('daily_report.LLMAnalyzer') as mock_llm_class:
        
        # Configure the mocks to return Mock instances
        mock_config_class.return_value = Mock()
        mock_llm_class.return_value = Mock()
        
        # Import after patching
        import importlib
        import daily_report as dr_module
        importlib.reload(dr_module)
        
        generator = dr_module.DailyReportGenerator()
        generator.config = Mock()
        generator.llm_analyzer = Mock()
        generator.llm_analyzer.client = Mock()
        
        yield generator
        
        # Cleanup: reload again to reset module state
        importlib.reload(dr_module)


def test_daily_report_generator_init(mock_report_generator):
    """Test DailyReportGenerator initialization"""
    assert mock_report_generator is not None
    assert hasattr(mock_report_generator, 'config')
    assert hasattr(mock_report_generator, 'llm_analyzer')


def test_analyze_logs_last_24h_no_files(mock_report_generator):
    """Test log analysis when files don't exist"""
    with patch('os.path.exists', return_value=False), \
         patch('builtins.open', side_effect=FileNotFoundError()):
        result = mock_report_generator.analyze_logs_last_24h()
        
        # Should return error dict when all files missing
        assert 'error' in result or result.get('total_log_entries') == 0


def test_analyze_logs_last_24h_with_trades(mock_report_generator):
    """Test log analysis with trade data"""
    today = datetime.now().strftime('%Y-%m-%d')
    log_content = f"{today} 01:00:00 - INFO - order executed: BUY 0.01 BTC\n"
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=log_content)):
        
        result = mock_report_generator.analyze_logs_last_24h()
        
        assert result['total_log_entries'] > 0
        assert len(result['trades_executed']) > 0


def test_get_portfolio_status_success(mock_report_generator):
    """Test portfolio status retrieval"""
    portfolio_data = {
        'portfolio_value_eur': {'amount': 1000.0},
        'BTC': {'amount': 0.01},
        'EUR': {'amount': 100.0}
    }
    
    with patch('builtins.open', mock_open(read_data=json.dumps(portfolio_data))):
        result = mock_report_generator.get_portfolio_status()
        
        # Returns portfolio dict directly, not wrapped in status
        assert result['portfolio_value_eur']['amount'] == 1000.0
        assert 'BTC' in result


def test_get_portfolio_status_file_not_found(mock_report_generator):
    """Test portfolio status when file doesn't exist"""
    with patch('builtins.open', side_effect=FileNotFoundError()):
        result = mock_report_generator.get_portfolio_status()
        
        assert 'error' in result


def test_calculate_value_changes(mock_report_generator):
    """Test value change calculations"""
    portfolio = {
        'portfolio_value_eur': {'amount': 1100.0},
        'initial_value_eur': {'amount': 1000.0},
        'trades_executed': 5,
        'BTC': {'initial_amount': 0.01},
        'ETH': {'initial_amount': 0.1},
        'SOL': {'initial_amount': 0},
        'EUR': {'initial_amount': 100}
    }
    
    # Mock the trading_vs_holding calculation
    mock_report_generator.calculate_trading_vs_holding = Mock(return_value={
        'status': 'success',
        'hold_value': 1050.0,
        'trading_alpha': 50.0
    })
    
    result = mock_report_generator.calculate_value_changes(portfolio)
    
    assert result['current_value'] == 1100.0
    assert result['initial_value'] == 1000.0
    assert result['total_change'] == 100.0
    assert result['total_change_pct'] == 10.0
    assert result['change_status'] == 'GAIN'


def test_calculate_value_changes_negative(mock_report_generator):
    """Test value change calculations with loss"""
    portfolio = {
        'portfolio_value_eur': {'amount': 900.0},
        'initial_value_eur': {'amount': 1000.0},
        'trades_executed': 3,
        'BTC': {'initial_amount': 0.01},
        'ETH': {'initial_amount': 0.1},
        'SOL': {'initial_amount': 0},
        'EUR': {'initial_amount': 100}
    }
    
    # Mock the trading_vs_holding calculation
    mock_report_generator.calculate_trading_vs_holding = Mock(return_value={
        'status': 'success',
        'hold_value': 950.0,
        'trading_alpha': -50.0
    })
    
    result = mock_report_generator.calculate_value_changes(portfolio)
    
    assert result['total_change'] == -100.0
    assert result['total_change_pct'] == -10.0
    assert result['change_status'] == 'LOSS'


# ============================================================================
# STEP 1: Comprehensive tests for calculate_trading_vs_holding()
# ============================================================================

def test_calculate_trading_vs_holding_outperforming(mock_report_generator):
    """Test trading vs holding when trading outperforms"""
    portfolio = {
        'portfolio_value_eur': {'amount': 1200.0},
        'BTC': {'initial_amount': 0.01},
        'ETH': {'initial_amount': 0.1},
        'SOL': {'initial_amount': 0.0},
        'EUR': {'initial_amount': 100.0}
    }
    
    # Mock Coinbase client at the import location
    with patch('coinbase_client.CoinbaseClient') as mock_coinbase:
        mock_client = Mock()
        mock_client.get_product_ticker.side_effect = [
            {'price': '50000.0'},  # BTC
            {'price': '3000.0'},   # ETH
            {'price': '100.0'}     # SOL
        ]
        mock_coinbase.return_value = mock_client
        
        result = mock_report_generator.calculate_trading_vs_holding(portfolio)
        
        assert result['status'] == 'success'
        assert result['hold_value'] == 900.0  # 0.01*50000 + 0.1*3000 + 100 = 900
        assert result['current_value'] == 1200.0
        assert result['trading_alpha'] == 300.0
        assert result['trading_alpha_pct'] > 0
        assert result['performance_status'] == 'OUTPERFORMING'
        assert result['performance_emoji'] == '🎯'


def test_calculate_trading_vs_holding_underperforming(mock_report_generator):
    """Test trading vs holding when trading underperforms"""
    portfolio = {
        'portfolio_value_eur': {'amount': 800.0},
        'BTC': {'initial_amount': 0.01},
        'ETH': {'initial_amount': 0.1},
        'SOL': {'initial_amount': 0.0},
        'EUR': {'initial_amount': 100.0}
    }
    
    with patch('coinbase_client.CoinbaseClient') as mock_coinbase:
        mock_client = Mock()
        mock_client.get_product_ticker.side_effect = [
            {'price': '50000.0'},
            {'price': '3000.0'},
            {'price': '100.0'}
        ]
        mock_coinbase.return_value = mock_client
        
        result = mock_report_generator.calculate_trading_vs_holding(portfolio)
        
        assert result['status'] == 'success'
        assert result['hold_value'] == 900.0
        assert result['current_value'] == 800.0
        assert result['trading_alpha'] == -100.0
        assert result['trading_alpha_pct'] < 0
        assert result['performance_status'] == 'UNDERPERFORMING'
        assert result['performance_emoji'] == '📉'


def test_calculate_trading_vs_holding_neutral(mock_report_generator):
    """Test trading vs holding when performance is neutral"""
    portfolio = {
        'portfolio_value_eur': {'amount': 900.0},
        'BTC': {'initial_amount': 0.01},
        'ETH': {'initial_amount': 0.1},
        'SOL': {'initial_amount': 0.0},
        'EUR': {'initial_amount': 100.0}
    }
    
    with patch('coinbase_client.CoinbaseClient') as mock_coinbase:
        mock_client = Mock()
        mock_client.get_product_ticker.side_effect = [
            {'price': '50000.0'},
            {'price': '3000.0'},
            {'price': '100.0'}
        ]
        mock_coinbase.return_value = mock_client
        
        result = mock_report_generator.calculate_trading_vs_holding(portfolio)
        
        assert result['status'] == 'success'
        assert result['trading_alpha'] == 0.0
        assert result['performance_status'] == 'NEUTRAL'
        assert result['performance_emoji'] == '➡️'


def test_calculate_trading_vs_holding_with_sol(mock_report_generator):
    """Test trading vs holding with SOL holdings"""
    portfolio = {
        'portfolio_value_eur': {'amount': 1500.0},
        'BTC': {'initial_amount': 0.01},
        'ETH': {'initial_amount': 0.1},
        'SOL': {'initial_amount': 5.0},
        'EUR': {'initial_amount': 100.0}
    }
    
    with patch('coinbase_client.CoinbaseClient') as mock_coinbase:
        mock_client = Mock()
        mock_client.get_product_ticker.side_effect = [
            {'price': '50000.0'},  # BTC
            {'price': '3000.0'},   # ETH
            {'price': '120.0'}     # SOL
        ]
        mock_coinbase.return_value = mock_client
        
        result = mock_report_generator.calculate_trading_vs_holding(portfolio)
        
        assert result['status'] == 'success'
        # hold_value = 0.01*50000 + 0.1*3000 + 5*120 + 100 = 500 + 300 + 600 + 100 = 1500
        assert result['hold_value'] == 1500.0
        assert result['current_value'] == 1500.0
        assert result['trading_alpha'] == 0.0


def test_calculate_trading_vs_holding_api_error(mock_report_generator):
    """Test trading vs holding when API fails"""
    portfolio = {
        'portfolio_value_eur': {'amount': 1000.0},
        'BTC': {'initial_amount': 0.01}
    }
    
    with patch('coinbase_client.CoinbaseClient') as mock_coinbase:
        mock_coinbase.side_effect = Exception("API Error")
        
        result = mock_report_generator.calculate_trading_vs_holding(portfolio)
        
        assert result['status'] == 'error'
        assert 'error' in result


def test_calculate_trading_vs_holding_zero_hold_value(mock_report_generator):
    """Test trading vs holding with zero initial holdings"""
    portfolio = {
        'portfolio_value_eur': {'amount': 1000.0},
        'BTC': {'initial_amount': 0.0},
        'ETH': {'initial_amount': 0.0},
        'SOL': {'initial_amount': 0.0},
        'EUR': {'initial_amount': 0.0}
    }
    
    with patch('coinbase_client.CoinbaseClient') as mock_coinbase:
        mock_client = Mock()
        mock_client.get_product_ticker.side_effect = [
            {'price': '50000.0'},
            {'price': '3000.0'},
            {'price': '100.0'}
        ]
        mock_coinbase.return_value = mock_client
        
        result = mock_report_generator.calculate_trading_vs_holding(portfolio)
        
        assert result['status'] == 'success'
        assert result['hold_value'] == 0.0
        assert result['trading_alpha_pct'] == 0.0  # Avoid division by zero


def test_calculate_trading_vs_holding_missing_price_data(mock_report_generator):
    """Test trading vs holding when price data is missing"""
    portfolio = {
        'portfolio_value_eur': {'amount': 1000.0},
        'BTC': {'initial_amount': 0.01},
        'ETH': {'initial_amount': 0.1},
        'SOL': {'initial_amount': 0.0},
        'EUR': {'initial_amount': 100.0}
    }
    
    with patch('coinbase_client.CoinbaseClient') as mock_coinbase:
        mock_client = Mock()
        mock_client.get_product_ticker.side_effect = [
            {},  # Missing price for BTC
            {'price': '3000.0'},
            {'price': '100.0'}
        ]
        mock_coinbase.return_value = mock_client
        
        result = mock_report_generator.calculate_trading_vs_holding(portfolio)
        
        # Should handle missing price gracefully (defaults to 0)
        assert result['status'] == 'success'
        assert result['hold_value'] == 400.0  # 0*0 + 0.1*3000 + 100 = 400

# ============================================================================


def test_generate_ai_analysis_success(mock_report_generator):
    """Test AI analysis generation"""
    log_data = {
        'total_log_entries': 100,
        'trades_executed': ['BUY 0.01 BTC'],
        'errors': []
    }
    portfolio = {
        'portfolio_value_eur': {'amount': 1000.0},
        'BTC': {'amount': 0.01},
        'EUR': {'amount': 100.0}
    }
    
    # Mock the LLM response
    mock_response = Mock()
    mock_candidate = Mock()
    mock_content = Mock()
    mock_part = Mock()
    mock_part.text = "### Test Analysis\n\n**Status:** Good"
    mock_content.parts = [mock_part]
    mock_candidate.content = mock_content
    mock_response.candidates = [mock_candidate]
    
    mock_report_generator.llm_analyzer.client = Mock()
    mock_report_generator.llm_analyzer.client.models.generate_content.return_value = mock_response
    
    result = mock_report_generator.generate_ai_analysis(log_data, portfolio)
    
    assert result is not None
    assert '<h3' in result or 'Test Analysis' in result


def test_generate_ai_analysis_failure(mock_report_generator):
    """Test AI analysis generation with failure"""
    log_data = {'total_log_entries': 0, 'trades_executed': [], 'errors': []}
    portfolio = {'portfolio_value_eur': {'amount': 1000.0}}
    
    # Mock LLM failure
    mock_report_generator.llm_analyzer.client = Mock()
    mock_report_generator.llm_analyzer.client.models.generate_content.side_effect = Exception("API Error")
    
    result = mock_report_generator.generate_ai_analysis(log_data, portfolio)
    
    assert 'failed' in result.lower() or 'error' in result.lower()


def test_send_email_report_success(mock_report_generator):
    """Test email sending success"""
    with patch('smtplib.SMTP') as mock_smtp, \
         patch.dict(os.environ, {'GMAIL_USER': 'test@example.com', 'GMAIL_APP_PASSWORD': 'password'}):
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = mock_report_generator.send_email_report(
            subject="Test Report",
            body="<html><body>Test</body></html>",
            to_email="recipient@example.com"
        )
        
        assert result is True
        mock_server.sendmail.assert_called_once()


def test_send_email_report_no_password(mock_report_generator):
    """Test email sending without password configured"""
    with patch.dict(os.environ, {'GMAIL_APP_PASSWORD': ''}, clear=True):
        result = mock_report_generator.send_email_report(
            subject="Test",
            body="Test",
            to_email="test@example.com"
        )
        
        assert result is False


def test_send_email_report_smtp_failure(mock_report_generator):
    """Test email sending with SMTP failure"""
    with patch('smtplib.SMTP') as mock_smtp, \
         patch.dict(os.environ, {'GMAIL_USER': 'test@example.com', 'GMAIL_APP_PASSWORD': 'password'}):
        
        mock_smtp.side_effect = Exception("SMTP Error")
        
        result = mock_report_generator.send_email_report(
            subject="Test",
            body="Test",
            to_email="test@example.com"
        )
        
        assert result is False


def test_create_html_email(mock_report_generator):
    """Test HTML email creation"""
    portfolio = {
        'BTC': {'amount': 0.01, 'last_price_eur': 50000},
        'ETH': {'amount': 0.1, 'last_price_eur': 3000},
        'EUR': {'amount': 100}
    }
    value_changes = {
        'current_value': 1100,
        'initial_value': 1000,
        'total_change': 100,
        'total_change_pct': 10.0,
        'trading_performance': {
            'status': 'success',
            'hold_value': 1050,
            'trading_alpha': 50,
            'trading_alpha_pct': 4.76
        }
    }
    
    # Mock the _format_trading_performance_html method
    mock_report_generator._format_trading_performance_html = Mock(return_value="<div>Trading performance</div>")
    
    result = mock_report_generator._create_html_email(
        total_value=1100,
        trades_count=5,
        errors_count=0,
        portfolio=portfolio,
        value_changes=value_changes,
        ai_analysis="<p>Test analysis</p>",
        server_ip="192.168.1.1"
    )
    
    assert '<!DOCTYPE html>' in result
    assert 'BTC' in result
    assert 'ETH' in result
    assert 'Test analysis' in result


def test_convert_html_to_text(mock_report_generator):
    """Test HTML to text conversion"""
    html = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>"
    
    result = mock_report_generator._convert_html_to_text(html)
    
    assert 'Title' in result
    assert 'Paragraph' in result
    assert '<html>' not in result


def test_get_server_ip(mock_report_generator):
    """Test server IP retrieval"""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '192.168.1.100'
        mock_run.return_value = mock_result
        
        result = mock_report_generator.get_server_ip()
        
        assert result == '192.168.1.100'


def test_get_server_ip_failure(mock_report_generator):
    """Test server IP retrieval failure"""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Network error")
        
        result = mock_report_generator.get_server_ip()
        
        # Falls back to hardcoded IP
        assert result == '34.29.9.115'


def test_format_trading_performance_success(mock_report_generator):
    """Test trading performance formatting"""
    trading_perf = {
        'status': 'success',
        'performance_status': 'OUTPERFORMING',
        'hold_value': 1000.0,
        'current_value': 1100.0,
        'trading_alpha': 100.0,
        'trading_alpha_pct': 10.0,
        'performance_emoji': '🎯'
    }
    
    result = mock_report_generator._format_trading_performance(trading_perf)
    
    assert 'OUTPERFORMING' in result
    assert '100.0' in result or '100' in result
    assert '🎯' in result


def test_format_trading_performance_unavailable(mock_report_generator):
    """Test trading performance formatting when unavailable"""
    trading_perf = {'status': 'error'}
    
    result = mock_report_generator._format_trading_performance(trading_perf)
    
    # Returns empty string when status is not success
    assert result == ""


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
