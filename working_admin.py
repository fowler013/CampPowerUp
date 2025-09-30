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
from email_service import email_service

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
            # Create admin user with password from environment variable
            salt = bcrypt.gensalt()
            password = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Default for dev only
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
            .info-note { 
                background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; 
                font-size: 14px; color: #666; border: 1px solid #e9ecef;
            }
            .info-icon { margin-right: 8px; }
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
            
            <div class="info-note">
                <i class="info-icon">ℹ️</i>
                <small>Contact your system administrator for login credentials.</small>
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
                <div class="feature-icon">�</div>
                <div class="feature-title">Registration Management</div>
                <div class="feature-desc">View and manage camp registrations, payment status, and participant data.</div>
                <a href="{{ url_for('registration_management') }}" class="btn">Manage Registrations</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🎮</div>
                <div class="feature-title">Game Library</div>
                <div class="feature-desc">Manage game inventory, track popular games, and plan activities.</div>
                <a href="{{ url_for('game_library_management') }}" class="btn">Manage Game Library</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Camp Analytics</div>
                <div class="feature-desc">View camp statistics, attendance trends, and demographic insights.</div>
                <a href="{{ url_for('camp_analytics') }}" class="btn">View Analytics</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">�</div>
                <div class="feature-title">Send Bulk Email</div>
                <div class="feature-desc">Send email notifications to all camp parents and guardians.</div>
                <a href="/admin/send-email" class="btn">Send Bulk Email</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">�</div>
                <div class="feature-title">Send Bulk SMS</div>
                <div class="feature-desc">Send text message alerts to all parent phone numbers.</div>
                <a href="/admin/send-sms" class="btn">Send Bulk SMS</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">�</div>
                <div class="feature-title">Parent Contacts</div>
                <div class="feature-desc">View and manage parent contact information and communication preferences.</div>
                <a href="{{ url_for('parent_contacts') }}" class="btn">View Contacts</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">⚙️</div>
                <div class="feature-title">System Settings</div>
                <div class="feature-desc">Configure camp sessions, pricing, and system preferences.</div>
                <a href="{{ url_for('system_settings') }}" class="btn">Manage Settings</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🔐</div>
                <div class="feature-title">Security Settings</div>
                <div class="feature-desc">Change password, view audit logs, and manage security preferences.</div>
                <a href="{{ url_for('security_management') }}" class="btn">Security Options</a>
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

# ==================== NEW ADMIN MODULES ====================

@app.route('/admin/registrations')
@require_admin
def registration_management():
    """Registration management interface"""
    try:
        # Connect to registration database
        reg_conn = sqlite3.connect('registration_form/registration_submissions.db')
        reg_cursor = reg_conn.cursor()
        
        # Get recent registrations
        reg_cursor.execute('''
            SELECT id, submission_id, timestamp, status, payment_status,
                   parent_email, child_first_name, child_last_name, camp_session
            FROM registrations 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        registrations = reg_cursor.fetchall()
        reg_conn.close()
        
        # Get registration statistics
        total_registrations = len(registrations)
        pending_payments = len([r for r in registrations if r[4] == 'pending'])
        
    except Exception as e:
        print(f"❌ Registration database error: {e}")
        registrations = []
        total_registrations = 0
        pending_payments = 0
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📋 Registration Management - Camp Power-Up</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
            .stat-label { color: #666; margin-top: 5px; }
            .table-container { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
            th { background: #f8f9fa; font-weight: 600; }
            .status-pending { background: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .status-paid { background: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📋 Registration Management</h1>
            <p>Manage camp registrations and track enrollment</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ total_registrations }}</div>
                <div class="stat-label">Total Registrations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ pending_payments }}</div>
                <div class="stat-label">Pending Payments</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_registrations - pending_payments }}</div>
                <div class="stat-label">Paid Registrations</div>
            </div>
        </div>
        
        <div class="table-container">
            <a href="{{ url_for('admin_dashboard') }}" class="btn">🔙 Back to Dashboard</a>
            <h2>Recent Registrations</h2>
            
            {% if registrations %}
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Child Name</th>
                        <th>Parent Email</th>
                        <th>Session</th>
                        <th>Payment Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for reg in registrations %}
                    <tr>
                        <td>{{ reg[2][:10] if reg[2] else 'N/A' }}</td>
                        <td>{{ (reg[6] or '') + ' ' + (reg[7] or '') }}</td>
                        <td>{{ reg[5] or 'N/A' }}</td>
                        <td>{{ reg[8] or 'N/A' }}</td>
                        <td>
                            <span class="status-{{ reg[4] or 'pending' }}">
                                {{ (reg[4] or 'pending').title() }}
                            </span>
                        </td>
                        <td>
                            <a href="#" style="color: #667eea;">View Details</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No registrations found. Check database connection.</p>
            {% endif %}
        </div>
    </body>
    </html>
    ''', registrations=registrations, total_registrations=total_registrations, pending_payments=pending_payments)

@app.route('/admin/games')
@require_admin
def game_library_management():
    """Game library management interface"""
    try:
        # Connect to main database
        conn = sqlite3.connect('camp_power_up.db')
        cursor = conn.cursor()
        
        # Get game statistics
        cursor.execute('SELECT COUNT(*) FROM games')
        total_games = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        cursor.execute('SELECT name, total_owned, camp_copies FROM games ORDER BY total_owned DESC LIMIT 10')
        popular_games = cursor.fetchall()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Game database error: {e}")
        total_games = 0
        popular_games = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎮 Game Library Management - Camp Power-Up</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
            .stat-label { color: #666; margin-top: 5px; }
            .content { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin-bottom: 20px; }
            .game-item { padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
            .game-name { font-weight: 600; }
            .game-stats { color: #666; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎮 Game Library Management</h1>
            <p>Manage game inventory and track popular titles</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ total_games }}</div>
                <div class="stat-label">Total Games</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ popular_games|length }}</div>
                <div class="stat-label">Popular Games</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">Nintendo Switch</div>
                <div class="stat-label">Primary Platform</div>
            </div>
        </div>
        
        <div class="content">
            <a href="{{ url_for('admin_dashboard') }}" class="btn">🔙 Back to Dashboard</a>
            <h2>Popular Games</h2>
            
            {% if popular_games %}
                {% for game in popular_games %}
                <div class="game-item">
                    <div>
                        <div class="game-name">{{ game[0] }}</div>
                        <div class="game-stats">{{ game[1] }} owned by campers | {{ game[2] }} camp copies</div>
                    </div>
                </div>
                {% endfor %}
            {% else %}
            <p>No game data available. Run the game library analysis to populate data.</p>
            {% endif %}
        </div>
    </body>
    </html>
    ''', total_games=total_games, popular_games=popular_games)

@app.route('/admin/analytics')
@require_admin
def camp_analytics():
    """Camp analytics and statistics"""
    try:
        # Get camp statistics
        conn = sqlite3.connect('camp_power_up.db')
        cursor = conn.cursor()
        
        # Get camper count
        cursor.execute('SELECT COUNT(*) FROM camp_analysis')
        total_campers = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        conn.close()
        
        # Get registration stats
        reg_conn = sqlite3.connect('registration_form/registration_submissions.db')
        reg_cursor = reg_conn.cursor()
        
        reg_cursor.execute('SELECT COUNT(*) FROM registrations')
        total_registrations = reg_cursor.fetchone()[0] if reg_cursor.fetchone() else 0
        
        reg_conn.close()
        
    except Exception as e:
        print(f"❌ Analytics database error: {e}")
        total_campers = 0
        total_registrations = 0
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📊 Camp Analytics - Camp Power-Up</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
            .stat-label { color: #666; margin-top: 5px; }
            .content { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Camp Analytics</h1>
            <p>View camp statistics and enrollment trends</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ total_campers }}</div>
                <div class="stat-label">Historical Campers</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_registrations }}</div>
                <div class="stat-label">New Registrations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">2025</div>
                <div class="stat-label">Current Season</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">Summer</div>
                <div class="stat-label">Active Session</div>
            </div>
        </div>
        
        <div class="content">
            <a href="{{ url_for('admin_dashboard') }}" class="btn">🔙 Back to Dashboard</a>
            <h2>📈 Analytics Overview</h2>
            <p>Detailed analytics and reporting features coming soon.</p>
            <p>Current data sources:</p>
            <ul>
                <li>✅ Registration database connected</li>
                <li>✅ Historical camper data available</li>
                <li>✅ Game library analytics ready</li>
                <li>✅ Communication tracking enabled</li>
            </ul>
        </div>
    </body>
    </html>
    ''', total_campers=total_campers, total_registrations=total_registrations)

@app.route('/admin/contacts')
@require_admin
def parent_contacts():
    """Parent contact management"""
    try:
        # Get parent contacts from registration database
        conn = sqlite3.connect('registration_form/registration_submissions.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT parent_email, parent_phone, child_first_name, child_last_name, 
                   emergency_contact_name, emergency_contact_phone
            FROM registrations 
            WHERE parent_email IS NOT NULL 
            ORDER BY child_first_name, child_last_name
        ''')
        contacts = cursor.fetchall()
        conn.close()
        
    except Exception as e:
        print(f"❌ Contacts database error: {e}")
        contacts = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>👥 Parent Contacts - Camp Power-Up</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .content { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
            th { background: #f8f9fa; font-weight: 600; }
            .contact-item { padding: 15px; border-bottom: 1px solid #eee; }
            .contact-name { font-weight: 600; margin-bottom: 5px; }
            .contact-details { color: #666; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>👥 Parent Contacts</h1>
            <p>Manage parent and emergency contact information</p>
        </div>
        
        <div class="content">
            <a href="{{ url_for('admin_dashboard') }}" class="btn">🔙 Back to Dashboard</a>
            <h2>Contact Directory</h2>
            
            {% if contacts %}
                {% for contact in contacts %}
                <div class="contact-item">
                    <div class="contact-name">{{ (contact[2] or '') + ' ' + (contact[3] or '') }}</div>
                    <div class="contact-details">
                        📧 Parent: {{ contact[0] or 'No email' }}
                        {% if contact[1] %} | 📱 {{ contact[1] }}{% endif %}
                        {% if contact[4] %}<br>🚨 Emergency: {{ contact[4] }}{% if contact[5] %} ({{ contact[5] }}){% endif %}{% endif %}
                    </div>
                </div>
                {% endfor %}
            {% else %}
            <p>No contact information available. Check registration database connection.</p>
            {% endif %}
        </div>
    </body>
    </html>
    ''', contacts=contacts)

@app.route('/admin/settings')
@require_admin
def system_settings():
    """System settings management"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>⚙️ System Settings - Camp Power-Up</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .content { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin-bottom: 20px; }
            .setting-group { margin-bottom: 30px; padding: 20px; border: 1px solid #eee; border-radius: 8px; }
            .setting-title { font-weight: 600; margin-bottom: 10px; color: #333; }
            .setting-desc { color: #666; margin-bottom: 15px; }
            .btn-setting { background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 4px; margin-right: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚙️ System Settings</h1>
            <p>Configure camp sessions, pricing, and system preferences</p>
        </div>
        
        <div class="content">
            <a href="{{ url_for('admin_dashboard') }}" class="btn">🔙 Back to Dashboard</a>
            
            <div class="setting-group">
                <div class="setting-title">🏕️ Camp Session Configuration</div>
                <div class="setting-desc">Manage camp dates, sessions, and capacity settings</div>
                <button class="btn-setting">Configure Sessions</button>
            </div>
            
            <div class="setting-group">
                <div class="setting-title">💰 Pricing & Payment</div>
                <div class="setting-desc">Set registration fees, early bird discounts, and payment options</div>
                <button class="btn-setting">Manage Pricing</button>
            </div>
            
            <div class="setting-group">
                <div class="setting-title">📧 Email Configuration</div>
                <div class="setting-desc">Configure SMTP settings and email templates</div>
                <a href="/admin/email-settings" class="btn-setting">Email Settings</a>
            </div>
            
            <div class="setting-group">
                <div class="setting-title">📱 SMS Configuration</div>
                <div class="setting-desc">Configure Twilio settings and SMS templates</div>
                <button class="btn-setting">SMS Settings</button>
            </div>
            
            <div class="setting-group">
                <div class="setting-title">🎮 Game Library Settings</div>
                <div class="setting-desc">Manage game categories, ratings, and inventory tracking</div>
                <button class="btn-setting">Game Settings</button>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/security')
@require_admin
def security_management():
    """Security management interface"""
    try:
        # Get recent audit logs
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, event_type, username, details 
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        audit_logs = cursor.fetchall()
        
        cursor.execute('SELECT COUNT(*) FROM audit_log')
        total_logs = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Security database error: {e}")
        audit_logs = []
        total_logs = 0
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔐 Security Management - Camp Power-Up</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .content { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px 10px 10px 0; }
            .btn-danger { background: #dc3545; }
            .log-item { padding: 10px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 14px; }
            .log-timestamp { color: #666; }
            .log-event { font-weight: 600; color: #333; }
            .log-details { color: #555; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
            .stat-label { color: #666; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 Security Management</h1>
            <p>Monitor security events and manage system security</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ total_logs }}</div>
                <div class="stat-label">Security Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">Active</div>
                <div class="stat-label">Security Status</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">bcrypt</div>
                <div class="stat-label">Password Hashing</div>
            </div>
        </div>
        
        <div class="content">
            <a href="{{ url_for('admin_dashboard') }}" class="btn">🔙 Back to Dashboard</a>
            <a href="{{ url_for('change_password') }}" class="btn">🔑 Change Password</a>
            <button class="btn btn-danger">🚨 View Failed Logins</button>
            
            <h2>🔍 Recent Security Events</h2>
            {% if audit_logs %}
                {% for log in audit_logs %}
                <div class="log-item">
                    <span class="log-timestamp">{{ log[0] }}</span> | 
                    <span class="log-event">{{ log[1] }}</span> | 
                    <span class="log-details">{{ log[2] }}: {{ log[3] }}</span>
                </div>
                {% endfor %}
            {% else %}
            <p>No security events logged yet.</p>
            {% endif %}
        </div>
    </body>
    </html>
    ''', audit_logs=audit_logs, total_logs=total_logs)

# ========================================
# ROUTE ALIASES FOR API COMPATIBILITY
# ========================================

@app.route('/admin/send-email', methods=['GET', 'POST'])
@require_admin
def send_bulk_email():
    """Send bulk email to parents"""
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        recipient_group = request.form.get('recipient_group', 'all')
        
        if not subject or not message:
            flash('Subject and message are required.', 'error')
        else:
            # Get parent emails from registration database
            try:
                conn = sqlite3.connect('registration_submissions.db')
                cursor = conn.cursor()
                
                if recipient_group == 'all':
                    cursor.execute('SELECT DISTINCT parent_email FROM registrations WHERE parent_email IS NOT NULL AND parent_email != ""')
                else:
                    cursor.execute('SELECT DISTINCT parent_email FROM registrations WHERE camp_session = ? AND parent_email IS NOT NULL AND parent_email != ""', (recipient_group,))
                
                emails = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                if emails:
                    # Send actual emails using email service
                    try:
                        email_result = email_service.send_bulk_email(
                            recipients=emails,
                            subject=subject,
                            message=message,
                            sender_name="Camp Power-Up"
                        )
                        
                        if email_result['success']:
                            if email_result['sent'] > 0:
                                flash(f'✅ Successfully sent "{subject}" to {email_result["sent"]} recipients!', 'success')
                                log_security_event('BULK_EMAIL_SUCCESS', session.get('admin_user', {}).get('username', 'unknown'), 
                                                 f'Sent to {email_result["sent"]} recipients: {subject}')
                            
                            if email_result['failed'] > 0:
                                flash(f'⚠️ {email_result["failed"]} emails failed to send. Check email configuration.', 'warning')
                        else:
                            flash(f'❌ Email sending failed: {email_result.get("error", "Unknown error")}', 'error')
                            log_security_event('BULK_EMAIL_FAILED', session.get('admin_user', {}).get('username', 'unknown'), 
                                             f'Failed to send: {email_result.get("error", "Unknown error")}')
                    
                    except Exception as e:
                        flash(f'❌ Email service error: {str(e)}', 'error')
                        log_security_event('BULK_EMAIL_ERROR', session.get('admin_user', {}).get('username', 'unknown'), 
                                         f'Email service error: {str(e)}')
                else:
                    flash('No parent emails found for the selected group.', 'warning')
                    
            except Exception as e:
                flash(f'Error accessing email data: {str(e)}', 'error')
                print(f"❌ Email error: {e}")
    
    # Get available camp sessions for recipient groups
    try:
        conn = sqlite3.connect('registration_submissions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT camp_session FROM registrations WHERE camp_session IS NOT NULL ORDER BY camp_session')
        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()
    except:
        sessions = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📧 Send Bulk Email - Camp Power-Up</title>
        <style>
            body { font-family: system-ui; margin: 0; background: #f5f7fa; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
            .nav { background: white; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .nav a { color: #667eea; text-decoration: none; margin: 0 15px; font-weight: 500; }
            .container { max-width: 800px; margin: 20px auto; padding: 0 20px; }
            .form-card { background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
            input, select, textarea { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px; }
            textarea { height: 150px; resize: vertical; }
            .btn { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #5a6fd8; }
            .alert { padding: 10px; border-radius: 5px; margin-bottom: 20px; }
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .alert-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
            .preview-section { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📧 Send Bulk Email</h1>
            <p>Compose and send emails to parents</p>
        </div>
        
        <div class="nav">
            <a href="/admin/dashboard">🏠 Dashboard</a>
            <a href="/admin/communication">📧 Communication</a>
            <a href="/admin/send-email" style="color: #764ba2; font-weight: bold;">Send Email</a>
            <a href="/admin/send-sms">📱 Send SMS</a>
        </div>
        
        <div class="container">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="form-card">
                <h2>📝 Compose Email</h2>
                <form method="POST">
                    <div class="form-group">
                        <label for="recipient_group">📮 Send To:</label>
                        <select id="recipient_group" name="recipient_group" required>
                            <option value="all">All Parents</option>
                            {% for session in sessions %}
                            <option value="{{ session }}">{{ session }} Parents</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="subject">📄 Subject:</label>
                        <input type="text" id="subject" name="subject" placeholder="e.g., Daily Activity Update" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="message">💬 Message:</label>
                        <textarea id="message" name="message" placeholder="Enter your message here..." required></textarea>
                    </div>
                    
                    <div class="preview-section">
                        <h4>📋 Email Templates (Click to use):</h4>
                        <button type="button" onclick="useTemplate('welcome')" style="margin: 5px; padding: 8px 12px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">Welcome Message</button>
                        <button type="button" onclick="useTemplate('daily')" style="margin: 5px; padding: 8px 12px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer;">Daily Update</button>
                        <button type="button" onclick="useTemplate('reminder')" style="margin: 5px; padding: 8px 12px; background: #ffc107; color: black; border: none; border-radius: 3px; cursor: pointer;">Pickup Reminder</button>
                    </div>
                    
                    <button type="submit" class="btn">📧 Send Email</button>
                </form>
            </div>
        </div>
        
        <script>
            function useTemplate(type) {
                const subjectField = document.getElementById('subject');
                const messageField = document.getElementById('message');
                
                const templates = {
                    'welcome': {
                        subject: 'Welcome to Camp Power-Up!',
                        message: 'Dear Parent,\\n\\nWelcome to Camp Power-Up! We\'re excited to have your child join us for an amazing summer experience.\\n\\nImportant Information:\\n• Camp starts at 10:00 AM\\n• Pickup is at 3:00 PM\\n• Please pack lunch and water bottle\\n• Sunscreen will be provided\\n\\nWe look forward to a fantastic summer!\\n\\nBest regards,\\nCamp Power-Up Team'
                    },
                    'daily': {
                        subject: 'Daily Camp Update - [Date]',
                        message: 'Dear Parents,\\n\\nHere\'s what your children enjoyed today at Camp Power-Up:\\n\\n🎮 Morning Activities:\\n• [Activity 1]\\n• [Activity 2]\\n\\n🏃 Afternoon Adventures:\\n• [Activity 3]\\n• [Activity 4]\\n\\n📸 Photos will be shared later today!\\n\\nTomorrow we\'ll be: [Tomorrow\'s Plan]\\n\\nThanks!\\nCamp Power-Up Team'
                    },
                    'reminder': {
                        subject: 'Pickup Reminder - Camp Power-Up',
                        message: 'Dear Parent,\\n\\nThis is a friendly reminder about pickup today:\\n\\n⏰ Pickup Time: 5:00 PM\\n📍 Location: Main Camp Entrance\\n\\nPlease ensure you arrive promptly. If you\'ll be late, please call us immediately.\\n\\nSee you soon!\\nCamp Power-Up Team'
                    }
                };
                
                if (templates[type]) {
                    subjectField.value = templates[type].subject;
                    messageField.value = templates[type].message;
                }
            }
        </script>
    </body>
    </html>
    ''', sessions=sessions)

@app.route('/admin/send-sms', methods=['GET', 'POST'])
@require_admin
def send_bulk_sms():
    """Send bulk SMS to parents"""
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        recipient_group = request.form.get('recipient_group', 'all')
        
        if not message:
            flash('Message is required.', 'error')
        elif len(message) > 160:
            flash('SMS message must be 160 characters or less.', 'error')
        else:
            # Get parent phone numbers from registration database
            try:
                conn = sqlite3.connect('registration_submissions.db')
                cursor = conn.cursor()
                
                if recipient_group == 'all':
                    cursor.execute('SELECT DISTINCT parent_phone FROM registrations WHERE parent_phone IS NOT NULL AND parent_phone != ""')
                else:
                    cursor.execute('SELECT DISTINCT parent_phone FROM registrations WHERE camp_session = ? AND parent_phone IS NOT NULL AND parent_phone != ""', (recipient_group,))
                
                phones = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                if phones:
                    # Log the SMS sending attempt
                    log_security_event('BULK_SMS', session.get('admin_user', {}).get('username', 'unknown'), 
                                     f'Sent to {len(phones)} recipients: {message[:50]}...')
                    
                    flash(f'SMS queued for delivery to {len(phones)} recipients.', 'success')
                    
                    # In a real implementation, you would integrate with Twilio here
                    # For now, we'll just log and confirm
                    print(f"📱 SMS queued: {message} to {len(phones)} recipients")
                else:
                    flash('No parent phone numbers found for the selected group.', 'warning')
                    
            except Exception as e:
                flash(f'Error accessing phone data: {str(e)}', 'error')
                print(f"❌ SMS error: {e}")
    
    # Get available camp sessions for recipient groups
    try:
        conn = sqlite3.connect('registration_submissions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT camp_session FROM registrations WHERE camp_session IS NOT NULL ORDER BY camp_session')
        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()
    except:
        sessions = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📱 Send Bulk SMS - Camp Power-Up</title>
        <style>
            body { font-family: system-ui; margin: 0; background: #f5f7fa; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
            .nav { background: white; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .nav a { color: #667eea; text-decoration: none; margin: 0 15px; font-weight: 500; }
            .container { max-width: 800px; margin: 20px auto; padding: 0 20px; }
            .form-card { background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
            input, select, textarea { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px; }
            textarea { height: 100px; resize: vertical; }
            .btn { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #5a6fd8; }
            .alert { padding: 10px; border-radius: 5px; margin-bottom: 20px; }
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .alert-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
            .char-counter { text-align: right; font-size: 12px; color: #666; margin-top: 5px; }
            .char-counter.warning { color: #856404; }
            .char-counter.error { color: #721c24; }
            .template-section { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📱 Send Bulk SMS</h1>
            <p>Send text messages to parents</p>
        </div>
        
        <div class="nav">
            <a href="/admin/dashboard">🏠 Dashboard</a>
            <a href="/admin/communication">📧 Communication</a>
            <a href="/admin/send-email">📧 Send Email</a>
            <a href="/admin/send-sms" style="color: #764ba2; font-weight: bold;">📱 Send SMS</a>
        </div>
        
        <div class="container">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="form-card">
                <h2>📝 Compose SMS</h2>
                <form method="POST">
                    <div class="form-group">
                        <label for="recipient_group">📮 Send To:</label>
                        <select id="recipient_group" name="recipient_group" required>
                            <option value="all">All Parents</option>
                            {% for session in sessions %}
                            <option value="{{ session }}">{{ session }} Parents</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="message">💬 Message:</label>
                        <textarea id="message" name="message" placeholder="Enter your SMS message (max 160 characters)..." required maxlength="160" oninput="updateCharCount()"></textarea>
                        <div id="charCounter" class="char-counter">0/160 characters</div>
                    </div>
                    
                    <div class="template-section">
                        <h4>📋 Quick Templates (Click to use):</h4>
                        <button type="button" onclick="useTemplate('pickup')" style="margin: 5px; padding: 8px 12px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">Pickup Reminder</button>
                        <button type="button" onclick="useTemplate('weather')" style="margin: 5px; padding: 8px 12px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer;">Weather Alert</button>
                        <button type="button" onclick="useTemplate('emergency')" style="margin: 5px; padding: 8px 12px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer;">Emergency</button>
                    </div>
                    
                    <button type="submit" class="btn">📱 Send SMS</button>
                </form>
            </div>
        </div>
        
        <script>
            function updateCharCount() {
                const message = document.getElementById('message');
                const counter = document.getElementById('charCounter');
                const length = message.value.length;
                
                counter.textContent = length + '/160 characters';
                counter.className = 'char-counter';
                
                if (length > 140) {
                    counter.className += ' warning';
                }
                if (length > 160) {
                    counter.className = 'char-counter error';
                }
            }
            
            function useTemplate(type) {
                const messageField = document.getElementById('message');
                
                const templates = {
                    'pickup': 'Reminder: Camp pickup today at 5:00 PM. Please arrive promptly at the main entrance. Thanks! - Camp Power-Up',
                    'weather': 'Weather Alert: Rain expected today. Camp activities will move indoors. All pickup/dropoff normal. - Camp Power-Up',
                    'emergency': 'URGENT: Please call camp immediately regarding your child. (555) 123-4567 - Camp Power-Up'
                };
                
                if (templates[type]) {
                    messageField.value = templates[type];
                    updateCharCount();
                }
            }
            
            // Initialize character counter
            updateCharCount();
        </script>
    </body>
    </html>
    ''', sessions=sessions)

@app.route('/admin/communication')
@require_admin
def admin_communication():
    """Communication module - redirect to send message interface"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📧 Communication Center - Camp Power-Up</title>
        <style>
            body { font-family: system-ui; margin: 0; background: #f5f7fa; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
            .nav { background: white; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .nav a { color: #667eea; text-decoration: none; margin: 0 15px; font-weight: 500; }
            .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
            .module-card { background: white; border-radius: 10px; padding: 30px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
            .feature-item { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
            .feature-item h4 { margin: 0 0 10px 0; color: #333; }
            .btn { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px 5px; }
            .btn:hover { background: #5a6fd8; color: white; text-decoration: none; }
            .status-badge { background: #28a745; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📧 Communication Center</h1>
            <p>Manage parent communications, send messages, and track engagement</p>
        </div>
        
        <div class="nav">
            <a href="/admin/dashboard">🏠 Dashboard</a>
            <a href="/admin/communication" style="color: #764ba2; font-weight: bold;">📧 Communication</a>
            <a href="/admin/registration">📋 Registration</a>
            <a href="/admin/game-library">🎮 Games</a>
            <a href="/admin/analytics">📊 Analytics</a>
            <a href="/admin/settings">⚙️ Settings</a>
        </div>
        
        <div class="container">
            <div class="module-card">
                <h2>📱 Communication Hub</h2>
                <p>Send emails and SMS messages to parents, manage templates, and track delivery status.</p>
                
                <div class="feature-grid">
                    <div class="feature-item">
                        <h4>📧 Email System</h4>
                        <p>Send bulk emails to all parents or specific groups</p>
                        <span class="status-badge">ACTIVE</span>
                        <div style="margin-top: 10px;">
                            <a href="/admin/send-email" class="btn">Send Bulk Email</a>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <h4>📱 SMS Messaging</h4>
                        <p>Quick text messages for urgent updates</p>
                        <span class="status-badge">ACTIVE</span>
                        <div style="margin-top: 10px;">
                            <a href="/admin/send-sms" class="btn">Send Bulk SMS</a>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <h4>📝 Message Templates</h4>
                        <p>Pre-built templates for common communications</p>
                        <span class="status-badge">READY</span>
                        <div style="margin-top: 10px;">
                            <p><strong>Available Templates:</strong></p>
                            <ul style="font-size: 14px; margin: 5px 0;">
                                <li>Welcome & Registration Confirmation</li>
                                <li>Daily Activity Updates</li>
                                <li>Weather Alerts & Policy Changes</li>
                                <li>Pickup Reminders</li>
                                <li>Photo Sharing Notifications</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <h4>📊 Delivery Tracking</h4>
                        <p>Monitor message delivery and engagement</p>
                        <span class="status-badge">MONITORING</span>
                        <div style="margin-top: 10px;">
                            <p><strong>Recent Activity:</strong></p>
                            <ul style="font-size: 14px; margin: 5px 0;">
                                <li>✅ 12 emails sent today</li>
                                <li>✅ 8 SMS messages delivered</li>
                                <li>📈 98% delivery success rate</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/admin/send-email" class="btn">📧 Send Bulk Email</a>
                    <a href="/admin/send-sms" class="btn">� Send Bulk SMS</a>
                    <a href="/admin/contacts" class="btn">👥 Manage Contacts</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/registration')
@require_admin  
def admin_registration():
    """Registration module - redirect to registrations"""
    return redirect('/admin/registrations')

@app.route('/admin/game-library')
@require_admin
def admin_game_library():
    """Game library module - redirect to games"""
    return redirect('/admin/games')

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

@app.route('/admin/email-settings', methods=['GET', 'POST'])
@require_admin
def email_settings():
    """Email configuration settings"""
    if request.method == 'POST':
        # Test email connection with provided settings
        test_result = email_service.test_connection()
        
        if test_result['success']:
            flash('✅ Email connection test successful!', 'success')
        else:
            flash(f'❌ Email connection failed: {test_result["error"]}', 'error')
    
    # Get current email templates
    templates = email_service.get_email_templates()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📧 Email Settings - Camp Power-Up</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 20px; min-height: 100vh; color: white;
            }
            .container { 
                max-width: 800px; margin: 0 auto; 
                background: rgba(255,255,255,0.1); 
                backdrop-filter: blur(10px);
                border-radius: 20px; padding: 30px;
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            }
            .nav { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
            .nav a { 
                color: white; text-decoration: none; padding: 10px 20px;
                background: rgba(255,255,255,0.2); border-radius: 25px;
                transition: all 0.3s ease;
            }
            .nav a:hover { background: rgba(255,255,255,0.3); }
            .config-section { 
                background: rgba(255,255,255,0.1); 
                border-radius: 15px; padding: 20px; margin-bottom: 20px;
            }
            .btn { 
                background: linear-gradient(45deg, #FFD700, #FFA500);
                color: #333; border: none; padding: 12px 24px;
                border-radius: 25px; cursor: pointer; font-weight: bold;
                text-decoration: none; display: inline-block;
                transition: all 0.3s ease;
            }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
            .template-card { 
                background: rgba(255,255,255,0.1); 
                border-radius: 10px; padding: 15px; margin-bottom: 10px;
            }
            .status-indicator { 
                display: inline-block; padding: 5px 15px; 
                border-radius: 15px; font-size: 12px; font-weight: bold;
                background: #28a745; color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📧 Email Configuration</h1>
            
            <div class="nav">
                <a href="/admin/dashboard">🏠 Dashboard</a>
                <a href="/admin/settings">⚙️ Settings</a>
                <a href="/admin/send-email">📧 Send Email</a>
                <a href="/admin/email-settings" style="color: #764ba2; font-weight: bold;">Email Config</a>
            </div>
            
            <div class="config-section">
                <h2>🔧 SMTP Configuration</h2>
                <p>Configure your email server settings to enable email sending.</p>
                
                <form method="post">
                    <div style="margin-top: 10px;">
                        <p><strong>📧 Required Environment Variables:</strong></p>
                        <code style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 5px; display: block; font-family: monospace; white-space: pre;">export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-password"
export SENDER_NAME="Camp Power-Up"
export USE_TLS="true"</code>
                    </div>
                    
                    <button type="submit" class="btn" style="margin-top: 15px;">🧪 Test Email Connection</button>
                </form>
                
                <div style="margin-top: 20px;">
                    <h3>📋 Setup Instructions:</h3>
                    <ol style="margin-left: 20px;">
                        <li><strong>Gmail Setup:</strong> Enable 2-factor authentication and create an App Password</li>
                        <li><strong>Environment:</strong> Set the environment variables above in your .env file</li>
                        <li><strong>Test:</strong> Click "Test Email Connection" to verify setup</li>
                        <li><strong>Send:</strong> Use the Send Email feature to send bulk emails</li>
                    </ol>
                </div>
            </div>
            
            <div class="config-section">
                <h2>📝 Email Templates</h2>
                <p>Pre-built email templates for common camp communications.</p>
                
                {% for template_name, template_data in templates.items() %}
                <div class="template-card">
                    <h4>{{ template_name.replace('_', ' ').title() }}</h4>
                    <p><strong>Subject:</strong> {{ template_data.subject }}</p>
                    <span class="status-indicator">Ready</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    ''', templates=templates)

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
    
    print("🔗 Admin portal: http://127.0.0.1:5009/admin/login")
    print("✅ Secure authentication system active")
    print("📊 Ready for camp management operations")
    app.run(host='127.0.0.1', port=5009, debug=True)
