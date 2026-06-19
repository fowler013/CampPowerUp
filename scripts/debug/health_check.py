#!/usr/bin/env python3
"""
Simple health check script for Railway deployment
===============================================

This creates a minimal Flask app that can help diagnose deployment issues.
"""
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>Camp Power-Up - Health Check</h1>
    <p>✅ Basic Flask app is working</p>
    <p>Environment: Railway</p>
    <p>Python path is accessible</p>
    <a href="/health">Health Check</a>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "service": "camp-power-up-registration"}, 200

if __name__ == "__main__":
    # Get port from environment variable, Railway sets this
    port_env = os.environ.get('PORT', '8080')
    print(f"🚀 Starting health check app on port {port_env}")
    
    try:
        port = int(port_env)
    except ValueError:
        print(f"❌ Invalid PORT value: {port_env}, using 8080")
        port = 8080
    
    print(f"🌐 Server starting on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)