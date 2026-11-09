# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a demonstration repository for building async web content processing pipelines using FastAPI + Celery, designed to be deployed on Upsun as a multi-app architecture. The project showcases:

- FastAPI web application with async endpoints
- Celery task queue with Redis as message broker
- Web scraping and content summarization using OpenAI API
- Flower dashboard for monitoring Celery workers
- Multi-app deployment configuration for Upsun platform
- Shared storage for result persistence across containers

## Current State

The repository is now fully implemented with a complete FastAPI + Celery AI pipeline:

### ✅ Completed Components
- **Complete project structure** with multi-app architecture (`api/`, `worker/`, `monitoring/`, `shared/`)
- **Isolated Dependencies** - Separate `pyproject.toml` and `uv.lock` files for each Upsun app
- **UV Package Manager** - Fast dependency resolution with reproducible builds
- **FastAPI Application** - Production-ready API with comprehensive error handling and validation
- **Celery Workers** - Full task definitions with AI/ML processing capabilities
- **Web Scraping** - Complete web content extraction with BeautifulSoup and readability
- **Content Summarization** - OpenAI-powered content summarization with multiple modes
- **Flower Monitoring** - Web dashboard for Celery worker monitoring
- **Shared Utilities** - Configuration management, logging, exceptions, utilities (copied to each service)
- **Upsun Deployment** - Complete `.upsun/config.yaml` for multi-app deployment with UV
- **Docker Setup** - `docker-compose.yml` for local Redis development
- **Comprehensive Testing** - System integration tests with `test_system.py`
- **Documentation** - Complete README with setup and usage instructions

## Development Setup

### Dependencies Management
- **Isolated Dependencies**: Each Upsun app (`api/`, `worker/`, `monitoring/`) has its own `pyproject.toml` and `uv.lock`
- **UV Package Manager**: Fast dependency resolution (10-100x faster than pip)
- **Reproducible Builds**: Locked dependencies ensure consistent deployments
- **Minimal Dependencies**: Each service only includes what it needs
- Requires Python 3.13+
- Virtual environments created per service (`.venv/` in each directory)

### Local Development with Docker

The project includes `docker-compose.yml` for easy local development:

```bash
# Start Redis for development
docker-compose up redis -d

# Stop services
docker-compose down
```

### Architecture (Implemented)

The project implements a complete multi-service architecture:

1. **FastAPI Application** (`api/`) - Main web service with web content processing endpoints
2. **Celery Workers** (`worker/`) - Background task processors for web scraping and summarization
3. **Redis** - Message broker and result backend (via Docker Compose)
4. **Flower** (`monitoring/`) - Web-based monitoring dashboard
5. **Shared Utilities** (`shared/`) - Common configuration, logging, and utilities

### Deployment Target

- **Upsun multi-app deployment** - Complete configuration in `.upsun/config.yaml`
- Each service (FastAPI, Celery workers, Redis, Flower) are separate apps
- Environment-based configuration for different deployment scenarios

## Development Commands

The project is fully implemented with web content processing. Use these commands for development and testing:

### Installation
```bash
# Install dependencies
pip install -e .
```

### Local Development with UV
```bash
# Start Redis (required)
docker-compose up redis -d

# Each service has its own virtual environment and dependencies

# API Service
cd api
uv sync  # Install dependencies (if not done)
.venv/bin/python main.py

# Worker Service (in another terminal)
cd worker
uv sync  # Install dependencies (if not done)
.venv/bin/celery -A tasks worker --loglevel=info --concurrency=4

# Set OpenAI API key for summarization
export OPENAI_API_KEY=your_openai_api_key

# Monitoring Service (optional, in another terminal)
cd monitoring
uv sync  # Install dependencies (if not done)
.venv/bin/python start_flower.py
```

### Alternative: Traditional pip installation
```bash
# Start Redis
docker-compose up redis -d

# Install in each directory
cd api && pip install -e . && python main.py &
cd worker && pip install -e . && celery -A tasks worker --loglevel=info &
cd monitoring && pip install -e . && python start_flower.py &
```

### Testing
```bash
# Run system integration tests
python test_system.py --verbose

# Manual API testing
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI
```

### Docker Development
```bash
# Start only Redis
docker-compose up redis -d

# View logs
docker-compose logs -f redis

# Stop services
docker-compose down
```

## Available Features & Enhancements

The project is feature-complete for demonstration purposes. For production use or further development, consider:

### Current Web Processing Capabilities
- **Web Scraping**: URL validation, robots.txt compliance, content extraction
- **Content Summarization**: OpenAI-powered summarization (brief, standard, detailed)
- **Result Storage**: Shared storage system with JSON persistence and caching
- **Extensible Pipeline**: Easy to add new web processing tasks

### Production Enhancements
1. **Authentication & Authorization**: Add JWT tokens, user management
2. **Real AI Models**: Replace mock implementations with actual models
3. **Database Integration**: Add PostgreSQL for task persistence
4. **Rate Limiting**: Implement request throttling
5. **Monitoring**: Add APM (Application Performance Monitoring)
6. **Caching**: Implement result caching strategies
7. **File Storage**: Add cloud storage integration (S3, etc.)
8. **WebSockets**: Real-time task progress updates

## Important Notes

- This is an example/demo repository for an Upsun article
- Focuses on web scraping and OpenAI-based summarization (no heavy ML models)
- All components are optimized for multi-app Upsun deployment
- Uses shared storage for result persistence across containers
- Includes comprehensive safety measures for web scraping (robots.txt, rate limiting)
- Clean, well-documented codebase suitable for production deployment