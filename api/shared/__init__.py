"""
Shared utilities and configurations for FastAPI Celery application
"""

from .config import (
    BaseConfig, APIConfig, WorkerConfig, MonitoringConfig,
    get_config, config, api_config, worker_config, monitoring_config,
    REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND,
    LOG_LEVEL, LOG_FORMAT, DEBUG, ENVIRONMENT
)

from .logging_config import (
    setup_logging, get_logger, LoggingMixin,
    log_function_call, log_task_execution,
    log_api_request, log_api_response,
    log_celery_task_start, log_celery_task_end
)

from .utils import (
    generate_uuid, generate_short_id, hash_string, hash_file_content,
    current_timestamp, current_iso_timestamp, format_bytes, format_duration,
    sanitize_filename, validate_file_type, extract_file_extension,
    encode_base64, decode_base64, safe_json_loads, safe_json_dumps,
    chunks, flatten_dict, retry_on_exception, async_retry_on_exception,
    rate_limit, Timer, CircuitBreaker, memoize, truncate_text,
    parse_content_type, is_valid_email, is_valid_url,
    generate_api_key, mask_sensitive_data, DataValidator
)

from .exceptions import (
    ErrorCode, BaseApplicationError, ValidationError, NotFoundError,
    UnauthorizedError, ForbiddenError, RateLimitError,
    FileProcessingError, FileTooLargeError, InvalidFileTypeError, FileCorruptedError,
    TaskProcessingError, TaskTimeoutError, TaskNotFoundError,
    AIProcessingError, AIAPIError, AIQuotaExceededError, UnsupportedOperationError,
    ExternalServiceError, ExternalServiceTimeoutError, ExternalServiceUnavailableError,
    handle_exception, create_error_response
)

__version__ = "1.0.0"
__author__ = "FastAPI Celery AI Pipeline"
__description__ = "Shared utilities for async AI pipeline using FastAPI + Celery"

__all__ = [
    # Config
    "BaseConfig", "APIConfig", "WorkerConfig", "MonitoringConfig",
    "get_config", "config", "api_config", "worker_config", "monitoring_config",
    "REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND",
    "LOG_LEVEL", "LOG_FORMAT", "DEBUG", "ENVIRONMENT",
    
    # Logging
    "setup_logging", "get_logger", "LoggingMixin",
    "log_function_call", "log_task_execution",
    "log_api_request", "log_api_response",
    "log_celery_task_start", "log_celery_task_end",
    
    # Utils
    "generate_uuid", "generate_short_id", "hash_string", "hash_file_content",
    "current_timestamp", "current_iso_timestamp", "format_bytes", "format_duration",
    "sanitize_filename", "validate_file_type", "extract_file_extension",
    "encode_base64", "decode_base64", "safe_json_loads", "safe_json_dumps",
    "chunks", "flatten_dict", "retry_on_exception", "async_retry_on_exception",
    "rate_limit", "Timer", "CircuitBreaker", "memoize", "truncate_text",
    "parse_content_type", "is_valid_email", "is_valid_url",
    "generate_api_key", "mask_sensitive_data", "DataValidator",
    
    # Exceptions
    "ErrorCode", "BaseApplicationError", "ValidationError", "NotFoundError",
    "UnauthorizedError", "ForbiddenError", "RateLimitError",
    "FileProcessingError", "FileTooLargeError", "InvalidFileTypeError", "FileCorruptedError",
    "TaskProcessingError", "TaskTimeoutError", "TaskNotFoundError",
    "AIProcessingError", "AIAPIError", "AIQuotaExceededError", "UnsupportedOperationError",
    "ExternalServiceError", "ExternalServiceTimeoutError", "ExternalServiceUnavailableError",
    "handle_exception", "create_error_response",
]