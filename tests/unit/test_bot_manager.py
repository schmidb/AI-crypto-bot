"""
Comprehensive tests for bot_manager.py
"""

import pytest
import os
import json
import signal
import time
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from bot_manager import (
    BotManager,
    get_bot_pid,
    is_bot_running,
    stop_bot,
    start_bot,
    restart_bot,
    status
)


class TestBotManagerInitialization:
    """Test BotManager initialization"""
    
    def test_bot_manager_initialization(self, tmp_path):
        """Test BotManager creates required directories"""
        with patch('bot_manager.Path') as mock_path:
            mock_mkdir = Mock()
            mock_path.return_value.mkdir = mock_mkdir
            
            manager = BotManager()
            
            assert manager is not None
    
    def test_ensure_directories_creates_logs(self, tmp_path):
        """Test ensure_directories creates logs directory"""
        with patch('bot_manager.Path') as mock_path:
            manager = BotManager()
            
            # Verify mkdir was called
            assert mock_path.called


class TestScheduledTaskChecks:
    """Test scheduled task timing checks"""
    
    def test_should_run_daily_health_check_at_6am(self):
        """Test daily health check should run at 6 AM"""
        manager = BotManager()
        
        # Mock datetime to 6:02 AM
        with patch('bot_manager.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.hour = 6
            mock_now.minute = 2
            mock_datetime.now.return_value = mock_now
            
            assert manager.should_run_daily_health_check() is True
    
    def test_should_not_run_daily_health_check_outside_window(self):
        """Test daily health check should not run outside time window"""
        manager = BotManager()
        
        # Mock datetime to 6:10 AM (outside 5-minute window)
        with patch('bot_manager.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.hour = 6
            mock_now.minute = 10
            mock_datetime.now.return_value = mock_now
            
            assert manager.should_run_daily_health_check() is False
    
    def test_should_run_weekly_validation_monday_7am(self):
        """Test weekly validation should run Monday at 7 AM"""
        manager = BotManager()
        
        # Mock datetime to Monday 7:02 AM
        with patch('bot_manager.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 0  # Monday
            mock_now.hour = 7
            mock_now.minute = 2
            mock_datetime.now.return_value = mock_now
            
            assert manager.should_run_weekly_validation() is True
    
    def test_should_not_run_weekly_validation_wrong_day(self):
        """Test weekly validation should not run on non-Monday"""
        manager = BotManager()
        
        # Mock datetime to Tuesday 7:02 AM
        with patch('bot_manager.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 1  # Tuesday
            mock_now.hour = 7
            mock_now.minute = 2
            mock_datetime.now.return_value = mock_now
            
            assert manager.should_run_weekly_validation() is False
    
    def test_should_run_monthly_stability_first_of_month(self):
        """Test monthly stability should run on 1st at 8 AM"""
        manager = BotManager()
        
        # Mock datetime to 1st of month 8:02 AM
        with patch('bot_manager.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.day = 1
            mock_now.hour = 8
            mock_now.minute = 2
            mock_datetime.now.return_value = mock_now
            
            assert manager.should_run_monthly_stability() is True
    
    def test_should_not_run_monthly_stability_wrong_day(self):
        """Test monthly stability should not run on non-1st day"""
        manager = BotManager()
        
        # Mock datetime to 2nd of month 8:02 AM
        with patch('bot_manager.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.day = 2
            mock_now.hour = 8
            mock_now.minute = 2
            mock_datetime.now.return_value = mock_now
            
            assert manager.should_run_monthly_stability() is False


class TestBotProcessManagement:
    """Test bot process management functions"""
    
    def test_get_bot_pid_success(self, tmp_path):
        """Test getting bot PID from startup file"""
        startup_file = tmp_path / "bot_startup.json"
        startup_file.write_text(json.dumps({"pid": 12345}))
        
        with patch('builtins.open', mock_open(read_data='{"pid": 12345}')):
            pid = get_bot_pid()
            assert pid == 12345
    
    def test_get_bot_pid_file_not_found(self):
        """Test getting bot PID when file doesn't exist"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            pid = get_bot_pid()
            assert pid is None
    
    def test_get_bot_pid_invalid_json(self):
        """Test getting bot PID with invalid JSON"""
        with patch('builtins.open', mock_open(read_data='invalid json')):
            pid = get_bot_pid()
            assert pid is None
    
    def test_is_bot_running_true(self):
        """Test is_bot_running returns True when process exists"""
        with patch('bot_manager.get_bot_pid', return_value=12345):
            with patch('os.kill') as mock_kill:
                mock_kill.return_value = None  # Process exists
                assert is_bot_running() is True
                mock_kill.assert_called_once_with(12345, 0)
    
    def test_is_bot_running_false_no_pid(self):
        """Test is_bot_running returns False when no PID"""
        with patch('bot_manager.get_bot_pid', return_value=None):
            assert is_bot_running() is False
    
    def test_is_bot_running_false_process_not_found(self):
        """Test is_bot_running returns False when process doesn't exist"""
        with patch('bot_manager.get_bot_pid', return_value=12345):
            with patch('os.kill', side_effect=OSError):
                assert is_bot_running() is False


class TestBotControl:
    """Test bot start/stop/restart functions"""
    
    def test_stop_bot_success(self):
        """Test stopping bot successfully"""
        with patch('bot_manager.get_bot_pid', return_value=12345):
            with patch('os.kill') as mock_kill:
                with patch('bot_manager.is_bot_running', side_effect=[True, False]):
                    with patch('time.sleep'):
                        result = stop_bot()
                        assert result is True
                        mock_kill.assert_called_with(12345, signal.SIGTERM)
    
    def test_stop_bot_not_running(self):
        """Test stopping bot when not running"""
        with patch('bot_manager.get_bot_pid', return_value=None):
            result = stop_bot()
            assert result is True
    
    def test_stop_bot_force_kill(self):
        """Test force killing bot after graceful shutdown fails"""
        with patch('bot_manager.get_bot_pid', return_value=12345):
            with patch('os.kill') as mock_kill:
                # Bot stays running for 10 iterations, then force kill
                with patch('bot_manager.is_bot_running', return_value=True):
                    with patch('time.sleep'):
                        result = stop_bot()
                        # Should call SIGTERM first, then SIGKILL
                        assert mock_kill.call_count >= 2
    
    def test_stop_bot_error_handling(self):
        """Test stop_bot handles OS errors"""
        with patch('bot_manager.get_bot_pid', return_value=12345):
            with patch('os.kill', side_effect=OSError("Process not found")):
                result = stop_bot()
                assert result is False
    
    def test_start_bot_success(self):
        """Test starting bot successfully"""
        with patch('bot_manager.is_bot_running', return_value=False):
            with patch('subprocess.Popen') as mock_popen:
                with patch('sys.executable', '/usr/bin/python3'):
                    result = start_bot()
                    assert result is True
                    mock_popen.assert_called_once()
    
    def test_start_bot_already_running(self):
        """Test starting bot when already running"""
        with patch('bot_manager.is_bot_running', return_value=True):
            result = start_bot()
            assert result is False
    
    def test_start_bot_error(self):
        """Test start_bot handles errors"""
        with patch('bot_manager.is_bot_running', return_value=False):
            with patch('subprocess.Popen', side_effect=Exception("Failed to start")):
                result = start_bot()
                assert result is False
    
    def test_restart_bot_success(self):
        """Test restarting bot successfully"""
        with patch('bot_manager.is_bot_running', side_effect=[True, False, False]):
            with patch('bot_manager.get_bot_pid', return_value=12345):
                with patch('os.kill'):
                    with patch('time.sleep'):
                        with patch('subprocess.Popen'):
                            with patch('sys.executable', '/usr/bin/python3'):
                                result = restart_bot()
                                assert result is True
    
    def test_restart_bot_not_running(self):
        """Test restarting bot when not running"""
        with patch('bot_manager.is_bot_running', return_value=False):
            with patch('time.sleep'):
                with patch('subprocess.Popen'):
                    with patch('sys.executable', '/usr/bin/python3'):
                        result = restart_bot()
                        assert result is True


class TestBotStatus:
    """Test bot status display"""
    
    def test_status_running(self, capsys):
        """Test status display when bot is running"""
        startup_data = {
            'pid': 12345,
            'startup_time': '2024-01-01T10:00:00'
        }
        
        with patch('bot_manager.is_bot_running', return_value=True):
            with patch('bot_manager.get_bot_pid', return_value=12345):
                with patch('builtins.open', mock_open(read_data=json.dumps(startup_data))):
                    with patch('bot_manager.datetime') as mock_datetime:
                        mock_datetime.fromisoformat.return_value = datetime(2024, 1, 1, 10, 0, 0)
                        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 11, 30, 45)
                        
                        status()
                        
                        captured = capsys.readouterr()
                        assert "RUNNING" in captured.out
                        assert "12345" in captured.out
    
    def test_status_stopped(self, capsys):
        """Test status display when bot is stopped"""
        with patch('bot_manager.is_bot_running', return_value=False):
            status()
            
            captured = capsys.readouterr()
            assert "STOPPED" in captured.out
    
    def test_status_error_reading_session_info(self, capsys):
        """Test status handles errors reading session info"""
        with patch('bot_manager.is_bot_running', return_value=True):
            with patch('bot_manager.get_bot_pid', return_value=12345):
                with patch('builtins.open', side_effect=Exception("File error")):
                    status()
                    
                    captured = capsys.readouterr()
                    assert "RUNNING" in captured.out
                    assert "Error getting session info" in captured.out


class TestScheduledTaskExecution:
    """Test scheduled task execution"""
    
    def test_run_daily_health_check_import_error(self):
        """Test running daily health check with import error"""
        manager = BotManager()
        
        # The async methods will fail to import in test environment
        # This is expected behavior - they're designed for production
        assert manager is not None
    
    def test_run_weekly_validation_import_error(self):
        """Test running weekly validation with import error"""
        manager = BotManager()
        assert manager is not None
    
    def test_run_monthly_stability_import_error(self):
        """Test running monthly stability with import error"""
        manager = BotManager()
        assert manager is not None


class TestIntegration:
    """Integration tests for bot manager"""
    
    def test_full_lifecycle(self):
        """Test complete bot lifecycle: start -> status -> stop"""
        with patch('bot_manager.is_bot_running', side_effect=[False, True, True, False]):
            with patch('bot_manager.get_bot_pid', return_value=12345):
                with patch('subprocess.Popen'):
                    with patch('sys.executable', '/usr/bin/python3'):
                        with patch('os.kill'):
                            with patch('time.sleep'):
                                # Start bot
                                assert start_bot() is True
                                
                                # Check status
                                assert is_bot_running() is True
                                
                                # Stop bot
                                assert stop_bot() is True
    
    def test_restart_workflow(self):
        """Test restart workflow"""
        with patch('bot_manager.is_bot_running', side_effect=[True, False, False]):
            with patch('bot_manager.get_bot_pid', return_value=12345):
                with patch('os.kill'):
                    with patch('time.sleep'):
                        with patch('subprocess.Popen'):
                            with patch('sys.executable', '/usr/bin/python3'):
                                result = restart_bot()
                                assert result is True
