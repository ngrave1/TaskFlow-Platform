import pytest

def test_register_user_success(test_client, async_session):
    new_user = {
        "email": "newuser@example.com",
        "password": "newpassword123"
    }
    
    response = test_client.post("/register/", json=new_user)
    
    assert response.status_code == 200
    data = response.json()
    assert "user added" in data["message"].lower()
    assert new_user["email"] in data["message"]


def test_register_duplicate_user(test_client, test_user):
    response = test_client.post("/register/", json={
        "email": test_user["email"],
        "password": "differentpassword"
    })
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "User already exists"


def test_register_invalid_email(test_client):
    response = test_client.post("/register/", json={
        "email": "not-an-email",
        "password": "password123"
    })
    
    assert response.status_code == 422  


def test_register_short_password(test_client):
    response = test_client.post("/register/", json={
        "email": "shortpass@example.com",
        "password": "123"
    })
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_success(test_client, async_session):
    from src.user_service.orm_utils import create_user, session_add
    delete_user = await create_user("delete_me@example.com", "password123")
    await session_add(async_session, delete_user)
    await async_session.refresh(delete_user)
    response = test_client.delete(f"/delete_user?user_id={delete_user.id}")
    assert response.status_code == 200
    from sqlalchemy import select
    from src.user_service.user_models import Users
    
    result = await async_session.execute(
        select(Users).where(Users.id == delete_user.id)
    )
    deleted_user = result.scalar_one_or_none()
    
    assert deleted_user is None


def test_delete_nonexistent_user(test_client):
    response = test_client.delete("/delete_user?user_id=999999")

    assert response.status_code == 500
    data = response.json()
    assert "Error deleting user" in data["detail"]

def test_delete_user_invalid_id(test_client):
    response = test_client.delete("/delete_user?user_id=not-a-number")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_full_user_cycle(test_client, async_session):
    user_data = {
        "email": "cycleuser@example.com",
        "password": "cyclepassword123"
    }
    
    register_response = test_client.post("/register/", json=user_data)
    assert register_response.status_code == 200
    
    login_response = test_client.post("/login/", json=user_data)
    assert login_response.status_code == 200
    
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    check_response = test_client.post("/check_token/", json={
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    })
    
    assert check_response.status_code == 200
    check_data = check_response.json()
    assert check_data["status"] is True


def test_password_hashing():
    from src.user_service.password_utils import hash_password, check_password
    
    password = "testpassword"
    hashed = hash_password(password)
    
    assert hashed != password.encode()
    
    assert check_password(password, hashed) is True
    
    assert check_password("wrongpassword", hashed) is False


@pytest.mark.asyncio
async def test_jwt_encode_decode(test_tokens):
    from src.user_service.token_utils import decode_jwt
    
    decoded = await decode_jwt(test_tokens["access_token"])
    
    assert "sub" in decoded
    assert "token_type" in decoded
    assert decoded["token_type"] == "access_token"
    assert "email" in decoded
