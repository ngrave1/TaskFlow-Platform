import pytest


def test_login_invalid_email(test_client):
    response = test_client.post(
        "/login/", json={"email": "nonexistent@example.com", "password": "password123"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"


def test_login_invalid_password(test_client, test_user):
    response = test_client.post(
        "/login/", json={"email": test_user["email"], "password": "wrongpassword"}
    )

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Invalid email or password"


def test_login_missing_fields(test_client):
    response = test_client.post("/login/", json={"password": "password123"})

    assert response.status_code == 422
    response = test_client.post("/login/", json={"email": "test@example.com"})

    assert response.status_code == 422


def test_check_valid_access_token(test_client, test_tokens):
    response = test_client.post(
        "/check_token/",
        json={
            "access_token": test_tokens["access_token"],
            "refresh_token": test_tokens["refresh_token"],
        },
    )

    assert response.status_code == 200
    data = response.json()

    if "token_type" in data:
        assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert "refresh_token" in data


def test_check_invalid_access_token(test_client, test_tokens):
    invalid_token = "invalid.token.here"
    response = test_client.post(
        "/check_token/",
        json={
            "access_token": invalid_token,
            "refresh_token": test_tokens["refresh_token"],
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert "Invalid token" in data["detail"]


def test_check_token_invalid_refresh(test_client, test_tokens):
    response = test_client.post(
        "/check_token/",
        json={
            "access_token": test_tokens["access_token"],
            "refresh_token": "invalid.refresh.token",
        },
    )

    assert response.status_code == 200
    data = response.json()
