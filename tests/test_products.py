import json
from datetime import datetime
from email import utils as email_utils

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.models.exceptions import NotFound
from app.models.products import Brand, Category, Product, FEATURED_THRESHOLD


def create_basic_db_brand() -> Category:
    return Brand(name="test", country_code="RU")


def create_basic_db_category() -> Category:
    return Category(name="test")


def create_basic_db_product() -> Product:
    # create product
    brand = create_basic_db_brand()
    category = create_basic_db_category()
    product = Product(name="test", rating=5, brand=brand, categories=[category], items_in_stock=1)
    return product


def test_get_all_products(client: FlaskClient, session: Session):
    # Test without any db records
    response = client.get('/products')
    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert not json_response.get('results')

    # Populate and test with db records
    for i in range(10):
        product = create_basic_db_product()
        session.add(product)
    session.commit()

    response = client.get('/products')
    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert len(json_response.get('results')) == 10


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


def test_acceptance_criteria_1(client: FlaskClient):
    # Try to break all validation rules (excluding ones from other criteria)
    response = client.post('/products', data=json.dumps({
        "name": "s" * 51,
        "rating": 11,
        "brand": -1,
        "categories": [-1],
        "items_in_stock": -1
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 400
    assert json_response["errors"]
    assert len(json_response["errors"]) == 3


def test_acceptance_criteria_2(client: FlaskClient):
    # Existence of categories doesn't matter as it is checked on validation step
    # before service even tries to fetch database objects

    # Try to pass more categories than is allowed
    response = client.post('/products', data=json.dumps({
        "name": "test",
        "rating": 5,
        "brand": 0,
        "categories": [0, 1, 2, 3, 4, 5, 6],
        "items_in_stock": 1
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 400
    assert json_response["errors"]
    assert len(json_response["errors"]) == 1

    # Try to pass less categories than is allowed
    response = client.post('/products', data=json.dumps({
        "name": "test",
        "rating": 5,
        "brand": 0,
        "categories": [],
        "items_in_stock": 1
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 400
    assert json_response["errors"]
    assert len(json_response["errors"]) == 1


def test_acceptance_criteria_3(client: FlaskClient):
    now = datetime.utcnow()

    # Try to pass expiration date that is too early
    response = client.post('/products', data=json.dumps({
        "name": "test",
        "rating": 5,
        "brand": 0,
        "categories": [0],
        "expiration_date": email_utils.format_datetime(now),
        "items_in_stock": 1
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 400
    assert len(json_response["errors"]) == 1
    assert json_response["errors"][0]["loc"][0] == 'expiration_date'


def test_acceptance_criteria_4(client: FlaskClient, session: Session):
    # create product
    product = create_basic_db_product()
    session.add(product)
    session.commit()

    assert product.featured is False

    # Make sure product doesn't become featured when rating is less then threshold
    response = client.put(f'/products/{product.id}', data=json.dumps({
        "name": product.name,
        "rating": FEATURED_THRESHOLD - 1,
        "brand": product.brand_id,
        "categories": [product.categories[0].id],
        "items_in_stock": product.items_in_stock
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert json_response["featured"] is False

    # Check if featured is updated when rating is more then threshold
    response = client.put(f'/products/{product.id}', data=json.dumps({
        "name": product.name,
        "rating": FEATURED_THRESHOLD + 1,
        "brand": product.brand_id,
        "categories": [product.categories[0].id],
        "items_in_stock": product.items_in_stock
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert json_response["featured"] is True

    # Make sure product do not stop being featured if rating becomes less then threshold
    response = client.put(f'/products/{product.id}', data=json.dumps({
        "name": product.name,
        "rating": FEATURED_THRESHOLD - 1,
        "brand": product.brand_id,
        "categories": [product.categories[0].id],
        "items_in_stock": product.items_in_stock
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert json_response["featured"] is True


def test_not_found(client: FlaskClient, session: Session):
    response = client.get(f"/products/0")
    json_response = json.loads(response.data)

    assert response.status_code == 404
    assert json_response["errors"]

    response = client.post('/products', data=json.dumps({
        "name": "test",
        "rating": 5,
        "brand": 0,
        "categories": [0],
        "items_in_stock": 10
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 404
    assert json_response["errors"]

    brand = create_basic_db_brand()
    session.add(brand)
    session.commit()

    response = client.post('/products', data=json.dumps({
        "name": "test",
        "rating": 5,
        "brand": brand.id,
        "categories": [0],
        "items_in_stock": 10
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 404
    assert json_response["errors"]
