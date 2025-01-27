from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.models import User, Herb
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.decorators import admin_required
from app.utils import identify_plant
import traceback

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

@admin_bp.route('/register-admin', methods=['POST'])
def register_admin():
    """
    Register a new admin.
    - If no admin exists, create the first admin without requiring a token.
    - If an admin exists, require a valid admin token.
    """
    try:
        # Check if any admin exists
        existing_admin = User.query.filter_by(is_admin=True).first()

        # If no admin exists, allow creating the first admin without a token
        if not existing_admin:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not username or not email or not password:
                return jsonify({"error": "Username, email, and password are required"}), 400

            if User.query.filter_by(email=email).first():
                return jsonify({"error": "Email already exists"}), 400

            if User.query.filter_by(username=username).first():
                return jsonify({"error": "Username already exists"}), 400

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Create the new admin user
            new_admin = User(
                username=username,
                email=email,
                password=hashed_password,
                role='admin',  # Set the role to 'admin'
                is_admin=True  # Set the user as an admin
            )
            db.session.add(new_admin)
            db.session.commit()

            # Convert the user ID to a string before creating the token
            access_token = create_access_token(identity=str(new_admin.id))
            return jsonify({"message": "First admin registered successfully", "access_token": access_token}), 201

        # If an admin exists, require a valid admin token
        else:
            # Verify the JWT token
            verify_jwt_in_request()

            # Get the current user's identity from the JWT token
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)

            if not current_user or not current_user.is_admin:
                return jsonify({"error": "Only an existing admin can create new admins"}), 403

            # Proceed with creating a new admin
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not username or not email or not password:
                return jsonify({"error": "Username, email, and password are required"}), 400

            if User.query.filter_by(email=email).first():
                return jsonify({"error": "Email already exists"}), 400

            if User.query.filter_by(username=username).first():
                return jsonify({"error": "Username already exists"}), 400

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Create the new admin user
            new_admin = User(
                username=username,
                email=email,
                password=hashed_password,
                role='admin',  # Set the role to 'admin'
                is_admin=True  # Set the user as an admin
            )
            db.session.add(new_admin)
            db.session.commit()

            # Convert the user ID to a string before creating the token
            access_token = create_access_token(identity=str(new_admin.id))
            return jsonify({"message": "New admin registered successfully", "access_token": access_token}), 201

    except Exception as e:
        # Log the error for debugging
        print(f"Error in /admin/register-admin: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500


@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """
    Log in an admin and return a JWT token.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    admin = User.query.filter_by(email=email, is_admin=True).first()
    if not admin or not check_password_hash(admin.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Include additional claims in the token
    additional_claims = {"is_admin": True, "role": "admin"}
    access_token = create_access_token(identity=str(admin.id), additional_claims=additional_claims)
    return jsonify({"access_token": access_token, "role": "admin"}), 200


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """
    Update a user's details (admin access only).
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        user.password = generate_password_hash(data['password'])
    if 'role' in data:
        user.role = data['role']

    db.session.commit()
    return jsonify({"message": "User updated successfully"}), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """
    Delete a user (admin access only).
    """
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200


@admin_bp.route('/users/role/<string:role>', methods=['GET'])
@jwt_required()
@admin_required
def get_users_by_role(role):
    """
    Get all users by role (admin access only).
    """
    users = User.query.filter_by(role=role).all()
    users_data = [{"id": user.id, "username": user.username, "email": user.email, "role": user.role} for user in users]
    return jsonify(users_data), 200


@admin_bp.route('/users/<int:user_id>/make-admin', methods=['PUT'])
@jwt_required()
@admin_required
def make_admin(user_id):
    """
    Make a user an admin and update their role to 'admin' (admin access only).
    """
    try:
        # Fetch the user by ID
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update the user's role to 'admin' and set is_admin to True
        user.role = 'admin'
        user.is_admin = True

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"message": "User is now an admin", "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_admin": user.is_admin
        }}), 200

    except Exception as e:
        # Log the error for debugging
        print(f"Error in /admin/users/{user_id}/make-admin: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500


@admin_bp.route('/herbs/upload', methods=['POST'])
@jwt_required()
@admin_required
def upload_herb_manually():
    """
    Admin manually uploads herb details (admin access only).
    """
    try:
        data = request.get_json()

        # Debugging: Log the incoming request data
        print("Incoming Request Data:", data)

        # Validate required fields
        required_fields = ["common_name", "scientific_name", "part_used", "toxicity", "description", "image_url"]
        for field in required_fields:
            if field not in data:
                print(f"Missing required field: {field}")  # Debugging
                return jsonify({"error": f"{field} is required"}), 400

        # Debugging: Log the extracted fields
        print("Extracted Fields:", {
            "common_name": data["common_name"],
            "scientific_name": data["scientific_name"],
            "part_used": data["part_used"],
            "toxicity": data["toxicity"],
            "description": data["description"],
            "image_url": data["image_url"]
        })

        # Create a new herb
        new_herb = Herb(
            common_name=data["common_name"],
            scientific_name=data["scientific_name"],
            part_used=data["part_used"],
            toxicity=data["toxicity"],
            description=data["description"],
            image_url=data["image_url"]
        )

        # Debugging: Log the new herb object
        print("New Herb Object:", new_herb)

        # Save the new herb to the database
        db.session.add(new_herb)
        db.session.commit()

        # Debugging: Log success
        print("Herb saved successfully:", new_herb.id)

        return jsonify({"message": "Herb uploaded successfully", "herb": {
            "id": new_herb.id,
            "common_name": new_herb.common_name,
            "scientific_name": new_herb.scientific_name,
            "part_used": new_herb.part_used,
            "toxicity": new_herb.toxicity,
            "description": new_herb.description,
            "image_url": new_herb.image_url
        }}), 201

    except Exception as e:
        # Log the full traceback of the error
        print(f"Error in /admin/herbs/upload: {e}")
        print("Traceback:")
        traceback.print_exc()  # This will print the full traceback to the terminal

        db.session.rollback()  # Rollback the transaction in case of an error
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500


@admin_bp.route('/herbs', methods=['GET'])
@jwt_required()
@admin_required
def view_all_herbs():
    """
    View all herbs in the database (admin access only).
    """
    try:
        herbs = Herb.query.all()
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

        return jsonify({"herbs": herbs_data}), 200

    except Exception as e:
        # Log the error for debugging
        print(f"Error in /admin/herbs: {e}")
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """
    Get all users (admin access only).
    """
    try:
        # Fetch all users from the database
        users = User.query.all()
        
        # Format the user data
        users_data = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_admin": user.is_admin
            }
            for user in users
        ]
        
        return jsonify({"users": users_data}), 200
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error in /admin/users: {e}")
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500


@admin_bp.route('/admins', methods=['GET'])
@jwt_required()
@admin_required
def get_all_admins():
    """
    Get all admins (admin access only).
    """
    try:
        # Fetch all admins from the database
        admins = User.query.filter_by(is_admin=True).all()
        
        # Format the admin data
        admins_data = [
            {
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "role": admin.role,
                "is_admin": admin.is_admin
            }
            for admin in admins
        ]
        
        return jsonify({"admins": admins_data}), 200
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error in /admin/admins: {e}")
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500

@admin_bp.route('/clear-database', methods=['POST'])
@jwt_required()
@admin_required
def clear_database():
    """
    Clear all data from the database (admin access only).
    WARNING: This will permanently delete all data!
    """
    try:
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()

        return jsonify({"message": "Database cleared successfully"}), 200

    except Exception as e:
        # Log the error for debugging
        print(f"Error in /admin/clear-database: {str(e)}")
        db.session.rollback()  # Rollback the transaction in case of an error
        return jsonify({"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500