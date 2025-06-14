#!/usr/bin/env python3
"""
Bot Manager - Helper script to manage bot lifecycle with proper uptime tracking
"""

import os
import sys
import json
import signal
import subprocess
import time
from datetime import datetime
from utils.uptime_manager import UptimeManager

def get_bot_pid():
    """Get the current bot process ID if running"""
    try:
        with open("data/cache/bot_startup.json", "r") as f:
            data = json.load(f)
            return data.get("pid")
    except:
        return None

def is_bot_running():
    """Check if the bot is currently running"""
    pid = get_bot_pid()
    if not pid:
        return False
    
    try:
        # Check if process exists
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def is_running_under_systemd():
    """Check if bot is running under systemd"""
    try:
        return os.environ.get('SYSTEMD_EXEC_PID') is not None or \
               os.path.exists('/run/systemd/system')
    except:
        return False

def is_running_under_supervisor():
    """Check if bot is running under supervisor"""
    try:
        return os.environ.get('SUPERVISOR_ENABLED') == '1' or \
               'supervisor' in os.environ.get('_', '').lower()
    except:
        return False

def stop_bot(explicit_stop=True):
    """Stop the bot with proper uptime tracking"""
    print("Stopping bot...")
    
    # Set environment variable to indicate stop context
    if explicit_stop:
        os.environ['BOT_RESTART_CONTEXT'] = 'stop'
    else:
        os.environ['BOT_RESTART_CONTEXT'] = 'restart'
    
    # Mark as explicit stop in uptime data
    uptime_manager = UptimeManager()
    uptime_manager.record_shutdown(is_explicit_stop=explicit_stop)
    
    pid = get_bot_pid()
    if pid:
        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            print(f"Sent SIGTERM to process {pid}")
            
            # Wait for graceful shutdown
            for i in range(10):
                if not is_bot_running():
                    print("Bot stopped gracefully")
                    return True
                time.sleep(1)
            
            # Force kill if still running
            print("Forcing bot shutdown...")
            os.kill(pid, signal.SIGKILL)
            return True
            
        except OSError as e:
            print(f"Error stopping bot: {e}")
            return False
    else:
        print("Bot is not running")
        return True

def start_bot():
    """Start the bot"""
    if is_bot_running():
        print("Bot is already running")
        return False
    
    print("Starting bot...")
    try:
        # Clear any restart context
        os.environ.pop('BOT_RESTART_CONTEXT', None)
        
        # Start the bot process
        subprocess.Popen([sys.executable, "main.py"], 
                        cwd=os.path.dirname(os.path.abspath(__file__)))
        print("Bot started successfully")
        return True
    except Exception as e:
        print(f"Error starting bot: {e}")
        return False

def restart_bot():
    """Restart the bot (preserves uptime)"""
    print("Restarting bot...")
    
    # Set environment variable to indicate restart context
    os.environ['BOT_RESTART_CONTEXT'] = 'restart'
    
    # Mark as restart (not explicit stop)
    if is_bot_running():
        uptime_manager = UptimeManager()
        uptime_manager.record_shutdown(is_explicit_stop=False)
        
        # Stop the bot
        pid = get_bot_pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                
                # Wait for shutdown
                for i in range(10):
                    if not is_bot_running():
                        break
                    time.sleep(1)
                else:
                    # Force kill if needed
                    os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    
    # Start the bot
    time.sleep(2)  # Brief pause
    return start_bot()

def systemctl_restart():
    """Restart via systemctl with proper uptime preservation"""
    print("Restarting bot via systemctl...")
    try:
        # Set restart context
        env = os.environ.copy()
        env['BOT_RESTART_CONTEXT'] = 'restart'
        
        # Use systemctl restart
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'crypto-bot'], 
                              env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Bot restarted successfully via systemctl")
            return True
        else:
            print(f"Error restarting via systemctl: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error with systemctl restart: {e}")
        return False

def systemctl_stop():
    """Stop via systemctl with explicit stop"""
    print("Stopping bot via systemctl...")
    try:
        # Set stop context
        env = os.environ.copy()
        env['BOT_RESTART_CONTEXT'] = 'stop'
        
        result = subprocess.run(['sudo', 'systemctl', 'stop', 'crypto-bot'], 
                              env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Bot stopped successfully via systemctl")
            return True
        else:
            print(f"Error stopping via systemctl: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error with systemctl stop: {e}")
        return False

def supervisorctl_restart():
    """Restart via supervisorctl with proper uptime preservation"""
    print("Restarting bot via supervisorctl...")
    try:
        # Set restart context
        env = os.environ.copy()
        env['BOT_RESTART_CONTEXT'] = 'restart'
        
        result = subprocess.run(['sudo', 'supervisorctl', 'restart', 'crypto-bot'], 
                              env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Bot restarted successfully via supervisorctl")
            return True
        else:
            print(f"Error restarting via supervisorctl: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error with supervisorctl restart: {e}")
        return False

def supervisorctl_stop():
    """Stop via supervisorctl with explicit stop"""
    print("Stopping bot via supervisorctl...")
    try:
        # Set stop context
        env = os.environ.copy()
        env['BOT_RESTART_CONTEXT'] = 'stop'
        
        result = subprocess.run(['sudo', 'supervisorctl', 'stop', 'crypto-bot'], 
                              env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Bot stopped successfully via supervisorctl")
            return True
        else:
            print(f"Error stopping via supervisorctl: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error with supervisorctl stop: {e}")
        return False

def status():
    """Show bot status"""
    print("Bot Status:")
    print("-" * 40)
    
    # Detect service manager
    if is_running_under_systemd():
        print("Service Manager: systemd")
    elif is_running_under_supervisor():
        print("Service Manager: supervisor")
    else:
        print("Service Manager: standalone")
    
    if is_bot_running():
        print("Status: RUNNING")
        pid = get_bot_pid()
        if pid:
            print(f"PID: {pid}")
    else:
        print("Status: STOPPED")
    
    # Show uptime information
    try:
        uptime_manager = UptimeManager()
        uptime_info = uptime_manager.get_current_uptime()
        
        if uptime_info['total_uptime_seconds'] > 0:
            total_uptime = uptime_info['total_uptime_seconds']
            hours = int(total_uptime // 3600)
            minutes = int((total_uptime % 3600) // 60)
            seconds = int(total_uptime % 60)
            print(f"Total Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            if uptime_info.get('restart_count', 0) > 0:
                print(f"Restarts: {uptime_info['restart_count']}")
            
            if uptime_info.get('original_start_time'):
                original_start = datetime.fromisoformat(uptime_info['original_start_time'])
                print(f"Original Start: {original_start.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    except Exception as e:
        print(f"Error getting uptime info: {e}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python bot_manager.py [start|stop|restart|status|systemctl-restart|systemctl-stop|supervisorctl-restart|supervisorctl-stop]")
        print("")
        print("Commands:")
        print("  start                - Start the bot")
        print("  stop                 - Stop the bot (resets uptime)")
        print("  restart              - Restart the bot (preserves uptime)")
        print("  status               - Show bot status and uptime")
        print("  systemctl-restart    - Restart via systemctl (preserves uptime)")
        print("  systemctl-stop       - Stop via systemctl (resets uptime)")
        print("  supervisorctl-restart - Restart via supervisorctl (preserves uptime)")
        print("  supervisorctl-stop   - Stop via supervisorctl (resets uptime)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_bot()
    elif command == "stop":
        stop_bot(explicit_stop=True)
    elif command == "restart":
        restart_bot()
    elif command == "systemctl-restart":
        systemctl_restart()
    elif command == "systemctl-stop":
        systemctl_stop()
    elif command == "supervisorctl-restart":
        supervisorctl_restart()
    elif command == "supervisorctl-stop":
        supervisorctl_stop()
    elif command == "status":
        status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
