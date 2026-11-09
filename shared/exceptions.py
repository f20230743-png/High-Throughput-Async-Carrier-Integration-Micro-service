"""
Custom exceptions for the FastAPI Celery application
"""

from typing import Any, Dict, Optional
from enum import Enum

class ErrorCode(Enum):
    """Standard error codes"""
    
    # Generic errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    
    # File processing errors
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_CORRUPTED = "FILE_CORRUPTED"
    FILE_PROCESSING_FAILED = "FILE_PROCESSING_FAILED"
    
    # Task processing errors
    TASK_FAILED = "TASK_FAILED"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_ALREADY_RUNNING = "TASK_ALREADY_RUNNING"
    QUEUE_FULL = "QUEUE_FULL"
    
    # AI/ML processing errors
    AI_MODEL_ERROR = "AI_MODEL_ERROR"
    AI_API_ERROR = "AI_API_ERROR"
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    
    # External service errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"

class BaseApplicationError(Exception):
    """Base exception class for application errors"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        result = {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details
        }
        
        if self.cause:
            result["cause"] = {
                "type": type(self.cause).__name__,
                "message": str(self.cause)
            }
        
        return result
    
    def __str__(self) -> str:
        return f"{self.error_code.value}: {self.message}"

class ValidationError(BaseApplicationError):
    """Validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details
        )

class NotFoundError(BaseApplicationError):
    """Resource not found error"""
    
    def __init__(self, resource_type: str, resource_id: Optional[str] = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            details=details
        )

class UnauthorizedError(BaseApplicationError):
    """Unauthorized access error"""
    
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED
        )

class ForbiddenError(BaseApplicationError):
    """Forbidden access error"""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN
        )

class RateLimitError(BaseApplicationError):
    """Rate limit exceeded error"""
    
    def __init__(self, limit: int, window: int, retry_after: Optional[int] = None):
        message = f"Rate limit exceeded: {limit} requests per {window} seconds"
        details = {"limit": limit, "window": window}
        
        if retry_after:
            message += f". Retry after {retry_after} seconds"
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMITED,
            details=details
        )

class FileProcessingError(BaseApplicationError):
    """File processing error"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.FILE_PROCESSING_FAILED,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None
    ):
        details = {}
        if filename:
            details["filename"] = filename
        if file_size:
            details["file_size"] = file_size
        if file_type:
            details["file_type"] = file_type
        
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )

class FileTooLargeError(FileProcessingError):
    """File too large error"""
    
    def __init__(self, filename: str, size: int, max_size: int):
        message = f"File '{filename}' is too large: {size} bytes (max: {max_size} bytes)"
        super().__init__(
            message=message,
            error_code=ErrorCode.FILE_TOO_LARGE,
            filename=filename,
            file_size=size
        )
        self.details["max_size"] = max_size

class InvalidFileTypeError(FileProcessingError):
    """Invalid file type error"""
    
    def __init__(self, filename: str, file_type: str, allowed_types: list):
        message = f"Invalid file type '{file_type}' for file '{filename}'. Allowed types: {', '.join(allowed_types)}"
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_FILE_TYPE,
            filename=filename,
            file_type=file_type
        )
        self.details["allowed_types"] = allowed_types

class FileCorruptedError(FileProcessingError):
    """File corrupted error"""
    
    def __init__(self, filename: str, reason: Optional[str] = None):
        message = f"File '{filename}' is corrupted"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.FILE_CORRUPTED,
            filename=filename
        )

class TaskProcessingError(BaseApplicationError):
    """Task processing error"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.TASK_FAILED,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None
    ):
        details = {}
        if task_id:
            details["task_id"] = task_id
        if task_name:
            details["task_name"] = task_name
        
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )

class TaskTimeoutError(TaskProcessingError):
    """Task timeout error"""
    
    def __init__(self, task_id: str, task_name: str, timeout: int):
        message = f"Task '{task_name}' ({task_id}) timed out after {timeout} seconds"
        super().__init__(
            message=message,
            error_code=ErrorCode.TASK_TIMEOUT,
            task_id=task_id,
            task_name=task_name
        )
        self.details["timeout"] = timeout

class TaskNotFoundError(TaskProcessingError):
    """Task not found error"""
    
    def __init__(self, task_id: str):
        message = f"Task not found: {task_id}"
        super().__init__(
            message=message,
            error_code=ErrorCode.TASK_NOT_FOUND,
            task_id=task_id
        )

class AIProcessingError(BaseApplicationError):
    """AI processing error"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.AI_MODEL_ERROR,
        model_name: Optional[str] = None,
        operation: Optional[str] = None
    ):
        details = {}
        if model_name:
            details["model_name"] = model_name
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )

class AIAPIError(AIProcessingError):
    """AI API error"""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        api_error_code: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.AI_API_ERROR,
            model_name=api_name
        )
        
        if status_code:
            self.details["status_code"] = status_code
        if api_error_code:
            self.details["api_error_code"] = api_error_code

class AIQuotaExceededError(AIProcessingError):
    """AI quota exceeded error"""
    
    def __init__(self, api_name: str, quota_type: str = "requests"):
        message = f"AI API quota exceeded for {api_name} ({quota_type})"
        super().__init__(
            message=message,
            error_code=ErrorCode.AI_QUOTA_EXCEEDED,
            model_name=api_name
        )
        self.details["quota_type"] = quota_type

class UnsupportedOperationError(BaseApplicationError):
    """Unsupported operation error"""
    
    def __init__(self, operation: str, context: Optional[str] = None):
        message = f"Unsupported operation: {operation}"
        if context:
            message += f" in context: {context}"
        
        details = {"operation": operation}
        if context:
            details["context"] = context
        
        super().__init__(
            message=message,
            error_code=ErrorCode.UNSUPPORTED_OPERATION,
            details=details
        )

class ExternalServiceError(BaseApplicationError):
    """External service error"""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        details = {"service_name": service_name}
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:1000]  # Limit response body length
        
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )

class ExternalServiceTimeoutError(ExternalServiceError):
    """External service timeout error"""
    
    def __init__(self, service_name: str, timeout: int):
        message = f"External service '{service_name}' timed out after {timeout} seconds"
        super().__init__(
            message=message,
            service_name=service_name,
            error_code=ErrorCode.EXTERNAL_SERVICE_TIMEOUT
        )
        self.details["timeout"] = timeout

class ExternalServiceUnavailableError(ExternalServiceError):
    """External service unavailable error"""
    
    def __init__(self, service_name: str, reason: Optional[str] = None):
        message = f"External service '{service_name}' is unavailable"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            service_name=service_name,
            error_code=ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE
        )

# Exception handling utilities

def handle_exception(exception: Exception) -> BaseApplicationError:
    """Convert generic exceptions to application exceptions"""
    
    if isinstance(exception, BaseApplicationError):
        return exception
    
    # Map common exceptions
    if isinstance(exception, FileNotFoundError):
        return NotFoundError("File", str(exception))
    elif isinstance(exception, PermissionError):
        return ForbiddenError(f"Permission denied: {exception}")
    elif isinstance(exception, TimeoutError):
        return ExternalServiceTimeoutError("Unknown service", 30)  # Default timeout
    elif isinstance(exception, ValueError):
        return ValidationError(str(exception))
    elif isinstance(exception, ConnectionError):
        return ExternalServiceUnavailableError("Unknown service", str(exception))
    else:
        # Generic internal error
        return BaseApplicationError(
            message=f"Unexpected error: {exception}",
            error_code=ErrorCode.INTERNAL_ERROR,
            cause=exception
        )

def create_error_response(exception: BaseApplicationError) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "success": False,
        "error": exception.to_dict(),
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'
    }