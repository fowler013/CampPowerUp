# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port (Railway will set the PORT environment variable)
EXPOSE 8080

# Health check - Railway will handle health checks
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:$PORT/ || exit 1

# Command to run the application - use registration form directly
CMD ["sh", "-c", "cd registration_form && gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120 app:app"]