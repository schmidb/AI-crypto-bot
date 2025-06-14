import logging
import os
from config import config
import shutil
import glob
from typing import Any
from config import WEBSERVER_SYNC_ENABLED, WEBSERVER_SYNC_PATH

logger = logging.getLogger(__name__)

class WebServerSync:
    """Handles synchronization of dashboard files to web server"""
    
    def __init__(self):
        """Initialize web server sync"""
        self.enabled = WEBSERVER_SYNC_ENABLED
        self.web_path = WEBSERVER_SYNC_PATH
        
        if self.enabled:
            logger.info(f"Web server sync enabled - target: {self.web_path}")
        else:
            logger.info("Web server sync disabled")
    
    def _are_same_file(self, path1: str, path2: str) -> bool:
        """Check if two paths point to the same file (same inode)"""
        try:
            if not os.path.exists(path1) or not os.path.exists(path2):
                return False
            return os.stat(path1).st_ino == os.stat(path2).st_ino
        except Exception:
            return False

    def _ensure_hard_link(self, source: str, dest: str) -> None:
        """Ensure destination is a hard link to source"""
        try:
            if not os.path.exists(source):
                logger.info(f"Source file does not exist: {source}")
                return
                
            # Create destination directory if needed
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            
            # If destination exists but isn't the same file, remove it
            if os.path.exists(dest) and not self._are_same_file(source, dest):
                os.unlink(dest)
            
            # Create hard link if needed
            if not os.path.exists(dest):
                os.link(source, dest)
                logger.info(f"Created hard link: {dest}")
            else:
                logger.info(f"Hard link already exists: {dest}")
                
        except Exception as e:
            logger.error(f"Error creating hard link {dest}: {e}")
    
    def sync_to_webserver(self) -> None:
        """Sync all dashboard files to web server if enabled"""
        if not self.enabled:
            logger.info("Web server sync disabled, skipping")
            return
        
        try:
            logger.info("Starting web server sync")
            
            # Ensure web server directory exists
            os.makedirs(self.web_path, exist_ok=True)
            
            # Sync data files
            self._sync_data_files()
            
            # Sync market data
            self._sync_market_data()
            
            # Sync static files
            self._sync_static_files()
            
            # Sync images
            self._sync_images()
            
            logger.info("Web server sync completed successfully")
            
        except Exception as e:
            logger.error(f"Error syncing to web server: {e}")
    
    def _sync_data_files(self) -> None:
        """Sync data files using hard links"""
        try:
            data_files = {
                "data/portfolio/portfolio.json": "data/portfolio/portfolio.json",
                "data/portfolio/portfolio_history.csv": "data/portfolio/portfolio_history.csv",
                "data/config/config.json": "data/config/config.json",
                "data/config/detailed_config.json": "data/config/detailed_config.json",
                "data/cache/latest_decisions.json": "data/cache/latest_decisions.json",
                "data/cache/trading_data.json": "data/cache/trading_data.json",
                "data/cache/last_updated.txt": "data/cache/last_updated.txt",
                "data/cache/bot_startup.json": "data/cache/bot_startup.json",
                "data/cache/bot_uptime.json": "data/cache/bot_uptime.json",
                "data/trades/trade_history.json": "data/trades/trade_history.json",
                "data/reports/strategy_performance.json": "data/reports/strategy_performance.json"
            }
            
            for source_rel_path, dest_rel_path in data_files.items():
                source_abs_path = os.path.abspath(source_rel_path)
                dest_abs_path = os.path.join(self.web_path, dest_rel_path)
                self._ensure_hard_link(source_abs_path, dest_abs_path)
            
            logger.info("Data files synced")
            
        except Exception as e:
            logger.error(f"Error syncing data files: {e}")
    
    def _sync_market_data(self) -> None:
        """Sync latest decision files directly (no separate market_data folder)"""
        try:
            data_dir = os.path.abspath("data")
            web_data_dir = f"{self.web_path}/data"
            
            # Ensure data directory exists
            os.makedirs(web_data_dir, exist_ok=True)
            
            # Update files for each trading pair - create direct links to latest files
            assets = ['BTC', 'ETH', 'SOL']
            
            for asset in assets:
                # Find the latest decision file for this asset
                pattern = f"{data_dir}/{asset}_{config.BASE_CURRENCY}_*.json"
                files = glob.glob(pattern)
                
                if files:
                    # Sort by filename (which includes timestamp) and get the latest
                    latest_file = sorted(files)[-1]
                    dest_file = f"{web_data_dir}/{asset}_{config.BASE_CURRENCY}_latest.json"
                    self._ensure_hard_link(latest_file, dest_file)
                else:
                    logger.warning(f"No decision files found for {asset}")
            
            logger.info("Latest decision files synced directly")
            
        except Exception as e:
            logger.error(f"Error syncing latest decision files: {e}")
    
    def _sync_static_files(self) -> None:
        """Sync static HTML, CSS, JS files using hard links"""
        try:
            if not os.path.exists("dashboard/static"):
                logger.warning("Dashboard static directory not found")
                return
            
            for file in os.listdir("dashboard/static"):
                if file.endswith((".html", ".css", ".js")):
                    source_path = os.path.abspath(f"dashboard/static/{file}")
                    dest_path = f"{self.web_path}/{file}"
                    
                    # For HTML files, we need to modify paths for web server
                    if file.endswith(".html"):
                        self._copy_and_modify_html(source_path, dest_path)
                    else:
                        self._ensure_hard_link(source_path, dest_path)
            
            logger.info("Static files synced")
            
        except Exception as e:
            logger.error(f"Error syncing static files: {e}")
    
    def _copy_and_modify_html(self, source_path: str, dest_path: str) -> None:
        """Copy HTML file and modify paths for web server"""
        try:
            with open(source_path, "r") as f:
                content = f.read()
            
            # Replace relative paths for web server
            content = content.replace("/crypto-bot/data/BTC_USD_latest.json", "./data/BTC_USD_latest.json")
            content = content.replace("/crypto-bot/data/ETH_USD_latest.json", "./data/ETH_USD_latest.json")
            content = content.replace("/crypto-bot/data/SOL_USD_latest.json", "./data/SOL_USD_latest.json")
            content = content.replace("/crypto-bot/data/portfolio/portfolio.json", "./data/portfolio/portfolio.json")
            content = content.replace("/crypto-bot/data/trades/trade_history.json", "./data/trades/trade_history.json")
            content = content.replace("/crypto-bot/data/config/config.json", "./data/config/config.json")
            content = content.replace("/crypto-bot/data/config/detailed_config.json", "./data/config/detailed_config.json")
            content = content.replace("/crypto-bot/data/cache/", "./data/cache/")
            content = content.replace("/crypto-bot/images/", "./images/")
            # Legacy path replacements for backward compatibility
            content = content.replace("../data/BTC_USD_latest.json", "./data/BTC_USD_latest.json")
            content = content.replace("../data/ETH_USD_latest.json", "./data/ETH_USD_latest.json")
            content = content.replace("../data/SOL_USD_latest.json", "./data/SOL_USD_latest.json")
            content = content.replace("../data/portfolio/portfolio.json", "./data/portfolio/portfolio.json")
            content = content.replace("../data/trades/trade_history.json", "./data/trades/trade_history.json")
            content = content.replace("../data/cache/", "./data/cache/")
            content = content.replace("../images/", "./images/")
            
            # Write the modified content
            with open(dest_path, "w") as f:
                f.write(content)
            
            logger.info(f"Modified and copied HTML file: {os.path.basename(source_path)}")
            
        except Exception as e:
            logger.error(f"Error copying and modifying HTML file {source_path}: {e}")
    
    def _sync_images(self) -> None:
        """Sync image files using hard links"""
        try:
            if not os.path.exists("dashboard/images"):
                logger.info("Dashboard images directory not found")
                return
            
            images_dir = f"{self.web_path}/images"
            os.makedirs(images_dir, exist_ok=True)
            
            for file in os.listdir("dashboard/images"):
                if file.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
                    source_path = os.path.abspath(f"dashboard/images/{file}")
                    dest_path = f"{images_dir}/{file}"
                    self._ensure_hard_link(source_path, dest_path)
            
            logger.info("Images synced")
            
        except Exception as e:
            logger.error(f"Error syncing images: {e}")
    
    def force_sync(self) -> None:
        """Force sync regardless of enabled status (for manual sync)"""
        original_enabled = self.enabled
        self.enabled = True
        try:
            self.sync_to_webserver()
        finally:
            self.enabled = original_enabled
