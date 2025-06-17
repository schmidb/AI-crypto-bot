import logging
import json
import os
import datetime
from typing import Dict, List, Any
import pandas as pd

# Import performance tracking components
try:
    from utils.performance_dashboard_updater import PerformanceDashboardUpdater
    PERFORMANCE_TRACKING_AVAILABLE = True
except ImportError:
    PERFORMANCE_TRACKING_AVAILABLE = False
    logger.warning("Performance tracking not available - dashboard will not include performance data")

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Updates local dashboard data files - web server sync handled separately"""
    
    def __init__(self):
        """Initialize the dashboard updater for local data management only"""
        # Create directories if they don't exist
        os.makedirs("data/portfolio", exist_ok=True)
        os.makedirs("data/cache", exist_ok=True)
        os.makedirs("data/config", exist_ok=True)
        os.makedirs("data/dashboard", exist_ok=True)  # For performance data
        os.makedirs("dashboard/images", exist_ok=True)
        
        # Initialize performance dashboard updater if available
        self.performance_updater = None
        if PERFORMANCE_TRACKING_AVAILABLE:
            try:
                self.performance_updater = PerformanceDashboardUpdater()
                logger.info("Performance dashboard updater initialized")
            except Exception as e:
                logger.error(f"Failed to initialize performance dashboard updater: {e}")
                self.performance_updater = None
    
    def update_dashboard(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Update local dashboard data files only"""
        try:
            logger.info("Updating local dashboard data")
            self._update_trading_cache(trading_data)
            self._update_portfolio_data(portfolio)
            self._update_config_data()
            self._update_detailed_config_data()
            self._update_latest_decisions(trading_data)
            self._update_logs_data()
            self._update_performance_data(portfolio)  # Add performance data update
            self._update_timestamp()
            logger.info("Local dashboard data updated successfully")
        except Exception as e:
            logger.error(f"Error updating local dashboard data: {e}")
    
    def _update_trading_cache(self, trading_data: Dict[str, Any]) -> None:
        """Update trading data cache file"""
        with open("data/cache/trading_data.json", "w") as f:
            json.dump(trading_data, f, indent=2)
        logger.debug("Updated trading data cache")
    
    def _update_portfolio_data(self, portfolio: Dict[str, Any]) -> None:
        """Update portfolio data file"""
        try:
            if not portfolio or not isinstance(portfolio, dict):
                logger.warning(f"Invalid portfolio data: {type(portfolio)}")
                return
            
            # Process portfolio data
            import copy
            portfolio_copy = copy.deepcopy(portfolio)
            
            # Get the most recent timestamp from trades or decisions
            latest_trade_time = self._get_latest_trade_timestamp()
            latest_decision_time = self._get_latest_decision_timestamp()
            latest_time = max(latest_trade_time, latest_decision_time)
            
            # Use the most recent timestamp for last_updated
            portfolio_copy["last_updated"] = latest_time
            
            # Save to portfolio data file (standardized to portfolio.json)
            with open("data/portfolio/portfolio.json", "w") as f:
                json.dump(portfolio_copy, f, indent=2, default=str)
            
            logger.debug("Updated portfolio data")
            
            # Update portfolio history
            self._append_portfolio_history(portfolio_copy)
            
        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}")
    
    def _append_portfolio_history(self, portfolio: Dict[str, Any]) -> None:
        """Append current portfolio value to historical data"""
        try:
            history_file = "data/portfolio/portfolio_history.csv"
            
            # Create new history file if it doesn't exist
            if not os.path.exists(history_file):
                with open(history_file, "w") as f:
                    f.write("timestamp,portfolio_value_usd,btc_amount,eth_amount,sol_amount,usd_amount,btc_price,eth_price,sol_price\n")
            
            # Extract and append data
            timestamp = datetime.datetime.now().isoformat()
            portfolio_value = float(portfolio.get("portfolio_value_usd", 0))
            
            # Extract asset data with validation
            btc_data = portfolio.get("BTC", {})
            eth_data = portfolio.get("ETH", {})
            sol_data = portfolio.get("SOL", {})
            usd_data = portfolio.get("USD", {})
            
            if not isinstance(btc_data, dict): btc_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(eth_data, dict): eth_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(sol_data, dict): sol_data = {"amount": 0, "last_price_usd": 0}
            if not isinstance(usd_data, dict): usd_data = {"amount": 0}
            
            btc_amount = float(btc_data.get("amount", 0))
            eth_amount = float(eth_data.get("amount", 0))
            sol_amount = float(sol_data.get("amount", 0))
            usd_amount = float(usd_data.get("amount", 0))
            btc_price = float(btc_data.get("last_price_usd", 0))
            eth_price = float(eth_data.get("last_price_usd", 0))
            sol_price = float(sol_data.get("last_price_usd", 0))
            
            with open(history_file, "a") as f:
                f.write(f"{timestamp},{portfolio_value},{btc_amount},{eth_amount},{sol_amount},{usd_amount},{btc_price},{eth_price},{sol_price}\n")
                
        except Exception as e:
            logger.error(f"Error appending portfolio history: {e}")
    
    def _update_config_data(self) -> None:
        """Update configuration data for the dashboard"""
        try:
            from config import (
                TRADING_PAIRS, DECISION_INTERVAL_MINUTES, RISK_LEVEL,
                LLM_MODEL, MAX_TRADE_PERCENTAGE,
                SIMULATION_MODE, TARGET_ALLOCATION, DASHBOARD_TRADE_HISTORY_LIMIT
            )
            
            # Get current market volatility from recent analysis
            market_volatility = self._get_current_market_volatility()
            
            config_data = {
                "trading_pairs": ",".join(TRADING_PAIRS),
                "decision_interval_minutes": DECISION_INTERVAL_MINUTES,
                "risk_level": RISK_LEVEL,
                "market_volatility": market_volatility,
                "llm_model": LLM_MODEL,
                "max_trade_percentage": MAX_TRADE_PERCENTAGE,
                "simulation_mode": SIMULATION_MODE,
                "target_allocation": TARGET_ALLOCATION,
                "dashboard_trade_history_limit": DASHBOARD_TRADE_HISTORY_LIMIT
            }
            
            with open("data/config/config.json", "w") as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating config data: {e}")
    
    def _update_detailed_config_data(self) -> None:
        """Update detailed configuration data including all environment variables"""
        try:
            import os
            from config import config
            
            # Get all configuration attributes from the config object
            detailed_config = {}
            
            # API Credentials
            detailed_config['COINBASE_API_KEY'] = getattr(config, 'COINBASE_API_KEY', None)
            detailed_config['COINBASE_API_SECRET'] = '***HIDDEN***' if getattr(config, 'COINBASE_API_SECRET', None) else None
            
            # Google Cloud Settings
            detailed_config['GOOGLE_CLOUD_PROJECT'] = getattr(config, 'GOOGLE_CLOUD_PROJECT', None)
            detailed_config['GOOGLE_APPLICATION_CREDENTIALS'] = getattr(config, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            
            # LLM Configuration
            detailed_config['LLM_PROVIDER'] = getattr(config, 'LLM_PROVIDER', None)
            detailed_config['LLM_MODEL'] = getattr(config, 'LLM_MODEL', None)
            detailed_config['LLM_LOCATION'] = getattr(config, 'LLM_LOCATION', None)
            
            # Trading Parameters
            detailed_config['TRADING_PAIRS'] = ",".join(getattr(config, 'TRADING_PAIRS', []))
            detailed_config['DECISION_INTERVAL_MINUTES'] = getattr(config, 'DECISION_INTERVAL_MINUTES', None)
            detailed_config['RISK_LEVEL'] = getattr(config, 'RISK_LEVEL', None)
            detailed_config['SIMULATION_MODE'] = getattr(config, 'SIMULATION_MODE', None)
            
            # Portfolio Management
            detailed_config['MAX_TRADE_PERCENTAGE'] = getattr(config, 'MAX_TRADE_PERCENTAGE', None)
            detailed_config['TARGET_CRYPTO_ALLOCATION'] = getattr(config, 'TARGET_CRYPTO_ALLOCATION', None)
            detailed_config['TARGET_USD_ALLOCATION'] = getattr(config, 'TARGET_USD_ALLOCATION', None)
            
            # Enhanced Trading Strategy
            detailed_config['CONFIDENCE_THRESHOLD_BUY'] = getattr(config, 'CONFIDENCE_THRESHOLD_BUY', None)
            detailed_config['CONFIDENCE_THRESHOLD_SELL'] = getattr(config, 'CONFIDENCE_THRESHOLD_SELL', None)
            detailed_config['CONFIDENCE_BOOST_TREND_ALIGNED'] = getattr(config, 'CONFIDENCE_BOOST_TREND_ALIGNED', None)
            detailed_config['CONFIDENCE_PENALTY_COUNTER_TREND'] = getattr(config, 'CONFIDENCE_PENALTY_COUNTER_TREND', None)
            
            # Technical Analysis
            detailed_config['RSI_NEUTRAL_MIN'] = getattr(config, 'RSI_NEUTRAL_MIN', None)
            detailed_config['RSI_NEUTRAL_MAX'] = getattr(config, 'RSI_NEUTRAL_MAX', None)
            detailed_config['MACD_SIGNAL_WEIGHT'] = getattr(config, 'MACD_SIGNAL_WEIGHT', None)
            detailed_config['RSI_SIGNAL_WEIGHT'] = getattr(config, 'RSI_SIGNAL_WEIGHT', None)
            detailed_config['BOLLINGER_SIGNAL_WEIGHT'] = getattr(config, 'BOLLINGER_SIGNAL_WEIGHT', None)
            
            # Risk Management
            detailed_config['RISK_HIGH_POSITION_MULTIPLIER'] = getattr(config, 'RISK_HIGH_POSITION_MULTIPLIER', None)
            detailed_config['RISK_MEDIUM_POSITION_MULTIPLIER'] = getattr(config, 'RISK_MEDIUM_POSITION_MULTIPLIER', None)
            detailed_config['RISK_LOW_POSITION_MULTIPLIER'] = getattr(config, 'RISK_LOW_POSITION_MULTIPLIER', None)
            
            # Trade Limits
            detailed_config['MIN_TRADE_USD'] = getattr(config, 'MIN_TRADE_USD', None)
            detailed_config['MAX_POSITION_SIZE_USD'] = getattr(config, 'MAX_POSITION_SIZE_USD', None)
            
            # Dashboard & Logging
            detailed_config['DASHBOARD_TRADE_HISTORY_LIMIT'] = getattr(config, 'DASHBOARD_TRADE_HISTORY_LIMIT', None)
            detailed_config['LOG_LEVEL'] = getattr(config, 'LOG_LEVEL', None)
            detailed_config['LOG_FILE'] = getattr(config, 'LOG_FILE', None)
            
            # Web Server Sync
            detailed_config['WEBSERVER_SYNC_ENABLED'] = getattr(config, 'WEBSERVER_SYNC_ENABLED', None)
            detailed_config['WEBSERVER_SYNC_PATH'] = getattr(config, 'WEBSERVER_SYNC_PATH', None)
            
            # Save detailed configuration
            with open("data/config/detailed_config.json", "w") as f:
                json.dump(detailed_config, f, indent=2, default=str)
                
            logger.debug("Updated detailed configuration data")
                
        except Exception as e:
            logger.error(f"Error updating detailed config data: {e}")
    
    def _update_latest_decisions(self, trading_data: Dict[str, Any]) -> None:
        """Update latest trading decisions cache"""
        try:
            latest_decisions = []
            assets = ["BTC", "ETH", "SOL"]
            
            # Get latest decision data for each asset
            for asset in assets:
                try:
                    # Read the latest decision file directly
                    import glob
                    pattern = f"data/{asset}_USD_*.json"
                    files = glob.glob(pattern)
                    
                    if files:
                        # Get the latest file
                        latest_file = sorted(files)[-1]
                        with open(latest_file, "r") as f:
                            decision_data = json.load(f)
                            
                        decision = {
                            "timestamp": decision_data.get("timestamp", ""),
                            "asset": asset,
                            "action": decision_data.get("action", "unknown"),
                            "confidence": decision_data.get("confidence", 0),
                            "reasoning": decision_data.get("reason", decision_data.get("reasoning", "No reasoning provided"))
                        }
                        latest_decisions.append(decision)
                    else:
                        logger.warning(f"No decision files found for {asset}")
                        
                except Exception as e:
                    logger.error(f"Error reading latest decision data for {asset}: {e}")
            
            # Sort by timestamp, newest first
            latest_decisions.sort(key=lambda x: x["timestamp"], reverse=True)
            
            with open("data/cache/latest_decisions.json", "w") as f:
                json.dump(latest_decisions, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error updating latest decisions: {e}")
    
    def _update_logs_data(self) -> None:
        """Update logs data for dashboard display"""
        try:
            from utils.log_reader import LogReader
            
            # Initialize log reader
            log_reader = LogReader()
            
            # Get recent logs (last 30 lines)
            logs_data = log_reader.get_formatted_logs(num_lines=30)
            
            # Save to dashboard data directory
            os.makedirs("data/cache", exist_ok=True)
            with open("data/cache/logs_data.json", "w") as f:
                json.dump(logs_data, f, indent=2)
            
            logger.debug("Updated logs data for dashboard")
            
        except Exception as e:
            logger.error(f"Error updating logs data: {e}")
            # Create empty logs data on error
            try:
                empty_logs = {
                    "logs": [],
                    "parsed_logs": [],
                    "stats": {"exists": False, "error": str(e)},
                    "count": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "error",
                    "error": str(e)
                }
                os.makedirs("data/cache", exist_ok=True)
                with open("data/cache/logs_data.json", "w") as f:
                    json.dump(empty_logs, f, indent=2)
            except Exception as nested_e:
                logger.error(f"Error creating empty logs data: {nested_e}")
    
    def _update_timestamp(self) -> None:
        """Update the last updated timestamp using most recent activity"""
        try:
            # Get the most recent timestamp from trades or decisions
            latest_trade_time = self._get_latest_trade_timestamp()
            latest_decision_time = self._get_latest_decision_timestamp()
            latest_time = max(latest_trade_time, latest_decision_time)
            
            # Convert to datetime for formatting
            timestamp = datetime.datetime.fromisoformat(latest_time.replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M:%S")
            
            with open("data/cache/last_updated.txt", "w") as f:
                f.write(timestamp)
        except Exception as e:
            logger.error(f"Error updating timestamp: {e}")
    
    def _get_latest_trade_timestamp(self) -> str:
        """Get the most recent trade timestamp from trade history file"""
        try:
            trade_history_file = "data/trades/trade_history.json"
            if os.path.exists(trade_history_file):
                with open(trade_history_file, "r") as f:
                    trade_history = json.load(f)
                if trade_history and isinstance(trade_history, list):
                    return max([trade.get('timestamp', '2000-01-01T00:00:00') 
                              for trade in trade_history], default='2000-01-01T00:00:00')
        except Exception as e:
            logger.error(f"Error reading trade history: {e}")
        return '2000-01-01T00:00:00'
    
    def _get_current_market_volatility(self) -> str:
        """Get current market volatility from recent analysis files"""
        try:
            import glob
            from datetime import datetime, timedelta
            
            # Get recent analysis files (last 2 hours)
            cutoff_time = datetime.now() - timedelta(hours=2)
            recent_files = []
            
            for pattern in ["data/*_EUR_*.json", "data/*_USD_*.json"]:
                files = glob.glob(pattern)
                for file in files:
                    try:
                        # Extract timestamp from filename - format: ASSET_CURRENCY_YYYYMMDD_HHMMSS.json
                        parts = file.split('_')
                        if len(parts) >= 4:
                            date_part = parts[-2]  # YYYYMMDD
                            time_part = parts[-1].replace('.json', '')  # HHMMSS
                            timestamp_str = f"{date_part}_{time_part}"
                            file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                            if file_time > cutoff_time:
                                recent_files.append(file)
                    except Exception as e:
                        logger.debug(f"Error parsing timestamp from {file}: {e}")
                        continue
            
            logger.debug(f"Found {len(recent_files)} recent analysis files for volatility calculation")
            
            # Analyze volatility from recent files
            volatility_levels = []
            for file in recent_files[-6:]:  # Last 6 files
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        market_conditions = data.get('ai_analysis', {}).get('market_conditions', {})
                        volatility = market_conditions.get('volatility', 'unknown')
                        if volatility != 'unknown':
                            volatility_levels.append(volatility)
                            logger.debug(f"Found volatility '{volatility}' in {file}")
                except Exception as e:
                    logger.debug(f"Error reading volatility from {file}: {e}")
                    continue
            
            if not volatility_levels:
                logger.debug("No volatility data found in recent files")
                return 'unknown'
            
            logger.debug(f"Volatility levels found: {volatility_levels}")
            
            # Determine overall volatility
            high_count = volatility_levels.count('high')
            medium_count = volatility_levels.count('medium')
            low_count = volatility_levels.count('low')
            
            if high_count >= len(volatility_levels) * 0.5:
                calculated_volatility = 'high'
            elif medium_count >= len(volatility_levels) * 0.4:
                calculated_volatility = 'medium'
            else:
                calculated_volatility = 'low'
                
            logger.debug(f"Calculated market volatility: {calculated_volatility} (high:{high_count}, medium:{medium_count}, low:{low_count})")
            return calculated_volatility
                
        except Exception as e:
            logger.error(f"Error getting market volatility: {e}")
            return 'unknown'

    def _get_latest_decision_timestamp(self) -> str:
        """Get the most recent decision timestamp from latest decisions file"""
        try:
            decisions_file = "data/cache/latest_decisions.json"
            if os.path.exists(decisions_file):
                with open(decisions_file, "r") as f:
                    latest_decisions = json.load(f)
                if latest_decisions and isinstance(latest_decisions, list):
                    return max([decision.get('timestamp', '2000-01-01T00:00:00') 
                              for decision in latest_decisions], default='2000-01-01T00:00:00')
        except Exception as e:
            logger.error(f"Error reading latest decisions: {e}")
        return '2000-01-01T00:00:00'
    
    def _update_performance_data(self, portfolio: Dict[str, Any]) -> None:
        """Update performance tracking data for dashboard"""
        try:
            if not self.performance_updater:
                logger.debug("Performance updater not available, skipping performance data update")
                return
            
            # Check if performance data is available
            if not self.performance_updater.is_data_available():
                logger.debug("Performance data not available yet, skipping update")
                return
            
            # Update performance data
            success = self.performance_updater.update_performance_data()
            
            if success:
                logger.info("Performance dashboard data updated successfully")
            else:
                logger.warning("Failed to update performance dashboard data")
                
        except Exception as e:
            logger.error(f"Error updating performance data: {e}")
    
    def get_performance_data_for_period(self, period: str = "30d") -> Dict[str, Any]:
        """
        Get performance data for specific period (for API endpoints)
        
        Args:
            period: Time period ("7d", "30d", "90d", "1y", "all")
            
        Returns:
            Dict containing performance data
        """
        try:
            if not self.performance_updater:
                return {"error": "Performance tracking not available"}
            
            return self.performance_updater.get_performance_data_for_period(period)
            
        except Exception as e:
            logger.error(f"Error getting performance data for period {period}: {e}")
            return {"error": str(e)}
    
    # Dummy methods to handle old chart generation calls gracefully
    def _generate_portfolio_value_chart(self, portfolio: Dict[str, Any]) -> None:
        """Dummy method - chart generation has been removed"""
        logger.debug("Chart generation has been disabled - portfolio value chart not generated")
        pass
    
    def _generate_portfolio_allocation_chart(self, portfolio: Dict[str, Any]) -> None:
        """Dummy method - chart generation has been removed"""
        logger.debug("Chart generation has been disabled - portfolio allocation chart not generated")
        pass
    
    def _generate_allocation_comparison_chart(self, portfolio: Dict[str, Any]) -> None:
        """Dummy method - chart generation has been removed"""
        logger.debug("Chart generation has been disabled - allocation comparison chart not generated")
        pass
