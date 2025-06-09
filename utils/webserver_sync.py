import logging
import os
import shutil
import glob
from typing import Dict, Any
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
    
    def sync_to_webserver(self) -> None:
        """Sync all dashboard files to web server if enabled"""
        if not self.enabled:
            logger.debug("Web server sync disabled, skipping")
            return
        
        try:
            logger.info("Starting web server sync")
            
            # Try no-sudo sync first
            try:
                self.sync_to_webserver_no_sudo()
                logger.info("Web server sync completed successfully (no sudo)")
                return
            except Exception as e:
                logger.warning(f"No-sudo sync failed, falling back to sudo: {e}")
            
            # Initialize web server directory if it doesn't exist
            if not self._initialize_webserver_directory():
                logger.error("Failed to initialize web server directory")
                return
            
            # Sync data files with sudo
            self._sync_data_files()
            
            # Sync market data with sudo
            self._sync_market_data()
            
            # Copy static files with sudo
            self._sync_static_files()
            
            # Copy images with sudo
            self._sync_images()
            
            # Set final permissions
            self._set_webserver_permissions()
            
            logger.info("Web server sync completed successfully (with sudo)")
            
        except Exception as e:
            logger.error(f"Error syncing to web server: {e}")
    
    def _initialize_webserver_directory(self) -> bool:
        """Initialize web server directory structure with proper permissions"""
        try:
            import subprocess
            
            # Check if web server directory exists
            if not os.path.exists(self.web_path):
                logger.info(f"Web server directory {self.web_path} not found, creating...")
                
                # Create the main directory with sudo
                try:
                    subprocess.run(['/usr/bin/sudo', '/bin/mkdir', '-p', self.web_path], check=True)
                    logger.info(f"Created web server directory: {self.web_path}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to create web server directory: {e}")
                    return False
            
            # Create required subdirectories
            subdirs = ['data', 'data/cache', 'data/portfolio', 'data/trades', 'data/reports', 
                      'data/market_data', 'data/config', 'images']
            
            for subdir in subdirs:
                full_path = os.path.join(self.web_path, subdir)
                if not os.path.exists(full_path):
                    try:
                        subprocess.run(['/usr/bin/sudo', '/bin/mkdir', '-p', full_path], check=True)
                        logger.debug(f"Created subdirectory: {full_path}")
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Failed to create subdirectory {full_path}: {e}")
            
            # Set initial ownership to www-data
            try:
                subprocess.run(['/usr/bin/sudo', '/bin/chown', '-R', 'www-data:www-data', self.web_path], check=True)
                logger.debug(f"Set ownership to www-data for {self.web_path}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to set ownership: {e}")
            
            # Set initial permissions
            try:
                subprocess.run(['/usr/bin/sudo', '/bin/chmod', '-R', '755', self.web_path], check=True)
                logger.debug(f"Set permissions 755 for {self.web_path}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to set permissions: {e}")
            
            # Create .htaccess file for proper web server configuration
            self._create_htaccess_file()
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing web server directory: {e}")
            return False
    
    def _create_htaccess_file(self) -> None:
        """Create .htaccess file for proper web server configuration"""
        try:
            htaccess_content = """# AI Crypto Bot Dashboard Configuration
DirectoryIndex index.html

# Enable CORS for API calls
<IfModule mod_headers.c>
    Header always set Access-Control-Allow-Origin "*"
    Header always set Access-Control-Allow-Methods "GET, POST, OPTIONS"
    Header always set Access-Control-Allow-Headers "Content-Type, Authorization"
</IfModule>

# Cache control for data files (short cache)
<FilesMatch "\\.(json|txt)$">
    Header set Cache-Control "max-age=60, must-revalidate"
</FilesMatch>

# Cache control for static files (longer cache)
<FilesMatch "\\.(html|css|js|png|jpg|jpeg|gif|svg)$">
    Header set Cache-Control "max-age=3600, must-revalidate"
</FilesMatch>

# Security headers
<IfModule mod_headers.c>
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
</IfModule>

# Prevent access to sensitive files
<Files "*.log">
    Order allow,deny
    Deny from all
</Files>

<Files ".env">
    Order allow,deny
    Deny from all
</Files>
"""
            
            htaccess_path = os.path.join(self.web_path, '.htaccess')
            
            # Write .htaccess file with sudo
            import subprocess
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write(htaccess_content)
                temp_file_path = temp_file.name
            
            try:
                subprocess.run(['/usr/bin/sudo', '/bin/cp', temp_file_path, htaccess_path], check=True)
                subprocess.run(['/usr/bin/sudo', '/bin/chown', 'www-data:www-data', htaccess_path], check=True)
                subprocess.run(['/usr/bin/sudo', '/bin/chmod', '644', htaccess_path], check=True)
                logger.debug("Created .htaccess file")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to create .htaccess file: {e}")
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.warning(f"Error creating .htaccess file: {e}")
    
    def sync_to_webserver_no_sudo(self) -> None:
        """Alternative sync method that doesn't require sudo"""
        if not self.enabled:
            logger.debug("Web server sync disabled, skipping")
            return
        
        try:
            logger.info("Starting web server sync (no sudo)")
            
            if not os.path.exists(self.web_path):
                logger.warning(f"Web server directory {self.web_path} not found")
                return
            
            # Sync data files without sudo
            self._sync_data_files_no_sudo()
            
            # Sync market data without sudo
            self._sync_market_data_no_sudo()
            
            # Copy static files without sudo
            self._sync_static_files_no_sudo()
            
            # Copy images without sudo
            self._sync_images_no_sudo()
            
            logger.info("Web server sync completed successfully (no sudo)")
            
        except Exception as e:
            logger.error(f"Error syncing to web server (no sudo): {e}")
    
    def _sync_data_files_no_sudo(self) -> None:
        """Sync data files using group permissions"""
        try:
            data_files = {
                "data/portfolio/portfolio_data.json": "data/portfolio/portfolio_data.json",
                "data/config/config.json": "data/config/config.json", 
                "data/cache/latest_decisions.json": "data/cache/latest_decisions.json",
                "data/cache/trading_data.json": "data/cache/trading_data.json",
                "data/cache/last_updated.txt": "data/cache/last_updated.txt",
                "data/cache/bot_startup.json": "data/cache/bot_startup.json",
                "data/trades/trade_history.json": "data/trades/trade_history.json"
            }
            
            for source_rel_path, dest_rel_path in data_files.items():
                source_abs_path = os.path.abspath(source_rel_path)
                dest_abs_path = os.path.join(self.web_path, dest_rel_path)
                
                if os.path.exists(source_abs_path):
                    try:
                        # Ensure destination directory exists
                        dest_dir = os.path.dirname(dest_abs_path)
                        os.makedirs(dest_dir, exist_ok=True)
                        
                        # Copy file using group permissions
                        shutil.copy2(source_abs_path, dest_abs_path)
                        os.chmod(dest_abs_path, 0o664)  # rw-rw-r--
                        logger.debug(f"Copied data file: {source_rel_path}")
                    except Exception as e:
                        logger.error(f"Failed to copy {source_rel_path}: {e}")
                else:
                    logger.debug(f"Source file does not exist: {source_abs_path}")
            
            logger.debug("Data files synced (no sudo)")
            
        except Exception as e:
            logger.error(f"Error syncing data files (no sudo): {e}")
    
    def _sync_market_data_no_sudo(self) -> None:
        """Sync market data files without sudo"""
        try:
            data_dir = os.path.abspath("data")
            web_market_dir = f"{self.web_path}/data/market_data"
            
            # Ensure market data directory exists
            os.makedirs(web_market_dir, exist_ok=True)
            
            # Update files for each trading pair
            assets = ['BTC', 'ETH', 'SOL']
            
            for asset in assets:
                # Find the latest market data file for this asset
                pattern = f"{data_dir}/{asset}_USD_*.json"
                files = glob.glob(pattern)
                
                if files:
                    # Sort by filename (which includes timestamp) and get the latest
                    latest_file = sorted(files)[-1]
                    dest_file = f"{web_market_dir}/{asset}_USD_latest.json"
                    
                    try:
                        shutil.copy2(latest_file, dest_file)
                        os.chmod(dest_file, 0o664)  # rw-rw-r--
                        logger.debug(f"Copied {asset} market data: {os.path.basename(latest_file)}")
                    except Exception as e:
                        logger.error(f"Failed to copy {asset} market data: {e}")
                else:
                    logger.warning(f"No market data files found for {asset}")
            
            logger.debug("Market data synced (no sudo)")
            
        except Exception as e:
            logger.error(f"Error syncing market data (no sudo): {e}")
    
    def _sync_static_files_no_sudo(self) -> None:
        """Sync static HTML, CSS, JS files without sudo"""
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
                        self._copy_and_modify_html_no_sudo(source_path, dest_path)
                    else:
                        try:
                            shutil.copy2(source_path, dest_path)
                            os.chmod(dest_path, 0o664)  # rw-rw-r--
                        except Exception as e:
                            logger.error(f"Failed to copy {file}: {e}")
            
            logger.debug("Static files synced (no sudo)")
            
        except Exception as e:
            logger.error(f"Error syncing static files (no sudo): {e}")
    
    def _copy_and_modify_html_no_sudo(self, source_path: str, dest_path: str) -> None:
        """Copy HTML file and modify paths for web server without sudo"""
        try:
            with open(source_path, "r") as f:
                content = f.read()
            
            # Replace relative paths for web server
            content = content.replace("../data/market_data/BTC_USD_latest.json", "data/market_data/BTC_USD_latest.json")
            content = content.replace("../data/market_data/ETH_USD_latest.json", "data/market_data/ETH_USD_latest.json")
            content = content.replace("../data/market_data/SOL_USD_latest.json", "data/market_data/SOL_USD_latest.json")
            content = content.replace("../data/portfolio/portfolio_data.json", "data/portfolio/portfolio_data.json")
            content = content.replace("../data/trades/trade_history.json", "data/trades/trade_history.json")
            content = content.replace("../data/cache/", "data/cache/")
            content = content.replace("../images/", "images/")
            
            # Write the modified content
            with open(dest_path, "w") as f:
                f.write(content)
            
            # Set proper permissions
            os.chmod(dest_path, 0o664)  # rw-rw-r--
            logger.debug(f"Modified and copied HTML file: {source_path}")
            
        except Exception as e:
            logger.error(f"Error copying and modifying HTML file {source_path}: {e}")
            # Fallback to regular copy
            try:
                shutil.copy2(source_path, dest_path)
                os.chmod(dest_path, 0o664)
            except Exception as fallback_error:
                logger.error(f"Fallback copy also failed: {fallback_error}")
    
    def _sync_images_no_sudo(self) -> None:
        """Sync image files without sudo"""
        try:
            if not os.path.exists("dashboard/images"):
                logger.debug("Dashboard images directory not found")
                return
            
            images_dir = f"{self.web_path}/images"
            os.makedirs(images_dir, exist_ok=True)
            
            for file in os.listdir("dashboard/images"):
                if file.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
                    source_path = os.path.abspath(f"dashboard/images/{file}")
                    dest_path = f"{images_dir}/{file}"
                    
                    try:
                        shutil.copy2(source_path, dest_path)
                        os.chmod(dest_path, 0o664)  # rw-rw-r--
                    except Exception as e:
                        logger.error(f"Failed to copy image {file}: {e}")
            
            logger.debug("Images synced (no sudo)")
            
        except Exception as e:
            logger.error(f"Error syncing images (no sudo): {e}")
    
    def _sync_data_files(self) -> None:
        """Sync data files by copying them directly with sudo"""
        try:
            import subprocess
            
            data_files = {
                "data/portfolio/portfolio_data.json": "data/portfolio/portfolio_data.json",
                "data/config/config.json": "data/config/config.json", 
                "data/cache/latest_decisions.json": "data/cache/latest_decisions.json",
                "data/cache/trading_data.json": "data/cache/trading_data.json",
                "data/cache/last_updated.txt": "data/cache/last_updated.txt",
                "data/cache/bot_startup.json": "data/cache/bot_startup.json",
                "data/trades/trade_history.json": "data/trades/trade_history.json"
            }
            
            for source_rel_path, dest_rel_path in data_files.items():
                source_abs_path = os.path.abspath(source_rel_path)
                dest_abs_path = os.path.join(self.web_path, dest_rel_path)
                
                if os.path.exists(source_abs_path):
                    try:
                        # Ensure destination directory exists
                        dest_dir = os.path.dirname(dest_abs_path)
                        os.makedirs(dest_dir, exist_ok=True)
                        
                        # Copy file with sudo
                        subprocess.run(['/usr/bin/sudo', '/bin/cp', source_abs_path, dest_abs_path], check=True)
                        subprocess.run(['/usr/bin/sudo', '/bin/chown', 'www-data:www-data', dest_abs_path], check=True)
                        subprocess.run(['/usr/bin/sudo', '/bin/chmod', '644', dest_abs_path], check=True)
                        logger.debug(f"Copied data file: {source_rel_path}")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to copy {source_rel_path}: {e}")
                else:
                    logger.debug(f"Source file does not exist: {source_abs_path}")
            
            logger.debug("Data files synced")
            
        except Exception as e:
            logger.error(f"Error syncing data files: {e}")
    
    def _sync_market_data(self) -> None:
        """Sync market data files by copying latest files directly with sudo"""
        try:
            import subprocess
            data_dir = os.path.abspath("data")
            web_market_dir = f"{self.web_path}/data/market_data"
            
            # Ensure market data directory exists
            os.makedirs(web_market_dir, exist_ok=True)
            
            # Update files for each trading pair
            assets = ['BTC', 'ETH', 'SOL']
            
            for asset in assets:
                # Find the latest market data file for this asset
                pattern = f"{data_dir}/{asset}_USD_*.json"
                files = glob.glob(pattern)
                
                if files:
                    # Sort by filename (which includes timestamp) and get the latest
                    latest_file = sorted(files)[-1]
                    dest_file = f"{web_market_dir}/{asset}_USD_latest.json"
                    
                    try:
                        # Copy file with sudo
                        subprocess.run(['/usr/bin/sudo', '/bin/cp', latest_file, dest_file], check=True)
                        subprocess.run(['/usr/bin/sudo', '/bin/chown', 'www-data:www-data', dest_file], check=True)
                        subprocess.run(['/usr/bin/sudo', '/bin/chmod', '644', dest_file], check=True)
                        logger.debug(f"Copied {asset} market data: {os.path.basename(latest_file)}")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to copy {asset} market data: {e}")
                else:
                    logger.warning(f"No market data files found for {asset}")
            
            logger.debug("Market data synced")
            
        except Exception as e:
            logger.error(f"Error syncing market data: {e}")
    
    def _sync_static_files(self) -> None:
        """Sync static HTML, CSS, JS files with sudo"""
        try:
            import subprocess
            
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
                        try:
                            subprocess.run(['/usr/bin/sudo', '/bin/cp', source_path, dest_path], check=True)
                            subprocess.run(['/usr/bin/sudo', '/bin/chown', 'www-data:www-data', dest_path], check=True)
                            subprocess.run(['/usr/bin/sudo', '/bin/chmod', '644', dest_path], check=True)
                        except subprocess.CalledProcessError as e:
                            logger.error(f"Failed to copy {file}: {e}")
            
            logger.debug("Static files synced")
            
        except Exception as e:
            logger.error(f"Error syncing static files: {e}")
    
    def _sync_images(self) -> None:
        """Sync image files with sudo"""
        try:
            import subprocess
            
            if not os.path.exists("dashboard/images"):
                logger.debug("Dashboard images directory not found")
                return
            
            images_dir = f"{self.web_path}/images"
            os.makedirs(images_dir, exist_ok=True)
            
            for file in os.listdir("dashboard/images"):
                if file.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
                    source_path = os.path.abspath(f"dashboard/images/{file}")
                    dest_path = f"{images_dir}/{file}"
                    
                    try:
                        subprocess.run(['/usr/bin/sudo', '/bin/cp', source_path, dest_path], check=True)
                        subprocess.run(['/usr/bin/sudo', '/bin/chown', 'www-data:www-data', dest_path], check=True)
                        subprocess.run(['/usr/bin/sudo', '/bin/chmod', '644', dest_path], check=True)
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to copy image {file}: {e}")
            
            logger.debug("Images synced")
            
        except Exception as e:
            logger.error(f"Error syncing images: {e}")
    
    def _set_webserver_permissions(self) -> None:
        """Set final permissions on all web server files"""
        try:
            import subprocess
            
            # Set ownership to www-data
            subprocess.run(['/usr/bin/sudo', '/bin/chown', '-R', 'www-data:www-data', self.web_path], 
                          check=False)  # Don't fail if this doesn't work
            
            # Set directory permissions
            subprocess.run(['/usr/bin/sudo', '/usr/bin/find', self.web_path, '-type', 'd', '-exec', '/bin/chmod', '755', '{}', '+'], 
                          check=False)
            
            # Set file permissions
            subprocess.run(['/usr/bin/sudo', '/usr/bin/find', self.web_path, '-type', 'f', '-exec', '/bin/chmod', '644', '{}', '+'], 
                          check=False)
            
            logger.debug("Set final web server permissions")
            
        except Exception as e:
            logger.warning(f"Error setting web server permissions: {e}")
    
    def force_sync(self) -> None:
        """Force sync regardless of enabled status (for manual sync)"""
        original_enabled = self.enabled
        self.enabled = True
        try:
            self.sync_to_webserver()
        finally:
            self.enabled = original_enabled
