import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import time
from celery import Celery

from shared import (
    api_config, setup_logging, get_logger,
    ValidationError, TaskProcessingError, BaseApplicationError, create_error_response,
    generate_uuid, Timer, log_api_request, log_api_response
)

# Setup logging
setup_logging("api", api_config.log_level, api_config.log_format)
logger = get_logger("api")

app = FastAPI(
    title="FastAPI Celery Web Content Processor",
    description="Async web content scraping and summarization using FastAPI + Celery",
    version="1.0.0",
    docs_url=api_config.docs_url,
    redoc_url=api_config.redoc_url,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config.cors_origins,
    allow_credentials=api_config.cors_allow_credentials,
    allow_methods=api_config.cors_allow_methods,
    allow_headers=api_config.cors_allow_headers,
)

# Celery app configuration
celery_app = Celery(
    "tasks",
    broker=api_config.celery_broker_url,
    backend=api_config.celery_result_backend
)

# Global exception handler
@app.exception_handler(BaseApplicationError)
async def application_exception_handler(request: Request, exc: BaseApplicationError):
    logger.error("Application error occurred", 
                error_code=exc.error_code.value,
                message=exc.message,
                details=exc.details,
                path=request.url.path,
                method=request.method)
    
    status_code_map = {
        "VALIDATION_ERROR": 400,
        "NOT_FOUND": 404,
        "UNAUTHORIZED": 401,
        "FORBIDDEN": 403,
        "RATE_LIMITED": 429,
        "TASK_TIMEOUT": 408,
        "EXTERNAL_SERVICE_UNAVAILABLE": 503,
    }
    
    status_code = status_code_map.get(exc.error_code.value, 500)
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(exc)
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error("HTTP error occurred",
                status_code=exc.status_code,
                detail=exc.detail,
                path=request.url.path,
                method=request.method)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "error_code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {"status_code": exc.status_code}
            },
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unexpected error occurred",
                error_type=type(exc).__name__,
                error_message=str(exc),
                path=request.url.path,
                method=request.method,
                exc_info=True)
    
    app_error = BaseApplicationError(
        message="An unexpected error occurred",
        cause=exc
    )
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(app_error)
    )

# Request/Response logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    log_api_request(
        method=request.method,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    try:
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        log_api_response(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration=duration
        )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Request processing failed",
                    method=request.method,
                    path=str(request.url.path),
                    duration=duration,
                    error=str(e))
        raise

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    submitted_at: float

class TaskResult(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None

class WebScrapeRequest(BaseModel):
    url: str
    summary_type: str = "standard"
    
    @validator('summary_type')
    def validate_summary_type(cls, v):
        allowed_types = ['brief', 'standard', 'detailed']
        if v not in allowed_types:
            raise ValueError(f'summary_type must be one of {allowed_types}')
        return v
    
    @validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip()

@app.get("/")
async def root():
    """Root endpoint returning basic API information"""
    return {
        "message": "FastAPI Celery Web Content Processor",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "web_scraping": "/tasks/web/summarize",
            "task_status": "/tasks/{task_id}/status",
            "task_result": "/tasks/{task_id}/result",
            "active_tasks": "/tasks"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed service status"""
    try:
        # Test Celery connection
        celery_status = "healthy"
        try:
            celery_app.control.inspect().stats()
        except Exception as e:
            celery_status = f"unhealthy: {str(e)}"
        
        return {
            "status": "healthy",
            "service": "api",
            "timestamp": time.time(),
            "dependencies": {
                "celery": celery_status
            },
            "config": {
                "environment": api_config.environment,
                "debug": api_config.debug
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "api",
                "error": str(e),
                "timestamp": time.time()
            }
        )

@app.post("/tasks/web/summarize", response_model=TaskResponse)
async def summarize_webpage(request: WebScrapeRequest):
    """Scrape and summarize web page content"""
    with Timer("web_scrape_task_queue") as timer:
        try:
            # Generate task ID
            task_id = generate_uuid()
            submission_time = time.time()
            
            # Queue web scraping task
            task = celery_app.send_task(
                "tasks.summarize_webpage",
                args=[request.url, task_id, request.summary_type],
                task_id=task_id
            )
            
            logger.info("Web scraping task queued",
                       task_id=task.id,
                       url=request.url,
                       summary_type=request.summary_type,
                       queue_time=timer.elapsed)
            
            return TaskResponse(
                task_id=task.id,
                status="queued",
                message=f"Web content summarization task queued successfully",
                submitted_at=submission_time
            )
            
        except ValidationError as e:
            logger.warning("Web scraping validation failed", error=str(e))
            raise e
        except Exception as e:
            logger.error("Failed to queue web scraping task",
                        error=str(e),
                        error_type=type(e).__name__,
                        url=request.url,
                        queue_time=timer.elapsed)
            raise TaskProcessingError(
                "Failed to queue web scraping task",
                task_name="summarize_webpage"
            )


@app.get("/tasks/{task_id}/status", response_model=TaskResult)
async def get_task_status(task_id: str):
    """Get status and results of a specific task"""
    try:
        # Validate task ID format
        if not task_id or len(task_id.strip()) == 0:
            raise ValidationError("Task ID cannot be empty")
        
        task_result = celery_app.AsyncResult(task_id)
        current_time = time.time()
        
        # Map Celery states to our response format
        state_mapping = {
            "PENDING": "pending",
            "RECEIVED": "queued",
            "STARTED": "processing",
            "PROGRESS": "processing",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "REVOKED": "cancelled",
            "RETRY": "retrying"
        }
        
        status = state_mapping.get(task_result.state, task_result.state.lower())
        
        result = TaskResult(
            task_id=task_id,
            status=status,
            updated_at=current_time
        )
        
        if task_result.state == "PENDING":
            # Task hasn't been received by worker yet
            result.result = None
            result.progress = None
        elif task_result.state in ["PROGRESS", "STARTED"]:
            # Task is being processed
            result.progress = task_result.info if isinstance(task_result.info, dict) else None
        elif task_result.state == "SUCCESS":
            # Task completed successfully
            result.result = task_result.result
            if isinstance(task_result.result, dict) and 'scraped_at' in task_result.result:
                result.created_at = task_result.result['scraped_at']
        elif task_result.state == "FAILURE":
            # Task failed
            result.error = str(task_result.info)
            if isinstance(task_result.info, dict) and 'scraped_at' in task_result.info:
                result.created_at = task_result.info['scraped_at']
        else:
            # Other states
            result.result = task_result.info if task_result.info else None
        
        logger.debug("Task status retrieved",
                    task_id=task_id,
                    status=status,
                    celery_state=task_result.state)
        
        return result
        
    except ValidationError as e:
        logger.warning("Task status validation failed", task_id=task_id, error=str(e))
        raise e
    except Exception as e:
        logger.error("Failed to get task status",
                    task_id=task_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise TaskProcessingError(
            "Failed to retrieve task status",
            task_id=task_id
        )

@app.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """Get detailed result from shared storage"""
    import json
    try:
        # Validate task ID format
        if not task_id or len(task_id.strip()) == 0:
            raise ValidationError("Task ID cannot be empty")
        
        # Try to read result from shared storage
        result_file = f"/app/data/results/{task_id}.json"
        if not os.path.exists(result_file):
            # Fall back to Celery result
            task_result = celery_app.AsyncResult(task_id)
            if task_result.state == "SUCCESS":
                return task_result.result
            else:
                raise HTTPException(status_code=404, detail="Result not found")
        
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        logger.info("Task result retrieved from storage", task_id=task_id)
        return result_data
        
    except ValidationError as e:
        logger.warning("Task result validation failed", task_id=task_id, error=str(e))
        raise e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task result",
                    task_id=task_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise TaskProcessingError(
            "Failed to retrieve task result",
            task_id=task_id
        )

@app.get("/tasks")
async def list_active_tasks():
    """List all active tasks across all workers"""
    try:
        with Timer("list_active_tasks") as timer:
            # Get active and scheduled tasks
            inspect = celery_app.control.inspect()
            
            active_tasks = inspect.active() or {}
            scheduled_tasks = inspect.scheduled() or {}
            reserved_tasks = inspect.reserved() or {}
            
            # Combine all task information
            all_tasks = {
                "active": active_tasks,
                "scheduled": scheduled_tasks,
                "reserved": reserved_tasks,
                "summary": {
                    "total_active": sum(len(tasks) for tasks in active_tasks.values()),
                    "total_scheduled": sum(len(tasks) for tasks in scheduled_tasks.values()),
                    "total_reserved": sum(len(tasks) for tasks in reserved_tasks.values()),
                    "workers": list(active_tasks.keys()),
                    "query_time": timer.elapsed,
                    "timestamp": time.time()
                }
            }
            
            logger.info("Active tasks retrieved",
                       total_active=all_tasks["summary"]["total_active"],
                       total_scheduled=all_tasks["summary"]["total_scheduled"],
                       workers=len(all_tasks["summary"]["workers"]),
                       query_time=timer.elapsed)
            
            return all_tasks
            
    except Exception as e:
        logger.error("Failed to get active tasks",
                    error=str(e),
                    error_type=type(e).__name__)
        raise TaskProcessingError("Failed to retrieve active tasks")

@app.get("/tasks/stats")
async def get_task_stats():
    """Get comprehensive task and worker statistics"""
    try:
        with Timer("get_task_stats") as timer:
            inspect = celery_app.control.inspect()
            
            stats = {
                "workers": inspect.stats() or {},
                "active_queues": inspect.active_queues() or {},
                "registered_tasks": inspect.registered() or {},
                "timestamp": time.time(),
                "query_time": timer.elapsed
            }
            
            # Calculate summary statistics
            worker_count = len(stats["workers"])
            total_tasks_completed = sum(
                worker_stats.get("total", {}).get("tasks.summarize_webpage", 0)
                for worker_stats in stats["workers"].values()
                if isinstance(worker_stats, dict) and "total" in worker_stats
            )
            
            stats["summary"] = {
                "worker_count": worker_count,
                "total_tasks_completed": total_tasks_completed,
                "available": worker_count > 0
            }
            
            logger.info("Task stats retrieved",
                       worker_count=worker_count,
                       total_completed=total_tasks_completed,
                       query_time=timer.elapsed)
            
            return stats
            
    except Exception as e:
        logger.error("Failed to get task stats",
                    error=str(e),
                    error_type=type(e).__name__)
        raise TaskProcessingError("Failed to retrieve task statistics")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application",
               host=api_config.host,
               port=api_config.port,
               environment=api_config.environment)
    uvicorn.run(
        "main:app",
        host=api_config.host,
        port=api_config.port,
        reload=api_config.debug,
        workers=1 if api_config.debug else api_config.workers,
        log_level=api_config.log_level.lower()
    )