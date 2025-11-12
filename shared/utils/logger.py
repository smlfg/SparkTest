"""
Shared Logging Utility
Provides consistent logging across all agents
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['agent'] = getattr(record, 'agent', 'unknown')
        log_record['playbook'] = getattr(record, 'playbook', 'unknown')


def setup_logger(
    name: str,
    level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    agent: Optional[str] = None,
    playbook: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with consistent formatting

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("json" or "text")
        log_file: Optional file path for logging
        agent: Agent identifier
        playbook: Playbook identifier

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create formatter
    if log_format == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Add agent/playbook info to all log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.agent = agent or "unknown"
        record.playbook = playbook or "unknown"
        return record

    logging.setLogRecordFactory(record_factory)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
