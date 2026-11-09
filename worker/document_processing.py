import os
import time
import httpx
from typing import Dict, List, Optional, Any
import structlog
from io import BytesIO
import tempfile
import asyncio

# Document processing imports
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
except ImportError:
    openai = None

logger = structlog.get_logger()

class DocumentProcessor:
    """Enhanced document processing with multiple AI models support"""
    
    def __init__(self):
        self.openai_enabled = openai is not None and os.getenv("OPENAI_API_KEY")
        
    async def extract_text_from_url(self, url: str, timeout: int = 30) -> str:
        """Extract text from a URL"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=timeout)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                
                if 'text/html' in content_type:
                    return self._extract_html_text(response.text)
                elif 'text/plain' in content_type:
                    return response.text
                elif 'application/pdf' in content_type:
                    return self._extract_pdf_text(response.content)
                else:
                    return response.text
                    
        except Exception as e:
            logger.error("Failed to extract text from URL", url=url, error=str(e))
            raise
    
    def _extract_html_text(self, html_content: str) -> str:
        """Extract plain text from HTML content"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except ImportError:
            # Fallback: simple HTML tag removal
            import re
            return re.sub(r'<[^>]+>', '', html_content)
    
    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF content"""
        if not PdfReader:
            raise ImportError("PyPDF2 is required for PDF processing")
            
        try:
            pdf_file = BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
                
            return text.strip()
            
        except Exception as e:
            logger.error("Failed to extract PDF text", error=str(e))
            raise
    
    def _extract_docx_text(self, docx_content: bytes) -> str:
        """Extract text from DOCX content"""
        if not Document:
            raise ImportError("python-docx is required for DOCX processing")
            
        try:
            with tempfile.NamedTemporaryFile() as tmp_file:
                tmp_file.write(docx_content)
                tmp_file.flush()
                
                doc = Document(tmp_file.name)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                    
                return text.strip()
                
        except Exception as e:
            logger.error("Failed to extract DOCX text", error=str(e))
            raise
    
    async def summarize_with_ai(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """Summarize text using AI models"""
        try:
            if self.openai_enabled:
                return await self._summarize_with_openai(text, max_length)
            else:
                return self._summarize_extractive(text, max_length)
                
        except Exception as e:
            logger.error("AI summarization failed, using extractive method", error=str(e))
            return self._summarize_extractive(text, max_length)
    
    async def _summarize_with_openai(self, text: str, max_length: int) -> Dict[str, Any]:
        """Summarize using OpenAI API"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Summarize the following text in approximately {max_length} words. Focus on key points and main ideas."},
                    {"role": "user", "content": text[:4000]}  # Limit input to avoid token limits
                ],
                max_tokens=max_length * 2,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            return {
                "summary": summary,
                "method": "openai_gpt35",
                "confidence": 0.9,
                "word_count": len(summary.split())
            }
            
        except Exception as e:
            logger.error("OpenAI summarization failed", error=str(e))
            raise
    
    def _summarize_extractive(self, text: str, max_length: int) -> Dict[str, Any]:
        """Simple extractive summarization"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not sentences:
            return {
                "summary": text[:max_length * 5],
                "method": "truncation",
                "confidence": 0.5,
                "word_count": len(text.split())
            }
        
        # Simple scoring based on sentence position and length
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            if len(words) < 5 or len(words) > 50:  # Filter very short/long sentences
                continue
                
            # Simple scoring: position weight + length weight
            position_score = 1 - (i / len(sentences))  # Earlier sentences score higher
            length_score = min(len(words) / 20, 1)  # Prefer moderate length
            score = position_score * 0.7 + length_score * 0.3
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and select top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        selected_sentences = []
        current_length = 0
        target_words = max_length
        
        for sentence, score in scored_sentences:
            sentence_words = len(sentence.split())
            if current_length + sentence_words <= target_words:
                selected_sentences.append(sentence)
                current_length += sentence_words
            
            if current_length >= target_words * 0.8:  # Allow 80% of target
                break
        
        summary = '. '.join(selected_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return {
            "summary": summary or text[:max_length * 5],
            "method": "extractive",
            "confidence": 0.7,
            "word_count": len(summary.split()) if summary else 0
        }
    
    def analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure and properties"""
        lines = text.split('\n')
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()
        
        # Character analysis
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        
        # Word analysis
        word_count = len(words)
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Sentence analysis
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Paragraph analysis
        paragraph_count = len(paragraphs)
        avg_paragraph_length = sentence_count / paragraph_count if paragraph_count > 0 else 0
        
        # Reading time estimation (average 200 words per minute)
        estimated_reading_time = max(1, round(word_count / 200))
        
        # Simple complexity scoring
        complexity_factors = []
        if avg_word_length > 6:
            complexity_factors.append("long_words")
        if avg_sentence_length > 20:
            complexity_factors.append("long_sentences")
        if word_count > 1000:
            complexity_factors.append("lengthy_document")
        
        complexity_score = len(complexity_factors)
        
        return {
            "structure": {
                "lines": len(lines),
                "paragraphs": paragraph_count,
                "sentences": sentence_count,
                "words": word_count,
                "characters": char_count,
                "characters_no_spaces": char_count_no_spaces
            },
            "averages": {
                "word_length": round(avg_word_length, 2),
                "sentence_length": round(avg_sentence_length, 2),
                "paragraph_length": round(avg_paragraph_length, 2)
            },
            "readability": {
                "estimated_reading_time_minutes": estimated_reading_time,
                "complexity_score": complexity_score,
                "complexity_factors": complexity_factors,
                "readability_level": "easy" if complexity_score == 0 else "medium" if complexity_score == 1 else "hard"
            }
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[Dict[str, Any]]:
        """Extract keywords using simple frequency analysis"""
        # Simple stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        # Clean and tokenize
        import re
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [word for word in words if word not in stopwords]
        
        # Count frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and select top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        keywords = []
        for word, freq in sorted_words[:max_keywords]:
            # Simple relevance score based on frequency and word length
            relevance = min(1.0, freq / len(words) * 100)
            keywords.append({
                "keyword": word,
                "frequency": freq,
                "relevance_score": round(relevance, 3)
            })
        
        return keywords