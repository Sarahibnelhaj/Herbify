import os
from datetime import timedelta

# Define the base directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Base configuration class. Contains settings common to all environments.
    """
    # Application secret key (used for session management, encryption, etc.)
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

    # Disable Flask-SQLAlchemy modification tracking to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT (JSON Web Token) configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default_jwt_secret_key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 1)))  # Token expiration time

    # Database configuration (can be overridden in environment-specific configs)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "app.db")}')

    # Enable or disable debugging (overridden in specific environments)
    DEBUG = False
    TESTING = False

    # Additional security settings
    SESSION_COOKIE_SECURE = False  # Set to True in production to enforce HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent client-side script access to cookies
    SESSION_COOKIE_SAMESITE = 'Lax'  # Prevent CSRF attacks

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # Default log level

    # API-specific settings
    API_TITLE = "Medicinal Herbs API"
    API_VERSION = "1.0"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


class DevelopmentConfig(Config):
    """
    Development-specific configuration.
    """
    DEBUG = True  # Enable debug mode for detailed error messages
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "app.db")}')  # Default to SQLite for development
    LOG_LEVEL = 'DEBUG'  # Enable verbose logging for debugging


class TestingConfig(Config):
    """
    Testing-specific configuration.
    """
    TESTING = True  # Enable testing mode
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'  # Use a separate test database
    LOG_LEVEL = 'DEBUG'  # Enable verbose logging for debugging


class ProductionConfig(Config):
    """
    Production-specific configuration.
    """
    DEBUG = False  # Disable debug mode for security
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "app.db")}')  # Use a production-ready database
    SESSION_COOKIE_SECURE = True  # Enforce HTTPS for session cookies
    LOG_LEVEL = 'WARNING'  # Reduce log verbosity in production