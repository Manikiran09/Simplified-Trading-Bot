"""
Logging configuration for the trading bot application.
Sets up structured logging with both file and console handlers.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> logging.Logger:
    """
    Configure logging with both file and console handlers.
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler (detailed logs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, f"trading_bot_{timestamp}.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (simple logs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "trading_bot") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
