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

# Copy user models
COPY backend/models/__init__.py models/
COPY backend/models/user models/user

# Copy db utilities
COPY backend/db db/

# Copy seeds
COPY backend/seeds seeds/

# Setup Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port
EXPOSE 8002

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting users service..."\n\
uvicorn services.users.main:app --host 0.0.0.0 --port 8002\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Run the entrypoint script
CMD ["/app/entrypoint.sh"]
