import json
from datetime import datetime, timedelta
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

    now = datetime.utcnow()

    # request creation of product
    product_create_request = {
        "name": "test",
        "rating": 5,
        "brand": brand.id,
        "categories": [category.id],
        "receipt_date": email_utils.format_datetime(now),
        "expiration_date": email_utils.format_datetime(now + timedelta(days=30)),
        "items_in_stock": 10
    }
    response = client.post('/products', data=json.dumps(product_create_request), content_type='application/json')
    json_response = json.loads(response.data)

    # check status
    assert response.status_code == 201

    # check if data is the same
    product = Product.get(json_response["id"])
    assert product.name == product_create_request["name"]
    assert product.rating == product_create_request["rating"]
    assert product.brand_id == brand.id
    assert product.categories == [category]
    assert product.items_in_stock == product_create_request["items_in_stock"]


def test_update_product(client: FlaskClient, session: Session):
    # create product
    product = create_basic_db_product()
    session.add(product)
    session.commit()

    # check before change
    product_pre_update = product.serialized

    # request update
    response = client.patch(
        f"/products/{product.id}",
        data=json.dumps({"name": "test2"}),
        content_type='application/json'
    )

    # check status
    assert response.status_code == 200

    # check if product changed in database
    session.refresh(product)
    assert product.name == "test2"

    # make sure everything else is NOT changed
    product_post_update = product.serialized
    assert product_post_update["id"] == product_pre_update["id"]
    assert product_post_update["featured"] == product_pre_update["featured"]
    assert product_post_update["brand"] == product_pre_update["brand"]
    assert product_post_update["categories"] == product_pre_update["categories"]
    assert product_post_update["items_in_stock"] == product_pre_update["items_in_stock"]
    assert product_post_update["receipt_date"] == product_pre_update["receipt_date"]
    assert product_post_update["expiration_date"] == product_pre_update["expiration_date"]
    assert product_post_update["created_at"] == product_pre_update["created_at"]


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
        "items_in_stock": -1
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 400
    assert json_response["errors"]
    assert len(json_response["errors"]) == 5


def test_acceptance_criteria_2(client: FlaskClient, session: Session):
    # Create brands and categories to test with
    brand = create_basic_db_brand()
    categories = [
        create_basic_db_category() for i in range(6)
    ]

    session.add(brand)
    session.add_all(categories)
    session.commit()

    # Try to pass more categories than is allowed
    response = client.post('/products', data=json.dumps({
        "name": "test",
        "rating": 5,
        "brand": brand.id,
        "categories": [c.id for c in categories],
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
        "brand": brand.id,
        "categories": [],
        "items_in_stock": 1
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 400
    assert json_response["errors"]
    assert len(json_response["errors"]) == 1


def test_acceptance_criteria_3(client: FlaskClient, session: Session):
    # create brand and category to add to new product
    brand = create_basic_db_brand()
    category = create_basic_db_category()

    session.add(brand)
    session.add(category)
    session.commit()

    now = datetime.utcnow()

    # Try to pass expiration date that is too early (creation)
    response = client.post('/products', data=json.dumps({
        "name": "test",
        "rating": 5,
        "brand": brand.id,
        "categories": [category.id],
        "expiration_date": email_utils.format_datetime(now),
        "items_in_stock": 1
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 400
    assert len(json_response["errors"]) == 1
    assert json_response["errors"][0]["loc"][0] == 'expiration_date'

    # Try to pass expiration date that is too early (update)
    product = create_basic_db_product()
    session.add(product)
    session.commit()

    response = client.patch(f"/products/{product.id}", data=json.dumps({
        "expiration_date": email_utils.format_datetime(now),
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
    response = client.patch(f'/products/{product.id}', data=json.dumps({
        "rating": FEATURED_THRESHOLD - 1,
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert json_response["featured"] is False

    # Check if featured is updated when rating is more then threshold
    response = client.patch(f'/products/{product.id}', data=json.dumps({
        "rating": FEATURED_THRESHOLD + 1,
    }), content_type='application/json')
    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert json_response["featured"] is True

    # Make sure product do not stop being featured if rating becomes less then threshold
    response = client.patch(f'/products/{product.id}', data=json.dumps({
        "rating": FEATURED_THRESHOLD - 1,
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
