import os
from dotenv import load_dotenv

load_dotenv()

# Flower configuration - Use environment variables with fallbacks
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")
broker = os.getenv("CELERY_BROKER_URL", f"redis://{redis_host}:{redis_port}/0")
backend = os.getenv("CELERY_RESULT_BACKEND", f"redis://{redis_host}:{redis_port}/0")

# Basic authentication (optional) - Flower expects a list for this one
basic_auth = os.getenv("FLOWER_BASIC_AUTH", "admin:admin").split(",")

# Server configuration
port = int(os.getenv("PORT", 5555))
address = "0.0.0.0"

# Enable auto-refresh
auto_refresh = True
refresh_interval = 30000  # 30 seconds

# Task columns to display (comma-separated string for Flower)
tasks_columns = 'name,uuid,state,args,kwargs,result,received,started,timestamp,runtime,worker,exchange,routing_key,retries,revoked'

# Worker columns to display (comma-separated string for Flower)
worker_columns = 'name,status,active,processed,load_avg,pool,pool_size'

# URL prefix (useful for reverse proxy setups)
url_prefix = os.getenv("FLOWER_URL_PREFIX", "")

# Persistent mode
persistent = False

# No database needed for non-persistent mode

# Maximum number of tasks to keep in memory
max_tasks = 10000

# Enable/disable task purging
purge_offline_workers = 300  # Purge offline workers after 5 minutes

# Logging configuration
logging = 'INFO'

# Custom task formatters
def format_task(task):
    """Custom task formatting for display"""
    if task.name:
        # Simplify task names for display
        task_name = task.name.split('.')[-1]  # Get last part of task name
        return task_name
    return task.uuid[:8]  # Show first 8 chars of UUID if no name

# Task runtime formatting
def format_time(timestamp):
    """Format timestamp for display"""
    if timestamp:
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'

# Custom CSS (optional)
custom_css = """
.navbar-brand {
    font-weight: bold;
    color: #2c3e50 !important;
}

.table-hover tbody tr:hover {
    background-color: #f8f9fa;
}

.badge {
    font-size: 0.8em;
    padding: 0.3em 0.6em;
}

.task-success {
    background-color: #d4edda;
    border-color: #c3e6cb;
}

.task-failure {
    background-color: #f8d7da;
    border-color: #f5c6cb;
}

.task-pending {
    background-color: #fff3cd;
    border-color: #ffeaa7;
}
"""