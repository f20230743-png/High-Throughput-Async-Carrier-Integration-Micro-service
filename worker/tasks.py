import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from celery import Celery
from dotenv import load_dotenv
import structlog
from typing import Optional, Dict, Any
import time

from web_scraper import WebScraper
from shared import worker_config, setup_logging, get_logger, log_task_execution

load_dotenv()

# Setup logging
setup_logging("worker", worker_config.log_level, worker_config.log_format)
logger = get_logger("worker")

app = Celery(
    "tasks",
    broker=worker_config.celery_broker_url,
    backend=worker_config.celery_result_backend
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=worker_config.worker_prefetch_multiplier,
    result_expires=worker_config.result_expires,
    task_time_limit=worker_config.task_timeout_seconds,
    task_soft_time_limit=worker_config.task_timeout_seconds - 30,
)

# Initialize web scraper
scraper = WebScraper()

def update_task_progress(task, current: int, total: int, message: str = "Processing..."):
    """Update task progress state"""
    task.update_state(
        state='PROGRESS',
        meta={
            'current': current,
            'total': total,
            'status': message,
            'progress_percent': int((current / total) * 100) if total > 0 else 0,
            'timestamp': time.time()
        }
    )

@app.task(bind=True, name='tasks.summarize_webpage')
def summarize_webpage(self, url: str, task_id: str, summary_type: str = "standard"):
    """Process webpage URL and generate summary"""
    
    with log_task_execution("summarize_webpage", task_id):
        try:
            logger.info("Starting webpage summarization", task_id=task_id, url=url, summary_type=summary_type)
            
            update_task_progress(self, 1, 4, "Validating URL...")
            
            # Validate URL first
            is_valid, validation_message = scraper.validate_url(url)
            if not is_valid:
                logger.warning("URL validation failed", task_id=task_id, url=url, reason=validation_message)
                raise ValueError(f"Invalid URL: {validation_message}")
            
            update_task_progress(self, 2, 4, "Fetching webpage...")
            
            # Check robots.txt
            if not scraper.check_robots_txt(url):
                logger.warning("Robots.txt disallows scraping", task_id=task_id, url=url)
                raise ValueError("Scraping not allowed by robots.txt")
            
            update_task_progress(self, 3, 4, "Extracting content and generating summary...")
            
            # Process URL using scraper
            result = scraper.process_url(url, task_id, summary_type)
            
            update_task_progress(self, 4, 4, "Task completed")
            
            if result['status'] == 'failed':
                logger.error("Webpage summarization failed", 
                            task_id=task_id, 
                            url=url, 
                            error=result.get('error'))
                raise ValueError(result.get('error', 'Unknown processing error'))
            
            logger.info("Webpage summarization completed", 
                       task_id=task_id, 
                       url=url,
                       title=result.get('title', 'No title')[:50],
                       word_count=result.get('metadata', {}).get('word_count', 0),
                       processing_time=result.get('metadata', {}).get('processing_time_seconds', 0))
            
            return result
            
        except Exception as e:
            logger.error("Webpage summarization failed", task_id=task_id, url=url, error=str(e))
            
            # Save error result
            error_result = {
                "task_id": task_id,
                "url": url,
                "status": "failed",
                "error": str(e),
                "scraped_at": time.time()
            }
            scraper.save_result(task_id, error_result)
            
            raise


if __name__ == '__main__':
    app.start()