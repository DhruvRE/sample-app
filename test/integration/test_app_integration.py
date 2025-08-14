import requests

BASE_URL = "http://localhost:8080"

def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}

def test_user_endpoint():
    response = requests.get(f"{BASE_URL}/user")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dhruv"
    assert data["role"] == "Developer"
