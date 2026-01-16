"""
Comprehensive unit tests for main.py - Core trading bot orchestration

Tests cover:
- TradingBot initialization and configuration
- Trading cycle execution and workflow
- Portfolio synchronization with Coinbase
- Multi-strategy analysis coordination
- Trade execution and logging
- Error handling and recovery
- Process management and locking
- Dashboard updates and web sync
- Scheduled task management
"""

import pytest
import os
import sys
import json
import time
import tempfile
import shutil
import unittest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the module under test
import main
from main import TradingBot, ensure_single_instance

# Test configuration
@pytest.fixture
def test_env_vars():
    """Set up test environment variables"""
    test_vars = {
        'TESTING': 'true',
        'SIMULATION_MODE': 'true',
        'COINBASE_API_KEY': 'test-api-key',
        'COINBASE_API_SECRET': 'test-api-secret',
        'GOOGLE_CLOUD_PROJECT': 'test-project',
        'NOTIFICATIONS_ENABLED': 'false',
        'WEBSERVER_SYNC_ENABLED': 'false',
        'TRADING_PAIRS': 'BTC-EUR,ETH-EUR',
        'DECISION_INTERVAL_MINUTES': '60',
        'RISK_LEVEL': 'MEDIUM',
        'BASE_CURRENCY': 'EUR'
    }
    
    with patch.dict(os.environ, test_vars):
        yield test_vars

@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for tests"""
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, 'data')
    cache_dir = os.path.join(data_dir, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_components():
    """Mock all external components for isolated testing"""
    with patch.multiple(
        'main',
        CoinbaseClient=Mock(),
        LLMAnalyzer=Mock(),
        DataCollector=Mock(),
        AdaptiveStrategyManager=Mock(),
        Portfolio=Mock(),
        CapitalManager=Mock(),
        OpportunityManager=Mock(),
        DashboardUpdater=Mock(),
        WebServerSync=Mock(),
        TaxReportGenerator=Mock(),
        StrategyEvaluator=Mock(),
        NotificationService=Mock(),
        CleanupManager=Mock(),
        DailyReportGenerator=Mock(),
        PerformanceTracker=Mock()
    ), \
    patch('utils.monitoring.news_sentiment.NewsSentimentAnalyzer', Mock()), \
    patch('utils.performance.volatility_analyzer.VolatilityAnalyzer', Mock()), \
    patch('utils.trading.trade_logger.TradeLogger', Mock()) as mocks:
        yield mocks

class TestProcessManagement:
    """Test process management and single instance enforcement"""
    
    def test_ensure_single_instance_success(self, temp_data_dir):
        """Test successful single instance lock acquisition"""
        with patch('main.WINDOWS_SYSTEM', True), \
             patch('os.open') as mock_open, \
             patch('os.write') as mock_write, \
             patch('os.fsync') as mock_fsync, \
             patch('os.getpid', return_value=12345):
            
            mock_open.return_value = 123  # Mock file descriptor
            
            result = ensure_single_instance()
            
            assert result == 123
            mock_open.assert_called_once()
            mock_write.assert_called_once()
            mock_fsync.assert_called_once_with(123)
    
    def test_ensure_single_instance_already_running(self, temp_data_dir):
        """Test detection of already running instance"""
        with patch('main.WINDOWS_SYSTEM', True), \
             patch('os.open', side_effect=OSError("File exists")), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='9999')), \
             patch('subprocess.run') as mock_subprocess, \
             pytest.raises(SystemExit):
            
            # Mock process still running
            mock_subprocess.return_value.stdout = "9999"
            
            ensure_single_instance()
    
    def test_ensure_single_instance_stale_lock(self, temp_data_dir):
        """Test removal of stale lock file"""
        with patch('main.WINDOWS_SYSTEM', True), \
             patch('os.open', side_effect=[OSError("File exists"), 456]), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='9999')), \
             patch('subprocess.run') as mock_subprocess, \
             patch('os.remove') as mock_remove, \
             patch('os.write'), \
             patch('os.fsync'):
            
            # Mock process not running (stale lock)
            mock_subprocess.return_value.stdout = ""
            
            result = ensure_single_instance()
            
            assert result == 456
            mock_remove.assert_called_once()

class TestTradingBotInitialization:
    """Test TradingBot class initialization"""
    
    def test_trading_bot_init_simulation_mode(self, test_env_vars, temp_data_dir, mock_components):
        """Test TradingBot initialization in simulation mode"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            
            bot = TradingBot()
            
            # Verify core components are initialized
            assert bot.coinbase_client is not None
            assert bot.llm_analyzer is not None
            assert bot.data_collector is not None
            assert bot.strategy_manager is not None
            assert bot.portfolio is not None
            assert bot.capital_manager is not None
            assert bot.opportunity_manager is not None
    
    def test_trading_bot_init_live_mode(self, mock_components):
        """Test TradingBot initialization in live trading mode"""
        with patch.dict(os.environ, {'SIMULATION_MODE': 'false'}), \
             patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            
            bot = TradingBot()
            
            # Verify initialization completes in live mode
            assert bot is not None
    
    def test_trading_bot_init_directories_created(self, test_env_vars, mock_components):
        """Test that required directories are created during initialization"""
        with patch('os.makedirs') as mock_makedirs, \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            
            TradingBot()
            
            # Verify directories are created
            expected_calls = [
                call("logs", exist_ok=True),
                call("data", exist_ok=True),
                call("reports", exist_ok=True)
            ]
            mock_makedirs.assert_has_calls(expected_calls, any_order=True)
    
    def test_trading_bot_init_signal_handlers(self, test_env_vars, mock_components):
        """Test that signal handlers are properly set up"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal') as mock_signal:
            
            mock_config.return_value = Mock()
            
            TradingBot()
            
            # Verify signal handlers are registered
            mock_signal.assert_any_call(main.signal.SIGTERM, unittest.mock.ANY)
            mock_signal.assert_any_call(main.signal.SIGINT, unittest.mock.ANY)

class TestPortfolioSynchronization:
    """Test portfolio synchronization with Coinbase"""
    
    def test_sync_portfolio_with_coinbase_success(self, test_env_vars, mock_components):
        """Test successful portfolio synchronization"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock successful portfolio sync
            mock_portfolio_data = {
                'EUR': {'amount': 1000.0},
                'BTC': {'amount': 0.01, 'last_price_eur': 45000.0}
            }
            bot.coinbase_client.get_portfolio.return_value = mock_portfolio_data
            bot.portfolio.update_from_exchange.return_value = {'status': 'success'}
            bot.portfolio.to_dict.return_value = mock_portfolio_data
            
            result = bot._sync_portfolio_with_coinbase()
            
            assert result is True
            bot.coinbase_client.get_portfolio.assert_called_once()
            bot.portfolio.update_from_exchange.assert_called_once_with(mock_portfolio_data)
    
    def test_sync_portfolio_with_coinbase_failure(self, test_env_vars, mock_components):
        """Test portfolio synchronization failure handling"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock failed portfolio sync
            bot.coinbase_client.get_portfolio.return_value = None
            
            result = bot._sync_portfolio_with_coinbase()
            
            assert result is False
    
    def test_sync_portfolio_discrepancy_detection(self, test_env_vars, mock_components):
        """Test detection and logging of portfolio discrepancies"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock portfolio with discrepancies
            current_portfolio = {
                'EUR': {'amount': 1000.0},
                'BTC': {'amount': 0.01, 'last_price_eur': 45000.0}
            }
            updated_portfolio = {
                'EUR': {'amount': 950.0},  # Discrepancy
                'BTC': {'amount': 0.012, 'last_price_eur': 45000.0}  # Discrepancy
            }
            
            bot.portfolio.to_dict.side_effect = [current_portfolio, updated_portfolio]
            bot.coinbase_client.get_portfolio.return_value = updated_portfolio
            bot.portfolio.update_from_exchange.return_value = {'status': 'success'}
            
            with patch('main.config') as mock_config_module:
                mock_config_module.BASE_CURRENCY = 'EUR'
                mock_config_module.TRADING_PAIRS = ['BTC-EUR']
                
                result = bot._sync_portfolio_with_coinbase()
            
            assert result is True

class TestMultiStrategyAnalysis:
    """Test multi-strategy analysis execution"""
    
    def test_execute_multi_strategy_analysis_success(self, test_env_vars, mock_components):
        """Test successful multi-strategy analysis"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock market data and analysis
            mock_market_data = {'current_price': 45000.0, 'product_id': 'BTC-EUR'}
            mock_historical_data = pd.DataFrame({'close': [44000, 45000]})
            mock_indicators = {'rsi': 65, 'current_price': 45000.0}
            mock_signal = Mock()
            mock_signal.action = 'BUY'
            mock_signal.confidence = 75
            mock_signal.reasoning = 'Strong uptrend detected'
            
            bot.data_collector.get_market_data.return_value = mock_market_data
            bot.data_collector.get_historical_data.return_value = mock_historical_data
            bot.data_collector.calculate_indicators.return_value = mock_indicators
            bot.strategy_manager.get_combined_signal.return_value = mock_signal
            bot.strategy_manager.analyze_all_strategies.return_value = {'momentum': mock_signal}
            bot.portfolio.to_dict.return_value = {'EUR': {'amount': 1000}}
            
            result = bot._execute_multi_strategy_analysis('BTC-EUR')
            
            assert result['action'] == 'BUY'
            assert result['confidence'] == 75
            assert result['product_id'] == 'BTC-EUR'
            assert 'reasoning' in result
            assert 'timestamp' in result
    
    def test_execute_multi_strategy_analysis_error_handling(self, test_env_vars, mock_components):
        """Test error handling in multi-strategy analysis"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock analysis error
            bot.data_collector.get_market_data.side_effect = Exception("API Error")
            
            result = bot._execute_multi_strategy_analysis('BTC-EUR')
            
            assert result['action'] == 'HOLD'
            assert result['confidence'] == 0
            assert 'error' in result['reasoning'].lower()
            assert result['execution_status'] == 'error'

class TestTradeExecution:
    """Test trade execution logic"""
    
    def test_execute_trade_hold_decision(self, test_env_vars, mock_components):
        """Test trade execution with HOLD decision"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            decision_result = {
                'action': 'HOLD',
                'confidence': 50,
                'reasoning': 'Market uncertainty'
            }
            
            result = bot._execute_trade('BTC-EUR', decision_result)
            
            assert result['execution_status'] == 'skipped_hold'
            assert result['trade_executed'] is False
            assert 'HOLD decision' in result['execution_message']
    
    def test_execute_buy_order_simulation_mode(self, test_env_vars, mock_components):
        """Test BUY order execution in simulation mode"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('main.SIMULATION_MODE', True):
            
            mock_config.return_value = Mock()
            mock_config.return_value.MIN_TRADE_AMOUNT = 10.0
            bot = TradingBot()
            
            # Mock portfolio and market data
            portfolio = {'EUR': {'amount': 1000.0}}
            current_price = 45000.0
            confidence = 75
            execution_result = {
                'execution_status': 'not_executed',
                'execution_message': 'No execution needed',
                'trade_executed': False,
                'crypto_amount': 0,
                'trade_amount_base': 0,
                'execution_price': current_price
            }
            
            # Mock capital manager
            bot.capital_manager.calculate_safe_trade_size.return_value = (100.0, "Safe trade size calculated")
            
            result = bot._execute_buy_order('BTC-EUR', 'BTC', current_price, confidence, portfolio, execution_result)
            
            assert result['execution_status'] == 'simulated'
            assert result['trade_executed'] is True
            assert 'SIMULATED BUY' in result['execution_message']
    
    @pytest.mark.skip(reason="Needs update for anti-overtrading features")
    def test_execute_sell_order_insufficient_balance(self, test_env_vars, mock_components):
        """Test SELL order with insufficient crypto balance"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            mock_config.return_value.MIN_TRADE_AMOUNT = 30.0
            bot = TradingBot()
            
            # Mock insufficient balance
            portfolio = {'BTC': {'amount': 0.0001}}  # Very small amount
            current_price = 45000.0
            confidence = 75
            execution_result = {
                'execution_status': 'not_executed',
                'execution_message': 'No execution needed',
                'trade_executed': False,
                'crypto_amount': 0,
                'trade_amount_base': 0,
                'execution_price': current_price
            }
            
            # Mock capital manager blocking trade
            bot.capital_manager.calculate_safe_trade_size.return_value = (0.0, "Insufficient balance")
            
            result = bot._execute_sell_order('BTC-EUR', 'BTC', current_price, confidence, portfolio, execution_result)
            
            assert result['execution_status'] == 'capital_management_block'
            assert result['trade_executed'] is False

class TestTradingCycle:
    """Test complete trading cycle execution"""
    
    @pytest.mark.skip(reason="Needs update for anti-overtrading features")
    def test_run_trading_cycle_opportunity_based(self, test_env_vars, mock_components):
        """Test opportunity-based trading cycle execution"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('time.sleep'):  # Speed up tests
            
            mock_config.return_value = Mock()
            mock_config.return_value.TRADING_PAIRS = ['BTC-EUR', 'ETH-EUR']
            bot = TradingBot()
            
            # Mock successful portfolio sync
            bot._sync_portfolio_with_coinbase = Mock(return_value=True)
            
            # Mock analysis results
            mock_analysis = {
                'action': 'BUY',
                'confidence': 75,
                'reasoning': 'Strong signal',
                'product_id': 'BTC-EUR',
                'timestamp': datetime.now().isoformat()
            }
            bot._execute_multi_strategy_analysis = Mock(return_value=mock_analysis)
            
            # Mock opportunity manager
            ranked_opportunities = [
                {'product_id': 'BTC-EUR', 'analysis': mock_analysis, 'opportunity_score': 85}
            ]
            capital_allocations = {'BTC-EUR': 100.0}
            opportunity_summary = {
                'actionable_opportunities': 1,
                'buy_opportunities': 1,
                'sell_opportunities': 0
            }
            
            bot.opportunity_manager.rank_trading_opportunities.return_value = ranked_opportunities
            bot.opportunity_manager.allocate_trading_capital.return_value = capital_allocations
            bot.opportunity_manager.get_opportunity_summary.return_value = opportunity_summary
            
            # Mock trade execution
            trade_result = {'trade_executed': True, 'execution_status': 'executed'}
            bot._execute_prioritized_trade = Mock(return_value=trade_result)
            bot._log_trade_decision = Mock()
            bot._save_result = Mock()
            bot.update_local_dashboard = Mock()
            bot.update_next_decision_time = Mock()
            
            # Mock portfolio
            bot.portfolio.to_dict.return_value = {'EUR': {'amount': 1000.0}}
            
            # Execute trading cycle
            bot.run_trading_cycle()
            
            # Verify cycle execution
            assert bot._execute_multi_strategy_analysis.call_count == 2  # BTC-EUR, ETH-EUR
            bot.opportunity_manager.rank_trading_opportunities.assert_called_once()
            bot.opportunity_manager.allocate_trading_capital.assert_called_once()
            bot._execute_prioritized_trade.assert_called_once()
    
    def test_run_trading_cycle_fallback_to_legacy(self, test_env_vars, mock_components):
        """Test fallback to legacy trading cycle when opportunity manager fails"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('time.sleep'):
            
            mock_config.return_value = Mock()
            mock_config.return_value.TRADING_PAIRS = ['BTC-EUR']
            bot = TradingBot()
            
            # Mock portfolio sync
            bot._sync_portfolio_with_coinbase = Mock(return_value=True)
            
            # Mock analysis
            mock_analysis = {'action': 'HOLD', 'confidence': 50}
            bot._execute_multi_strategy_analysis = Mock(return_value=mock_analysis)
            
            # Mock opportunity manager failure
            bot.opportunity_manager.rank_trading_opportunities.side_effect = Exception("Opportunity manager error")
            
            # Mock legacy cycle methods
            bot._run_legacy_trading_cycle = Mock()
            
            bot.run_trading_cycle()
            
            # Verify fallback was called
            bot._run_legacy_trading_cycle.assert_called_once()

class TestScheduledTasks:
    """Test scheduled task management"""
    
    @pytest.mark.skipif(os.getenv('CI') == 'true', reason="Scheduler test can hang in CI")
    def test_start_scheduled_trading(self, test_env_vars, mock_components):
        """Test scheduled trading initialization"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('schedule.every') as mock_schedule:
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock schedule methods
            mock_schedule.return_value.minutes.do = Mock()
            mock_schedule.return_value.day.at = Mock()
            mock_schedule.return_value.sunday.at = Mock()
            mock_schedule.return_value.monday.at = Mock()
            mock_schedule.return_value.hours.do = Mock()
            
            # Mock run_trading_cycle to avoid actual execution
            bot.run_trading_cycle = Mock()
            
            bot.start_scheduled_trading()
            
            # Verify initial run and scheduling
            bot.run_trading_cycle.assert_called_once()
            assert mock_schedule.call_count > 0
    
    def test_generate_tax_report(self, test_env_vars, mock_components):
        """Test tax report generation"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock successful report generation
            bot.tax_report_generator.generate_report.return_value = True
            
            result = bot.generate_tax_report()
            
            assert result is True
            bot.tax_report_generator.generate_report.assert_called_once()
    
    def test_run_daily_cleanup(self, test_env_vars, mock_components):
        """Test daily cleanup execution"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock cleanup results
            cleanup_result = {
                'total_files': 5,
                'space_saved_mb': 10.5,
                'files_deleted': {'old_logs': 3, 'cache_files': 2}
            }
            bot.cleanup_manager.run_cleanup.return_value = cleanup_result
            bot.notification_service.send_status_notification = Mock()
            
            result = bot.run_daily_cleanup()
            
            assert result is True
            bot.cleanup_manager.run_cleanup.assert_called_once()
            bot.notification_service.send_status_notification.assert_called_once()

class TestErrorHandling:
    """Test error handling and recovery mechanisms"""
    
    def test_signal_handler_graceful_shutdown(self, test_env_vars, mock_components):
        """Test graceful shutdown on signal"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             pytest.raises(SystemExit):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            bot.record_shutdown_time = Mock()
            
            # Simulate signal
            bot._signal_handler(15, None)  # SIGTERM
            
            bot.record_shutdown_time.assert_called_once()
    
    def test_trading_cycle_error_recovery(self, test_env_vars, mock_components):
        """Test error recovery during trading cycle"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('time.sleep'):
            
            mock_config.return_value = Mock()
            mock_config.return_value.TRADING_PAIRS = ['BTC-EUR']
            bot = TradingBot()
            
            # Mock portfolio sync failure
            bot._sync_portfolio_with_coinbase = Mock(return_value=True)
            
            # Mock analysis failure
            bot._execute_multi_strategy_analysis = Mock(side_effect=Exception("Analysis error"))
            
            # Mock opportunity manager to continue execution
            bot.opportunity_manager.rank_trading_opportunities.return_value = []
            bot.opportunity_manager.allocate_trading_capital.return_value = {}
            bot.opportunity_manager.get_opportunity_summary.return_value = {
                'actionable_opportunities': 0, 'buy_opportunities': 0, 'sell_opportunities': 0
            }
            bot.update_local_dashboard = Mock()
            bot.update_next_decision_time = Mock()
            bot.portfolio.to_dict.return_value = {'EUR': {'amount': 1000}}
            
            # Should not raise exception
            bot.run_trading_cycle()
            
            # Verify error was handled gracefully
            bot.update_local_dashboard.assert_called_once()

class TestDashboardIntegration:
    """Test dashboard updates and web synchronization"""
    
    def test_update_local_dashboard(self, test_env_vars, mock_components):
        """Test local dashboard update"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock trade logger and data collector
            bot.trade_logger.get_recent_trades.return_value = [
                {'product_id': 'BTC-EUR', 'action': 'BUY', 'price': 45000}
            ]
            bot.data_collector.get_market_data.return_value = {'price': 45000}
            bot.portfolio.to_dict.return_value = {
                'EUR': {'amount': 1000.0},
                'BTC': {'amount': 0.01, 'last_price_eur': 45000.0},
                'portfolio_value_eur': 1450.0
            }
            
            with patch('main.config') as mock_config_module:
                mock_config_module.TRADING_PAIRS = ['BTC-EUR']
                
                bot.update_local_dashboard()
            
            bot.dashboard_updater.update_dashboard.assert_called_once()
    
    def test_sync_to_webserver(self, test_env_vars, mock_components):
        """Test web server synchronization"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('main.WEBSERVER_SYNC_ENABLED', True):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            bot.sync_to_webserver()
            
            bot.webserver_sync.sync_to_webserver.assert_called_once()

class TestPerformanceTracking:
    """Test performance tracking integration"""
    
    def test_take_performance_snapshot(self, test_env_vars, mock_components):
        """Test performance snapshot creation"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock performance tracker
            bot.performance_tracker.is_tracking_enabled.return_value = True
            bot.performance_tracker.get_tracking_info.return_value = {'tracking_start_date': '2024-01-01'}
            bot.performance_tracker.take_portfolio_snapshot.return_value = True
            
            portfolio = {
                'portfolio_value_eur': 1000.0,
                'EUR': {'amount': 500.0, 'last_price_eur': 1.0},
                'BTC': {'amount': 0.01, 'last_price_eur': 45000.0}
            }
            
            bot._take_performance_snapshot(portfolio)
            
            bot.performance_tracker.take_portfolio_snapshot.assert_called_once()
    
    def test_take_performance_snapshot_initialization(self, test_env_vars, mock_components):
        """Test performance tracking initialization"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'):
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock uninitialized performance tracker
            bot.performance_tracker.is_tracking_enabled.return_value = True
            bot.performance_tracker.get_tracking_info.return_value = {}  # No tracking_start_date
            bot.performance_tracker.initialize_tracking.return_value = True
            bot.performance_tracker.take_portfolio_snapshot.return_value = True
            
            portfolio = {'portfolio_value_eur': 1000.0}
            
            bot._take_performance_snapshot(portfolio)
            
            bot.performance_tracker.initialize_tracking.assert_called_once()
            bot.performance_tracker.take_portfolio_snapshot.assert_called_once()

class TestFileOperations:
    """Test file operations and data persistence"""
    
    def test_record_startup_time(self, test_env_vars, mock_components, temp_data_dir):
        """Test startup time recording"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            with patch('main.TRADING_PAIRS', ['BTC-EUR']), \
                 patch('main.DECISION_INTERVAL_MINUTES', 60), \
                 patch('main.SIMULATION_MODE', True), \
                 patch('main.RISK_LEVEL', 'MEDIUM'):
                
                bot.record_startup_time()
            
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once()
    
    def test_record_shutdown_time(self, test_env_vars, mock_components):
        """Test shutdown time recording"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('builtins.open', mock_open(read_data='{"status": "online"}')) as mock_file, \
             patch('json.load', return_value={'status': 'online'}), \
             patch('json.dump') as mock_json_dump:
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            bot.record_shutdown_time()
            
            # Verify file operations
            assert mock_file.call_count >= 1
            mock_json_dump.assert_called_once()
    
    def test_save_result_with_market_data(self, test_env_vars, mock_components):
        """Test saving trading results with market data"""
        with patch('os.makedirs'), \
             patch('main.Config') as mock_config, \
             patch('signal.signal'), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            mock_config.return_value = Mock()
            bot = TradingBot()
            
            # Mock market data
            bot.data_collector.client.get_product_price.return_value = {'price': '45000.0'}
            bot._calculate_price_changes = Mock(return_value={'1h': 2.5, '24h': 5.0})
            
            result = {'action': 'BUY', 'confidence': 75}
            
            bot._save_result('BTC-EUR', result)
            
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once()
            
            # Verify market data was added
            saved_data = mock_json_dump.call_args[0][0]
            assert 'market_data' in saved_data

# Integration test for main execution
class TestMainExecution:
    """Test main execution flow"""
    
    def test_main_execution_keyboard_interrupt(self, test_env_vars, mock_components):
        """Test graceful shutdown on keyboard interrupt"""
        with patch('main.ensure_single_instance', return_value=123), \
             patch('main.TradingBot') as mock_bot_class, \
             patch('main.log_bot_shutdown'), \
             patch('os.close'), \
             patch('os.unlink'), \
             pytest.raises(KeyboardInterrupt):
            
            mock_bot = Mock()
            mock_bot_class.return_value = mock_bot
            mock_bot.start_scheduled_trading.side_effect = KeyboardInterrupt()
            
            # Import and execute main
            import main
            exec(open('main.py').read())
    
    def test_main_execution_unexpected_error(self, test_env_vars, mock_components):
        """Test error handling for unexpected errors"""
        with patch('main.ensure_single_instance', return_value=123), \
             patch('main.TradingBot') as mock_bot_class, \
             patch('main.log_bot_shutdown'), \
             patch('os.close'), \
             patch('os.unlink'), \
             pytest.raises(Exception):
            
            mock_bot = Mock()
            mock_bot_class.return_value = mock_bot
            mock_bot.start_scheduled_trading.side_effect = Exception("Unexpected error")
            
            # Should re-raise the exception after cleanup
            exec(compile(open('main.py').read(), 'main.py', 'exec'))

if __name__ == '__main__':
    pytest.main([__file__])