from venv import logger
from flask import Blueprint, app, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import Herb, Product, User
from app.extensions import db
from app.decorators import researcher_required, seller_required
from app.utils import identify_plant

# Create a blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    # Validate input
    if not username or not email or not password or not role:
        return jsonify({
            "error": "Username, email, password, and role are required.",
            "role_description": {
                "researcher": "Can search and view herbs, buy products.",
                "seller": "Can create, update, and manage products."
            }
        }), 400

    # Check if email or username already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    # Validate role
    if role not in ['researcher', 'seller']:
        return jsonify({
            "error": "Invalid role. Choose 'researcher' or 'seller'.",
            "role_description": {
                "researcher": "Can search and view herbs, buy products.",
                "seller": "Can create, update, and manage products."
            }
        }), 400

    # Create the new user
    new_user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        role=role,
        is_admin=False  # Default to False for regular users
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Log in a user and return a JWT token.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Validate input
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Check if the user exists
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create and return the JWT token
    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "role": user.role}), 200

@auth_bp.route('/research/identify-plant', methods=['POST'])
@jwt_required()
@researcher_required
def identify_and_save_plant():
    """
    Researcher identifies a plant using the Plant.id API and saves it to their dashboard.
    """
    try:
        data = request.get_json()
        image_url = data.get('image_url')

        # Validate the image URL
        if not image_url:
            return jsonify({"error": "Image URL is required"}), 400

        # Call the Plant.id API
        result = identify_plant(image_url)

        # Debugging: Log the Plant.id API response
        print("Plant.id API Response:", result)

        if not result:
            return jsonify({"error": "Failed to identify plant"}), 500

        # Extract relevant data from the API response
        suggestions = result.get("suggestions", [])
        if not suggestions:
            return jsonify({"error": "No plant suggestions found in the API response"}), 500

        plant_data = suggestions[0]  # Get the first suggestion
        plant_details = plant_data.get("plant_details", {})

        # Extract fields with fallback values
        common_name = plant_details.get("common_names", ["Unknown"])[0]
        scientific_name = plant_details.get("scientific_name", "Unknown")
        part_used = plant_details.get("part_used", "Unknown")
        toxicity = plant_details.get("toxicity", "Unknown")

        # Extract the description value from the dictionary
        description_dict = plant_details.get("description", {})
        description = description_dict.get("value", "No description available")

        # Get the current researcher's ID
        researcher_id = get_jwt_identity()

        # Create a new herb entry for the researcher's dashboard
        new_herb = Herb(
            common_name=common_name,
            scientific_name=scientific_name,
            part_used=part_used,
            toxicity=toxicity,
            description=description,  # Use the extracted description value
            image_url=image_url,
            researcher_id=researcher_id  # Associate the herb with the researcher
        )

        # Save the new herb to the database
        db.session.add(new_herb)
        db.session.commit()

        return jsonify({"message": "Plant identified and saved to your dashboard", "herb": {
            "id": new_herb.id,
            "common_name": new_herb.common_name,
            "scientific_name": new_herb.scientific_name,
            "part_used": new_herb.part_used,
            "toxicity": new_herb.toxicity,
            "description": new_herb.description,
            "image_url": new_herb.image_url
        }}), 201

    except Exception as e:
        # Log the error for debugging
        print(f"Error in /research/identify-plant: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500
    
@auth_bp.route('/research/history', methods=['GET'])
@jwt_required()
@researcher_required
def view_research_history():
    """
    View a researcher's personal research history.
    """
    try:
        researcher_id = get_jwt_identity()
        herbs = Herb.query.filter_by(researcher_id=researcher_id).all()
        herbs_data = [
            {
                "id": herb.id,
                "common_name": herb.common_name,
                "scientific_name": herb.scientific_name,
                "part_used": herb.part_used,
                "toxicity": herb.toxicity,
                "description": herb.description,
                "image_url": herb.image_url
            }
            for herb in herbs
        ]

        return jsonify({"research_history": herbs_data}), 200

    except Exception as e:
        # Log the error for debugging
        print(f"Error in /research/history: {e}")
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500

@auth_bp.route('/marketplace', methods=['GET'])
@jwt_required()
@researcher_required
def view_marketplace():
    """
    View all products in the marketplace (researcher access only).
    """
    try:
        logger.debug("Fetching all products from the database")
        products = Product.query.all()
        logger.debug(f"Found {len(products)} products")

        products_data = [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock
            }
            for product in products
        ]

        return jsonify({"products": products_data}), 200

    except Exception as e:
        logger.error(f"Error in /auth/marketplace: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

@auth_bp.route('/products', methods=['POST'])
@jwt_required()
@seller_required
def add_product():
    """
    Add a new product (seller access only).
    """
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')

    if not name or not price or not stock:
        return jsonify({"error": "Name, price, and stock are required"}), 400

    new_product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        seller_id=get_jwt_identity()  # Associate the product with the seller
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Product added successfully", "product": {
        "id": new_product.id,
        "name": new_product.name,
        "description": new_product.description,
        "price": new_product.price,
        "stock": new_product.stock
    }}), 201

@auth_bp.route('/seller/products', methods=['GET'])
@jwt_required()
@seller_required
def view_seller_products():
    """
    View all products added by the seller (seller access only).
    """
    seller_id = get_jwt_identity()
    products = Product.query.filter_by(seller_id=seller_id).all()
    products_data = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock
        }
        for product in products
    ]

    return jsonify({"products": products_data}), 200
