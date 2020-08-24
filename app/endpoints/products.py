from typing import Dict, Any

from flask import Blueprint, jsonify, request

from app import db
from app.models.products import Product, Brand, Category
from app.schema.products import ProductSchema, ProductUpdateSchema

products_blueprint = Blueprint('products', __name__)


def build_product_args(data: ProductSchema) -> Dict[str, Any]:
    """
    Turn ProductSchema into dict for updating Product orm object.
    Result can be used can be used as constructor argument
    or can be iterated to replace field values.
    Result always has enough data to create new Product instance.
    @param data: request data ProductSchema
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

    @see ProductSchema for request body fields.
    @return: Created product representation.
    """
    create_input = ProductSchema(**request.get_json())

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
    Update product. Endpoint accepts changes (patch update).

    @see ProductUpdateSchema for request body fields.
    @param product_id: ID of product we want to update.
    @return: Representation of product after update.
    """

    update_input = ProductUpdateSchema(**request.get_json())
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
