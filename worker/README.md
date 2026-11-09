# Celery Worker Service

This is the Celery worker component of the FastAPI + Celery AI pipeline.

## Features

- AI/ML task processing for documents and images
- Text summarization and document analysis
- Image analysis and captioning
- Scalable task processing with configurable concurrency
- Progress tracking and result storage

## Dependencies

This service includes all necessary dependencies for:
- Celery task queue processing
- AI/ML libraries (Transformers, PyTorch, OpenAI)
- Document processing (PDF, DOCX)
- Image processing (PIL, OpenCV)
- Configuration and logging utilities

## Usage

```bash
cd worker
pip install -e .
celery -A tasks worker --loglevel=info --concurrency=4
```