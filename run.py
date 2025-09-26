#!/usr/bin/env python3
"""
Production startup script for Camp Power-Up
"""
import os
import sys
from app import app
from config import get_config

def main():
    """Start the application in production mode"""
    # Load production configuration
    config = get_config()
    app.config.from_object(config)
    
    # Get port from environment (for cloud platforms like Heroku, Railway)
    port = int(os.environ.get('PORT', 5002))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🏕️ Starting Camp Power-Up in {os.environ.get('FLASK_ENV', 'development')} mode")
    print(f"🌐 Server will be available at: http://{host}:{port}")
    
    # Run with appropriate settings based on environment
    if os.environ.get('FLASK_ENV') == 'production':
        # Production mode - use gunicorn in real deployment
        print("⚠️  For production, use: gunicorn -w 4 -b 0.0.0.0:5002 wsgi:app")
        app.run(host=host, port=port, debug=False)
    else:
        # Development mode
        app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    main()