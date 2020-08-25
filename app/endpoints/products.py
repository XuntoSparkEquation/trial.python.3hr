from typing import Dict

from flask import Blueprint, jsonify, request

from app import db
from app.models.products import Product, Brand, Category
from app.schema.products import ProductCreateRequest, ProductUpdateRequest

products_blueprint = Blueprint('products', __name__)


def build_product_args(data: ProductUpdateRequest) -> Dict:
    """
    Turn ProductSchema into dict for updating Product orm object.
    Result can be used can be used as constructor argument
    or can be iterated through to update field values.

    @param data: request data ProductCreateRequest
    @return: dict with data
    """
    create_args = data.dict(exclude_unset=True)

    if data.brand is not None:
        create_args["brand"] = Brand.get(data.brand)

    if data.categories is not None:
        create_args["categories"] = Category.get_all(data.categories)

    return create_args


@products_blueprint.route('/products', methods=['GET'])
def get_products():
    """
    Get full list of products.
    @return: List of product representations.
    """
    return jsonify({
        'results': [p.serialized for p in Product.query.all()]
    })


@products_blueprint.route('/products', methods=['POST'])
def create_product():
    """
    Create new product.

    @see ProductCreateRequest for request body fields.
    @return: Created product representation.
    """
    create_input = ProductCreateRequest(**request.get_json())

    create_data = build_product_args(create_input)
    product: Product = Product.create(create_data)

    db.session.add(product)
    db.session.commit()

    return jsonify(product.serialized), 201


@products_blueprint.route('/products/<int:product_id>', methods=['GET'])
def read_product(product_id: int):
    """
    Get product by its ID.
    @param product_id: ID of wanted product.
    @return: Wanted product representation.
    """
    product: Product = Product.get(product_id)
    return jsonify(product.serialized)


@products_blueprint.route('/products/<int:product_id>', methods=['PATCH'])
def update_product(product_id: int):
    """
    Update product. Endpoint accepts difference (patch update).

    @see ProductUpdateRequest for request body fields.
    @param product_id: ID of product we want to update.
    @return: Representation of product after update.
    """

    update_input = ProductUpdateRequest(**request.get_json())
    update_data = build_product_args(update_input)

    product: Product = Product.get(product_id)
    product.update(update_data)
    db.session.commit()

    return jsonify(product.serialized)


@products_blueprint.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id: int):
    """
    Remove product by its ID.

    @param product_id: ID of product we want to delete.
    @return: Simple status message.
    """
    product: Product = Product.get(product_id)
    db.session.delete(product)
    db.session.commit()

    return jsonify({"status": "ok"})
