import pytest
from sqlalchemy import select
from src.user_service.orm_utils import create_user
from src.user_service.user_models import Users

from .conftest import session_add


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
    assert new_user["email"] in data["message"]

    await async_session.commit()
    result = await async_session.execute(select(Users).where(Users.email == new_user["email"]))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == new_user["email"]


@pytest.mark.asyncio
async def test_register_duplicate_user(
    test_client, override_dependencies, async_session, test_user
):
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


def test_register_invalid_email(test_client):
    response = test_client.post(
        "/register/",
        json={"email": "not-an-email", "password": "password123"},  # pragma: allowlist secret
    )

    assert response.status_code == 422


def test_register_short_password(test_client):
    response = test_client.post(
        "/register/",
        json={"email": "shortpass@example.com", "password": "123"},  # pragma: allowlist secret
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_success(test_client, override_dependencies, async_session):
    delete_user = await create_user(
        "delete_me@example.com", "password123"
    )  # pragma: allowlist secret
    await session_add(async_session, delete_user)
    user_id = delete_user.id

    response = test_client.delete(f"/delete_user?user_id={user_id}")
    assert response.status_code == 200

    await async_session.commit()
    result = await async_session.execute(select(Users).where(Users.id == user_id))
    deleted_user = result.scalar_one_or_none()
    assert deleted_user is None


@pytest.mark.asyncio
async def test_delete_nonexistent_user(test_client, override_dependencies, async_session):
    response = test_client.delete("/delete_user?user_id=999999")

    assert response.status_code == 404
    data = response.json()
    assert "User with id 999999 not found" in data["detail"]


def test_delete_user_invalid_id(test_client):
    response = test_client.delete("/delete_user?user_id=not-a-number")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(test_client, override_dependencies, async_session):
    response = test_client.get("/receive_user_by_id/999999")

    assert response.status_code == 404
    data = response.json()
    assert "There is no user with this id" in data["detail"]


@pytest.mark.asyncio
async def test_full_user_cycle(test_client, override_dependencies, async_session):
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
