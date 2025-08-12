import json
from app import app

def test_health_check():
    tester = app.test_client()
    response = tester.get("/health")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["status"] == "UP"

def test_get_user():
    tester = app.test_client()
    response = tester.get("/user")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["name"] == "DhruvRE"
    assert data["role"] == "Developer"
