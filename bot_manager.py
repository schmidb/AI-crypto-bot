#!/usr/bin/env python3
"""
Bot Manager - Helper script to manage bot lifecycle and scheduled tasks
"""

import os
import sys
import json
import signal
import subprocess
import time
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotManager:
    """Enhanced bot manager with scheduled task integration"""
    
    def __init__(self):
        """Initialize the bot manager"""
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        Path('./logs').mkdir(exist_ok=True)
        Path('./data/cache').mkdir(parents=True, exist_ok=True)
    
    async def run_daily_health_check(self):
        """Run daily health check analysis"""
        try:
            logger.info("🏥 Starting daily health check...")
            
            # Import and run the daily health check
            from run_daily_health_check import run_daily_health_check
            success = run_daily_health_check(sync_gcs=True)
            
            if success:
                logger.info("✅ Daily health check completed successfully")
                return {"status": "success", "message": "Daily health check completed"}
            else:
                logger.error("❌ Daily health check failed")
                return {"status": "error", "message": "Daily health check failed"}
                
        except Exception as e:
            logger.error(f"Error in daily health check: {e}")
            return {"status": "error", "message": f"Daily health check error: {e}"}
    
    async def run_weekly_validation(self):
        """Run weekly validation and backtesting"""
        try:
            logger.info("📊 Starting weekly validation...")
            
            # Import and run the weekly validation
            from run_weekly_validation import run_weekly_validation
            success = run_weekly_validation(sync_gcs=True)
            
            if success:
                logger.info("✅ Weekly validation completed successfully")
                return {"status": "success", "message": "Weekly validation completed"}
            else:
                logger.error("❌ Weekly validation failed")
                return {"status": "error", "message": "Weekly validation failed"}
                
        except Exception as e:
            logger.error(f"Error in weekly validation: {e}")
            return {"status": "error", "message": f"Weekly validation error: {e}"}
    
    async def run_monthly_stability(self):
        """Run monthly stability analysis"""
        try:
            logger.info("🔬 Starting monthly stability analysis...")
            
            # Import and run the monthly stability analysis
            from run_monthly_stability import run_monthly_stability
            success = run_monthly_stability(sync_gcs=True)
            
            if success:
                logger.info("✅ Monthly stability analysis completed successfully")
                return {"status": "success", "message": "Monthly stability analysis completed"}
            else:
                logger.error("❌ Monthly stability analysis failed")
                return {"status": "error", "message": "Monthly stability analysis failed"}
                
        except Exception as e:
            logger.error(f"Error in monthly stability analysis: {e}")
            return {"status": "error", "message": f"Monthly stability analysis error: {e}"}
    
    def should_run_daily_health_check(self):
        """Check if daily health check should run (6 AM daily)"""
        now = datetime.now()
        return now.hour == 6 and now.minute < 5  # Run at 6 AM with 5-minute window
    
    def should_run_weekly_validation(self):
        """Check if weekly validation should run (Monday 7 AM)"""
        now = datetime.now()
        return now.weekday() == 0 and now.hour == 7 and now.minute < 5  # Monday at 7 AM
    
    def should_run_monthly_stability(self):
        """Check if monthly stability should run (1st of month 8 AM)"""
        now = datetime.now()
        return now.day == 1 and now.hour == 8 and now.minute < 5  # 1st of month at 8 AM

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
                    session_duration = (datetime.now(timezone.utc) - startup_time).total_seconds()
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
        print("Usage: python bot_manager.py [start|stop|restart|status|daily_health|weekly_validation|monthly_stability]")
        print("")
        print("Commands:")
        print("  start              - Start the bot")
        print("  stop               - Stop the bot")
        print("  restart            - Restart the bot")
        print("  status             - Show bot status")
        print("  daily_health       - Run daily health check manually")
        print("  weekly_validation  - Run weekly validation manually")
        print("  monthly_stability  - Run monthly stability analysis manually")
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
    elif command == "daily_health":
        # Run daily health check manually
        bot_manager = BotManager()
        result = asyncio.run(bot_manager.run_daily_health_check())
        print(f"Daily health check result: {result}")
    elif command == "weekly_validation":
        # Run weekly validation manually
        bot_manager = BotManager()
        result = asyncio.run(bot_manager.run_weekly_validation())
        print(f"Weekly validation result: {result}")
    elif command == "monthly_stability":
        # Run monthly stability analysis manually
        bot_manager = BotManager()
        result = asyncio.run(bot_manager.run_monthly_stability())
        print(f"Monthly stability analysis result: {result}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
