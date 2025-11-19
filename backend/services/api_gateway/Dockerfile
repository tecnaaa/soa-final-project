FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared services/utilities
COPY backend/services services/

# Copy API Gateway main file
COPY backend/api_gateway.py .

# Copy db utilities
COPY backend/db db/

# Setup Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the API gateway
CMD ["uvicorn", "api_gateway:app", "--host", "0.0.0.0", "--port", "8001"]