# FastAPI API Service

This is the FastAPI web application component of the FastAPI + Celery AI pipeline.

## Features

- RESTful API endpoints for AI task processing
- Document and image processing task submission
- Task status monitoring and results retrieval
- Comprehensive error handling and validation
- Health checks and monitoring endpoints

## Dependencies

This service includes all necessary dependencies for:
- FastAPI web framework
- Celery task queue client
- HTTP clients for external requests
- File processing and validation
- Configuration and logging utilities

## Usage

```bash
cd api
pip install -e .
python main.py
```

Access the API documentation at: http://localhost:8000/docs