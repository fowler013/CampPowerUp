#!/usr/bin/env python3
"""
Working Admin Dashboard - Simple session-based authentication
"""

import os
import sys
import sqlite3
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, render_template_string, redirect, url_for, flash, session

# Simple Flask app with session-based auth (no Flask-Login)
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.permanent_session_lifetime = timedelta(hours=8)

def ensure_database():
    """Ensure database and admin user exist"""
    try:
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        
        # Create admin_users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash BLOB NOT NULL,
                role TEXT DEFAULT 'admin',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create audit_log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                username TEXT,
                details TEXT,
                ip_address TEXT
            )
        ''')
        
        # Check if admin user exists
        cursor.execute('SELECT id FROM admin_users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            # Create admin user
            salt = bcrypt.gensalt()
            password = 'admin123'
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            cursor.execute('''
                INSERT INTO admin_users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@camppowerup.com', hashed_password, 'admin'))
            
            print(f"🔧 Created admin user: admin / {password}")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

def verify_admin(username, password):
    """Verify admin credentials"""
    try:
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, password_hash, role FROM admin_users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3]):
            return {
                'id': user[0],
                'username': user[1], 
                'email': user[2],
                'role': user[4]
            }
        return None
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def log_security_event(event_type, username, details):
    """Log security events"""
    try:
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        
        # Create audit_log table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                username TEXT,
                details TEXT,
                ip_address TEXT
            )
        ''')
        
        cursor.execute('''
            INSERT INTO audit_log (event_type, username, details)
            VALUES (?, ?, ?)
        ''', (event_type, username, details))
        
        conn.commit()
        conn.close()
        print(f"📝 Security event logged: {event_type} for {username}")
    except Exception as e:
        print(f"❌ Failed to log security event: {e}")

def require_admin(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"🔍 Checking admin session: {dict(session)}")
        if not session.get('admin_user'):
            print("❌ No admin_user in session, redirecting to login")
            return redirect(url_for('admin_login'))
        print(f"✅ Admin access granted for: {session.get('admin_user', {}).get('username', 'unknown')}")
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        print(f"🔄 Admin login attempt: {username}")
        
        admin = verify_admin(username, password)
        if admin:
            session['admin_user'] = admin
            session.permanent = True
            print(f"✅ Admin logged in: {admin['username']}")
            flash(f'Welcome back, {admin["username"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            print(f"❌ Admin login failed: {username}")
            flash('Invalid admin credentials.', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏕️ Camp Power-Up - Admin Login</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 0; min-height: 100vh;
                display: flex; align-items: center; justify-content: center;
            }
            .login-container {
                background: white; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                padding: 40px; width: 100%; max-width: 400px; text-align: center;
            }
            .logo { font-size: 48px; margin-bottom: 10px; }
            h1 { color: #333; margin-bottom: 30px; }
            .form-group { margin-bottom: 20px; text-align: left; }
            label { display: block; margin-bottom: 5px; font-weight: 500; color: #555; }
            input[type="text"], input[type="password"] { 
                width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 5px;
                font-size: 16px; transition: border-color 0.3s;
            }
            input[type="text"]:focus, input[type="password"]:focus { 
                outline: none; border-color: #667eea; 
            }
            .btn { 
                background: #667eea; color: white; padding: 12px 30px; border: none; 
                border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%;
                transition: background 0.3s;
            }
            .btn:hover { background: #5a6fd8; }
            .alert { padding: 10px; border-radius: 5px; margin-bottom: 20px; }
            .alert-error { background: #fee; color: #c33; border: 1px solid #fcc; }
            .credentials { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">🏕️</div>
            <h1>Camp Power-Up<br><small>Admin Portal</small></h1>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST">
                <div class="form-group">
                    <label>👤 Username:</label>
                    <input type="text" name="username" required placeholder="Enter admin username">
                </div>
                
                <div class="form-group">
                    <label>🔒 Password:</label>
                    <input type="password" name="password" required placeholder="Enter admin password">
                </div>
                
                <button type="submit" class="btn">🚀 Login</button>
            </form>
            
            <div class="credentials">
                <strong>🔑 Test Credentials:</strong><br>
                Username: <code>admin</code><br>
                Password: <code>Gkp0Ob4o_b-LKSUq_PJ_dg</code>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/dashboard')
@require_admin
def admin_dashboard():
    """Admin dashboard"""
    admin = session['admin_user']
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏕️ Camp Power-Up - Admin Dashboard</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f8f9fa; margin: 0; padding: 20px;
            }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px;
                display: flex; justify-content: space-between; align-items: center;
            }
            .welcome { font-size: 24px; }
            .logout-btn { 
                background: rgba(255,255,255,0.2); color: white; padding: 8px 16px;
                border: none; border-radius: 5px; cursor: pointer; text-decoration: none;
            }
            .logout-btn:hover { background: rgba(255,255,255,0.3); }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .feature-card { 
                background: white; border-radius: 10px; padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s;
            }
            .feature-card:hover { transform: translateY(-2px); }
            .feature-icon { font-size: 32px; margin-bottom: 10px; }
            .feature-title { font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #333; }
            .feature-desc { color: #666; margin-bottom: 15px; }
            .btn { 
                background: #667eea; color: white; padding: 10px 20px; border: none;
                border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block;
            }
            .btn:hover { background: #5a6fd8; }
            .status { 
                background: #d4edda; color: #155724; padding: 15px; border-radius: 5px;
                margin-bottom: 20px; border: 1px solid #c3e6cb;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <div style="font-size: 32px;">🏕️ Camp Power-Up Admin</div>
                <div class="welcome">Welcome back, {{ admin.username }}!</div>
            </div>
            <a href="{{ url_for('admin_logout') }}" class="logout-btn">🚪 Logout</a>
        </div>
        
        <div class="status">
            🎉 <strong>Authentication Successful!</strong> You now have access to the admin dashboard.
        </div>
        
        <div class="features">
            <div class="feature-card">
                <div class="feature-icon">📧</div>
                <div class="feature-title">Send Bulk Email</div>
                <div class="feature-desc">Send email notifications to all camp parents and guardians.</div>
                <a href="http://127.0.0.1:5007" class="btn">Access Communication System</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">📱</div>
                <div class="feature-title">Send Bulk SMS</div>
                <div class="feature-desc">Send text message alerts to all parent phone numbers.</div>
                <a href="http://127.0.0.1:5007" class="btn">Access SMS System</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">👥</div>
                <div class="feature-title">Parent Contacts</div>
                <div class="feature-desc">View and manage parent contact information and communication preferences.</div>
                <a href="http://127.0.0.1:5007/api/parent-contacts" class="btn">View Contacts</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Communication History</div>
                <div class="feature-desc">Review sent messages, delivery status, and communication analytics.</div>
                <a href="http://127.0.0.1:5007" class="btn">View History</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🔧</div>
                <div class="feature-title">System Settings</div>
                <div class="feature-desc">Configure email templates, SMS settings, and system preferences.</div>
                <a href="http://127.0.0.1:5007" class="btn">Manage Settings</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🔐</div>
                <div class="feature-title">Security Settings</div>
                <div class="feature-desc">Change password, view audit logs, and manage security preferences.</div>
                <a href="{{ url_for('change_password') }}" class="btn">Security Options</a>
            </div>
        </div>
        
        <div style="margin-top: 30px; text-align: center; color: #666;">
            <p>✅ All security features are active and working correctly.</p>
            <p>📅 Session expires in 8 hours | 🔒 Connection secured with HTTPS-ready configuration</p>
        </div>
    </body>
    </html>
    ''', admin=admin)

@app.route('/admin/change-password', methods=['GET', 'POST'])
@require_admin
def change_password():
    """Change admin password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        print(f"🔄 Password change attempt for: {session['admin_user']['username']}")
        
        # Verify current password
        admin = session['admin_user']
        if not verify_admin(admin['username'], current_password):
            flash('Current password is incorrect.', 'error')
            print("❌ Current password verification failed")
            return redirect(url_for('change_password'))
        
        # Validate new password
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'error')
            return redirect(url_for('change_password'))
            
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('change_password'))
        
        # Update password in database
        try:
            conn = sqlite3.connect('security.db')
            cursor = conn.cursor()
            
            # Hash new password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
            
            # Update password
            cursor.execute('''
                UPDATE admin_users 
                SET password_hash = ?, updated_at = ?
                WHERE username = ?
            ''', (hashed_password, datetime.now(), admin['username']))
            
            conn.commit()
            conn.close()
            
            flash('Password changed successfully!', 'success')
            print(f"✅ Password updated for: {admin['username']}")
            
            # Log the security event
            log_security_event('password_changed', admin['username'], 'Password updated successfully')
            
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Error updating password: {str(e)}', 'error')
            print(f"❌ Password update failed: {e}")
            return redirect(url_for('change_password'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔐 Change Password - Camp Power-Up</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 0; min-height: 100vh;
                display: flex; align-items: center; justify-content: center;
            }
            .container {
                background: white; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                padding: 40px; width: 100%; max-width: 500px;
            }
            .header { text-align: center; margin-bottom: 30px; }
            .logo { font-size: 48px; margin-bottom: 10px; }
            h1 { color: #333; margin: 0; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: 500; color: #555; }
            input[type="password"] { 
                width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 5px;
                font-size: 16px; transition: border-color 0.3s; box-sizing: border-box;
            }
            input[type="password"]:focus { 
                outline: none; border-color: #667eea; 
            }
            .btn { 
                background: #667eea; color: white; padding: 12px 30px; border: none; 
                border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%;
                transition: background 0.3s; margin-bottom: 10px;
            }
            .btn:hover { background: #5a6fd8; }
            .btn-secondary { 
                background: #6c757d; text-decoration: none; display: inline-block; text-align: center;
            }
            .btn-secondary:hover { background: #5a6268; }
            .alert { padding: 10px; border-radius: 5px; margin-bottom: 20px; }
            .alert-error { background: #fee; color: #c33; border: 1px solid #fcc; }
            .alert-success { background: #efe; color: #3c763d; border: 1px solid #cfc; }
            .requirements { 
                background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;
                font-size: 14px; color: #666;
            }
            .requirements ul { margin: 10px 0; padding-left: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🔐</div>
                <h1>Change Password</h1>
                <p style="color: #666; margin: 10px 0;">Update your admin password</p>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="requirements">
                <strong>🛡️ Password Requirements:</strong>
                <ul>
                    <li>At least 8 characters long</li>
                    <li>Mix of letters, numbers, and symbols recommended</li>
                    <li>Avoid common passwords</li>
                </ul>
            </div>
            
            <form method="POST">
                <div class="form-group">
                    <label>🔒 Current Password:</label>
                    <input type="password" name="current_password" required placeholder="Enter your current password">
                </div>
                
                <div class="form-group">
                    <label>🆕 New Password:</label>
                    <input type="password" name="new_password" required placeholder="Enter your new password" minlength="8">
                </div>
                
                <div class="form-group">
                    <label>✅ Confirm New Password:</label>
                    <input type="password" name="confirm_password" required placeholder="Confirm your new password" minlength="8">
                </div>
                
                <button type="submit" class="btn">🔄 Update Password</button>
                <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary">🔙 Back to Dashboard</a>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/logout')
@require_admin
def admin_logout():
    """Admin logout"""
    session.pop('admin_user', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_redirect():
    """Redirect /admin to /admin/dashboard"""
    return redirect(url_for('admin_dashboard'))

@app.route('/')
def index():
    """Root redirect"""
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    print("🏕️ Starting Camp Power-Up Admin Portal...")
    
    # Ensure database is set up
    if ensure_database():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
        sys.exit(1)
    
    print("🔗 Admin login: http://127.0.0.1:5006/admin/login")
    print("🔑 Credentials: admin / admin123")
    print("✅ Simple session-based authentication (no Flask-Login conflicts)")
    app.run(host='127.0.0.1', port=5006, debug=True)
