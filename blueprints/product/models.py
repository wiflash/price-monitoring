from sqlalchemy.orm import relationship
from blueprints import db
from flask_restful import fields
from datetime import datetime


class Price(db.Model):
    __tablename__ = "prices"
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    actual_price = db.Column(db.Integer, nullable=False, default=0)
    sale_price = db.Column(db.Integer, nullable=False, default=0)
    created = db.Column(db.DateTime, nullable=False)
    product = relationship("Product", back_populates="prices")

    response = {
        "created": fields.DateTime(dt_format="iso8601"),
        "id": fields.Integer,
        "product_id": fields.Integer,
        "actual_price": fields.Integer,
        "sale_price": fields.Integer
    }

    def __init__(self, product_id, actual_price, sale_price):
        self.product_id = product_id
        self.actual_price = actual_price
        self.sale_price = sale_price
        self.created = datetime.now()
    
    def __repr__(self):
        return "<Price %r>" % self.id


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    description_id = db.Column(db.Integer, db.ForeignKey("descriptions.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False, default="")
    parent_product = relationship("Product", back_populates="products")
    price = relationship("Price", back_populates="products")

    response = {
        "id": fields.Integer,
        "parent_id": fields.Integer,
        "description_id": fields.Integer,
        "name": fields.String
    }

    def __init__(self, id, parent_id=None, description_id, name):
        self.id = id
        self.parent_id = parent_id
        self.description_id = description_id
        self.name = name

    def __repr__(self):
        return "<Product %r>" % self.id
