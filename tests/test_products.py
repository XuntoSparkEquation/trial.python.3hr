import json

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.models.exceptions import NotFound
from app.models.products import Brand, Category, Product


def create_basic_db_brand():
    return Brand(name="test", country_code="RU")


def create_basic_db_category():
    return Category(name="test")


def create_basic_db_product() -> Product:
    # create product
    brand = create_basic_db_brand()
    category = create_basic_db_category()
    product = Product(name="test", rating=5, brand=brand, categories=[category], items_in_stock=1)
    return product


def test_get_all_products(client):
    response = client.get('/products')

    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert not json_response.get('results')


def test_read_product(client: FlaskClient, session: Session):
    # create product that we should read
    product = create_basic_db_product()
    session.add(product)
    session.commit()

    # request product by id
    response = client.get(f"/products/{product.id}")
    json_response = json.loads(response.data)

    # Check status
    assert response.status_code == 200

    # Check if returned object is similar
    assert json_response["id"] == product.id
    assert json_response["name"] == product.name
    assert json_response["rating"] == product.rating
    assert json_response["brand"]["id"] == product.brand_id
    assert json_response["items_in_stock"] == product.items_in_stock


def test_create_product(client: FlaskClient, session: Session):
    # create brand and category to add to new product
    brand = create_basic_db_brand()
    category = create_basic_db_category()
    session.add(brand)
    session.add(category)
    session.commit()

    # request creation of product
    response = client.post('/products', data=json.dumps({
        "name": "",
        "rating": 5,
        "brand": brand.id,
        "categories": [category.id],
        "items_in_stock": 10
    }), content_type='application/json')

    # check status
    assert response.status_code == 201


def test_update_product(client: FlaskClient, session: Session):
    # create product
    product = create_basic_db_product()
    session.add(product)

    # create new brand and category to update with
    new_brand = Brand(name="test2", country_code="RU")
    new_category = Category(name="test2")

    session.add(new_brand)
    session.add(new_category)

    # Commit everything
    session.commit()

    # request update
    response = client.put(f"/products/{product.id}", data=json.dumps({
        "name": "test2",
        "rating": 6,
        "brand": new_brand.id,
        "categories": [new_category.id],
        "items_in_stock": 2
    }), content_type='application/json')

    # check status
    assert response.status_code == 200

    # check if product changed in database
    session.refresh(product)
    assert product.name == "test2"
    assert product.rating == 6
    assert product.brand_id == new_brand.id
    assert set(product.categories) == {new_category}
    assert product.items_in_stock == 2


def test_delete_product(client: FlaskClient, session: Session):
    # create product
    product = create_basic_db_product()
    session.add(product)
    session.commit()

    # request delete
    product_id = product.id
    response = client.delete(f"/products/{product_id}")

    # check if successful
    assert response.status_code == 200

    # check if product deleted
    with pytest.raises(NotFound):
        Product.get(product_id)
