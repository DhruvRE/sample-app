import json
from app import app

def test_health_check_pass():
    tester = app.test_client()
    response = tester.get("/health")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["status"] == "UP"  # ✅ Pass

def test_get_user_pass():
    tester = app.test_client()
    response = tester.get("/user")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["name"] == "Dhruv"  # ✅ Pass
    assert data["role"] == "Developer"  # ✅ Pass

# def test_user_role_fail():
#     tester = app.test_client()
#     response = tester.get("/user")
#     data = json.loads(response.data)
#     assert data["role"] == "Tester"  # ❌ Fail

# def test_health_status_fail():
#     tester = app.test_client()
#     response = tester.get("/health")
#     data = json.loads(response.data)
#     assert data["status"] == "DOWN"  # ❌ Fail

def test_user_id_pass():
    tester = app.test_client()
    response = tester.get("/user")
    data = json.loads(response.data)
    assert data["id"] == 1  # ✅ Pass
