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

# Copy seeds
COPY backend/seeds seeds/

# Copy models (needed by seed scripts)
COPY backend/models/__init__.py models/
COPY backend/models/user models/user
COPY backend/models/workout models/workout
COPY backend/models/nutrition models/nutrition
COPY backend/models/calorie models/calorie
COPY backend/models/payment models/payment

# Copy db utilities
COPY backend/db db/

# Setup Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Run seed manager
CMD ["python", "seeds/seed_manager.py"]
