from sqlalchemy.orm import relationship
from blueprints import db
from flask_restful import fields
from datetime import datetime


class Price(db.Model):
    __tablename__ = "prices"
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    unit_price = db.Column(db.Integer, nullable=False, default=0)
    unit_sale_price = db.Column(db.Integer, nullable=False, default=0)
    created = db.Column(db.DateTime, nullable=False)
    product = relationship("Product", back_populates="price")

    response = {
        "created": fields.DateTime(dt_format="iso8601"),
        "id": fields.Integer,
        "product_id": fields.Integer,
        "unit_price": fields.Integer,
        "unit_sale_price": fields.Integer
    }

    def __init__(self, product_id, unit_price, unit_sale_price):
        self.product_id = product_id
        self.unit_price = unit_price
        self.unit_sale_price = unit_sale_price
        self.created = datetime.now()
    
    def __repr__(self):
        return "<Price %r>" % self.id


class Description(db.Model):
    __tablename__ = "descriptions"
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    content = db.Column(db.String(5000), nullable=False, default="")
    link = db.Column(db.String(100), nullable=False, default="")
    product = relationship("Product", back_populates="description")

    response = {
        "id": fields.Integer,
        "content": fields.String,
        "link": fields.String
    }

    def __init__(self, content, link):
        self.content = content
        self.link = link

    def __repr__(self):
        return "<Description %r>" % self.id


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    description_id = db.Column(db.Integer, db.ForeignKey("descriptions.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False, default="")
    product_parent = relationship("Product", remote_side=[id])
    description = relationship("Description", back_populates="product")
    price = relationship("Price", back_populates="product")
    photo = relationship("Photo", back_populates="product")

    response = {
        "id": fields.Integer,
        "parent_id": fields.Integer,
        "description_id": fields.Integer,
        "name": fields.String
    }

    def __init__(self, id, parent_id, description_id, name):
        self.id = id
        self.parent_id = parent_id
        self.description_id = description_id
        self.name = name

    def __repr__(self):
        return "<Product %r>" % self.id


class Photo(db.Model):
    __tablename__ = "photos"
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    source = db.Column(db.String(1000), nullable=False, default="")
    product = relationship("Product", back_populates="photo")

    response = {
        "id": fields.Integer,
        "product_id": fields.Integer,
        "source": fields.String
    }

    def __init__(self, product_id, source):
        self.product_id = product_id
        self.source = source

    def __repr__(self):
        return "<Photo %r>" % self.id
