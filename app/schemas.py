# app/schemas.py
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    """
    Schema for User model.
    """
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6))
    role = fields.Str(
        required=True,
        validate=validate.OneOf(['researcher', 'seller']),
        metadata={
            "description": "Choose your role: "
                           "'researcher' - Can search and view herbs, buy products. "
                           "'seller' - Can create, update, and manage products."
        }
    )
    is_admin = fields.Bool(dump_only=True)


class HerbSchema(Schema):
    """
    Schema for Herb model.
    """
    id = fields.Int(dump_only=True)
    common_name = fields.Str(required=True)
    scientific_name = fields.Str(required=True)
    part_used = fields.Str(required=True)
    toxicity = fields.Str(required=True)
    description = fields.Str(required=False)
    image_url = fields.Str(required=False)


class ProductSchema(Schema):
    """
    Schema for Product model.
    """
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    price = fields.Float(required=True)
    seller_id = fields.Int(required=True)