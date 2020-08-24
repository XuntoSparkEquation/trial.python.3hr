import datetime
from typing import Set, Dict, Any

from app import db
from app.models.exceptions import NotFound

FEATURED_THRESHOLD = 8


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.Unicode(50), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    featured = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=True)

    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    categories = db.relationship('Category', secondary='products_categories', backref='products')

    items_in_stock = db.Column(db.Integer, nullable=False)
    receipt_date = db.Column(db.DateTime, nullable=True)

    def on_update(self, data: Dict[str, Any]):
        if data["featured"] is None and data["rating"] > FEATURED_THRESHOLD:
            self.featured = True

    @classmethod
    def create(cls, data: Dict[str, Any]):
        product = Product(**data)
        product.on_update(data)
        return product

    @classmethod
    def get(cls, product_id: int):
        product: Product = db.session.query(Product).filter_by(id=product_id).first()

        if product is None:
            raise NotFound([f"Product[{product_id}]"])

        return product

    def update(self, data: Dict[str, Any]):
        for key, value in data.items():
            if key == "featured" and value is None:
                continue

            if not hasattr(self, key):
                continue

            setattr(self, key, value)
        self.on_update(data)

    @property
    def serialized(self):
        return {
            'id': self.id,
            'name': self.name,
            'rating': self.rating,
            'featured': self.featured,
            'items_in_stock': self.items_in_stock,
            'receipt_date': self.receipt_date,
            'brand': self.brand.serialized,
            'categories': [c.serialized for c in self.categories],
            'expiration_date': self.expiration_date,
            'created_at': self.created_at
        }


class Brand(db.Model):
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), nullable=False)
    country_code = db.Column(db.Unicode(2), nullable=False)

    products = db.relationship('Product', backref='brand')

    @classmethod
    def get(cls, brand_id: int):
        brand: Brand = db.session.query(Brand).filter_by(id=brand_id).first()

        if brand is None:
            raise NotFound([f"Brand[{brand_id}]"])

        return brand

    @property
    def serialized(self):
        return {
            'id': self.id,
            'name': self.name,
            'country_code': self.country_code
        }


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), nullable=False)

    @classmethod
    def get_all(cls, ids: Set[int]):
        categories = db.session.query(Category).filter(
            Category.id.in_(ids)
        ).all()

        db_ids = {record.id for record in categories}

        if len(categories) != len(ids):
            raise NotFound([f"Category[{category_id}]" for category_id in ids.difference(db_ids)])

        return categories

    @property
    def serialized(self):
        return {
            'id': self.id,
            'name': self.name,
        }


products_categories = db.Table(
    'products_categories',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)
