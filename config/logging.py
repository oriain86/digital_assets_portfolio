# src/config/logging.py

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys


def setup_logging(
        log_level: str = "INFO",
        log_dir: str = "logs",
        log_to_console: bool = True,
        log_to_file: bool = True
):
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
    """

    # Create log directory if needed
    global log_path
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

    # File handlers
    if log_to_file:
        # Main log file (rotating)
        main_log_file = log_path / f"portfolio_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        # Error log file
        error_log_file = log_path / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)

    # Configure specific loggers
    loggers_config = {
        'src.core': logging.DEBUG,
        'src.application': logging.DEBUG,
        'src.infrastructure': logging.INFO,
        'src.presentation': logging.INFO,
        'werkzeug': logging.WARNING,  # Reduce Flask/Dash noise
        'urllib3': logging.WARNING,  # Reduce requests noise
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    # Log startup
    root_logger.info("=" * 60)
    root_logger.info("Crypto Portfolio Tracker - Logging Initialized")
    root_logger.info(f"Log Level: {log_level}")
    root_logger.info(f"Log Directory: {log_dir if log_to_file else 'N/A'}")
    root_logger.info("=" * 60)


# Convenience functions
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def log_function_call(logger: logging.Logger):
    """Decorator to log function calls."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed with error: {str(e)}", exc_info=True)
                raise

        return wrapper

    return decorator


def log_performance(logger: logging.Logger):
    """Decorator to log function performance."""
    import time

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                logger.info(f"{func.__name__} executed in {elapsed_time:.3f} seconds")
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed_time:.3f} seconds")
                raise

        return wrapper

    return decorator
