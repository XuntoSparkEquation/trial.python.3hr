import datetime
from typing import Set, Dict

from app import db
from app.models.exceptions import NotFound
from app.schema.products import ProductPresentation, BrandPresentation, CategoryPresentation

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

    def on_update(self, data: Dict):
        if data.get("featured", None) is None and data.get("rating", 0) > FEATURED_THRESHOLD:
            self.featured = True

    @classmethod
    def create(cls, data: Dict):
        """
        Create new product.
        @param data: Product data. Should include all needed fields.
        @return: New product.
        """
        product = Product(**data)
        product.on_update(data)
        return product

    @classmethod
    def get(cls, product_id: int):
        """
        Get product by its ID.
        Throws NotFound if there is product with such id.
        @param product_id: ID of product we need.
        @return: Wanted product.
        """
        product: Product = db.session.query(Product).filter_by(id=product_id).first()

        if product is None:
            raise NotFound([f"Product[{product_id}]"])

        return product

    def update(self, data: Dict):
        """
        Update product.
        @param data: Product data. Can be partial.
        """
        data = {
            key: value
            for key, value in data.items()
            if hasattr(self, key)
        }

        for key, value in data.items():
            setattr(self, key, value)

        self.on_update(data)

    @property
    def serialized(self) -> ProductPresentation:
        """
        Get product presentation, prepared to be turned into JSON.
        @return: Product representation.
        """
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
        """
        Get brand by its ID.
        Throws NotFound if there is brand with such id.
        @param brand_id: ID of brand we need.
        @return: Wanted brand.
        """
        brand: Brand = db.session.query(Brand).filter_by(id=brand_id).first()

        if brand is None:
            raise NotFound([f"Brand[{brand_id}]"])

        return brand

    @property
    def serialized(self) -> BrandPresentation:
        """
        Get brand presentation, prepared to be turned into JSON.
        @return: Brand presentation.
        """
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
        """
        Get categories with specified ids.
        Throws NotFound if any Category not found.
        @param ids: IDs of wanted Categories.
        @return: Wanted categories.
        """
        categories = db.session.query(Category).filter(
            Category.id.in_(ids)
        ).all()

        db_ids = {record.id for record in categories}

        if len(categories) != len(ids):
            raise NotFound([f"Category[{category_id}]" for category_id in ids.difference(db_ids)])

        return categories

    @property
    def serialized(self) -> CategoryPresentation:
        """
        Get category presentation, prepared to be turned into JSON.
        @return: Category presentation.
        """
        return {
            'id': self.id,
            'name': self.name,
        }


products_categories = db.Table(
    'products_categories',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)
