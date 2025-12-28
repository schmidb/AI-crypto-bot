import logging
import json
import os
import datetime
from typing import Dict, List, Any
import pandas as pd
from config import config

logger = logging.getLogger(__name__)

# Import performance tracking components
try:
    from utils.performance.performance_dashboard_updater import PerformanceDashboardUpdater
    PERFORMANCE_TRACKING_AVAILABLE = True
except ImportError:
    PERFORMANCE_TRACKING_AVAILABLE = False
    logger.warning("Performance tracking not available - dashboard will not include performance data")

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
            self._update_html_detailed_analysis()  # Add HTML detailed analysis update
            self._create_individual_latest_files()  # Create individual latest files for dashboard
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
                    f.write("timestamp,portfolio_value_usd,btc_amount,eth_amount,sol_amount,usd_amount,btc_price,eth_price,sol_price,portfolio_value_eur\n")
            
            # Extract and append data
            timestamp = datetime.datetime.now().isoformat()
            
            # Handle portfolio values that might be dictionaries or numbers
            portfolio_value_usd_raw = portfolio.get("portfolio_value_usd", 0)
            portfolio_value_eur_raw = portfolio.get("portfolio_value_eur", 0)
            
            # Convert to float, handling dict case
            if isinstance(portfolio_value_usd_raw, dict):
                portfolio_value_usd = float(portfolio_value_usd_raw.get("amount", 0))
            else:
                portfolio_value_usd = float(portfolio_value_usd_raw) if portfolio_value_usd_raw else 0
                
            if isinstance(portfolio_value_eur_raw, dict):
                portfolio_value_eur = float(portfolio_value_eur_raw.get("amount", 0))
            else:
                portfolio_value_eur = float(portfolio_value_eur_raw) if portfolio_value_eur_raw else 0
            
            # Extract asset data with validation
            btc_data = portfolio.get("BTC", {})
            eth_data = portfolio.get("ETH", {})
            sol_data = portfolio.get("SOL", {})
            usd_data = portfolio.get("USD", {})
            eur_data = portfolio.get("EUR", {})  # Add EUR support
            
            if not isinstance(btc_data, dict): btc_data = {"amount": 0, "last_price_eur": 0}
            if not isinstance(eth_data, dict): eth_data = {"amount": 0, "last_price_eur": 0}
            if not isinstance(sol_data, dict): sol_data = {"amount": 0, "last_price_eur": 0}
            if not isinstance(usd_data, dict): usd_data = {"amount": 0}
            if not isinstance(eur_data, dict): eur_data = {"amount": 0}
            
            btc_amount = float(btc_data.get("amount", 0))
            eth_amount = float(eth_data.get("amount", 0))
            sol_amount = float(sol_data.get("amount", 0))
            usd_amount = float(usd_data.get("amount", 0))
            eur_amount = float(eur_data.get("amount", 0))  # Use EUR amount instead of USD
            btc_price = float(btc_data.get("last_price_eur", 0))  # Use EUR prices
            eth_price = float(eth_data.get("last_price_eur", 0))  # Use EUR prices
            sol_price = float(sol_data.get("last_price_eur", 0))  # Use EUR prices
            
            # Use EUR amount instead of USD amount for the CSV
            with open(history_file, "a") as f:
                f.write(f"{timestamp},{portfolio_value_usd},{btc_amount},{eth_amount},{sol_amount},{eur_amount},{btc_price},{eth_price},{sol_price},{portfolio_value_eur}\n")
                
        except Exception as e:
            logger.error(f"Error appending portfolio history: {e}")
            logger.debug(f"Portfolio data causing error: {portfolio}")
    
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
        """Update latest trading decisions cache with multi-strategy data"""
        try:
            latest_decisions = []
            # Get assets from trading pairs
            assets = [pair.split('-')[0] for pair in config.TRADING_PAIRS]
            
            # Get latest decision data for each asset
            for asset in assets:
                try:
                    # Read the latest decision file directly, excluding *_latest.json files
                    import glob
                    import os
                    pattern = f"data/{asset}_EUR_*.json"  # Updated to EUR
                    files = glob.glob(pattern)
                    
                    # Filter out *_latest.json files as they may contain stale data
                    files = [f for f in files if not f.endswith('_latest.json')]
                    
                    if files:
                        # Sort by modification time to get the truly latest file
                        latest_file = max(files, key=os.path.getmtime)
                        with open(latest_file, "r") as f:
                            decision_data = json.load(f)
                        
                        # Extract strategy details if available
                        strategy_details = decision_data.get("strategy_details", {})
                        
                        decision = {
                            "timestamp": decision_data.get("timestamp", ""),
                            "asset": asset,
                            "action": decision_data.get("action", "unknown"),
                            "confidence": decision_data.get("confidence", 0),
                            "reasoning": decision_data.get("reason", decision_data.get("reasoning", "No reasoning provided")),
                            "strategy_details": strategy_details
                        }
                        
                        # Add multi-strategy specific data
                        if strategy_details:
                            decision["market_regime"] = strategy_details.get("market_regime", "unknown")
                            decision["individual_strategies"] = strategy_details.get("individual_strategies", {})
                            decision["combined_signal"] = strategy_details.get("combined_signal", {})
                            decision["strategy_weights"] = strategy_details.get("strategy_weights", {})
                            
                            # Create ai_analysis structure for JavaScript compatibility
                            individual_strategies = strategy_details.get("individual_strategies", {})
                            detailed_reasoning = []
                            for strategy_name, strategy_data in individual_strategies.items():
                                strategy_reasoning = strategy_data.get("reasoning", "")
                                if strategy_reasoning:
                                    detailed_reasoning.append(f"{strategy_name.replace('_', ' ').title()}: {strategy_reasoning}")
                            
                            decision["ai_analysis"] = {
                                "detailed_reasoning": detailed_reasoning if detailed_reasoning else ["No detailed reasoning available"]
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
                
            logger.debug(f"Updated latest decisions with multi-strategy data for {len(latest_decisions)} assets")
                
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
                        
                        # Try to get volatility from ai_analysis first (legacy format)
                        market_conditions = data.get('ai_analysis', {}).get('market_conditions', {})
                        volatility = market_conditions.get('volatility', 'unknown')
                        
                        # If not found, calculate from price changes (current format)
                        if volatility == 'unknown':
                            market_data = data.get('market_data', {})
                            price_changes = market_data.get('price_changes', {})
                            
                            if price_changes:
                                # Calculate volatility based on price changes
                                changes = [abs(price_changes.get('1h', 0)), 
                                          abs(price_changes.get('4h', 0)), 
                                          abs(price_changes.get('24h', 0))]
                                avg_change = sum(changes) / len(changes) if changes else 0
                                
                                if avg_change > 3.0:  # >3% average change = high volatility
                                    volatility = 'high'
                                elif avg_change > 1.5:  # >1.5% average change = medium volatility
                                    volatility = 'medium'
                                else:
                                    volatility = 'low'
                                
                                logger.debug(f"Calculated volatility '{volatility}' from price changes {changes} in {file}")
                        
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
    
    def _update_html_detailed_analysis(self) -> None:
        """Update HTML template with detailed analysis data"""
        try:
            # Read the latest decisions data
            latest_decisions_file = "data/cache/latest_decisions.json"
            if not os.path.exists(latest_decisions_file):
                logger.warning("Latest decisions file not found, skipping HTML detailed analysis update")
                return
                
            with open(latest_decisions_file, "r") as f:
                latest_decisions = json.load(f)
            
            # Read the HTML template
            html_file = "dashboard/static/index.html"
            if not os.path.exists(html_file):
                logger.warning("HTML template not found, skipping detailed analysis update")
                return
                
            with open(html_file, "r") as f:
                html_content = f.read()
            
            # Update detailed analysis for each asset
            for decision in latest_decisions:
                asset = decision.get("asset", "")
                if not asset:
                    continue
                    
                # Extract detailed analysis data
                strategy_details = decision.get("strategy_details", {})
                individual_strategies = strategy_details.get("individual_strategies", {})
                combined_signal = strategy_details.get("combined_signal", {})
                
                # Build detailed reasoning list
                reasoning_items = []
                if individual_strategies:
                    for strategy_name, strategy_data in individual_strategies.items():
                        strategy_reasoning = strategy_data.get("reasoning", "")
                        if strategy_reasoning:
                            reasoning_items.append(f"<li><strong>{strategy_name.replace('_', ' ').title()}:</strong> {strategy_reasoning}</li>")
                
                if not reasoning_items:
                    reasoning_items = ["<li>No detailed reasoning available</li>"]
                
                # Build bot decision logic
                confidence = decision.get("confidence", 0)
                action = decision.get("action", "unknown")
                confidence_threshold = 70  # Default threshold
                
                threshold_check = f"Confidence {confidence}% {'meets' if confidence >= confidence_threshold else 'below'} threshold ({confidence_threshold}%)"
                risk_assessment = f"Risk level: {strategy_details.get('market_regime', 'unknown').title()}"
                final_reason = f"Final decision: {action} based on combined analysis"
                
                # Build execution context
                analysis_duration = decision.get("analysis_duration_ms", 0)
                model_used = "Multi-Strategy Analysis"
                data_quality = "Good" if strategy_details else "Limited"
                
                # Update HTML for this asset
                asset_section_pattern = f'<div class="col-md-4" data-asset="{asset}">'
                asset_start = html_content.find(asset_section_pattern)
                
                if asset_start != -1:
                    # Find the detailed analysis section for this asset
                    detailed_analysis_start = html_content.find('<div class="detailed-analysis">', asset_start)
                    if detailed_analysis_start != -1:
                        # Find the end of this detailed analysis section
                        detailed_analysis_end = html_content.find('</div>', detailed_analysis_start)
                        # Find the actual end (there are nested divs)
                        div_count = 1
                        search_pos = detailed_analysis_start + len('<div class="detailed-analysis">')
                        while div_count > 0 and search_pos < len(html_content):
                            next_open = html_content.find('<div', search_pos)
                            next_close = html_content.find('</div>', search_pos)
                            
                            if next_close == -1:
                                break
                            if next_open != -1 and next_open < next_close:
                                div_count += 1
                                search_pos = next_open + 4
                            else:
                                div_count -= 1
                                search_pos = next_close + 6
                                if div_count == 0:
                                    detailed_analysis_end = next_close + 6
                        
                        if detailed_analysis_end != -1:
                            # Replace the detailed analysis section
                            new_detailed_analysis = f'''<div class="detailed-analysis">
                                                    <div class="analysis-section">
                                                        <h6>AI Detailed Reasoning</h6>
                                                        <ul class="analysis-list ai-reasoning-list">
                                                            {''.join(reasoning_items)}
                                                        </ul>
                                                    </div>
                                                    
                                                    <div class="analysis-section">
                                                        <h6>Bot Decision Logic <span class="tooltip"><i class="fas fa-question-circle help-icon" style="font-size: 0.8rem;"></i><span class="tooltiptext"><h6>AI Decision Making Process</h6>Shows how the bot processes AI recommendations:<ul><li><strong>Confidence Check:</strong> Verifies AI confidence meets minimum threshold</li><li><strong>Risk Assessment:</strong> Evaluates market conditions and portfolio risk</li><li><strong>Final Decision:</strong> Combines AI analysis with risk management rules</li></ul><div class="example">Bot may override AI recommendations if risk is too high</div></span></span></h6>
                                                        <ul class="analysis-list bot-logic-list">
                                                            <li class="threshold-info">Confidence threshold check: {threshold_check}</li>
                                                            <li class="risk-info">Risk management applied: {risk_assessment}</li>
                                                            <li class="final-reason">Final decision reason: {final_reason}</li>
                                                        </ul>
                                                    </div>
                                                    
                                                    <div class="analysis-section">
                                                        <h6>Execution Context</h6>
                                                        <ul class="analysis-list execution-context-list">
                                                            <li class="data-quality">Market data quality: {data_quality}</li>
                                                            <li class="analysis-duration">Analysis duration: {analysis_duration:.2f}ms</li>
                                                            <li class="model-used">Analysis model: {model_used}</li>
                                                        </ul>
                                                    </div>
                                                </div>'''
                            
                            html_content = html_content[:detailed_analysis_start] + new_detailed_analysis + html_content[detailed_analysis_end:]
            
            # Write the updated HTML back
            with open(html_file, "w") as f:
                f.write(html_content)
                
            logger.debug("Updated HTML detailed analysis sections")
            
        except Exception as e:
            logger.error(f"Error updating HTML detailed analysis: {e}")
    
    def _create_individual_latest_files(self) -> None:
        """Create individual latest decision files for dashboard JavaScript"""
        try:
            # Read the latest decisions data
            latest_decisions_file = "data/cache/latest_decisions.json"
            if not os.path.exists(latest_decisions_file):
                logger.warning("Latest decisions file not found, skipping individual file creation")
                return
                
            with open(latest_decisions_file, "r") as f:
                latest_decisions = json.load(f)
            
            # Create individual files for each asset
            for decision in latest_decisions:
                asset = decision.get("asset", "")
                if not asset:
                    continue
                    
                # Create individual latest file
                individual_file = f"data/{asset}_EUR_latest.json"
                with open(individual_file, "w") as f:
                    json.dump(decision, f, indent=2, default=str)
                    
            logger.debug(f"Created individual latest files for {len(latest_decisions)} assets")
            
        except Exception as e:
            logger.error(f"Error creating individual latest files: {e}")

    
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
