from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Annotated
from .orm_utils import (
    get_user_by_email,
    create_user,
    session_add,
    delete_user_orm,
)
from .token_utils import (
    create_access_token,
    create_refresh_token,
    valid_auth_user,
    sub_check_access_token,
)
from .dependencies import SessionDep
from .user_schemes import UserCreateSchema, UserLoginSchema, UserDeleteSchema, TokensSchema
from .user_models import Users

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "user-service",
        "environment": "development",
    }

@router.post("/login/")
async def login(
    user_data: UserLoginSchema,
    session: SessionDep,
):
    from .token_utils import valid_auth_user
    user = await valid_auth_user(user_data, session)
    token = await create_access_token(user)
    refresh_token = await create_refresh_token(user)
    response = JSONResponse(
        content={
            "refresh_token": refresh_token,
            "access_token": token,
            "token_type": "Bearer",
        }
    )
    return response

@router.post("/register/")
async def register_user(
    session: SessionDep,
    user: UserCreateSchema,
):
    existing_user = await get_user_by_email(session, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User already exists"
        )

    new_user = await create_user(user.email, user.password)
    await session_add(session, new_user)
    return {"message": f"user added, email {user.email}"}

@router.delete("/delete_user")
async def delete_user(
    user_id: int,
    session: SessionDep,
):
    try:
        await delete_user_orm(session=session, user_id=user_id)
        return {"message": f"User with id {user_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@router.post("/check_token/")
async def check_access_token(
    tokens: TokensSchema,
    session: SessionDep,
):
    access_token = tokens.access_token
    refresh_token = tokens.refresh_token
    return await sub_check_access_token(
        session=session, access_token=access_token, refresh_token=refresh_token
    )