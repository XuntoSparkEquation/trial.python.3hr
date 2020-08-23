import json

from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.models.products import Brand, Category, Product


def test_get_all_products(client):
    response = client.get('/products')

    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert not json_response.get('results')


def test_read_product(client: FlaskClient, session: Session):
    brand = Brand(name="test1", country_code="RU")
    category1 = Category(name="test1")
    category2 = Category(name="test2")

    product = Product(
        name="test",
        rating=5,
        brand=brand,
        featured=False,
        categories=[category1, category2],
        items_in_stock=10
    )

    session.add(product)
    session.commit()

    response = client.get(f"/products/{product.id}")

    json_response = json.loads(response.data)

    assert response.status_code == 200
    assert json_response["id"] == product.id
    assert json_response["name"] == product.name
    assert json_response["rating"] == product.rating
    assert json_response["brand"]["id"] == product.brand_id
    assert json_response["items_in_stock"] == product.items_in_stock


def test_create_product(client: FlaskClient, session: Session):
    brand = Brand(name="test", country_code="RU")
    category = Category(name="test")

    session.add(brand)
    session.add(category)
    session.commit()

    response = client.post('/products', data=json.dumps({
        "name": "",
        "rating": 5,
        "brand": brand.id,
        "categories": [category.id],
        "items_in_stock": 10
    }), content_type='application/json')

    assert response.status_code == 201


def test_update_product(client: FlaskClient, session: Session):
    brand1 = Brand(name="test1", country_code="RU")
    brand2 = Brand(name="test2", country_code="RU")

    category1 = Category(name="test1")
    category2 = Category(name="test2")

    product = Product(
        name="test",
        rating=5,
        brand=brand1,
        featured=False,
        categories=[category1],
        items_in_stock=1
    )

    session.add(product)
    session.add(brand1)
    session.add(brand2)
    session.add(category1)
    session.add(category2)

    session.commit()

    response = client.put(f"/products/{product.id}", data=json.dumps({
        "name": "test2",
        "rating": 6,
        "brand": brand2.id,
        "categories": [category2.id],
        "items_in_stock": 2
    }), content_type='application/json')

    assert response.status_code == 200

    session.refresh(product)

    assert product.name == "test2"
    assert product.rating == 6
    assert product.brand_id == brand2.id
    assert set(product.categories) == {category2}
    assert product.items_in_stock == 2
