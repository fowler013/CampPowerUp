#!/usr/bin/env python3
"""
Minimal login test to bypass Flask-Login property issues
"""
import os
import sys
from datetime import datetime, timedelta
import sqlite3
import bcrypt
from flask import Flask, request, render_template_string, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect

# Minimal User class that should work with Flask-Login
class SimpleUser(UserMixin):
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username  
        self.email = email
        self.role = role
        self.is_active = True
        self.is_authenticated = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)

# Create Flask app
app = Flask(__name__)
app.secret_key = 'test-secret-key'
# Temporarily disable CSRF for testing
# csrf = CSRFProtect(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    try:
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return SimpleUser(row[0], row[1], row[2], row[3])
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

def verify_password(username, password):
    """Simple password verification"""
    try:
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, password_hash, role FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row and bcrypt.checkpw(password.encode('utf-8'), row[3].encode('utf-8')):
            return SimpleUser(row[0], row[1], row[2], row[4])
        return None
    except Exception as e:
        print(f"Password verification error: {e}")
        return None

@app.route('/test-login', methods=['GET', 'POST'])
def test_login():
    """Test login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        print(f"🔄 Testing login for: {username}")
        
        user = verify_password(username, password)
        if user:
            print(f"✅ User verified: {user.username}")
            login_user(user)
            print(f"✅ User logged in successfully")
            return redirect(url_for('test_dashboard'))
        else:
            print(f"❌ Login failed for: {username}")
            flash('Invalid credentials', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Login</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input[type="text"], input[type="password"] { width: 100%; padding: 8px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h2>🔐 Test Login</h2>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="error">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <!-- <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/> -->
            
            <div class="form-group">
                <label>Username:</label>
                <input type="text" name="username" required>
            </div>
            
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" required>
            </div>
            
            <button type="submit">Login</button>
        </form>
        
        <p><strong>Test Credentials:</strong></p>
        <p>Username: admin<br>Password: Gkp0Ob4o_b-LKSUq_PJ_dg</p>
    </body>
    </html>
    ''')

@app.route('/test-dashboard')
@login_required
def test_dashboard():
    """Test dashboard"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .success { color: green; font-size: 18px; }
            .info { background: #f0f8ff; padding: 15px; border-left: 4px solid #007cba; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>🎉 Login Successful!</h1>
        
        <div class="success">
            ✅ Authentication is working correctly!
        </div>
        
        <div class="info">
            <strong>Logged in as:</strong> {{ current_user.username }}<br>
            <strong>Email:</strong> {{ current_user.email }}<br>
            <strong>Role:</strong> {{ current_user.role }}<br>
            <strong>User ID:</strong> {{ current_user.id }}
        </div>
        
        <p><a href="/logout">🚪 Logout</a></p>
        <p><a href="http://127.0.0.1:5004">🔙 Back to Main App</a></p>
    </body>
    </html>
    ''')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('test_login'))

@app.route('/')
def index():
    """Root redirect"""
    return redirect(url_for('test_login'))

if __name__ == '__main__':
    print("🔧 Starting minimal login test server...")
    print("📍 Test login at: http://127.0.0.1:5005/test-login")
    print("🔑 Credentials: admin / Gkp0Ob4o_b-LKSUq_PJ_dg")
    app.run(host='127.0.0.1', port=5005, debug=True)
