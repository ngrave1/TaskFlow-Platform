"""Tests for database utilities."""

import contextlib

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.user_service.orm_utils import (
    create_user,
    delete_user_orm,
    get_session,
    get_user_by_email,
    get_user_by_id,
)
from src.user_service.password_utils import check_password
from src.user_service.user_models import Users

from .conftest import session_add


class TestGetSession:
    """Test get_session function."""

    @pytest.mark.asyncio
    async def test_get_session_returns_async_session(self, async_session):
        """Test get_session returns AsyncSession."""
        session_gen = get_session()
        session = await session_gen.__anext__()

        assert isinstance(session, AsyncSession)
        assert session.is_active

        with contextlib.suppress(StopAsyncIteration):
            await session_gen.__anext__()


class TestGetUserByEmail:
    """Test get_user_by_email function."""

    @pytest.mark.asyncio
    async def test_get_existing_user_by_email(self, async_session, test_user):
        """Test getting existing user by email."""
        user = await get_user_by_email(async_session, test_user["email"])

        assert user is not None
        assert user.email == test_user["email"]
        assert user.id == test_user["id"]
        assert isinstance(user.password, bytes)

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_by_email(self, async_session):
        """Test getting non-existent user by email."""
        user = await get_user_by_email(async_session, "nonexistent@example.com")
        assert user is None


class TestGetUserById:
    """Test get_user_by_id function."""

    @pytest.mark.asyncio
    async def test_get_existing_user_by_id(self, async_session, test_user):
        """Test getting existing user by ID."""
        user = await get_user_by_id(async_session, test_user["id"])

        assert user is not None
        assert user.id == test_user["id"]
        assert user.email == test_user["email"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_by_id(self, async_session):
        """Test getting non-existent user by ID."""
        user = await get_user_by_id(async_session, 999999)
        assert user is None


class TestCreateUser:
    """Test create_user function."""

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation."""
        email = "newuser@test.com"
        password = "securepassword123"

        user = await create_user(email, password)

        assert user is not None
        assert user.email == email
        assert isinstance(user.password, bytes)
        assert len(user.password) > 0
        assert check_password(password, user.password)

    @pytest.mark.asyncio
    async def test_create_user_with_special_characters(self):
        """Test user creation with special characters."""
        email = "user.name+tag@example.co.uk"
        password = "password123!@#"

        user = await create_user(email, password)

        assert user.email == email
        assert isinstance(user.password, bytes)

    @pytest.mark.asyncio
    async def test_create_user_empty_password(self):
        """Test user creation with empty password."""
        email = "empty@test.com"
        password = ""

        user = await create_user(email, password)

        assert user.email == email
        assert isinstance(user.password, bytes)
        assert len(user.password) > 0


class TestSessionAdd:
    """Test session_add helper function."""

    @pytest.mark.asyncio
    async def test_session_add_success(self, async_session):
        """Test successful session addition."""
        email = "sessionadd@test.com"
        password = "password123"

        user = await create_user(email, password)
        assert user.id is None

        await session_add(async_session, user)
        assert user.id is not None

        result = await async_session.execute(select(Users).where(Users.id == user.id))
        db_user = result.scalar_one()

        assert db_user.email == email
        assert db_user.password == user.password

    @pytest.mark.asyncio
    async def test_session_add_rollback_on_error(self, async_session):
        """Test rollback on error."""
        invalid_user = Users(password=b"hashedpassword")

        with pytest.raises(Exception) as exc_info:
            await session_add(async_session, invalid_user)
        assert exc_info.value is not None
        assert async_session.is_active


class TestDeleteUserOrm:
    """Test delete_user_orm function."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, async_session):
        """Test successful user deletion."""
        email = "todelete@test.com"
        password = "password123"

        user = await create_user(email, password)
        await session_add(async_session, user)

        user_id = user.id
        await delete_user_orm(async_session, user_id)

        result = await async_session.execute(select(Users).where(Users.id == user_id))
        deleted_user = result.scalar_one_or_none()

        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, async_session):
        """Test deleting non-existent user."""
        with pytest.raises(ValueError, match="User with id 999999 not found"):
            await delete_user_orm(async_session, 999999)

    @pytest.mark.asyncio
    async def test_delete_user_twice(self, async_session):
        """Test deleting same user twice."""
        user = await create_user("double@test.com", "password123")
        await session_add(async_session, user)

        user_id = user.id
        await delete_user_orm(async_session, user_id)

        with pytest.raises(ValueError, match=f"User with id {user_id} not found"):
            await delete_user_orm(async_session, user_id)


class TestPasswordHashingIntegration:
    """Test password hashing integration."""

    @pytest.mark.asyncio
    async def test_password_hashing_roundtrip(self, async_session):
        """Test password hashing roundtrip."""
        email = "hash_test@example.com"
        plain_password = "MySecurePassword123!"

        user = await create_user(email, plain_password)
        await session_add(async_session, user)

        db_user = await get_user_by_email(async_session, email)

        assert db_user is not None
        assert check_password(plain_password, db_user.password) is True
        assert check_password("WrongPassword", db_user.password) is False

    @pytest.mark.asyncio
    async def test_password_salts_are_unique(self, async_session):
        """Test password salts are unique."""
        password = "samepassword"
        user1 = await create_user("user1@test.com", password)
        user2 = await create_user("user2@test.com", password)

        await session_add(async_session, user1)
        await session_add(async_session, user2)

        assert user1.password != user2.password
        assert check_password(password, user1.password)
        assert check_password(password, user2.password)


class TestTransactionHandling:
    """Test transaction handling."""

    @pytest.mark.asyncio
    async def test_independent_sessions(self, async_engine):
        """Test independent sessions."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        async_session_factory = async_sessionmaker(
            async_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        async with async_session_factory() as session1, async_session_factory() as session2:
            user = await create_user("session1@test.com", "pass123")
            session1.add(user)
            await session1.commit()

            result = await session2.execute(select(Users).where(Users.email == "session1@test.com"))
            user_in_session2 = result.scalar_one_or_none()

            assert user_in_session2 is not None
