# Flower Monitoring Service

This is the Flower monitoring dashboard component of the FastAPI + Celery AI pipeline.

## Features

- Web-based monitoring dashboard for Celery workers
- Real-time task queue visualization
- Worker status and performance metrics
- Task history and execution statistics
- Configurable authentication and access control

## Dependencies

This service includes all necessary dependencies for:
- Celery monitoring with Flower
- Redis connection for task queue inspection
- Configuration and logging utilities

## Usage

```bash
cd monitoring
pip install -e .
python start_flower.py
```

Access the monitoring dashboard at: http://localhost:5555