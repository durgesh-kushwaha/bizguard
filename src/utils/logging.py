"""
Logging configuration for BizGuard.

Sets up structured logging for debugging without exposing
technical tracebacks to the user interface.
"""

import logging
from pathlib import Path


def setup_logging(level: int = logging.INFO):
    """
    Configure application logging.
    
    Logs go to console (for development) and can be extended
    to file logging if needed.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("pyspark").setLevel(logging.WARNING)
    logging.getLogger("py4j").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)
