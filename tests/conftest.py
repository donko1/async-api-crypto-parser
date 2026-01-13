import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def sample_coin_data():
    return {"id": "bitcoin", "name": "Bitcoin", "price": 45000}
