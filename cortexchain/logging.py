"""Logging integration for cortexchain — proper Python logging, not print()."""
import logging
import sys
from typing import Optional

_LOGGER_NAME = "cortexchain"
_logger: Optional[logging.Logger] = None


def get_logger(name: str = None) -> logging.Logger:
    """Get a cortexchain logger. Sub-modules use: get_logger(__name__)"""
    if name:
        return logging.getLogger(f"{_LOGGER_NAME}.{name}")
    return logging.getLogger(_LOGGER_NAME)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Configure cortexchain logging. Call once at app startup.

    Usage:
        from cortexchain.logging import setup_logging
        setup_logging(level="DEBUG", log_file="cortexchain.log")
    """
    global _logger
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    fmt = format_string or "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def set_level(level: str) -> None:
    """Change log level at runtime."""
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))


def quiet() -> None:
    """Suppress all cortexchain logs (set to WARNING only)."""
    set_level("WARNING")


def verbose() -> None:
    """Enable debug-level cortexchain logs."""
    set_level("DEBUG")
