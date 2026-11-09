# FastAPI + Celery Web Content Processor

A comprehensive demonstration of building async web content processing pipelines using FastAPI + Celery
## 🚀 Features

- **FastAPI Web Application**: High-performance async web server with automatic OpenAPI documentation
- **Celery Task Queue**: Distributed task processing for AI/ML operations
- **Redis Message Broker**: Fast and reliable message queuing
- **Flower Monitoring**: Web-based monitoring dashboard for Celery workers
- **Web Content Processing**: Web scraping and content summarization using OpenAI
- **Multi-App Architecture**: Designed for Upsun platform deployment
- **Comprehensive Logging**: Structured logging with JSON output
- **Error Handling**: Robust error handling with custom exception types
- **Validation**: Thorough input validation and file type checking

## 📁 Project Structure

```
fastapi-celery/
├── api/                    # FastAPI web application (Upsun app)
│   ├── main.py            # Main FastAPI app with endpoints
│   ├── pyproject.toml     # API service dependencies
│   ├── uv.lock            # UV lock file for API
│   ├── shared/            # Local copy of shared utilities
│   └── .venv/             # Virtual environment
├── worker/                # Celery worker processes (Upsun app)
│   ├── tasks.py           # Celery task definitions
│   ├── web_scraper.py      # Web content scraping and processing
│   ├── pyproject.toml     # Worker service dependencies
│   ├── uv.lock            # UV lock file for worker
│   ├── shared/            # Local copy of shared utilities
│   └── .venv/             # Virtual environment
├── monitoring/            # Flower monitoring (Upsun app)
│   ├── tasks.py           # Celery config for monitoring
│   ├── flowerconfig.py    # Flower configuration
│   ├── start_flower.py    # Flower startup script
│   ├── pyproject.toml     # Monitoring service dependencies
│   ├── uv.lock            # UV lock file for monitoring
│   ├── shared/            # Local copy of shared utilities
│   └── .venv/             # Virtual environment
├── shared/                # Original shared utilities (template)
│   ├── __init__.py        # Package exports
│   ├── config.py          # Configuration management
│   ├── logging_config.py  # Logging utilities
│   ├── utils.py           # Common utilities
│   ├── exceptions.py      # Custom exception classes
│   └── pyproject.toml     # Shared utilities dependencies
├── .upsun/
│   └── config.yaml        # Upsun multi-app deployment config
├── docker-compose.yml     # Local development with Redis
├── pyproject.toml         # Root project dependencies (dev only)
├── test_system.py         # System integration tests
├── main.py                # Legacy main file
└── README.md              # This file
```

## 🛠️ Dependencies

The project uses the following key dependencies:

- **Web Framework**: FastAPI, Uvicorn
- **Task Queue**: Celery, Redis, Flower
- **AI/ML**: OpenAI API for content summarization
- **Web Scraping**: BeautifulSoup, requests, readability-lxml
- **Utilities**: Pydantic, python-dotenv, structlog, tenacity

## ⚙️ Configuration

The application uses environment-based configuration with the following key variables:

### Required Environment Variables

```bash
# Redis/Celery Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# AI/ML (Required for summarization)
OPENAI_API_KEY=your_openai_api_key
```

### Optional Environment Variables

```bash
# File Processing Limits
MAX_FILE_SIZE_MB=100

# Task Configuration
TASK_TIMEOUT_SECONDS=300
MAX_RETRIES=3

# Flower Monitoring
FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:admin

# CORS Configuration
CORS_ORIGINS=*

# Web Scraping Configuration
STORAGE_PATH=/app/data
USER_AGENT=FastAPI-Celery-WebScraper/1.0
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Start Redis Server

#### Option A: Using Docker Compose (Recommended)

```bash
docker-compose up redis -d
```

#### Option B: Using standalone Docker

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

#### Option C: Local Redis installation

```bash
redis-server
```

### 3. Start Celery Worker

```bash
cd worker
celery -A tasks worker --loglevel=info --concurrency=4
```

### 4. Start FastAPI Application

```bash
cd api
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start Flower Monitoring (Optional)

```bash
cd monitoring
python start_flower.py

# Or using celery flower command
celery -A tasks flower --port=5555
```

## 🐳 Docker Development Setup

The project includes a `docker-compose.yml` for easy local development:

```bash
# Start Redis only
docker-compose up redis -d

# Start all services (when Docker images are built)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The Docker Compose setup includes:
- **Redis**: Message broker on port 6379
- **API**: FastAPI application on port 8000 (when built)
- **Worker**: Celery worker processes (when built)
- **Flower**: Monitoring dashboard on port 5555 (when built)

## 🧪 Testing the System

### Automated Testing

Run the comprehensive test suite:

```bash
python test_system.py --verbose
```

This will test:
- API health checks
- Web content processing endpoints
- Task status monitoring
- Worker statistics

### Manual Testing

#### 1. Check API Health

```bash
curl http://localhost:8000/health
```

#### 2. Scrape and Summarize a Web Page

```bash
curl -X POST "http://localhost:8000/tasks/web/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "summary_type": "standard"
  }'
```

#### 3. Get Task Result from Storage

```bash
curl http://localhost:8000/tasks/{task_id}/result
```

#### 4. Check Task Status

```bash
curl http://localhost:8000/tasks/{task_id}/status
```

#### 5. View Active Tasks

```bash
curl http://localhost:8000/tasks
```

## 📊 Monitoring

### FastAPI Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Flower Dashboard

- **Flower UI**: http://localhost:5555
- Monitor worker status, task queues, and execution statistics

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check with dependencies
- `POST /tasks/web/summarize` - Scrape and summarize web pages
- `GET /tasks/{task_id}/result` - Get detailed results from storage
- `GET /tasks/{task_id}/status` - Get task status
- `GET /tasks` - List active tasks
- `GET /tasks/stats` - Worker statistics

## ☁️ Upsun Deployment

This project is designed for deployment on Upsun platform with a multi-app architecture. Each service runs in its own container with isolated dependencies.

### Multi-App Architecture

The project uses Upsun's multi-app deployment with three separate applications:

1. **API Application** (`api/`)
   - Source root: `api/`
   - Python 3.13 runtime
   - UV package manager for fast dependency resolution
   - Isolated dependencies in `pyproject.toml` and `uv.lock`
   - FastAPI-specific dependencies only

2. **Worker Application** (`worker/`)
   - Source root: `worker/`
   - Python 3.13 runtime
   - UV package manager for fast dependency resolution
   - Web scraping dependencies (BeautifulSoup, requests, readability)
   - Celery worker with web content processing capabilities

3. **Flower Application** (`monitoring/`)
   - Source root: `monitoring/`
   - Python 3.13 runtime
   - UV package manager for fast dependency resolution
   - Minimal dependencies for monitoring dashboard
   - Flower monitoring with Celery inspection

### UV Package Manager

Each application uses UV for fast dependency installation:

```yaml
dependencies:
  python3:
    uv: "*"
hooks:
  build: |
    # Use uv for fast dependency installation
    uv sync --frozen
```

Benefits of UV:
- **Fast Installation**: 10-100x faster than pip
- **Reproducible Builds**: Locked dependencies with `uv.lock`
- **Isolated Environments**: Each app has its own dependencies
- **Better Caching**: Efficient dependency resolution

### Deployment Steps

1. **Connect Repository**: Link your Git repository to Upsun
2. **Configure Environment Variables**: Set required environment variables in Upsun dashboard
3. **Deploy**: Push to main branch to trigger deployment

Each application will:
- Create its own container
- Install only required dependencies using UV
- Use shared utilities from local copies
- Connect to the shared Redis service

### Upsun Services

- **API**: FastAPI web application (`https://api.{default}/`)
- **Worker**: Celery background processors (internal service)
- **Flower**: Monitoring dashboard (`https://monitor.{default}/`)
- **Redis**: Message broker service (internal service)

### Access URLs

- **API**: `https://api.{default}/`
- **API Documentation**: `https://api.{default}/docs`
- **Monitoring**: `https://monitor.{default}/`
- **Main**: `https://www.{default}/` (redirects to API)

### Environment Variables

Each application uses environment-based configuration:

```bash
# Required for all services
CELERY_BROKER_URL=redis://redis.internal:6379/0
CELERY_RESULT_BACKEND=redis://redis.internal:6379/0

# Required AI/ML API keys (for worker)
OPENAI_API_KEY=your_openai_key

# Web Scraping Configuration
STORAGE_PATH=/app/data
USER_AGENT=FastAPI-Celery-WebScraper/1.0
```

## 🔧 Development

### Adding New Tasks

1. **Define Task**: Add new task function in `worker/tasks.py`
2. **Add Processing Logic**: Create processing module in `worker/`
3. **Add API Endpoint**: Add new endpoint in `api/main.py`
4. **Update Tests**: Add tests in `test_system.py`

### Example New Task

```python
# worker/tasks.py
@app.task(bind=True, name='tasks.new_ai_task')
def new_ai_task(self, input_data: dict, task_id: str):
    # Implementation here
    pass

# api/main.py  
@app.post("/tasks/new-ai/process")
async def process_new_ai_task(request: NewAIRequest):
    # Implementation here
    pass
```

### Configuration Changes

Modify settings in `shared/config.py` and update environment variables accordingly.

### Logging

The application uses structured logging with JSON output. Logs include:

- Request/response logging
- Task execution tracking
- Error handling with context
- Performance metrics

## 🐛 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Ensure Redis is running: `docker-compose up redis -d`
   - Check REDIS_URL environment variable
   - Verify port 6379 is not in use by other services

2. **Tasks Not Processing**
   - Verify Celery worker is running
   - Check worker logs for errors
   - Ensure tasks are properly registered

3. **File Upload Errors**
   - Check file size limits (MAX_FILE_SIZE_MB)
   - Verify file types are supported
   - Check disk space

4. **High Memory Usage**
   - Reduce worker concurrency
   - Implement result expiration
   - Monitor task memory usage

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

### Health Checks

Monitor service health:

```bash
# API Health
curl http://localhost:8000/health

# Worker Stats  
curl http://localhost:8000/tasks/stats
```

## 📝 License

This project is a demonstration/example for Upsun deployment and is provided as-is for educational purposes.

## 🤝 Contributing

This is a demonstration project. For production use, consider:

- Adding authentication/authorization
- Implementing real AI models
- Adding database persistence
- Implementing rate limiting
- Adding comprehensive monitoring
- Setting up CI/CD pipelines

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Upsun Documentation](https://docs.upsun.com/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)
