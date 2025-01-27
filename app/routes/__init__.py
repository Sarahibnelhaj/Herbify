# app/routes/__init__.py
from flask import Blueprint
from .auth import auth_bp
from .admin import admin_bp

# Create a main blueprint for all routes
routes_bp = Blueprint('routes', __name__)

# Register the auth and admin blueprints
routes_bp.register_blueprint(auth_bp, url_prefix='/auth')
routes_bp.register_blueprint(admin_bp, url_prefix='/admin')
