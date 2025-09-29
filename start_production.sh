#!/bin/bash
# Production startup script for Railway deployment

echo "🚀 Starting Camp Power-Up Production Server"
echo "Environment: ${RAILWAY_ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"

# Set production environment variables
export FLASK_ENV=${FLASK_ENV:-production}
export DEBUG=${DEBUG:-false}

# Start with gunicorn for production
if [ "$FLASK_ENV" = "production" ]; then
    echo "🔒 Starting PRODUCTION server with Gunicorn..."
    exec gunicorn --bind 0.0.0.0:${PORT:-8000} \
                  --workers 2 \
                  --timeout 300 \
                  --access-logfile - \
                  --error-logfile - \
                  --log-level info \
                  registration_form.app:app
else
    echo "🔧 Starting STAGING server..."
    exec gunicorn --bind 0.0.0.0:${PORT:-8000} \
                  --workers 1 \
                  --timeout 300 \
                  --reload \
                  --access-logfile - \
                  --error-logfile - \
                  --log-level debug \
                  registration_form.app:app
fi