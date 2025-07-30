#!/usr/bin/env python3
"""
Camp Power-Up Configuration Management
=====================================

Handles environment-specific configuration with secure defaults
"""

import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration with secure defaults"""
    
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Database Settings
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///camp_power_up.db')
    SECURITY_DB_URL = os.environ.get('SECURITY_DB_URL', 'sqlite:///security.db')
    
    # Email Configuration
    EMAIL_SMTP_SERVER = os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.environ.get('EMAIL_SMTP_PORT', 587))
    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    EMAIL_SENDER_NAME = os.environ.get('EMAIL_SENDER_NAME', 'Camp Power-Up Team')
    
    # SMS Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Security Settings
    SESSION_TIMEOUT_HOURS = int(os.environ.get('SESSION_TIMEOUT_HOURS', 8))
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    ACCOUNT_LOCKOUT_MINUTES = int(os.environ.get('ACCOUNT_LOCKOUT_MINUTES', 30))
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    
    # Rate Limiting
    RATE_LIMIT_STORAGE = os.environ.get('RATE_LIMIT_STORAGE', 'memory')
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '200 per day, 50 per hour')
    RATE_LIMIT_LOGIN = os.environ.get('RATE_LIMIT_LOGIN', '5 per minute')
    RATE_LIMIT_EMAIL = os.environ.get('RATE_LIMIT_EMAIL', '10 per minute')
    RATE_LIMIT_SMS = os.environ.get('RATE_LIMIT_SMS', '10 per minute')
    
    # Security Features
    WTF_CSRF_ENABLED = True
    CSRF_PROTECTION = os.environ.get('CSRF_PROTECTION', 'True').lower() == 'true'
    HTTPS_ONLY = os.environ.get('HTTPS_ONLY', 'False').lower() == 'true'
    SECURE_COOKIES = os.environ.get('SECURE_COOKIES', 'False').lower() == 'true'
    
    # Audit & Logging
    AUDIT_LOG_ENABLED = os.environ.get('AUDIT_LOG_ENABLED', 'True').lower() == 'true'
    SECURITY_LOG_LEVEL = os.environ.get('SECURITY_LOG_LEVEL', 'INFO')
    SECURITY_LOG_FILE = os.environ.get('SECURITY_LOG_FILE', 'security.log')
    
    # Encryption
    DATA_ENCRYPTION_ENABLED = os.environ.get('DATA_ENCRYPTION_ENABLED', 'True').lower() == 'true'
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = SESSION_TIMEOUT_HOURS * 3600  # Convert to seconds
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration settings"""
        required_settings = []
        warnings = []
        
        # Check email configuration
        if not cls.EMAIL_ADDRESS:
            required_settings.append('EMAIL_ADDRESS')
        if not cls.EMAIL_PASSWORD:
            required_settings.append('EMAIL_PASSWORD')
        
        # Check Twilio configuration (optional but recommended)
        if not cls.TWILIO_ACCOUNT_SID:
            warnings.append('TWILIO_ACCOUNT_SID not set - SMS features will use simulation mode')
        
        # Check security settings for production
        if cls.FLASK_ENV == 'production':
            if cls.SECRET_KEY and len(cls.SECRET_KEY) < 32:
                required_settings.append('SECRET_KEY (must be at least 32 characters for production)')
            
            if not cls.HTTPS_ONLY:
                warnings.append('HTTPS_ONLY should be enabled in production')
            
            if not cls.SECURE_COOKIES:
                warnings.append('SECURE_COOKIES should be enabled in production')
        
        return required_settings, warnings

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'
    HTTPS_ONLY = False
    SECURE_COOKIES = False

class ProductionConfig(Config):
    """Production configuration with enhanced security"""
    DEBUG = False
    FLASK_ENV = 'production'
    HTTPS_ONLY = True
    SECURE_COOKIES = True
    WTF_CSRF_ENABLED = True
    
    # Enhanced rate limiting for production
    RATE_LIMIT_DEFAULT = '100 per day, 20 per hour'
    RATE_LIMIT_LOGIN = '3 per minute'
    RATE_LIMIT_EMAIL = '5 per minute'
    RATE_LIMIT_SMS = '5 per minute'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    DATABASE_URL = 'sqlite:///:memory:'
    SECURITY_DB_URL = 'sqlite:///:memory:'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

def validate_environment():
    """Validate current environment configuration"""
    current_config = get_config()
    required, warnings = current_config.validate_config()
    
    if required:
        print("❌ CONFIGURATION ERRORS:")
        for setting in required:
            print(f"   - Missing required setting: {setting}")
        print("\n💡 Please check your .env file or environment variables")
        return False
    
    if warnings:
        print("⚠️  CONFIGURATION WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
        print()
    
    print(f"✅ Configuration validated for {current_config.FLASK_ENV} environment")
    return True

if __name__ == '__main__':
    # Validate configuration when run directly
    validate_environment()
