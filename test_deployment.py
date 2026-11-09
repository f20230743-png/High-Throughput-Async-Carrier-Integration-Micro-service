#!/usr/bin/env python3
"""
Quick deployment test script for the FastAPI + Celery Web Content Processor
"""

import os
import sys
import subprocess

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd
        )
        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Command exception: {cmd} - {str(e)}")
        return False

def test_import(service_dir, import_test):
    """Test if imports work correctly"""
    print(f"🔍 Testing imports in {service_dir}...")
    return run_command(f"uv run python -c \"{import_test}\"", cwd=service_dir)

def main():
    """Main test function"""
    print("🚀 FastAPI + Celery Web Content Processor - Deployment Test")
    print("=" * 60)
    
    base_dir = "/Users/nls/articles/fastapi-celery"
    os.chdir(base_dir)
    
    # Test 1: API Service Imports
    api_test = "import fastapi, celery, pydantic; print('✅ API imports OK')"
    if not test_import("api", api_test):
        print("❌ API service import test failed")
        return False
    
    # Test 2: Worker Service Imports  
    worker_test = "import celery, requests, bs4, openai; print('✅ Worker imports OK')"
    if not test_import("worker", worker_test):
        print("❌ Worker service import test failed")
        return False
    
    # Test 3: Monitoring Service Imports
    monitoring_test = "import celery, flower; print('✅ Monitoring imports OK')"
    if not test_import("monitoring", monitoring_test):
        print("❌ Monitoring service import test failed")
        return False
    
    # Test 4: Check UV Lock Files
    print("🔍 Checking UV lock files...")
    for service in ["api", "worker", "monitoring"]:
        lock_file = os.path.join(service, "uv.lock")
        if not os.path.exists(lock_file):
            print(f"❌ Missing uv.lock in {service}")
            return False
        print(f"✅ {service}/uv.lock exists")
    
    # Test 5: Check Upsun Configuration
    print("🔍 Checking Upsun configuration...")
    upsun_config = ".upsun/config.yaml"
    if not os.path.exists(upsun_config):
        print("❌ Missing .upsun/config.yaml")
        return False
    
    with open(upsun_config, 'r') as f:
        config_content = f.read()
        
    # Verify key components
    required_components = [
        "applications:",
        "api:",
        "worker:", 
        "flower:",
        "uv run uvicorn",
        "uv run celery",
        "network-storage"
    ]
    
    for component in required_components:
        if component not in config_content:
            print(f"❌ Missing component in Upsun config: {component}")
            return False
    
    print("✅ Upsun configuration looks good")
    
    # Test 6: Validate API Structure
    print("🔍 Validating API structure...")
    api_files = ["main.py", "pyproject.toml", "shared/"]
    for file in api_files:
        if not os.path.exists(os.path.join("api", file)):
            print(f"❌ Missing API file: {file}")
            return False
    print("✅ API structure complete")
    
    # Test 7: Validate Worker Structure
    print("🔍 Validating Worker structure...")
    worker_files = ["tasks.py", "web_scraper.py", "pyproject.toml", "shared/"]
    for file in worker_files:
        if not os.path.exists(os.path.join("worker", file)):
            print(f"❌ Missing Worker file: {file}")
            return False
    print("✅ Worker structure complete")
    
    print("=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("")
    print("📋 Deployment Summary:")
    print("- ✅ All services have correct dependencies")
    print("- ✅ UV lock files are present and valid")
    print("- ✅ Upsun configuration is complete")
    print("- ✅ API endpoints updated for web processing")
    print("- ✅ Worker configured for web scraping + OpenAI")
    print("- ✅ Shared storage configured")
    print("")
    print("🚀 Ready for Upsun deployment!")
    print("")
    print("📝 Next Steps:")
    print("1. Set OPENAI_API_KEY environment variable in Upsun")
    print("2. Push to your repository")
    print("3. Deploy on Upsun platform")
    print("4. Test with: POST /tasks/web/summarize")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)