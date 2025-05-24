"""Logging configuration for Invasive Species Tracker."""

import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Remove default logger
logger.remove()

# Console logging
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
    colorize=True
)

# File logging
log_file = os.getenv("LOG_FILE", "logs/invasive_tracker.log")
log_dir = Path(log_file).parent
log_dir.mkdir(parents=True, exist_ok=True)

logger.add(
    log_file,
    rotation="10 MB",
    retention="7 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)