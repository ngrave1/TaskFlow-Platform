import structlog
from common.models.models import UserDtoSchema
from fastapi import APIRouter, HTTPException, status

from .dependencies import SessionDep
from .orm_utils import (
    create_user,
    delete_user_orm,
    get_user_by_email,
    get_user_by_id,
)
from .token_utils import (
    create_access_token,
    create_refresh_token,
    sub_check_access_token,
    valid_auth_user,
)
from .user_schemes import TokensSchema, UserCreateSchema, UserLoginSchema

logger = structlog.get_logger(__name__)

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
    logger.info("login.check.attempt", user_data=user_data)
    user = await valid_auth_user(user_data, session)
    token = await create_access_token(user)
    refresh_token = await create_refresh_token(user)
    logger.debug("login.check.success", user_data=user_data)
    return TokensSchema(access_token=token, refresh_token=refresh_token)


@router.post("/register/")
async def register_user(
    session: SessionDep,
    user: UserCreateSchema,
):
    existing_user = await get_user_by_email(session, user.email)
    if existing_user:
        logger.error("register.user_create.user_already_exist", user=user)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    new_user = await create_user(user.email, user.password)
    try:
        session.add(new_user)
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}") from e
    logger.info("register.user_create.success", user=user)
    return {"message": f"user added, email {user.email}"}


@router.delete("/delete_user")
async def delete_user(
    user_id: int,
    session: SessionDep,
):
    try:
        await delete_user_orm(session=session, user_id=user_id)
        logger.info("delete.user_delete.success", user_id=user_id)
        return {"message": f"User with id {user_id} deleted successfully"}
    except ValueError as e:
        logger.error("delete.user_delete.user_does_not_exist", user_id=user_id)
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}") from e


@router.post("/check_token/")
async def check_access_token(
    tokens: TokensSchema,
    session: SessionDep,
):
    logger.info("check_token.check_token.attempt", tokens=tokens)
    access_token = tokens.access_token
    refresh_token = tokens.refresh_token
    return await sub_check_access_token(
        session=session, access_token=access_token, refresh_token=refresh_token
    )


@router.get("/receive_user_by_id/{user_id}")
async def receive_user_by_id(
    session: SessionDep,
    user_id: int,
):
    try:
        logger.info("receive_user_by_id.receive_user.attempt", user_id=user_id)
        user = await get_user_by_id(session=session, user_id=user_id)
        if user is None:
            raise HTTPException(status_code=404, detail=f"There is no user with this id {user_id}")
        user_dto = UserDtoSchema.model_validate(user, from_attributes=True)
        return user_dto
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"There is no user with this id {user_id}"
        ) from e
