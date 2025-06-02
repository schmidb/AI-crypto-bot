import logging
import json
import os
import datetime
import shutil
import subprocess
from typing import Dict, List, Any, Union
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Updates the web dashboard with latest trading data and portfolio information"""
    
    def __init__(self, dashboard_dir="dashboard"):
        """Initialize the dashboard updater"""
        self.dashboard_dir = dashboard_dir
        os.makedirs(f"{dashboard_dir}/data", exist_ok=True)
        os.makedirs(f"{dashboard_dir}/images", exist_ok=True)
        
        # Ensure dashboard template files exist
        self._ensure_dashboard_files_exist()
    
    def update_dashboard(self, trading_data: Dict[str, Any], portfolio: Dict[str, Any]) -> None:
        """Update the dashboard with latest trading and portfolio data"""
        try:
            logger.info(f"Starting dashboard update")
            self._update_trading_data(trading_data)
            logger.info(f"Trading data updated to {self.dashboard_dir}/data/trading_data.json")
            self._update_portfolio_data(portfolio)
            logger.info(f"Portfolio data updated to {self.dashboard_dir}/data/portfolio_data.json")
            self._update_config_data()
            logger.info(f"Config data updated to {self.dashboard_dir}/data/config.json")
            self._update_latest_decisions(trading_data)
            logger.info(f"Latest decisions updated to {self.dashboard_dir}/data/latest_decisions.json")
            self._generate_charts(trading_data, portfolio)
            logger.info(f"Charts generated in {self.dashboard_dir}/images/")
            self._update_timestamp()
            logger.info(f"Timestamp updated to {self.dashboard_dir}/data/last_updated.txt")
            self._sync_to_webserver()  # Sync files to web server
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def _ensure_dashboard_files_exist(self) -> None:
        """Ensure all necessary dashboard files exist"""
        # Check if index.html exists
        index_path = os.path.join(self.dashboard_dir, "index.html")
        if not os.path.exists(index_path):
            # Copy from template
            template_path = os.path.join("dashboard_templates", "index.html")
            if os.path.exists(template_path):
                shutil.copy(template_path, index_path)
                logger.info(f"Created dashboard index file from template: {index_path}")
            else:
                logger.warning(f"Dashboard template not found: {template_path}")
        
        # Check if analysis.html exists
        analysis_path = os.path.join(self.dashboard_dir, "analysis.html")
        if not os.path.exists(analysis_path):
            # Copy from template
            template_path = os.path.join("dashboard_templates", "analysis.html")
            if os.path.exists(template_path):
                shutil.copy(template_path, analysis_path)
                logger.info(f"Created dashboard analysis file from template: {analysis_path}")
            else:
                logger.warning(f"Dashboard analysis template not found: {template_path}")
            
    def _update_config_data(self) -> None:
        """Update configuration data for the dashboard"""
        try:
            from config import (
                TRADING_PAIRS, DECISION_INTERVAL_MINUTES, RISK_LEVEL,
                LLM_MODEL, PORTFOLIO_REBALANCE, MAX_TRADE_PERCENTAGE,
                SIMULATION_MODE, TARGET_ALLOCATION_BTC, TARGET_ALLOCATION_ETH,
                TARGET_ALLOCATION_USD
            )
