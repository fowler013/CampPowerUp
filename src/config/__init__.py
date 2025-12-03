"""
Configuration Management System
Implements environment-based configuration with validation
Following CYBV 302 system integration principles
"""
import os
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int = 10
    ssl_mode: str = "prefer"


@dataclass
class EmailConfig:
    """Email service configuration"""
    provider: str
    api_key: str
    from_email: str
    from_name: str


@dataclass
class SecurityConfig:
    """Security configuration (CYBV 301)"""
    secret_key: str
    session_timeout: int
    max_login_attempts: int
    password_min_length: int
    require_https: bool
    csrf_enabled: bool


class BaseConfig(ABC):
    """
    Base configuration class
    All environments inherit from this
    """
    
    # Application
    APP_NAME = "Camp Power-Up Registration"
    VERSION = "2.0.0"
    DEBUG = False
    TESTING = False
    
    # Security (CYBV 301 principles)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_TIMEOUT = 3600  # 1 hour
    MAX_LOGIN_ATTEMPTS = 5
    PASSWORD_MIN_LENGTH = 12
    CSRF_ENABLED = True
    
    # Database (APCV 360 principles)
    DATABASE_POOL_SIZE = 10
    DATABASE_POOL_TIMEOUT = 30
    DATABASE_POOL_RECYCLE = 3600
    
    # Email
    EMAIL_PROVIDER = 'sendgrid'
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    SENDGRID_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL', 'camppowerup2025@gmail.com')
    SENDGRID_FROM_NAME = os.environ.get('SENDGRID_FROM_NAME', 'Camp Power-Up')
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/app.log'
    
    # Rate Limiting (CYBV 301)
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
    
    @abstractmethod
    def get_database_uri(self) -> str:
        """Get database connection URI"""
        pass
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith('_') and not callable(getattr(cls, key))
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        required = ['SECRET_KEY', 'SENDGRID_API_KEY']
        missing = [key for key in required if not getattr(cls, key, None)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Use SQLite for local development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///camp_power_up_dev.db'
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    # Relaxed security for development
    REQUIRE_HTTPS = False
    SESSION_TIMEOUT = 86400  # 24 hours
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    def get_database_uri(self) -> str:
        return self.SQLALCHEMY_DATABASE_URI


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    DEBUG = False
    TESTING = True
    
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    # Disable CSRF for testing
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False
    
    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Mock email service
    EMAIL_PROVIDER = 'mock'
    
    def get_database_uri(self) -> str:
        return self.SQLALCHEMY_DATABASE_URI


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Railway PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://'
    )
    SQLALCHEMY_ECHO = False
    
    # Strict security (CYBV 301)
    REQUIRE_HTTPS = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Rate limiting with Redis
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    def get_database_uri(self) -> str:
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL not set in production environment")
        return self.SQLALCHEMY_DATABASE_URI


class StagingConfig(ProductionConfig):
    """Staging environment configuration"""
    
    DEBUG = True
    LOG_LEVEL = 'INFO'
    
    # Staging database
    SQLALCHEMY_DATABASE_URI = os.environ.get('STAGING_DATABASE_URL', '').replace(
        'postgres://', 'postgresql://'
    )


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> BaseConfig:
    """
    Get configuration for specified environment
    
    Args:
        env: Environment name (development, testing, production, staging)
             If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration object
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    config_class = config_by_name.get(env.lower(), DevelopmentConfig)
    
    # Validate configuration
    config_class.validate()
    
    return config_class


def is_production() -> bool:
    """Check if running in production"""
    return os.environ.get('FLASK_ENV', '').lower() == 'production'


def is_development() -> bool:
    """Check if running in development"""
    return os.environ.get('FLASK_ENV', '').lower() in ('development', '')


def is_testing() -> bool:
    """Check if running tests"""
    return os.environ.get('FLASK_ENV', '').lower() == 'testing'
