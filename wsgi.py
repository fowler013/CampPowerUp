"""
WSGI entry point for Camp Power-Up application
==============================================

This file is used by production WSGI servers like Gunicorn
"""
import os
from app import app
from config import get_config

# Load configuration based on environment
config_class = get_config()
app.config.from_object(config_class)

# This is what gunicorn will look for
application = app

if __name__ == "__main__":
    # For testing the WSGI app directly
    app.run()