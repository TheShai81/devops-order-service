import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_orders_route_exists(client):
    response = client.get("/orders")
    assert response.status_code in [200, 500]
