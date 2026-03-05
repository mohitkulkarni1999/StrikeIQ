"""
Production-grade logging configuration for StrikeIQ
Prevents terminal spam while maintaining full observability
"""

import logging
import os
from typing import Optional

# Global debug flags - set to True only when debugging needed
AI_DEBUG = os.getenv("AI_DEBUG", "False").lower() == "true"
TICK_DEBUG = os.getenv("TICK_DEBUG", "False").lower() == "true"
FORMULA_DEBUG = os.getenv("FORMULA_DEBUG", "False").lower() == "true"

# Log level configuration
LOG_LEVEL = logging.INFO

def configure_logging():
    """Configure structured logging for the entire application"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return logging.getLogger(name)

# Export debug flags for use in other modules
__all__ = [
    'AI_DEBUG',
    'TICK_DEBUG', 
    'FORMULA_DEBUG',
    'LOG_LEVEL',
    'configure_logging',
    'get_logger'
]
