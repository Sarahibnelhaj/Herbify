from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """
    User model representing application users.
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # Default to 'user' role
    is_admin = db.Column(db.Boolean, nullable=False, default=False)  # Default to False for regular users

    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        """
        Hash and set the user's password.
        """
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify the user's password.
        """
        return check_password_hash(self.password, password)


class Herb(db.Model):
    """
    Herb model representing medicinal herbs.
    """
    __tablename__ = 'herb'

    id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(100), nullable=False)
    part_used = db.Column(db.String(100), nullable=False)
    toxicity = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    researcher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Link to the researcher

    def __repr__(self):
        return f"<Herb {self.common_name} ({self.scientific_name})>"


class Product(db.Model):
    """
    Product model representing herbal products.
    """
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to the seller

    def __repr__(self):
        return f"<Product {self.name}>"