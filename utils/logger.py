import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

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
    logger.setLevel(level)
    
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
