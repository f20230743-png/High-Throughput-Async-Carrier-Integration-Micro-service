# Upsun Multi-App Deployment Guide

This document explains the multi-app deployment structure for the FastAPI + Celery AI pipeline on Upsun.

## 🏗️ Architecture Overview

The project uses Upsun's multi-app deployment pattern where each service runs in its own container with isolated dependencies.

### Applications Structure

```
┌─────────────────┬─────────────────┬─────────────────┐
│   API Service   │ Worker Service  │Monitor Service  │
├─────────────────┼─────────────────┼─────────────────┤
│ api/            │ worker/         │ monitoring/     │
│ ├── main.py     │ ├── tasks.py    │ ├── tasks.py    │
│ ├── pyproject.  │ ├── document_*  │ ├── flower*     │
│ ├── uv.lock     │ ├── image_*     │ ├── pyproject.  │
│ ├── shared/     │ ├── pyproject.  │ ├── uv.lock     │
│ └── .venv/      │ ├── uv.lock     │ ├── shared/     │
│                 │ ├── shared/     │ └── .venv/      │
│                 │ └── .venv/      │                 │
└─────────────────┴─────────────────┴─────────────────┘
                           │
                   ┌─────────────────┐
                   │ Redis Service   │
                   │ (Managed by     │
                   │  Upsun)         │
                   └─────────────────┘
```

## 📦 Dependency Isolation

Each application has minimal, focused dependencies:

### API Service (`api/pyproject.toml`)
- FastAPI web framework
- Celery client (task submission only)
- HTTP clients and validation
- Shared utilities (local copy)

### Worker Service (`worker/pyproject.toml`)
- Celery worker runtime
- Heavy AI/ML libraries (PyTorch, Transformers, OpenCV)
- Document processing libraries
- Shared utilities (local copy)

### Monitoring Service (`monitoring/pyproject.toml`)
- Flower monitoring dashboard
- Celery inspection tools
- Minimal dependencies for monitoring
- Shared utilities (local copy)

## ⚡ UV Package Manager Benefits

Each service uses UV for dependency management:

- **Speed**: 10-100x faster than pip
- **Reproducible**: `uv.lock` ensures consistent builds
- **Isolated**: Each app has only required dependencies
- **Cached**: Efficient dependency resolution

## 🚀 Deployment Process

### Upsun Configuration (`.upsun/config.yaml`)

```yaml
applications:
  api:
    source:
      root: api
    type: python:3.13
    dependencies:
      python3:
        uv: "*"
    hooks:
      build: |
        uv sync --frozen
    web:
      commands:
        start: "uvicorn main:app --host 0.0.0.0 --port $PORT"

  worker:
    source:
      root: worker
    # ... similar configuration

  flower:
    source:
      root: monitoring
    # ... similar configuration

services:
  redis:
    type: redis:7.0
```

### Build Process for Each App

1. **Container Creation**: Upsun creates separate container for each app
2. **Dependency Installation**: `uv sync --frozen` installs exact versions
3. **Shared Code**: Each app includes local copy of shared utilities
4. **Service Start**: Each app starts with its specific command

## 🔧 Local Development

### With UV (Recommended)

```bash
# Start Redis
docker-compose up redis -d

# Each service in separate terminal
cd api && uv sync && .venv/bin/python main.py
cd worker && uv sync && .venv/bin/celery -A tasks worker --loglevel=info
cd monitoring && uv sync && .venv/bin/python start_flower.py
```

### With Traditional pip

```bash
# Start Redis
docker-compose up redis -d

# Install and run each service
cd api && pip install -e . && python main.py
cd worker && pip install -e . && celery -A tasks worker --loglevel=info
cd monitoring && pip install -e . && python start_flower.py
```

## 📊 Dependency Comparison

| Service    | Dependencies | Size  | Purpose |
|------------|-------------|-------|---------|
| API        | 43 packages | ~50MB | Web interface |
| Worker     | 94 packages | ~2GB  | AI/ML processing |
| Monitoring | 32 packages | ~30MB | Dashboard |

This isolation means:
- API containers are lightweight and start fast
- Worker containers have all AI libraries but only where needed
- Monitoring containers are minimal for quick startup
- Each service can scale independently

## 🌐 Access Points

After deployment:
- **API**: `https://api.{your-project}.upsun.app/`
- **API Docs**: `https://api.{your-project}.upsun.app/docs`
- **Monitoring**: `https://monitor.{your-project}.upsun.app/`

## 🔑 Environment Variables

Set in Upsun dashboard:

```bash
# Required for all services
CELERY_BROKER_URL=redis://redis.internal:6379/0
CELERY_RESULT_BACKEND=redis://redis.internal:6379/0

# Optional for AI features
OPENAI_API_KEY=your_key
HUGGINGFACE_API_KEY=your_key
```

## 📈 Scaling Strategy

- **API**: Scale horizontally for more web traffic
- **Worker**: Scale based on task queue length
- **Monitoring**: Usually single instance sufficient
- **Redis**: Managed service handles scaling automatically