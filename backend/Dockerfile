# ── Backend Dockerfile ──────────────────────────────────────────
# FastAPI + Celery + ML dependencies
# Python 3.11 slim for smaller image size
# ────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# curl → used by healthcheck
# build-essential → needed for some Python packages (e.g. scipy, faiss-cpu)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# (Member 3 creates requirements.txt in ./backend/)
COPY requirements-dev.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default command — starts FastAPI with hot reload for development
# Member 3: change to gunicorn for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
