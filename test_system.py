#!/usr/bin/env python3
"""
System testing script for FastAPI Celery AI Pipeline
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

import asyncio
import time
import json
import requests
from typing import Dict, Any, List
from shared import get_logger, Timer

logger = get_logger("system_test")

class SystemTester:
    """Test the complete multi-service architecture"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.test_results: List[Dict[str, Any]] = []
    
    def log_test_result(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Log and store test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✓ {test_name}: {message}", **details)
        else:
            logger.error(f"✗ {test_name}: {message}", **details)
    
    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        try:
            with Timer() as timer:
                response = self.session.get(f"{self.api_base_url}/health")
                
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "API Health Check",
                    True,
                    "API is healthy",
                    {
                        "status": data.get("status"),
                        "service": data.get("service"),
                        "response_time": timer.elapsed
                    }
                )
                return True
            else:
                self.log_test_result(
                    "API Health Check",
                    False,
                    f"API health check failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "API Health Check",
                False,
                f"Failed to connect to API: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_document_processing(self) -> bool:
        """Test document processing functionality"""
        try:
            # Test text summarization
            with Timer() as timer:
                payload = {
                    "text": "This is a test document for summarization. It contains multiple sentences to test the AI pipeline functionality. The system should be able to process this text and generate a meaningful summary.",
                    "task_type": "summarize"
                }
                
                response = self.session.post(
                    f"{self.api_base_url}/tasks/document/process",
                    json=payload
                )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                
                self.log_test_result(
                    "Document Summarization Request",
                    True,
                    "Document summarization task queued successfully",
                    {
                        "task_id": task_id,
                        "status": data.get("status"),
                        "queue_time": timer.elapsed
                    }
                )
                
                # Wait and check task status
                return self._wait_for_task_completion(task_id, "Document Summarization")
            else:
                self.log_test_result(
                    "Document Summarization Request",
                    False,
                    f"Failed to queue document processing task: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Document Processing",
                False,
                f"Document processing test failed: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_image_processing(self) -> bool:
        """Test image processing functionality"""
        try:
            # Create a simple test image (1x1 PNG)
            import base64
            from io import BytesIO
            
            # Simple 1x1 red pixel PNG
            png_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
            )
            
            with Timer() as timer:
                files = {
                    'file': ('test.png', BytesIO(png_data), 'image/png')
                }
                data = {'task_type': 'analyze'}
                
                response = self.session.post(
                    f"{self.api_base_url}/tasks/image/process",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                
                self.log_test_result(
                    "Image Processing Request",
                    True,
                    "Image processing task queued successfully",
                    {
                        "task_id": task_id,
                        "status": data.get("status"),
                        "queue_time": timer.elapsed
                    }
                )
                
                # Wait and check task status
                return self._wait_for_task_completion(task_id, "Image Processing")
            else:
                self.log_test_result(
                    "Image Processing Request",
                    False,
                    f"Failed to queue image processing task: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Image Processing",
                False,
                f"Image processing test failed: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_task_status_api(self) -> bool:
        """Test task status API"""
        try:
            with Timer() as timer:
                response = self.session.get(f"{self.api_base_url}/tasks")
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_test_result(
                    "Task Status API",
                    True,
                    "Task status API is working",
                    {
                        "response_time": timer.elapsed,
                        "active_tasks": data.get("summary", {}).get("total_active", 0),
                        "workers": len(data.get("summary", {}).get("workers", []))
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Task Status API",
                    False,
                    f"Task status API failed: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Task Status API",
                False,
                f"Task status API test failed: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_task_stats_api(self) -> bool:
        """Test task statistics API"""
        try:
            with Timer() as timer:
                response = self.session.get(f"{self.api_base_url}/tasks/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_test_result(
                    "Task Stats API",
                    True,
                    "Task statistics API is working",
                    {
                        "response_time": timer.elapsed,
                        "worker_count": data.get("summary", {}).get("worker_count", 0),
                        "available": data.get("summary", {}).get("available", False)
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Task Stats API",
                    False,
                    f"Task stats API failed: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Task Stats API",
                False,
                f"Task stats API test failed: {e}",
                {"error": str(e)}
            )
            return False
    
    def _wait_for_task_completion(self, task_id: str, test_name: str, timeout: int = 30) -> bool:
        """Wait for task completion and verify results"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.api_base_url}/tasks/{task_id}/status")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "completed":
                        self.log_test_result(
                            f"{test_name} Completion",
                            True,
                            "Task completed successfully",
                            {
                                "task_id": task_id,
                                "result": data.get("result", {}),
                                "execution_time": time.time() - start_time
                            }
                        )
                        return True
                    elif status == "failed":
                        self.log_test_result(
                            f"{test_name} Completion",
                            False,
                            "Task failed",
                            {
                                "task_id": task_id,
                                "error": data.get("error"),
                                "execution_time": time.time() - start_time
                            }
                        )
                        return False
                    elif status in ["pending", "processing", "queued"]:
                        # Still processing, wait a bit more
                        time.sleep(2)
                        continue
                    else:
                        logger.info(f"Task {task_id} status: {status}")
                        time.sleep(2)
                        continue
                else:
                    self.log_test_result(
                        f"{test_name} Status Check",
                        False,
                        f"Failed to check task status: {response.status_code}",
                        {"task_id": task_id, "status_code": response.status_code}
                    )
                    return False
                    
            except Exception as e:
                self.log_test_result(
                    f"{test_name} Status Check",
                    False,
                    f"Error checking task status: {e}",
                    {"task_id": task_id, "error": str(e)}
                )
                return False
        
        # Timeout
        self.log_test_result(
            f"{test_name} Completion",
            False,
            f"Task timed out after {timeout} seconds",
            {"task_id": task_id, "timeout": timeout}
        )
        return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all system tests"""
        logger.info("Starting comprehensive system tests...")
        
        tests = [
            ("API Health", self.test_api_health),
            ("Task Status API", self.test_task_status_api),
            ("Task Stats API", self.test_task_stats_api),
            ("Document Processing", self.test_document_processing),
            ("Image Processing", self.test_image_processing),
        ]
        
        total_tests = len(tests)
        passed_tests = 0
        
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test {test_name} raised exception: {e}")
        
        # Generate summary
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "test_results": self.test_results,
            "timestamp": time.time()
        }
        
        logger.info(f"Test Summary: {passed_tests}/{total_tests} tests passed ({summary['success_rate']:.1f}%)")
        
        return summary

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FastAPI Celery AI Pipeline")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", "-o", help="Output file for test results (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Run tests
    tester = SystemTester(args.api_url)
    results = tester.run_all_tests()
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Test results saved to {args.output}")
    
    # Exit with appropriate code
    if results["success_rate"] == 100:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"✗ {results['failed_tests']} tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()