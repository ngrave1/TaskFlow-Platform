import pytest


@pytest.mark.asyncio
async def test_register_user_success(test_client, override_dependencies, async_session):
    new_user = {
        "email": "newuser@example.com",
        "password": "newpassword123",
    }  # pragma: allowlist secret

    response = test_client.post("/register/", json=new_user)

    assert response.status_code == 200
    data = response.json()
    assert "user added" in data["message"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_user(test_client, override_dependencies, test_user):
    response = test_client.post(
        "/register/",
        json={
            "email": test_user["email"],
            "password": "differentpassword",
        },  # pragma: allowlist secret
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_login_success(test_client, override_dependencies, test_user):
    login_data = {
        "email": test_user["email"],
        "password": "testpassword123",
    }  # pragma: allowlist secret

    response = test_client.post("/login/", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_email(test_client, override_dependencies):
    login_data = {
        "email": "nonexistent@example.com",
        "password": "password123",
    }  # pragma: allowlist secret

    response = test_client.post("/login/", json=login_data)

    assert response.status_code == 401
    data = response.json()
    assert "Invalid email or password" in data["detail"]


@pytest.mark.asyncio
async def test_login_invalid_password(test_client, override_dependencies, test_user):
    login_data = {
        "email": test_user["email"],
        "password": "wrongpassword",
    }  # pragma: allowlist secret

    response = test_client.post("/login/", json=login_data)

    assert response.status_code == 401
    data = response.json()
    assert "Invalid email or password" in data["detail"]


@pytest.mark.asyncio
async def test_login_missing_fields(test_client, override_dependencies):
    response = test_client.post(
        "/login/", json={"password": "password123"}
    )  # pragma: allowlist secret
    assert response.status_code == 422

    response = test_client.post("/login/", json={"email": "test@example.com"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_check_valid_access_token(test_client, override_dependencies, test_user):
    # Сначала логинимся чтобы получить токены
    login_data = {
        "email": test_user["email"],
        "password": "testpassword123",
    }  # pragma: allowlist secret
    login_response = test_client.post("/login/", json=login_data)
    tokens = login_response.json()

    response = test_client.post(
        "/check_token/",
        json={
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_check_token_invalid_refresh(test_client, override_dependencies, test_user):
    login_data = {
        "email": test_user["email"],
        "password": "testpassword123",
    }  # pragma: allowlist secret
    login_response = test_client.post("/login/", json=login_data)
    tokens = login_response.json()

    response = test_client.post(
        "/check_token/",
        json={
            "access_token": tokens["access_token"],
            "refresh_token": "invalid.refresh.token",
        },
    )

    assert response.status_code == 200
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_full_user_cycle(test_client, override_dependencies):
    user_data = {
        "email": "cycleuser@example.com",
        "password": "cyclepassword123",
    }  # pragma: allowlist secret

    register_response = test_client.post("/register/", json=user_data)
    assert register_response.status_code == 200

    login_response = test_client.post("/login/", json=user_data)
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    check_response = test_client.post(
        "/check_token/",
        json={
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        },
    )
    assert check_response.status_code == 200
