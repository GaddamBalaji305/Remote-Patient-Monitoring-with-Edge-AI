# Edge AI Pipeline Dockerfile for Remote Patient Monitoring
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Edge AI source code and shared modules
COPY edge_ai /app/edge_ai
COPY backend /app/backend
COPY scripts /app/scripts

# Run Edge AI integrated pipeline runner
CMD ["python", "edge_ai/run.py"]
