import os
import time
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
import structlog
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from readability import Document
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)

class WebScraper:
    """Web content scraping and processing"""
    
    def __init__(self, storage_path: str = "/app/data"):
        # Use local ./data directory if /app/data doesn't exist (for development)
        if not os.path.exists(storage_path) and storage_path == "/app/data":
            storage_path = "./data"
        
        self.storage_path = storage_path
        self.results_path = os.path.join(storage_path, "results")
        self.cache_path = os.path.join(storage_path, "cache")
        self.logs_path = os.path.join(storage_path, "logs")
        
        # Create directories (with error handling for read-only filesystems)
        for path in [self.results_path, self.cache_path, self.logs_path]:
            try:
                os.makedirs(path, exist_ok=True)
            except (OSError, PermissionError) as e:
                logger.warning("Could not create storage directory", 
                              path=path, error=str(e))
                # Continue without failing - directories might be created later or mounted
        
        # Setup OpenAI (optional for development)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None
            logger.warning("No OpenAI API key found - summarization will use fallback method")
        
        # Request session with retry strategy
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FastAPI-Celery-WebScraper/1.0 (+https://github.com/fastapi-celery)'
        })
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate URL format and accessibility"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"
            
            if parsed.scheme not in ['http', 'https']:
                return False, "Only HTTP and HTTPS URLs are supported"
            
            return True, "Valid URL"
            
        except Exception as e:
            return False, f"URL validation error: {str(e)}"
    
    def check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            user_agent = self.session.headers.get('User-Agent', '*')
            return rp.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.warning("Failed to check robots.txt, allowing scraping", 
                          url=url, error=str(e))
            return True  # Allow scraping if robots.txt check fails
    
    def get_url_hash(self, url: str) -> str:
        """Generate hash for URL caching"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_cached_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached content if available and fresh"""
        try:
            url_hash = self.get_url_hash(url)
            cache_file = os.path.join(self.cache_path, f"{url_hash}.json")
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Check if cache is still fresh (24 hours)
            cache_age = time.time() - cached.get('cached_at', 0)
            if cache_age < 24 * 3600:  # 24 hours
                logger.info("Using cached content", url=url, age_hours=cache_age/3600)
                return cached
            
            return None
            
        except Exception as e:
            logger.warning("Failed to retrieve cached content", url=url, error=str(e))
            return None
    
    def cache_content(self, url: str, content_data: Dict[str, Any]) -> None:
        """Cache scraped content"""
        try:
            # Ensure cache directory exists
            os.makedirs(self.cache_path, exist_ok=True)
            
            url_hash = self.get_url_hash(url)
            cache_file = os.path.join(self.cache_path, f"{url_hash}.json")
            
            cache_data = {
                **content_data,
                'cached_at': time.time(),
                'url': url
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning("Failed to cache content", url=url, error=str(e))
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_webpage(self, url: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Fetch webpage content with retries"""
        try:
            response = self.session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return False, "Not an HTML page", {}
            
            # Check content size (max 5MB)
            content_length = len(response.content)
            if content_length > 5 * 1024 * 1024:  # 5MB
                return False, "Content too large", {}
            
            metadata = {
                'final_url': response.url,
                'status_code': response.status_code,
                'content_type': content_type,
                'content_length': content_length,
                'encoding': response.encoding or 'utf-8'
            }
            
            return True, response.text, metadata
            
        except requests.exceptions.Timeout:
            return False, "Request timeout", {}
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}", {}
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", {}
    
    def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract readable content from HTML"""
        try:
            # Use readability-lxml for main content extraction
            doc = Document(html)
            
            # Also parse with BeautifulSoup for metadata
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract title
            title = doc.title() or ""
            if not title:
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else ""
            
            # Extract main content
            content = doc.summary()
            content_soup = BeautifulSoup(content, 'lxml')
            text_content = content_soup.get_text(separator='\n').strip()
            
            # Clean up text
            lines = [line.strip() for line in text_content.split('\n')]
            clean_lines = [line for line in lines if line and len(line) > 3]
            clean_text = '\n'.join(clean_lines)
            
            # Extract metadata
            meta_description = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag:
                meta_description = meta_tag.get('content', '').strip()
            
            # Calculate reading stats
            word_count = len(clean_text.split())
            reading_time_minutes = max(1, round(word_count / 200))  # Average reading speed
            
            return {
                'title': title,
                'content': clean_text,
                'meta_description': meta_description,
                'word_count': word_count,
                'reading_time_minutes': reading_time_minutes,
                'character_count': len(clean_text)
            }
            
        except Exception as e:
            logger.error("Content extraction failed", url=url, error=str(e))
            # Fallback: basic text extraction
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            title = soup.title.string if soup.title else ""
            text = soup.get_text(separator='\n')
            
            # Clean up
            lines = [line.strip() for line in text.split('\n')]
            clean_lines = [line for line in lines if line and len(line) > 3]
            clean_text = '\n'.join(clean_lines[:500])  # Limit fallback content
            
            return {
                'title': title,
                'content': clean_text,
                'meta_description': "",
                'word_count': len(clean_text.split()),
                'reading_time_minutes': max(1, round(len(clean_text.split()) / 200)),
                'character_count': len(clean_text)
            }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_summary(self, content: str, title: str, summary_type: str = "standard") -> Dict[str, str]:
        """Generate summary using OpenAI"""
        # If no OpenAI client, use fallback immediately
        if not self.openai_client:
            return self._fallback_summary(content, summary_type)
        
        try:
            # Configure prompts based on summary type
            prompts = {
                "brief": {
                    "system": "You are a concise summarizer. Create very brief, one-sentence summaries.",
                    "max_tokens": 50,
                    "instruction": "Summarize this article in one clear, informative sentence:"
                },
                "standard": {
                    "system": "You are a skilled summarizer. Create clear, informative summaries that capture the main points.",
                    "max_tokens": 200,
                    "instruction": "Summarize this article in 2-3 sentences, capturing the key points:"
                },
                "detailed": {
                    "system": "You are a comprehensive summarizer. Create detailed summaries that cover all important aspects.",
                    "max_tokens": 500,
                    "instruction": "Create a detailed summary of this article, covering all main points and key details:"
                }
            }
            
            prompt_config = prompts.get(summary_type, prompts["standard"])
            
            # Truncate content if too long (max ~3000 words for GPT context)
            words = content.split()
            if len(words) > 3000:
                content = ' '.join(words[:3000]) + "..."
            
            # Create prompt
            user_message = f"{prompt_config['instruction']}\n\nTitle: {title}\n\nContent: {content}"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt_config["system"]},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=prompt_config["max_tokens"],
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            return {
                "summary": summary,
                "model": "gpt-3.5-turbo",
                "summary_type": summary_type,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error("OpenAI summarization failed", error=str(e))
            return self._fallback_summary(content, summary_type)
    
    def _fallback_summary(self, content: str, summary_type: str = "standard") -> Dict[str, str]:
        """Generate fallback summary without OpenAI"""
        # Simple extractive summary based on type
        word_limits = {
            "brief": 1,      # 1 sentence
            "standard": 3,   # 3 sentences  
            "detailed": 6    # 6 sentences
        }
        
        sentence_count = word_limits.get(summary_type, 3)
        sentences = content.split('. ')[:sentence_count]
        fallback_summary = '. '.join(sentences)
        
        # Ensure proper ending punctuation
        if fallback_summary and not fallback_summary.endswith('.'):
            fallback_summary += '.'
        
        return {
            "summary": fallback_summary or "Summary not available due to processing error.",
            "model": "fallback",
            "summary_type": summary_type,
            "tokens_used": 0
        }
    
    def save_result(self, task_id: str, result_data: Dict[str, Any]) -> None:
        """Save processing result to shared storage"""
        try:
            # Ensure results directory exists
            os.makedirs(self.results_path, exist_ok=True)
            
            result_file = os.path.join(self.results_path, f"{task_id}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            # Update index
            self.update_results_index(task_id, result_data)
            
            logger.info("Result saved", task_id=task_id, file=result_file)
            
        except Exception as e:
            logger.error("Failed to save result", task_id=task_id, error=str(e))
    
    def update_results_index(self, task_id: str, result_data: Dict[str, Any]) -> None:
        """Update results index for quick lookup"""
        try:
            index_file = os.path.join(self.results_path, "index.json")
            
            # Load existing index
            index = {}
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            
            # Add new entry
            index[task_id] = {
                "url": result_data.get("url"),
                "title": result_data.get("title"),
                "status": result_data.get("status"),
                "created_at": result_data.get("scraped_at"),
                "word_count": result_data.get("metadata", {}).get("word_count", 0)
            }
            
            # Save updated index
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning("Failed to update results index", task_id=task_id, error=str(e))
    
    def process_url(self, url: str, task_id: str, summary_type: str = "standard") -> Dict[str, Any]:
        """Main processing function: scrape URL and generate summary"""
        start_time = time.time()
        
        try:
            # Validate URL
            is_valid, validation_message = self.validate_url(url)
            if not is_valid:
                return {
                    "task_id": task_id,
                    "url": url,
                    "status": "failed",
                    "error": validation_message,
                    "scraped_at": time.time()
                }
            
            # Check robots.txt
            if not self.check_robots_txt(url):
                return {
                    "task_id": task_id,
                    "url": url,
                    "status": "failed",
                    "error": "Scraping not allowed by robots.txt",
                    "scraped_at": time.time()
                }
            
            # Check cache first
            cached_content = self.get_cached_content(url)
            if cached_content and summary_type in cached_content.get('summaries', {}):
                logger.info("Using cached summary", url=url, task_id=task_id)
                
                result = {
                    "task_id": task_id,
                    "url": url,
                    "title": cached_content.get('title'),
                    "summary": cached_content['summaries'][summary_type]['summary'],
                    "metadata": {
                        **cached_content.get('metadata', {}),
                        "processing_time_seconds": time.time() - start_time,
                        "from_cache": True
                    },
                    "status": "completed",
                    "scraped_at": time.time()
                }
                
                self.save_result(task_id, result)
                return result
            
            # Fetch webpage
            success, html_content, fetch_metadata = self.fetch_webpage(url)
            if not success:
                return {
                    "task_id": task_id,
                    "url": url,
                    "status": "failed",
                    "error": html_content,  # Error message
                    "scraped_at": time.time()
                }
            
            # Extract content
            extracted_content = self.extract_content(html_content, url)
            
            # Generate summary
            summary_data = self.generate_summary(
                extracted_content['content'], 
                extracted_content['title'], 
                summary_type
            )
            
            # Prepare result
            result = {
                "task_id": task_id,
                "url": url,
                "title": extracted_content['title'],
                "summary": summary_data['summary'],
                "metadata": {
                    "word_count": extracted_content['word_count'],
                    "reading_time_minutes": extracted_content['reading_time_minutes'],
                    "character_count": extracted_content['character_count'],
                    "summary_type": summary_type,
                    "ai_model": summary_data['model'],
                    "tokens_used": summary_data['tokens_used'],
                    "processing_time_seconds": time.time() - start_time,
                    "from_cache": False,
                    **fetch_metadata
                },
                "status": "completed",
                "scraped_at": time.time()
            }
            
            # Cache content with summary
            cache_data = {
                'title': extracted_content['title'],
                'content': extracted_content['content'],
                'metadata': extracted_content,
                'summaries': {
                    summary_type: summary_data
                }
            }
            self.cache_content(url, cache_data)
            
            # Save result
            self.save_result(task_id, result)
            
            logger.info("URL processing completed", 
                       task_id=task_id, 
                       url=url, 
                       processing_time=result['metadata']['processing_time_seconds'])
            
            return result
            
        except Exception as e:
            logger.error("URL processing failed", task_id=task_id, url=url, error=str(e))
            
            error_result = {
                "task_id": task_id,
                "url": url,
                "status": "failed",
                "error": f"Processing error: {str(e)}",
                "metadata": {
                    "processing_time_seconds": time.time() - start_time
                },
                "scraped_at": time.time()
            }
            
            self.save_result(task_id, error_result)
            return error_result