from functools import wraps
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from flask import jsonify, request
from app.models import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()  # Verify the JWT token
        claims = get_jwt()  # Get the claims from the token
        if not claims.get("is_admin", False):  # Check if the user is an admin
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def researcher_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role != 'researcher':
            return jsonify({"error": "Researcher access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def seller_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role != 'seller':
            return jsonify({"error": "Seller access required"}), 403
        return fn(*args, **kwargs)
    return wrapper