import os
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class BaseConfig(BaseSettings):
    """Base configuration class with common settings"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Redis Configuration - Use environment variables with fallbacks
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    @property
    def celery_broker_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    @property
    def celery_result_backend(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    
    # AI/ML Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # File Processing
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    allowed_image_types: List[str] = Field(default=["image/jpeg", "image/png", "image/gif", "image/webp"])
    allowed_document_types: List[str] = Field(default=["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"])
    
    # Task Configuration
    task_timeout_seconds: int = Field(default=300, env="TASK_TIMEOUT_SECONDS")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay_seconds: int = Field(default=60, env="RETRY_DELAY_SECONDS")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @field_validator('log_format')
    @classmethod
    def validate_log_format(cls, v):
        valid_formats = ['json', 'text']
        if v.lower() not in valid_formats:
            raise ValueError(f'log_format must be one of {valid_formats}')
        return v.lower()
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class APIConfig(BaseConfig):
    """Configuration specific to FastAPI application"""
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    workers: int = Field(default=1, env="API_WORKERS")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    # API Documentation
    docs_url: Optional[str] = Field(default="/docs", env="DOCS_URL")
    redoc_url: Optional[str] = Field(default="/redoc", env="REDOC_URL")
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

class WorkerConfig(BaseConfig):
    """Configuration specific to Celery workers"""
    
    # Worker Configuration
    worker_concurrency: int = Field(default=4, env="WORKER_CONCURRENCY")
    worker_prefetch_multiplier: int = Field(default=1, env="WORKER_PREFETCH_MULTIPLIER")
    worker_max_tasks_per_child: int = Field(default=1000, env="WORKER_MAX_TASKS_PER_CHILD")
    
    # Task Configuration
    task_always_eager: bool = Field(default=False, env="TASK_ALWAYS_EAGER")
    task_eager_propagates: bool = Field(default=True, env="TASK_EAGER_PROPAGATES")
    task_ignore_result: bool = Field(default=False, env="TASK_IGNORE_RESULT")
    task_store_eager_result: bool = Field(default=True, env="TASK_STORE_EAGER_RESULT")
    
    # Result Backend Configuration
    result_expires: int = Field(default=3600, env="RESULT_EXPIRES")  # 1 hour
    result_compression: str = Field(default="gzip", env="RESULT_COMPRESSION")
    
    # Monitoring
    worker_send_task_events: bool = Field(default=True, env="WORKER_SEND_TASK_EVENTS")
    task_send_sent_event: bool = Field(default=True, env="TASK_SEND_SENT_EVENT")

class MonitoringConfig(BaseConfig):
    """Configuration specific to Flower monitoring"""
    
    # Flower Configuration
    flower_port: int = Field(default=5555, env="FLOWER_PORT")
    flower_address: str = Field(default="0.0.0.0", env="FLOWER_ADDRESS")
    flower_url_prefix: str = Field(default="", env="FLOWER_URL_PREFIX")
    flower_basic_auth: Optional[str] = Field(default=None, env="FLOWER_BASIC_AUTH")
    flower_db_url: str = Field(default="sqlite:///flower.db", env="FLOWER_DB_URL")
    
    # Display Configuration
    flower_max_tasks: int = Field(default=10000, env="FLOWER_MAX_TASKS")
    flower_auto_refresh: bool = Field(default=True, env="FLOWER_AUTO_REFRESH")
    flower_refresh_interval: int = Field(default=30000, env="FLOWER_REFRESH_INTERVAL")  # milliseconds

# Configuration factory
def get_config(config_type: str = "base") -> BaseConfig:
    """Get configuration instance based on type"""
    config_map = {
        "base": BaseConfig,
        "api": APIConfig,
        "worker": WorkerConfig,
        "monitoring": MonitoringConfig,
    }
    
    config_class = config_map.get(config_type.lower(), BaseConfig)
    return config_class()

# Global configuration instances
config = get_config("base")
api_config = get_config("api")
worker_config = get_config("worker")
monitoring_config = get_config("monitoring")

# Export commonly used settings
REDIS_URL = config.redis_url
CELERY_BROKER_URL = config.celery_broker_url
CELERY_RESULT_BACKEND = config.celery_result_backend
LOG_LEVEL = config.log_level
LOG_FORMAT = config.log_format
DEBUG = config.debug
ENVIRONMENT = config.environment