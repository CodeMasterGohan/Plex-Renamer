"""
Logging utilities for the Plex Media Renamer application.
"""

import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: The logging level to use (default: INFO)
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"plex_renamer_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Log the start of the session
    logger = logging.getLogger(__name__)
    logger.info(f"Logging session started - Log file: {log_file}")
    
    return log_file

def get_logger(name):
    """
    Get a logger instance for the given name.
    
    Args:
        name: The name for the logger (usually __name__)
    
    Returns:
        logging.Logger: The logger instance
    """
    return logging.getLogger(name) 