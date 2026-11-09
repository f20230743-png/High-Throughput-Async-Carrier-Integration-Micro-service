from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")

app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", f"redis://{redis_host}:{redis_port}/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", f"redis://{redis_host}:{redis_port}/0")
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)