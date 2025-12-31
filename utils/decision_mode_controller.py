"""
Decision Mode Controller
Provides runtime control over decision logic switching and A/B testing
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

class DecisionModeController:
    """
    Controller for managing decision mode switching and A/B testing
    """
    
    def __init__(self):
        self.logger = logging.getLogger("supervisor")
        self.config_file = Path("data/decision_mode_config.json")
        self.results_file = Path("data/ab_test_results.json")
        
        # Ensure data directory exists
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Load or create configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load decision mode configuration"""
        default_config = {
            "current_mode": "conservative",
            "ab_test_config": {
                "enabled": False,
                "conservative_allocation": 0.7,
                "aggressive_allocation": 0.3,
                "test_duration_days": 30,
                "start_date": None,
                "end_date": None
            },
            "mode_history": [],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                self._save_config(default_config)
                return default_config
        except Exception as e:
            self.logger.error(f"Error loading decision mode config: {e}")
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save decision mode configuration"""
        try:
            config["last_updated"] = datetime.utcnow().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving decision mode config: {e}")
    
    def get_current_mode(self) -> str:
        """Get current decision mode"""
        return self.config.get("current_mode", "conservative")
    
    def set_decision_mode(self, mode: str, reason: str = "Manual change") -> bool:
        """
        Set decision mode
        
        Args:
            mode: One of 'conservative', 'aggressive', 'hybrid', 'ab_test'
            reason: Reason for the change
            
        Returns:
            bool: Success status
        """
        valid_modes = ['conservative', 'aggressive', 'hybrid', 'ab_test']
        
        if mode not in valid_modes:
            self.logger.error(f"Invalid decision mode: {mode}. Valid modes: {valid_modes}")
            return False
        
        try:
            old_mode = self.config.get("current_mode", "conservative")
            
            # Record mode change in history
            mode_change = {
                "timestamp": datetime.utcnow().isoformat(),
                "old_mode": old_mode,
                "new_mode": mode,
                "reason": reason
            }
            
            self.config["mode_history"].append(mode_change)
            self.config["current_mode"] = mode
            
            # Keep only last 100 history entries
            if len(self.config["mode_history"]) > 100:
                self.config["mode_history"] = self.config["mode_history"][-100:]
            
            self._save_config(self.config)
            
            # Set environment variable for immediate effect
            os.environ['DECISION_MODE'] = mode
            
            self.logger.info(f"🔄 Decision mode changed: {old_mode} -> {mode} ({reason})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting decision mode: {e}")
            return False
    
    def start_ab_test(self, 
                     duration_days: int = 30,
                     conservative_allocation: float = 0.7,
                     aggressive_allocation: float = 0.3) -> bool:
        """
        Start A/B testing between conservative and aggressive modes
        
        Args:
            duration_days: Test duration in days
            conservative_allocation: Percentage of decisions for conservative (0.0-1.0)
            aggressive_allocation: Percentage of decisions for aggressive (0.0-1.0)
            
        Returns:
            bool: Success status
        """
        try:
            # Validate allocations
            if abs(conservative_allocation + aggressive_allocation - 1.0) > 0.01:
                self.logger.error("Conservative and aggressive allocations must sum to 1.0")
                return False
            
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=duration_days)
            
            # Update A/B test configuration
            self.config["ab_test_config"] = {
                "enabled": True,
                "conservative_allocation": conservative_allocation,
                "aggressive_allocation": aggressive_allocation,
                "test_duration_days": duration_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
            # Switch to A/B test mode
            success = self.set_decision_mode("ab_test", f"A/B test started: {duration_days} days, {conservative_allocation:.0%}/{aggressive_allocation:.0%} split")
            
            if success:
                self.logger.info(f"🧪 A/B test started: {duration_days} days, Conservative: {conservative_allocation:.0%}, Aggressive: {aggressive_allocation:.0%}")
                self.logger.info(f"📅 Test period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error starting A/B test: {e}")
            return False
    
    def stop_ab_test(self, return_to_mode: str = "conservative") -> bool:
        """
        Stop current A/B test and return to specified mode
        
        Args:
            return_to_mode: Mode to return to after stopping test
            
        Returns:
            bool: Success status
        """
        try:
            if not self.config["ab_test_config"].get("enabled", False):
                self.logger.warning("No A/B test is currently running")
                return False
            
            # Disable A/B test
            self.config["ab_test_config"]["enabled"] = False
            self.config["ab_test_config"]["actual_end_date"] = datetime.utcnow().isoformat()
            
            # Generate A/B test results
            results = self._generate_ab_test_results()
            
            # Switch back to specified mode
            success = self.set_decision_mode(return_to_mode, f"A/B test completed, returning to {return_to_mode}")
            
            if success:
                self.logger.info(f"🧪 A/B test stopped, returned to {return_to_mode} mode")
                if results:
                    self.logger.info(f"📊 A/B test results: {results.get('summary', 'No summary available')}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error stopping A/B test: {e}")
            return False
    
    def _generate_ab_test_results(self) -> Optional[Dict[str, Any]]:
        """Generate A/B test results summary"""
        try:
            # This would analyze the performance of both modes during the test
            # For now, return a placeholder structure
            
            test_config = self.config["ab_test_config"]
            
            results = {
                "test_period": {
                    "start_date": test_config.get("start_date"),
                    "planned_end_date": test_config.get("end_date"),
                    "actual_end_date": test_config.get("actual_end_date"),
                    "duration_days": test_config.get("test_duration_days")
                },
                "allocation": {
                    "conservative": test_config.get("conservative_allocation"),
                    "aggressive": test_config.get("aggressive_allocation")
                },
                "summary": "A/B test completed - detailed analysis would be implemented here",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Save results
            with open(self.results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating A/B test results: {e}")
            return None
    
    def get_ab_test_status(self) -> Dict[str, Any]:
        """Get current A/B test status"""
        ab_config = self.config.get("ab_test_config", {})
        
        status = {
            "enabled": ab_config.get("enabled", False),
            "current_mode": self.get_current_mode()
        }
        
        if status["enabled"]:
            from datetime import datetime
            start_date = datetime.fromisoformat(ab_config["start_date"])
            end_date = datetime.fromisoformat(ab_config["end_date"])
            now = datetime.utcnow()
            
            status.update({
                "start_date": ab_config["start_date"],
                "end_date": ab_config["end_date"],
                "days_remaining": max(0, (end_date - now).days),
                "conservative_allocation": ab_config.get("conservative_allocation"),
                "aggressive_allocation": ab_config.get("aggressive_allocation"),
                "progress": min(1.0, (now - start_date).total_seconds() / (end_date - start_date).total_seconds())
            })
        
        return status
    
    def get_mode_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent mode change history"""
        history = self.config.get("mode_history", [])
        return history[-limit:] if limit > 0 else history
    
    def get_performance_comparison(self) -> Dict[str, Any]:
        """Get performance comparison between modes (placeholder)"""
        # This would integrate with the actual performance tracking system
        return {
            "conservative": {
                "total_decisions": 0,
                "avg_confidence": 0,
                "success_rate": 0
            },
            "aggressive": {
                "total_decisions": 0,
                "avg_confidence": 0,
                "success_rate": 0
            },
            "hybrid": {
                "total_decisions": 0,
                "avg_confidence": 0,
                "success_rate": 0
            },
            "last_updated": datetime.utcnow().isoformat(),
            "note": "Performance tracking integration would be implemented here"
        }