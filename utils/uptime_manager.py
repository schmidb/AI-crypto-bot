"""
Uptime Manager - Handles persistent uptime tracking across bot restarts
Only resets uptime on explicit stops, not on restarts
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class UptimeManager:
    """Manages persistent uptime tracking across bot restarts"""
    
    def __init__(self):
        self.uptime_file = "data/cache/bot_uptime.json"
        self.startup_file = "data/cache/bot_startup.json"
        os.makedirs("data/cache", exist_ok=True)
    
    def record_startup(self, is_restart: bool = False) -> Dict:
        """
        Record bot startup and manage uptime persistence
        
        Args:
            is_restart: True if this is a restart, False if it's a fresh start
        """
        try:
            current_time = datetime.utcnow()
            
            # Load existing uptime data
            uptime_data = self._load_uptime_data()
            
            if is_restart and uptime_data and uptime_data.get('original_start_time'):
                # This is a restart - preserve original start time
                original_start_time = uptime_data['original_start_time']
                logger.info(f"Bot restart detected - preserving original start time: {original_start_time}")
            else:
                # This is a fresh start or no previous data exists
                original_start_time = current_time.isoformat()
                logger.info(f"Fresh bot start - recording new original start time: {original_start_time}")
            
            # Calculate total uptime including previous sessions
            total_uptime_seconds = 0
            if uptime_data and uptime_data.get('total_uptime_seconds'):
                total_uptime_seconds = uptime_data['total_uptime_seconds']
                
                # Add time from last session if it was a clean shutdown
                if uptime_data.get('last_shutdown_time') and uptime_data.get('last_startup_time'):
                    last_start = datetime.fromisoformat(uptime_data['last_startup_time'])
                    last_shutdown = datetime.fromisoformat(uptime_data['last_shutdown_time'])
                    session_duration = (last_shutdown - last_start).total_seconds()
                    total_uptime_seconds += max(0, session_duration)
                    logger.info(f"Added previous session duration: {session_duration:.0f} seconds")
            
            # Update uptime data
            uptime_data = {
                'original_start_time': original_start_time,
                'current_session_start': current_time.isoformat(),
                'last_startup_time': current_time.isoformat(),
                'total_uptime_seconds': total_uptime_seconds,
                'restart_count': uptime_data.get('restart_count', 0) + (1 if is_restart else 0),
                'last_updated': current_time.isoformat(),
                'status': 'running'
            }
            
            # Save uptime data
            self._save_uptime_data(uptime_data)
            
            return uptime_data
            
        except Exception as e:
            logger.error(f"Error recording startup: {e}")
            return {}
    
    def record_shutdown(self, is_explicit_stop: bool = True) -> Dict:
        """
        Record bot shutdown
        
        Args:
            is_explicit_stop: True for explicit stops, False for crashes/restarts
        """
        try:
            current_time = datetime.utcnow()
            uptime_data = self._load_uptime_data()
            
            if not uptime_data:
                logger.warning("No uptime data found during shutdown")
                return {}
            
            # Calculate current session duration
            if uptime_data.get('current_session_start'):
                session_start = datetime.fromisoformat(uptime_data['current_session_start'])
                session_duration = (current_time - session_start).total_seconds()
                
                # Update total uptime
                uptime_data['total_uptime_seconds'] = uptime_data.get('total_uptime_seconds', 0) + session_duration
                logger.info(f"Current session duration: {session_duration:.0f} seconds")
            
            uptime_data.update({
                'last_shutdown_time': current_time.isoformat(),
                'last_updated': current_time.isoformat(),
                'status': 'stopped' if is_explicit_stop else 'restarting'
            })
            
            # If explicit stop, reset the uptime tracking
            if is_explicit_stop:
                logger.info("Explicit stop detected - uptime will reset on next start")
                uptime_data.update({
                    'original_start_time': None,
                    'total_uptime_seconds': 0,
                    'restart_count': 0
                })
            
            self._save_uptime_data(uptime_data)
            return uptime_data
            
        except Exception as e:
            logger.error(f"Error recording shutdown: {e}")
            return {}
    
    def get_current_uptime(self) -> Dict:
        """Get current uptime information"""
        try:
            uptime_data = self._load_uptime_data()
            
            if not uptime_data or not uptime_data.get('current_session_start'):
                return {'total_uptime_seconds': 0, 'status': 'unknown'}
            
            current_time = datetime.utcnow()
            session_start = datetime.fromisoformat(uptime_data['current_session_start'])
            current_session_duration = (current_time - session_start).total_seconds()
            
            total_uptime = uptime_data.get('total_uptime_seconds', 0) + current_session_duration
            
            return {
                'total_uptime_seconds': total_uptime,
                'current_session_seconds': current_session_duration,
                'original_start_time': uptime_data.get('original_start_time'),
                'current_session_start': uptime_data.get('current_session_start'),
                'restart_count': uptime_data.get('restart_count', 0),
                'status': uptime_data.get('status', 'running')
            }
            
        except Exception as e:
            logger.error(f"Error getting current uptime: {e}")
            return {'total_uptime_seconds': 0, 'status': 'error'}
    
    def _load_uptime_data(self) -> Dict:
        """Load uptime data from file"""
        try:
            if os.path.exists(self.uptime_file):
                with open(self.uptime_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading uptime data: {e}")
        return {}
    
    def _save_uptime_data(self, data: Dict) -> None:
        """Save uptime data to file"""
        try:
            with open(self.uptime_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving uptime data: {e}")
    
    def update_startup_file(self, startup_data: Dict) -> None:
        """Update the startup file with uptime information"""
        try:
            uptime_info = self.get_current_uptime()
            
            # Add uptime information to startup data
            startup_data.update({
                'total_uptime_seconds': uptime_info['total_uptime_seconds'],
                'original_start_time': uptime_info.get('original_start_time'),
                'restart_count': uptime_info.get('restart_count', 0)
            })
            
            with open(self.startup_file, 'w') as f:
                json.dump(startup_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating startup file with uptime: {e}")
