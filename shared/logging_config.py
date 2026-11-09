import logging
import sys
import structlog
from typing import Any, Dict, Optional
import json
from datetime import datetime
from .config import config

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'task_id'):
            log_entry['task_id'] = record.task_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'service'):
            log_entry['service'] = record.service
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

class TextFormatter(logging.Formatter):
    """Human-readable text formatter"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def setup_logging(
    service_name: str,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_structlog: bool = True
) -> logging.Logger:
    """
    Set up logging configuration for the application
    
    Args:
        service_name: Name of the service (api, worker, monitoring)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json, text)
        enable_structlog: Whether to enable structlog
    
    Returns:
        Configured logger instance
    """
    
    # Use config defaults if not specified
    log_level = log_level or config.log_level
    log_format = log_format or config.log_format
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Set formatter based on format preference
    if log_format == 'json':
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure structlog if enabled
    if enable_structlog:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if log_format == 'json' else structlog.dev.ConsoleRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Create service-specific logger
    logger = logging.getLogger(service_name)
    
    # Add service name to all log records
    class ServiceFilter(logging.Filter):
        def filter(self, record):
            record.service = service_name
            return True
    
    logger.addFilter(ServiceFilter())
    
    # Set third-party library log levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.INFO)
    
    logger.info(f"Logging configured for service: {service_name}", 
                extra={'level': log_level, 'format': log_format})
    
    return logger

def get_logger(name: str) -> Any:
    """Get a structlog logger instance"""
    return structlog.get_logger(name)

class LoggingMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> Any:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            class_name = self.__class__.__name__
            self._logger = get_logger(class_name)
        return self._logger
    
    def log_method_call(self, method_name: str, **kwargs) -> None:
        """Log method call with parameters"""
        self.logger.debug(f"Calling {method_name}", method=method_name, **kwargs)
    
    def log_method_result(self, method_name: str, result: Any = None, **kwargs) -> None:
        """Log method result"""
        self.logger.debug(f"Completed {method_name}", method=method_name, result_type=type(result).__name__, **kwargs)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with context"""
        context = context or {}
        self.logger.error(f"Error occurred: {error}", 
                         error_type=type(error).__name__, 
                         error_message=str(error),
                         **context)

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling function {func.__name__}", 
                    function=func.__name__, 
                    args_count=len(args), 
                    kwargs_keys=list(kwargs.keys()))
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully", 
                        function=func.__name__,
                        result_type=type(result).__name__)
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed", 
                        function=func.__name__,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        exc_info=True)
            raise
    
    return wrapper

def log_task_execution(task_name: str, task_id: str):
    """Context manager for task execution logging"""
    class TaskLogger:
        def __init__(self, name: str, task_id: str):
            self.name = name
            self.task_id = task_id
            self.logger = get_logger("task_execution")
            
        def __enter__(self):
            self.logger.info(f"Starting task {self.name}", 
                           task_name=self.name, 
                           task_id=self.task_id)
            self.start_time = datetime.utcnow()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            end_time = datetime.utcnow()
            duration = (end_time - self.start_time).total_seconds()
            
            if exc_type:
                self.logger.error(f"Task {self.name} failed", 
                                task_name=self.name,
                                task_id=self.task_id,
                                duration=duration,
                                error_type=exc_type.__name__,
                                error_message=str(exc_val))
            else:
                self.logger.info(f"Task {self.name} completed successfully", 
                               task_name=self.name,
                               task_id=self.task_id,
                               duration=duration)
    
    return TaskLogger(task_name, task_id)

# Convenience functions for common logging patterns
def log_api_request(method: str, path: str, **kwargs):
    """Log API request"""
    logger = get_logger("api_requests")
    logger.info("API request received", method=method, path=path, **kwargs)

def log_api_response(method: str, path: str, status_code: int, duration: float, **kwargs):
    """Log API response"""
    logger = get_logger("api_responses")
    logger.info("API response sent", 
                method=method, 
                path=path, 
                status_code=status_code, 
                duration=duration, 
                **kwargs)

def log_celery_task_start(task_name: str, task_id: str, **kwargs):
    """Log Celery task start"""
    logger = get_logger("celery_tasks")
    logger.info("Celery task started", task_name=task_name, task_id=task_id, **kwargs)

def log_celery_task_end(task_name: str, task_id: str, status: str, duration: float, **kwargs):
    """Log Celery task completion"""
    logger = get_logger("celery_tasks")
    logger.info("Celery task completed", 
                task_name=task_name, 
                task_id=task_id, 
                status=status, 
                duration=duration, 
                **kwargs)