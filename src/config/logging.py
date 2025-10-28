"""Configuration module for setting up logging in the application."""

import functools
import logging
import logging.config
import os
import time
from typing import Callable, Optional

# Verbosity level constants
QUIET = "quiet"
NORMAL = "normal"
VERBOSE = "verbose"
DEBUG = "debug"


def setup_logging(verbosity: Optional[str] = None):
    """
    Configure and set up logging for the application.

    Args:
        verbosity: Verbosity level (quiet, normal, verbose, debug).
                   If None, uses DEBUG_MODE environment variable.

    Verbosity levels:
        - quiet: Only ERROR and CRITICAL to stderr
        - normal: INFO and above to stdout (user-friendly format)
        - verbose: INFO and above to stdout (detailed format with timestamps)
        - debug: DEBUG and above to stdout (full technical format)
    """
    # Determine verbosity level
    if verbosity is None:
        # Fallback to environment variable (backward compatibility)
        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        verbosity = DEBUG if debug_mode else NORMAL

    # Map verbosity to log levels and formatters
    if verbosity == QUIET:
        console_level = logging.ERROR
        console_formatter = "minimal"
        console_stream = "ext://sys.stderr"
    elif verbosity == NORMAL:
        console_level = logging.INFO
        console_formatter = "user_friendly"
        console_stream = "ext://sys.stdout"
    elif verbosity == VERBOSE:
        console_level = logging.INFO
        console_formatter = "detailed"
        console_stream = "ext://sys.stdout"
    elif verbosity == DEBUG:
        console_level = logging.DEBUG
        console_formatter = "technical"
        console_stream = "ext://sys.stdout"
    else:
        # Default to NORMAL for unknown values
        console_level = logging.INFO
        console_formatter = "user_friendly"
        console_stream = "ext://sys.stdout"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # Minimal format for QUIET mode (errors only)
            "minimal": {
                "format": "ERROR: %(message)s",
            },
            # User-friendly format for NORMAL mode (no module paths, no timestamps)
            "user_friendly": {
                "format": "%(message)s",
            },
            # Detailed format for VERBOSE mode (timestamps, no module paths)
            "detailed": {
                "format": "[%(levelname)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            # Technical format for DEBUG mode (full details)
            "technical": {
                "format": ("%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            # File format (always full details for forensics)
            "file_format": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(funcName)s:%(lineno)d - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "level": console_level,
                "formatter": console_formatter,
                "class": "logging.StreamHandler",
                "stream": console_stream,
            },
            "file": {
                "level": logging.DEBUG,
                "formatter": "file_format",
                "class": "logging.FileHandler",
                "filename": "app.log",
                "mode": "a",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file"],
                "level": logging.DEBUG,  # Capture all, handlers filter
                "propagate": True,
            },
            # Suppress noisy third-party libraries (unless DEBUG mode)
            "httpx": {
                "level": logging.WARNING if verbosity != DEBUG else logging.DEBUG,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "httpcore": {
                "level": logging.WARNING if verbosity != DEBUG else logging.DEBUG,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "urllib3": {
                "level": logging.WARNING if verbosity != DEBUG else logging.DEBUG,
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def log_performance(func: Callable) -> Callable:
    """
    Decorator to log function execution time.

    Usage:
        @log_performance
        def my_function():
            pass

    Logs at DEBUG level: "my_function completed in 1.23s"
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.perf_counter()

        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.debug("%s completed in %.2fs", func.__name__, elapsed)
            return result
        except Exception:
            elapsed = time.perf_counter() - start_time
            logger.debug("%s failed after %.2fs", func.__name__, elapsed)
            raise

    return wrapper


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
