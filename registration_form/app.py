#!/usr/bin/env python3
import os
from flask import Flask, jsonify

# Create Flask app - this is what Railway/gunicorn looks for
app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
    <head><title>Camp Power-Up Registration</title></head>
    <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
    <h1>🏕️ Camp Power-Up 2025 Registration</h1>
    <p><strong>System is ONLINE!</strong> Registration form is being restored.</p>
    <p>For assistance: fowler0613@gmail.com</p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Camp Power-Up is online!"})

# Make sure the app is accessible for gunicorn
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))