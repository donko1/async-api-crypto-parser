from fastapi.testclient import TestClient
from app.main import app


def test_read_status():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_active_status():
    client = TestClient(app)
    response = client.get("/")
    assert response.json()["status"] == "active"
