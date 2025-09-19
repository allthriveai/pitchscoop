import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
import traceback


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra context if present
        if hasattr(record, 'event_id'):
            log_data["event_id"] = record.event_id
        if hasattr(record, 'session_id'):
            log_data["session_id"] = record.session_id
        if hasattr(record, 'judge_id'):
            log_data["judge_id"] = record.judge_id
        if hasattr(record, 'tool_name'):
            log_data["tool_name"] = record.tool_name
        if hasattr(record, 'operation'):
            log_data["operation"] = record.operation
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        
        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """Setup application logging configuration with structured format."""
    
    # Create structured formatter
    structured_formatter = StructuredFormatter()
    
    # Create file handler with structured format
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(structured_formatter)
    
    # Create console handler with readable format for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.handlers.clear()  # Remove default handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    loggers_config = {
        "uvicorn": "INFO",
        "uvicorn.access": "INFO", 
        "fastapi": "INFO",
        "websockets": "INFO",
        "aiohttp": "WARNING",
        "gladia": "DEBUG",
        "pitchscoop.scoring": "DEBUG",
        "pitchscoop.langchain": "DEBUG",
        "pitchscoop.azure_openai": "DEBUG"
    }
    
    for logger_name, log_level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level))
    
    # Get main application logger
    app_logger = logging.getLogger("pitchscoop")
    app_logger.info("Structured logging configuration initialized")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(f"pitchscoop.{name}")


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    event_id: Optional[str] = None,
    session_id: Optional[str] = None,
    judge_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    operation: Optional[str] = None,
    duration_ms: Optional[float] = None,
    **extra_context
) -> None:
    """Log a message with structured context information."""
    extra = {}
    if event_id:
        extra['event_id'] = event_id
    if session_id:
        extra['session_id'] = session_id
    if judge_id:
        extra['judge_id'] = judge_id
    if tool_name:
        extra['tool_name'] = tool_name
    if operation:
        extra['operation'] = operation
    if duration_ms:
        extra['duration_ms'] = duration_ms
    
    # Add any additional context
    extra.update(extra_context)
    
    logger.log(getattr(logging, level.upper()), message, extra=extra)


class ScoringLogger:
    """Specialized logger for scoring operations with context management."""
    
    def __init__(self, event_id: str, session_id: Optional[str] = None, judge_id: Optional[str] = None):
        self.logger = get_logger("scoring")
        self.event_id = event_id
        self.session_id = session_id
        self.judge_id = judge_id
        self.start_time = datetime.utcnow()
    
    def info(self, message: str, operation: Optional[str] = None, **extra):
        """Log info message with scoring context."""
        log_with_context(
            self.logger, "INFO", message,
            event_id=self.event_id,
            session_id=self.session_id,
            judge_id=self.judge_id,
            operation=operation,
            **extra
        )
    
    def error(self, message: str, operation: Optional[str] = None, exception: Optional[Exception] = None, **extra):
        """Log error message with scoring context and exception details."""
        if exception:
            self.logger.error(
                message,
                exc_info=True,
                extra={
                    'event_id': self.event_id,
                    'session_id': self.session_id,
                    'judge_id': self.judge_id,
                    'operation': operation,
                    **extra
                }
            )
        else:
            log_with_context(
                self.logger, "ERROR", message,
                event_id=self.event_id,
                session_id=self.session_id,
                judge_id=self.judge_id,
                operation=operation,
                **extra
            )
    
    def warning(self, message: str, operation: Optional[str] = None, **extra):
        """Log warning message with scoring context."""
        log_with_context(
            self.logger, "WARNING", message,
            event_id=self.event_id,
            session_id=self.session_id,
            judge_id=self.judge_id,
            operation=operation,
            **extra
        )
    
    def debug(self, message: str, operation: Optional[str] = None, **extra):
        """Log debug message with scoring context."""
        log_with_context(
            self.logger, "DEBUG", message,
            event_id=self.event_id,
            session_id=self.session_id,
            judge_id=self.judge_id,
            operation=operation,
            **extra
        )
    
    def log_duration(self, operation: str, **extra):
        """Log operation duration from start time."""
        duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        self.info(
            f"Operation '{operation}' completed",
            operation=operation,
            duration_ms=duration_ms,
            **extra
        )
