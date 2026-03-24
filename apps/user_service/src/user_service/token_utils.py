from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .orm_utils import get_user_by_email, get_user_by_id
from .password_utils import check_password
from .user_models import Users
from .user_schemes import TokensSchema, UserLoginSchema


async def encode_jwt(
    payload: dict,
    token_type: str,
    private_key: str = settings.auth_jwt.private_key_path.read_text(),
    algorithm: str = settings.auth_jwt.algorithm,
):
    if token_type == "access_token":
        expire_time = timedelta(minutes=settings.auth_jwt.access_token_expire)
    else:
        expire_time = timedelta(days=settings.auth_jwt.refresh_token_expire)

    now = datetime.now(timezone.utc)
    expire = now + expire_time
    payload_exp = payload.copy()
    payload_exp.update(
        exp=expire,
        iat=now,
    )
    encoded = jwt.encode(payload_exp, private_key, algorithm=algorithm)
    return encoded


async def decode_jwt(
    token: str | bytes,
    public_key: str = settings.auth_jwt.public_key_path.read_text(),
    algorithm: str = settings.auth_jwt.algorithm,
):
    try:
        decoded = jwt.decode(token, public_key, algorithms=[algorithm])
        return decoded
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


async def valid_auth_user(credentials: UserLoginSchema, session: AsyncSession):
    result = await get_user_by_email(session, credentials.email)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access = check_password(password=credentials.password, hashed_password=result.password)
    if access:
        return result
    raise HTTPException(status_code=401, detail="Invalid email or password")


async def create_access_token(
    user: Users,
):
    jwt_payload = {
        "sub": str(user.id),
        "token_type": "access_token",
        "email": user.email,
    }
    return await encode_jwt(payload=jwt_payload, token_type="access_token")


async def create_refresh_token(
    user: Users,
):
    jwt_payload = {
        "sub": str(user.id),
        "token_type": "refresh_token",
    }
    return await encode_jwt(payload=jwt_payload, token_type="refresh_token")


async def check_user(payload: dict, token_type: str, session: AsyncSession):
    if token_type == "access_token":
        result = await get_user_by_email(session, payload["email"])
    else:
        result = await get_user_by_id(session, int(payload["sub"]))
    return result


async def sub_check_access_token(
    session: AsyncSession,
    access_token: str,
    refresh_token: str,
):
    try:
        payload = await decode_jwt(access_token)
        result = await check_user(payload=payload, token_type="access_token", session=session)
        if result and payload["token_type"] == "access_token":
            return TokensSchema(access_token=access_token, refresh_token=refresh_token)
    except HTTPException:
        try:
            refreshed_token = await release_access_token(refresh_token, session)
            return TokensSchema(access_token=refreshed_token, refresh_token=refresh_token)
        except Exception as e:
            raise HTTPException(status_code=401, detail="Authorization failed") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


async def release_access_token(
    refresh_token: str,
    session: AsyncSession,
):
    try:
        payload = await decode_jwt(refresh_token)
        result = await check_user(payload=payload, token_type="refresh_token", session=session)
        if result and payload["token_type"] == "refresh_token":
            token = await create_access_token(result)
            return token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token release failed") from e
