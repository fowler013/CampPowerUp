#!/usr/bin/env python3
"""
Railway-specific WSGI entry point for Camp Power-Up Registration Form
====================================================================

This file is specifically designed for Railway deployment with enhanced
error handling and logging. Startup output must never include configuration
values, environment values or exception messages, because they can contain
secrets such as SECRET_KEY, ADMIN_PASSWORD or DATABASE_URL.
"""
import os
import sys
import traceback

MIN_SECRET_KEY_LENGTH = 32


def describe_secret_key_status():
    """Describe how SECRET_KEY is configured without revealing its value."""
    value = os.environ.get('SECRET_KEY')
    if value is None:
        return "not set - registration app is using its insecure development fallback key"
    if not value:
        return "set but empty - sessions will not work"
    if len(value) < MIN_SECRET_KEY_LENGTH:
        return f"set, shorter than the recommended {MIN_SECRET_KEY_LENGTH} characters"
    return f"set ({MIN_SECRET_KEY_LENGTH}+ characters)"


print("🚀 Starting Railway WSGI entry point...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Add the registration_form directory to Python path
registration_form_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'registration_form')
sys.path.insert(0, registration_form_path)
print(f"Added to Python path: {registration_form_path}")

try:
    # Import the Flask app from registration_form directory
    print("📦 Importing Flask app from registration_form...")
    from app import app
    print("✅ Flask app imported successfully!")

    print(f"Flask app name: {app.name}")
    print(f"SECRET_KEY status: {describe_secret_key_status()}")
    print(f"Available routes: {sorted(rule.rule for rule in app.url_map.iter_rules())}")

    # This is what gunicorn will look for
    application = app
    print("✅ WSGI application ready!")

except Exception as import_error:
    # Exception messages can embed configuration values, so log only the type and code locations.
    print(f"❌ Error importing Flask app: {type(import_error).__name__}", file=sys.stderr)
    print("".join(traceback.format_tb(import_error.__traceback__)), file=sys.stderr)

    # Create a minimal error app so Railway doesn't crash
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def error():
        return "Registration service is temporarily unavailable.", 503

    @app.route('/health')
    def health():
        return "unhealthy", 503

    application = app
    print("⚠️ Created minimal error app to prevent crash")

if __name__ == "__main__":
    # For testing this WSGI entry point directly
    port = int(os.environ.get('PORT', 8080))
    print(f"🌐 Starting development server on port {port}")
    application.run(host='0.0.0.0', port=port, debug=False)
