#!/usr/bin/env python3
"""
Camp Power-Up Security Module
============================

Handles authentication, authorization, and security features.
"""

import os
import bcrypt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, redirect, url_for, flash, render_template_string
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import hashlib
from cryptography.fernet import Fernet

class SecurityManager:
    """Centralized security management for Camp Power-Up"""
    
    def __init__(self, app=None):
        self.app = app
        self.login_manager = LoginManager()
        self.encryption_key = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security with Flask app"""
        self.app = app
        
        # Configure Flask-Login
        self.login_manager.init_app(app)
        self.login_manager.login_view = 'admin_login'
        self.login_manager.login_message = 'Please log in to access this page.'
        self.login_manager.login_message_category = 'info'
        
        # Set up user loader
        @self.login_manager.user_loader
        def load_user(user_id):
            return self.get_user_by_id(user_id)
        
        # Generate or load encryption key
        self._init_encryption()
        
        # Create admin tables
        self._create_security_tables()
    
    def _init_encryption(self):
        """Initialize encryption key for sensitive data"""
        key_file = 'security_key.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            # Generate new encryption key
            self.encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)
            
            # Secure the key file
            os.chmod(key_file, 0o600)
        
        self.cipher = Fernet(self.encryption_key)
    
    def _create_security_tables(self):
        """Create security-related database tables"""
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                is_active BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                must_change_password BOOLEAN DEFAULT 1
            )
        ''')
        
        # Session tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Security audit log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                resource TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create default admin user if none exists
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user if no users exist"""
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Generate secure default password
            default_password = secrets.token_urlsafe(16)
            password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role, must_change_password)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', 'admin@camppowerup.com', password_hash.decode('utf-8'), 'admin', True))
            
            conn.commit()
            
            # Save default credentials securely
            with open('INITIAL_ADMIN_CREDENTIALS.txt', 'w') as f:
                f.write(f"🔐 CAMP POWER-UP INITIAL ADMIN CREDENTIALS\n")
                f.write(f"==========================================\n\n")
                f.write(f"Username: admin\n")
                f.write(f"Password: {default_password}\n\n")
                f.write(f"⚠️  IMPORTANT SECURITY NOTES:\n")
                f.write(f"1. Change this password immediately after first login\n")
                f.write(f"2. Delete this file after recording credentials securely\n")
                f.write(f"3. Enable two-factor authentication if available\n")
                f.write(f"4. Use a strong, unique password for production\n\n")
                f.write(f"Generated: {datetime.now()}\n")
            
            # Secure the credentials file
            os.chmod('INITIAL_ADMIN_CREDENTIALS.txt', 0o600)
            
            print("🔐 Default admin user created!")
            print("📄 Credentials saved to INITIAL_ADMIN_CREDENTIALS.txt")
            print("⚠️  Please change the default password immediately!")
        
        conn.close()

class User(UserMixin):
    """User model for Flask-Login"""
    
    def __init__(self, id, username, email, role, is_active=True, must_change_password=False):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.is_active = is_active
        self.must_change_password = must_change_password
    
    def get_id(self):
        return str(self.id)
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role or self.role == 'admin'
    
    def can_access(self, resource):
        """Check if user can access specific resource"""
        role_permissions = {
            'admin': ['all'],
            'manager': ['communication', 'registration', 'reports'],
            'staff': ['communication', 'registration'],
            'viewer': ['reports']
        }
        
        user_permissions = role_permissions.get(self.role, [])
        return 'all' in user_permissions or resource in user_permissions

def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_role(role):
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def audit_log(action, resource=None, success=True, details=None):
    """Log security-related actions"""
    try:
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        
        user_id = current_user.id if current_user.is_authenticated else None
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        cursor.execute('''
            INSERT INTO security_audit 
            (user_id, action, resource, ip_address, user_agent, success, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action, resource, ip_address, user_agent, success, details))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit logging failed: {e}")

def encrypt_sensitive_data(data):
    """Encrypt sensitive data before storage"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # This would use the global security manager's cipher
    # For now, return base64 encoded (implement proper encryption)
    import base64
    return base64.b64encode(data).decode('utf-8')

def decrypt_sensitive_data(encrypted_data):
    """Decrypt sensitive data after retrieval"""
    # This would use the global security manager's cipher
    # For now, return base64 decoded (implement proper decryption)
    import base64
    return base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')

# Initialize global security manager
security_manager = SecurityManager()
