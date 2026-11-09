import hashlib
import uuid
import time
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
from functools import wraps
import json
import base64
from datetime import datetime, timedelta
import re
from pathlib import Path

def generate_uuid() -> str:
    """Generate a unique UUID string"""
    return str(uuid.uuid4())

def generate_short_id(length: int = 8) -> str:
    """Generate a short random ID"""
    return str(uuid.uuid4()).replace('-', '')[:length]

def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Hash a string using specified algorithm"""
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()

def hash_file_content(content: bytes, algorithm: str = 'sha256') -> str:
    """Hash file content"""
    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()

def current_timestamp() -> float:
    """Get current timestamp"""
    return time.time()

def current_iso_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat() + 'Z'

def format_bytes(bytes_value: int) -> str:
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        return f"{seconds/60:.2f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.2f}h"
    else:
        return f"{seconds/86400:.2f}d"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        name, ext = Path(filename).stem, Path(filename).suffix
        filename = name[:255-len(ext)] + ext
    return filename or 'unnamed_file'

def validate_file_type(content_type: str, allowed_types: List[str]) -> bool:
    """Validate if content type is allowed"""
    return content_type.lower() in [t.lower() for t in allowed_types]

def extract_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    return Path(filename).suffix.lower()

def encode_base64(data: Union[str, bytes]) -> str:
    """Encode data to base64 string"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')

def decode_base64(data: str) -> bytes:
    """Decode base64 string to bytes"""
    return base64.b64decode(data)

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: Any = None) -> Optional[str]:
    """Safely dump object to JSON string"""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default

def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """Yield successive n-sized chunks from list"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for retrying functions on exceptions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        raise e
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

async def async_retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for retrying async functions on exceptions"""
    def decorator(func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        raise e
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(max_calls: int, time_window: int):
    """Simple rate limiting decorator"""
    calls = []
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove old calls outside the time window
            calls[:] = [call_time for call_time in calls if now - call_time < time_window]
            
            if len(calls) >= max_calls:
                raise ValueError(f"Rate limit exceeded: {max_calls} calls per {time_window} seconds")
            
            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    @property
    def elapsed_formatted(self) -> str:
        """Get formatted elapsed time"""
        return format_duration(self.elapsed)

class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == 'open':
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = 'half_open'
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                if self.state == 'half_open':
                    self.state = 'closed'
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'open'
                
                raise e
        
        return wrapper

def memoize(ttl: int = 300):
    """Memoization decorator with TTL (time to live) in seconds"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    return result
                else:
                    del cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result
        
        return wrapper
    return decorator

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def parse_content_type(content_type: str) -> tuple:
    """Parse content type header"""
    if ';' in content_type:
        main_type, params = content_type.split(';', 1)
        return main_type.strip(), params.strip()
    return content_type.strip(), ''

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#[^\s]*)?$'
    return re.match(pattern, url) is not None

def generate_api_key(length: int = 32) -> str:
    """Generate a secure API key"""
    import secrets
    return secrets.token_urlsafe(length)

def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first/last few characters"""
    if len(data) <= visible_chars * 2:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars * 2) + data[-visible_chars:]

class DataValidator:
    """Common data validation utilities"""
    
    @staticmethod
    def validate_image_file(content_type: str, content_length: int, max_size_mb: int = 10) -> tuple:
        """Validate image file"""
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        
        if content_type not in allowed_types:
            return False, f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if content_length > max_size_bytes:
            return False, f"File too large. Maximum size: {max_size_mb}MB"
        
        return True, "Valid"
    
    @staticmethod
    def validate_document_file(content_type: str, content_length: int, max_size_mb: int = 50) -> tuple:
        """Validate document file"""
        allowed_types = [
            'text/plain',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
        
        if content_type not in allowed_types:
            return False, f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if content_length > max_size_bytes:
            return False, f"File too large. Maximum size: {max_size_mb}MB"
        
        return True, "Valid"