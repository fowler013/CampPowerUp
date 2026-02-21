#!/bin/bash

# Railway startup script for Camp Power-Up
# Handles PORT environment variable and starts gunicorn

# Set default port if not provided by Railway
export PORT=${PORT:-5001}

echo "🚀 Starting Camp Power-Up on port $PORT"
echo "📧 Email configured for: $CAMP_EMAIL"
echo "🗄️  Database URL: ${DATABASE_URL:-sqlite}"

# Start gunicorn with proper configuration
exec python -m gunicorn \
  --bind "0.0.0.0:$PORT" \
  --workers 2 \
  --timeout 300 \
  --worker-class sync \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --preload \
  --access-logfile - \
  --error-logfile - \
  registration_form.app:app