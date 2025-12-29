"""
Centralized logging configuration for the AI crypto trading bot.
Provides structured, filtered, and rotated logging.
"""

import logging
import logging.handlers
import os
from datetime import datetime

class TradingBotFormatter(logging.Formatter):
    """Custom formatter for trading bot logs with color coding and filtering."""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    # Keywords that indicate important trading events
    IMPORTANT_KEYWORDS = [
        'Trading decision', 'BUY', 'SELL', 'HOLD', 'Order', 'Trade',
        'Portfolio', 'Balance', 'ERROR', 'CRITICAL', 'Failed', 'Exception',
        'Daily report', 'Alert', 'Monitoring', 'Health check'
    ]
    
    def __init__(self, use_colors=False, filter_noise=True):
        super().__init__()
        self.use_colors = use_colors
        self.filter_noise = filter_noise
        
    def format(self, record):
        # Filter out noisy logs if enabled
        if self.filter_noise and self._is_noise(record):
            return None
            
        # Create timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Determine if this is an important message
        is_important = any(keyword in record.getMessage() for keyword in self.IMPORTANT_KEYWORDS)
        
        # Format level name
        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, '')
            level = f"{color}{level:<8}{self.COLORS['RESET']}"
        else:
            level = f"{level:<8}"
            
        # Format module name (shortened)
        module = record.name.split('.')[-1] if '.' in record.name else record.name
        module = f"{module:<15}"
        
        # Create the log message
        message = record.getMessage()
        
        # Add emphasis for important messages
        if is_important and self.use_colors:
            message = f"\033[1m{message}\033[0m"  # Bold
            
        return f"{timestamp} {level} {module} {message}"
    
    def _is_noise(self, record):
        """Determine if a log record is noise that should be filtered."""
        message = record.getMessage().lower()
        
        # Filter out common noisy patterns
        noise_patterns = [
            'hard link already exists',
            'http request:',
            'afc is enabled',
            'synced.*files for trade history',
            'modified and copied html file',
            'static files synced',
            'web server sync completed',
            'loading.*data',
            'data validation complete',
            'fetched.*candles',
        ]
        
        return any(pattern in message for pattern in noise_patterns)

def setup_logging(log_level=logging.INFO, console_output=True, filter_noise=True):
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Minimum log level to capture
        console_output: Whether to output to console
        filter_noise: Whether to filter out noisy log messages
    """
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set root logger level
    root_logger.setLevel(log_level)
    
    # Create formatters
    console_formatter = TradingBotFormatter(use_colors=True, filter_noise=filter_noise)
    file_formatter = TradingBotFormatter(use_colors=False, filter_noise=False)  # Keep all in files
    
    # Console handler (filtered and colored)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        
        # Add filter to console handler
        if filter_noise:
            console_handler.addFilter(lambda record: console_formatter.format(record) is not None)
            
        root_logger.addHandler(console_handler)
    
    # Main application log (rotating)
    main_handler = logging.handlers.RotatingFileHandler(
        'logs/trading_bot.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    main_handler.setLevel(log_level)
    main_handler.setFormatter(file_formatter)
    root_logger.addHandler(main_handler)
    
    # Trading decisions log (separate, important events only)
    trading_handler = logging.handlers.RotatingFileHandler(
        'logs/trading_decisions.log',
        maxBytes=2*1024*1024,  # 2MB
        backupCount=5,
        encoding='utf-8'
    )
    trading_handler.setLevel(logging.INFO)
    trading_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    # Add filter for trading-related messages only
    def trading_filter(record):
        message = record.getMessage()
        trading_keywords = ['Trading decision', 'BUY', 'SELL', 'HOLD', 'Order', 'Trade', 'Portfolio']
        return any(keyword in message for keyword in trading_keywords)
    
    trading_handler.addFilter(trading_filter)
    root_logger.addHandler(trading_handler)
    
    # Error log (errors and warnings only)
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/errors.log',
        maxBytes=2*1024*1024,  # 2MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d'
    ))
    root_logger.addHandler(error_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('google_genai').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name)

# Trading-specific logging functions
def log_trading_decision(asset, action, confidence, reasoning):
    """Log a trading decision with structured format."""
    logger = get_logger('trading')
    logger.info(f"🎯 TRADING DECISION: {asset} -> {action} ({confidence:.1f}%) | {reasoning}")

def log_portfolio_update(portfolio_value, change_pct=None):
    """Log portfolio value updates."""
    logger = get_logger('portfolio')
    change_str = f" ({change_pct:+.2f}%)" if change_pct else ""
    logger.info(f"💰 Portfolio Value: €{portfolio_value:.2f}{change_str}")

def log_system_health(component, status, details=None):
    """Log system health checks."""
    logger = get_logger('health')
    status_emoji = "✅" if status == "healthy" else "❌"
    details_str = f" | {details}" if details else ""
    logger.info(f"{status_emoji} {component}: {status}{details_str}")

def log_performance_metric(metric_name, value, unit=""):
    """Log performance metrics."""
    logger = get_logger('performance')
    logger.info(f"📊 {metric_name}: {value}{unit}")
