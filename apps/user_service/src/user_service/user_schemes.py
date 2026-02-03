from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBaseSchema(BaseModel):
    email: EmailStr

class UserCreateSchema(UserBaseSchema):
    password: str = Field(min_length=6)

class UserLoginSchema(UserBaseSchema):
    password: str

class UserSchema(UserBaseSchema):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class UserDeleteSchema(BaseModel):
    id: int

class TokensSchema(BaseModel):
    access_token: str
    refresh_token: str