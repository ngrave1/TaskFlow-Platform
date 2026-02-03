from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field, PostgresDsn
from pathlib import Path
from typing import ClassVar


class DatabaseSettings(BaseSettings):
    url: PostgresDsn = Field(
    default="postgresql+asyncpg://admin:admin123@postgres:5432/user_service",
    alias="USER_SERVICE_DATABASE_URL"
    )
    
    env_path: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.parent / ".env"
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    
class AuthJWT(BaseModel):
    private_key_path: Path = Path(__file__).parent.parent / "certs/jwt-private.pem"
    public_key_path: Path = Path(__file__).parent.parent / "certs/jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire: int = Field(default= 15)
    refresh_token_expire: int = Field(default= 30)
    env_path: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.parent / ".env"
    model_config = SettingsConfigDict(env_file=str(env_path),
                                      env_file_encoding="utf-8",
                                      extra="ignore",
                                      )


class Settings(BaseSettings):
    database: DatabaseSettings = DatabaseSettings()
    auth_jwt: AuthJWT = AuthJWT()


settings = Settings()