"""
shared/utils/logger.py
Standardized logging setup for all DGX Spark agents
"""

import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger
from datetime import datetime


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()

        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Add agent name if available
        if hasattr(record, 'agent_name'):
            log_record['agent_name'] = record.agent_name


def setup_logger(
    name: str = __name__,
    level: str = "INFO",
    json_format: bool = True,
    agent_name: Optional[str] = None
) -> logging.Logger:
    """
    Set up a standardized logger for agents.

    Args:
        name: Logger name (typically __name__ of the module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting (default: True)
        agent_name: Optional agent name to include in logs

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger(__name__, level="INFO", agent_name="agent1_infra")
        >>> logger.info("Service started")
    """
    logger = logging.getLogger(name)

    # Clear existing handlers
    logger.handlers = []

    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter based on json_format
    if json_format:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add agent name as filter if provided
    if agent_name:
        class AgentNameFilter(logging.Filter):
            def filter(self, record):
                record.agent_name = agent_name
                return True

        logger.addFilter(AgentNameFilter())

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str, agent_name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with standard configuration.

    Args:
        name: Logger name
        agent_name: Optional agent name to include in logs

    Returns:
        Logger instance
    """
    import os

    log_level = os.getenv("LOG_LEVEL", "INFO")
    json_format = os.getenv("LOG_FORMAT", "json").lower() == "json"

    return setup_logger(name, level=log_level, json_format=json_format, agent_name=agent_name)


class LoggerMixin:
    """
    Mixin class to add logger property to any class.

    Example:
        >>> class MyAgent(LoggerMixin):
        ...     agent_name = "agent1_infra"
        ...
        ...     def run(self):
        ...         self.logger.info("Agent is running")
    """

    @property
    def logger(self) -> logging.Logger:
        agent_name = getattr(self, 'agent_name', None)
        return get_logger(self.__class__.__name__, agent_name=agent_name)


if __name__ == "__main__":
    # Example usage
    logger = setup_logger(__name__, level="DEBUG", agent_name="test_agent")

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Example with LoggerMixin
    class TestAgent(LoggerMixin):
        agent_name = "test_agent"

        def run(self):
            self.logger.info("Agent is running")
            self.logger.warning("This is a warning from the agent")

    agent = TestAgent()
    agent.run()
