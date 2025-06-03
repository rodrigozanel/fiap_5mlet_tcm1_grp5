# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Build arguments for version information
ARG VERSION=1.0.0
ARG BUILD_DATE=unknown
ARG ENVIRONMENT=production

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    APP_VERSION=${VERSION} \
    APP_BUILD_DATE=${BUILD_DATE} \
    APP_ENVIRONMENT=${ENVIRONMENT}

# Add labels for image metadata
LABEL version="${VERSION}" \
      build_date="${BUILD_DATE}" \
      environment="${ENVIRONMENT}" \
      maintainer="Flask Web Scraping API Team" \
      description="API Flask para extração de dados vitivinícolas do site da Embrapa"

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY utils.py .
COPY simple_version.py .

# Copy directories (only if they exist)
COPY cache/ ./cache/
COPY apis/ ./apis/

# Create data directory if needed
RUN mkdir -p data/fallback

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"] 