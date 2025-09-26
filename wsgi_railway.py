#!/usr/bin/env python3
"""
Railway-specific WSGI entry point for Camp Power-Up Registration Form
====================================================================

This file is specifically designed for Railway deployment with enhanced
error handling and logging.
"""
import os
import sys

print("🚀 Starting Railway WSGI entry point...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Add the registration_form directory to Python path
registration_form_path = os.path.join(os.path.dirname(__file__), 'registration_form')
sys.path.insert(0, registration_form_path)
print(f"Added to Python path: {registration_form_path}")

try:
    # Import the Flask app from registration_form directory
    print("📦 Importing Flask app from registration_form...")
    from app import app
    print("✅ Flask app imported successfully!")
    
    # Print some debug info
    print(f"Flask app name: {app.name}")
    print(f"Flask app config: {dict(app.config)}")
    print(f"Available routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
    
    # This is what gunicorn will look for
    application = app
    print("✅ WSGI application ready!")
    
except Exception as e:
    print(f"❌ Error importing Flask app: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal error app so Railway doesn't crash
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return f"Import Error: {e}", 500
        
    @app.route('/health')  
    def health():
        return "Import failed", 500
        
    application = app
    print("⚠️ Created minimal error app to prevent crash")

if __name__ == "__main__":
    # For testing this WSGI entry point directly
    port = int(os.environ.get('PORT', 8080))
    print(f"🌐 Starting development server on port {port}")
    application.run(host='0.0.0.0', port=port, debug=False)