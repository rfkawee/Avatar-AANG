"""
Logging Utility Module
Provides a centralized logging configuration for the application.
"""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger instance.

    Args:
        name: The name for the logger (typically __name__).

    Returns:
        A logging.Logger instance with stream handler attached.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
