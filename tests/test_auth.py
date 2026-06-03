import pytest

def test_register_success(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 201
    assert response.json()["success"] == True
    assert response.json()["data"]["username"] == "testuser"

def test_register_duplicate_username(client):
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    response = client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_register_short_username(client):
    response = client.post("/auth/register", json={
        "username": "ab",
        "password": "testpass123"
    })
    assert response.status_code == 400

def test_register_short_password(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "password": "abc"
    })
    assert response.status_code == 400

def test_login_success(client):
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_token" in response.json()["data"]

def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert "Invalid credentials" in response.json()["detail"]

def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={
        "username": "nobody",
        "password": "testpass123"
    })
    assert response.status_code == 400

def test_refresh_token_success(client):
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    login = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    refresh_token = login.json()["data"]["refresh_token"]
    response = client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_refresh_token_reuse(client):
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    login = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    refresh_token = login.json()["data"]["refresh_token"]
    client.post("/auth/refresh", json={"refresh_token": refresh_token})
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401

def test_brute_force_lockout(client):
    client.post("/auth/register", json={
        "username": "bruteuser",
        "password": "testpass123"
    })
    for _ in range(5):
        client.post("/auth/login", json={
            "username": "bruteuser",
            "password": "wrongpassword"
        })
    response = client.post("/auth/login", json={
        "username": "bruteuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert "Too many failed login attempts" in response.json()["detail"]

def test_brute_force_clears_on_success(client):
    client.post("/auth/register", json={
        "username": "clearuser",
        "password": "testpass123"
    })
    for _ in range(3):
        client.post("/auth/login", json={
            "username": "clearuser",
            "password": "wrongpassword"
        })
    response = client.post("/auth/login", json={
        "username": "clearuser",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_brute_force_wrong_username(client):
    for _ in range(5):
        client.post("/auth/login", json={
            "username": "nonexistentuser",
            "password": "wrongpassword"
        })
    response = client.post("/auth/login", json={
        "username": "nonexistentuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert "Too many failed login attempts" in response.json()["detail"]