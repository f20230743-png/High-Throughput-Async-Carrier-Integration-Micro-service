#!/usr/bin/env python3
"""
Flower monitoring dashboard startup script - Simplified version
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Start Flower using command line interface"""
    
    # Set up environment variables
    port = os.getenv('PORT', '5555')
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')
    broker_url = os.getenv('CELERY_BROKER_URL', f'redis://{redis_host}:{redis_port}/0')
    
    # Ensure database directory exists for local development
    db_dir = '/app/db'
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
        except (OSError, PermissionError):
            print(f"Warning: Could not create {db_dir}, using local directory")
    
    print(f"Starting Flower monitoring dashboard on port {port}")
    print(f"Broker: {broker_url}")
    
    # Use celery flower command directly (with corrected argument order)
    cmd = [
        'celery',
        f'--broker={broker_url}',
        '-A', 'tasks', 
        'flower',
        f'--port={port}',
        '--address=0.0.0.0',
        '--conf=flowerconfig.py',
    ]
    
    # Add optional basic auth if configured
    basic_auth = os.getenv('FLOWER_BASIC_AUTH')
    if basic_auth:
        cmd.append(f'--basic_auth={basic_auth}')
    
    # Add URL prefix if configured
    url_prefix = os.getenv('FLOWER_URL_PREFIX')
    if url_prefix:
        cmd.append(f'--url_prefix={url_prefix}')
    
    try:
        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down Flower monitoring dashboard...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Failed to start Flower: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()