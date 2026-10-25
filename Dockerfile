# ==========================================================
# SlothPFN - Zero-Effort Tabular AI Agent
# Production Multi-Platform Dockerfile
# ==========================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

# Install minimal OS dependencies required for PyTorch, LightGBM, and audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements specification first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application directories and files
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY sample_data/ ./sample_data/
COPY drop_data/ ./drop_data/

# Expose default application port
EXPOSE 8000

# Health check to ensure FastAPI container is alive and responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Start Uvicorn server in production mode
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
