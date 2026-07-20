from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_register_and_login():
    email = "test@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "rahasia123", "full_name": "Tester"})
    assert r.status_code in (201, 409)  # 409 kalau test dijalankan ulang

    r = client.post("/api/v1/auth/login", json={"email": email, "password": "rahasia123"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email
