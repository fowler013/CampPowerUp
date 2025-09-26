#!/usr/bin/env python3
"""
Railway-specific WSGI entry point for Camp Power-Up Registration Form
====================================================================

This file is specifically designed for Railway deployment.
"""
import os
import sys

# Add the registration_form directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'registration_form'))

# Import the Flask app from registration_form directory
from app import app

# This is what gunicorn will look for
application = app

if __name__ == "__main__":
    # For testing this WSGI entry point directly
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)