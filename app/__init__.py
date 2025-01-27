import os
import datetime
from flask import Blueprint, Flask, app, jsonify, render_template, request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_smorest import Api
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from app import routes
from app.extensions import db, migrate, ma
from flask_cors import CORS

# Load environment variables
load_dotenv()

def create_app(config_name=None):
    """
    Create and configure the Flask app.
    """
    app = Flask(__name__)
    
    app.config['DEBUG'] = True 
    # Enable CORS
    CORS(app)

    # Load configuration based on the config_name
    if config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    elif config_name == 'production':
        app.config.from_object('app.config.ProductionConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')  # Default to development

    # Flask-Smorest and OpenAPI Configuration
    app.config["API_TITLE"] = "Medicinal Herbs API"
    app.config["API_VERSION"] = "1.0"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # JWT Configuration
    app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1)

    # Customize token location and header name
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = ""  # Remove the "Bearer" prefix

    # Initialize Flask-Smorest API
    api = Api(app)

    # Swagger UI Setup (only if swagger.json exists)
    SWAGGER_URL = "/api/docs"
    API_URL = "/static/swagger.json"
    if os.path.exists(os.path.join(app.static_folder, "swagger.json")):
        swagger_ui_blueprint = get_swaggerui_blueprint(
            SWAGGER_URL,
            API_URL,
            config={"app_name": "Medicinal Herbs API"}
        )
        app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

        @app.route('/static/swagger.json')
        def serve_swagger():
            return app.send_static_file('swagger.json')
    else:
        print("Warning: swagger.json not found. Swagger UI will not be available.")

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Initialize JWT
    jwt = JWTManager(app)

    # Register the routes blueprint
    from app.routes import routes_bp
    from app.routes.admin import admin_bp  # Import the admin blueprint
    app.register_blueprint(routes_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')  # Register admin blueprint with /admin prefix

    # Import the auth blueprint
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Debug: Print registered routes
    print("Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(rule)

    # Create database tables if they don't exist (only in development/testing)
    if config_name != 'production':
        with app.app_context():
            try:
                db.create_all()
                print("Database tables created successfully.")
            except Exception as e:
                print(f"Failed to create database tables: {e}")

    # Global Error Handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        """
        Handle Marshmallow validation errors.
        """
        return jsonify({
            "error_code": "VALIDATION_ERROR",
            "message": "Invalid input data",
            "details": err.messages
        }), 400

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        """
        Handle HTTP exceptions (e.g., 404, 500).
        """
        return jsonify({
            "error_code": err.name,
            "message": err.description
        }), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        """
        Handle unexpected errors (e.g., server errors).
        """
        return jsonify({
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred"
        }), 500

    # Serve the homepage
    @app.route('/')
    def index():
        return render_template('index.html')

    # Serve the herbs page
    @app.route('/herbs')
    def herbs():
        return render_template('herbs.html')

    # Serve the products page
    @app.route('/products')
    def products():
        return render_template('products.html')

    # Serve the login page
    @app.route('/login')
    def login():
        return render_template('login.html')

    # Serve the register page
    @app.route('/register')
    def register():
        return render_template('register.html')
    
    # Serve the dashboard page
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    # Serve the admin page
    @app.route('/admin')
    def admin():
        return render_template('admin.html')
    
    @app.route('/research')
    def research():
        return render_template('research.html')

    return app