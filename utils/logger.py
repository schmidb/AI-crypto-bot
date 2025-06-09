import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(level)
        
        # Prevent propagation to root logger to avoid duplicates
        logger.propagate = False
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create file handler if log_file is provided
        if log_file:
            # Create logs directory if it doesn't exist
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Create rotating file handler (10 MB max size, keep 5 backup files)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def get_trade_logger():
    """
    Get a logger specifically for trading activities
    
    Returns:
        Configured logger for trading
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = f"logs/trading_{timestamp}.log"
    return setup_logger("trading", log_file)

def get_api_logger():
    """
    Get a logger specifically for API calls
    
    Returns:
        Configured logger for API calls
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = f"logs/api_{timestamp}.log"
    return setup_logger("api", log_file)

def get_llm_logger():
    """
    Get a logger specifically for LLM interactions
    
    Returns:
        Configured logger for LLM interactions
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = f"logs/llm_{timestamp}.log"
    return setup_logger("llm", log_file)

def get_daily_rotating_logger(name, log_file_prefix, level=logging.INFO):
    """
    Get a logger with daily rotation
    
    Args:
        name: Logger name
        log_file_prefix: Prefix for log file (e.g., 'supervisor', 'main')
        level: Logging level
        
    Returns:
        Configured logger with daily rotation
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(level)
        
        # Prevent propagation to root logger to avoid duplicates
        logger.propagate = False
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Create daily rotating file handler
        log_file = f"logs/{log_file_prefix}.log"
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        file_handler.suffix = "%Y%m%d"
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_supervisor_logger():
    """
    Get a logger specifically for supervisor/main application logs with daily rotation
    
    Returns:
        Configured logger with daily rotation
    """
    import os
    
    # Check if running under supervisor by looking for supervisor-specific environment
    # or by checking if stdout is being redirected
    running_under_supervisor = (
        os.environ.get('SUPERVISOR_ENABLED') == '1' or
        not os.isatty(1)  # stdout is not a terminal (likely redirected by supervisor)
    )
    
    if running_under_supervisor:
        # When running under supervisor, only log to console
        # Supervisor will capture and redirect to its log file
        logger = logging.getLogger("supervisor")
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            logger.propagate = False
            
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # Log a clear separation line for bot startup
            logger.info("="*80)
            logger.info("BOT STARTUP - NEW SESSION STARTING")
            logger.info("="*80)
        
        return logger
    else:
        # When running standalone, use file logging
        logger = get_daily_rotating_logger("supervisor", "supervisor")
        
        # Log a clear separation line for bot startup
        logger.info("="*80)
        logger.info("BOT STARTUP - NEW SESSION STARTING")
        logger.info("="*80)
        
        return logger

def log_bot_shutdown(logger):
    """
    Log a clear separation line for bot shutdown
    
    Args:
        logger: The logger instance to use
    """
    logger.info("="*80)
    logger.info("BOT SHUTDOWN - SESSION ENDING")
    logger.info("="*80)

def log_bot_restart(logger):
    """
    Log a clear separation line for bot restart
    
    Args:
        logger: The logger instance to use
    """
    logger.info("="*80)
    logger.info("BOT RESTART - RESTARTING SESSION")
    logger.info("="*80)
