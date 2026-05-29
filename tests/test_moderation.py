import pytest
from unittest.mock import patch, MagicMock

def get_auth_headers(client):
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    login = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

def mock_openai_response(decision: str, reason: str):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = f'{{"decision": "{decision}", "reason": "{reason}"}}'
    return mock_response

@patch("services.moderation_service.client.chat.completions.create")
def test_moderate_safe_content(mock_create, client):
    mock_create.return_value = mock_openai_response("safe", "Content is appropriate")
    headers = get_auth_headers(client)
    response = client.post("/moderations/", json={
        "content": "This is a friendly message"
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["data"]["decision"] == "safe"

@patch("services.moderation_service.client.chat.completions.create")
def test_moderate_rejected_content(mock_create, client):
    mock_create.return_value = mock_openai_response("rejected", "Content is harmful")
    headers = get_auth_headers(client)
    response = client.post("/moderations/", json={
        "content": "I want to harm people"
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["data"]["decision"] == "rejected"

@patch("services.moderation_service.client.chat.completions.create")
def test_moderate_empty_content(mock_create, client):
    headers = get_auth_headers(client)
    response = client.post("/moderations/", json={
        "content": ""
    }, headers=headers)
    assert response.status_code == 400

@patch("services.moderation_service.client.chat.completions.create")
def test_moderate_requires_auth(mock_create, client):
    response = client.post("/moderations/", json={
        "content": "test content"
    })
    assert response.status_code == 401

@patch("services.moderation_service.client.chat.completions.create")
def test_get_moderations_pagination(mock_create, client):
    mock_create.return_value = mock_openai_response("safe", "Content is appropriate")
    headers = get_auth_headers(client)
    for i in range(3):
        client.post("/moderations/", json={"content": f"test message {i}"}, headers=headers)
    response = client.get("/moderations/?page=1&limit=2", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]["moderations"]) == 2
    assert response.json()["data"]["meta"]["total"] == 3
    assert response.json()["data"]["meta"]["total_pages"] == 2

@patch("services.moderation_service.client.chat.completions.create")
def test_get_moderation_by_id(mock_create, client):
    mock_create.return_value = mock_openai_response("safe", "Content is appropriate")
    headers = get_auth_headers(client)
    create = client.post("/moderations/", json={"content": "test message"}, headers=headers)
    moderation_id = create.json()["data"]["id"]
    response = client.get(f"/moderations/{moderation_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == moderation_id

@patch("services.moderation_service.client.chat.completions.create")
def test_get_stats(mock_create, client):
    mock_create.return_value = mock_openai_response("safe", "Content is appropriate")
    headers = get_auth_headers(client)
    client.post("/moderations/", json={"content": "safe message"}, headers=headers)
    mock_create.return_value = mock_openai_response("rejected", "Content is harmful")
    client.post("/moderations/", json={"content": "harmful message"}, headers=headers)
    response = client.get("/moderations/stats", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["safe"] == 1
    assert response.json()["data"]["rejected"] == 1