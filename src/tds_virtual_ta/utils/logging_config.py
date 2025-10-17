"""
=== COMPLETE: src/tds_virtual_ta/utils/logging_config.py ===
Structured logging configuration with all required functions
"""

import logging
import sys
from typing import Any, Dict, List

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    # Fallback if python-json-logger not installed
    jsonlogger = None

from ..config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter if jsonlogger else logging.Formatter):
    """Custom JSON formatter with standard fields."""
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to log record."""
        if jsonlogger:
            super().add_fields(log_record, record, message_dict)
            
            log_record['timestamp'] = self.formatTime(record, self.datefmt)
            log_record['level'] = record.levelname
            log_record['logger'] = record.name
            log_record['module'] = record.module
            log_record['function'] = record.funcName
            log_record['line'] = record.lineno


def setup_logging() -> logging.Logger:
    """
    Configure application logging.
    
    Returns:
        Configured root logger
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))
    
    # Set formatter
    if settings.log_format == "json" and jsonlogger:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("github").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class TaskLogger:
    """Logger with task context for tracing."""
    
    def __init__(self, task_id: str, logger: logging.Logger):
        """
        Initialize task logger.
        
        Args:
            task_id: Unique task identifier
            logger: Base logger instance
        """
        self.task_id = task_id
        self.logger = logger
        self.logs: List[str] = []
    
    def _add_context(self, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add task_id to log context."""
        if extra is None:
            extra = {}
        extra['task_id'] = self.task_id
        return extra
    
    def debug(self, msg: str, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, extra=self._add_context(kwargs.get('extra')))
        self.logs.append(f"DEBUG: {msg}")
    
    def info(self, msg: str, **kwargs):
        """Log info message."""
        self.logger.info(msg, extra=self._add_context(kwargs.get('extra')))
        self.logs.append(f"INFO: {msg}")
    
    def warning(self, msg: str, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, extra=self._add_context(kwargs.get('extra')))
        self.logs.append(f"WARNING: {msg}")
    
    def error(self, msg: str, **kwargs):
        """Log error message."""
        exc_info = kwargs.get('exc_info', False)
        self.logger.error(msg, extra=self._add_context(kwargs.get('extra')), exc_info=exc_info)
        self.logs.append(f"ERROR: {msg}")
    
    def critical(self, msg: str, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, extra=self._add_context(kwargs.get('extra')))
        self.logs.append(f"CRITICAL: {msg}")
    
    def get_logs(self) -> List[str]:
        """Get all accumulated logs for this task."""
        return self.logs.copy()


# Initialize logging on module import
setup_logging()