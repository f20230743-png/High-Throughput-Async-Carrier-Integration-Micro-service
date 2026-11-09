# Shared Utilities

This package contains shared utilities used across all services in the FastAPI + Celery AI pipeline.

## Features

- Configuration management with environment-based settings
- Structured logging with JSON output support
- Custom exception classes for error handling
- Common utilities for validation, file processing, and more
- Type-safe configuration classes for different services

## Usage

This package is included in each service directory and provides:

- `config.py` - Configuration classes for API, Worker, and Monitoring services
- `logging_config.py` - Logging setup and utilities
- `exceptions.py` - Custom exception classes with error codes
- `utils.py` - Common utility functions and classes