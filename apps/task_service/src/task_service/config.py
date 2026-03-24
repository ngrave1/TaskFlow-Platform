import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    @property
    def url(self) -> str:
        if os.getenv("TESTING") == "true":
            return os.getenv(
                "TASK_SERVICE_DATABASE_URL", 
                "sqlite+aiosqlite:///file::memory:?cache=shared"
            )
        
        from common.config import common_settings
        base = common_settings.database.url.rstrip('/')
        if not base.endswith('/'):
            base = base + '/'
        return f"{base}task_service"
    
    @property
    def pool_size(self) -> int:
        if os.getenv("TESTING") == "true":
            return 5
        from common.config import common_settings
        return common_settings.database.pool_size
    
    @property
    def echo(self) -> bool:
        if os.getenv("TESTING") == "true":
            return False
        from common.config import common_settings
        return common_settings.database.echo


settings = Settings()