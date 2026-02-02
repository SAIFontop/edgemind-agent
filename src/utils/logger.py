"""
EdgeMind Agent - Logger
=========================
Advanced logging system
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path
from datetime import datetime

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


class EdgeMindLogger:
    """
    Custom logging system for EdgeMind Agent
    
    - Color support
    - File rotation
    - Multiple levels
    """
    
    def __init__(
        self,
        name: str = "EdgeMind",
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        console_output: bool = True
    ):
        """
        Initialize logging system
        
        Args:
            name: Logger name
            level: Log level
            log_file: Log file path
            max_size: Maximum file size
            backup_count: Number of backups
            console_output: Console output
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers = []  # Clear previous handlers
        
        # Log format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # Console handler
        if console_output:
            if HAS_COLORLOG:
                # With colors
                color_format = (
                    "%(log_color)s%(asctime)s - %(name)s - "
                    "%(levelname)s - %(message)s%(reset)s"
                )
                color_formatter = colorlog.ColoredFormatter(
                    color_format,
                    datefmt=date_format,
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(color_formatter)
            else:
                # Without colors
                formatter = logging.Formatter(log_format, date_format)
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            # Create directory if doesn't exist
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(log_format, date_format)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)


# Global logger
_default_logger: Optional[EdgeMindLogger] = None


def get_logger(
    name: str = "EdgeMind",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> EdgeMindLogger:
    """
    Get logger
    
    Args:
        name: Logger name
        level: Level
        log_file: Log file
    
    Returns:
        EdgeMindLogger
    """
    global _default_logger
    
    if _default_logger is None:
        # Set default log path
        if log_file is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_file = str(log_dir / "edgemind.log")
        
        _default_logger = EdgeMindLogger(
            name=name,
            level=level,
            log_file=log_file
        )
    
    return _default_logger


# For testing
if __name__ == "__main__":
    logger = get_logger(level="DEBUG")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    try:
        raise ValueError("Test exception")
    except:
        logger.exception("An exception occurred")
