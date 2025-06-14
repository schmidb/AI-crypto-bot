#!/usr/bin/env python3
"""
Bot Manager - Helper script to manage bot lifecycle
"""

import os
import sys
import json
import signal
import subprocess
import time
from datetime import datetime

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

def stop_bot():
    """Stop the bot"""
    print("Stopping bot...")
    
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
        # Start the bot process
        subprocess.Popen([sys.executable, "main.py"], 
                        cwd=os.path.dirname(os.path.abspath(__file__)))
        print("Bot started successfully")
        return True
    except Exception as e:
        print(f"Error starting bot: {e}")
        return False

def restart_bot():
    """Restart the bot"""
    print("Restarting bot...")
    
    # Stop the bot
    if is_bot_running():
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

def status():
    """Show bot status"""
    print("Bot Status:")
    print("-" * 40)
    
    if is_bot_running():
        print("Status: RUNNING")
        pid = get_bot_pid()
        if pid:
            print(f"PID: {pid}")
            
        # Show session uptime
        try:
            with open("data/cache/bot_startup.json", "r") as f:
                data = json.load(f)
                if data.get('startup_time'):
                    startup_time = datetime.fromisoformat(data['startup_time'])
                    session_duration = (datetime.utcnow() - startup_time).total_seconds()
                    hours = int(session_duration // 3600)
                    minutes = int((session_duration % 3600) // 60)
                    seconds = int(session_duration % 60)
                    print(f"Session Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
                    print(f"Started: {startup_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        except Exception as e:
            print(f"Error getting session info: {e}")
    else:
        print("Status: STOPPED")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python bot_manager.py [start|stop|restart|status]")
        print("")
        print("Commands:")
        print("  start    - Start the bot")
        print("  stop     - Stop the bot")
        print("  restart  - Restart the bot")
        print("  status   - Show bot status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_bot()
    elif command == "stop":
        stop_bot()
    elif command == "restart":
        restart_bot()
    elif command == "status":
        status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
