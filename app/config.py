from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_env: str = "development"
    port: int = 3001
    database_url: str = "sqlite+aiosqlite:///./eventguard.db"
    openweather_api_key: str = ""
    openweather_mode: str = "mock"
    jwt_secret: str = "supersecretjwtkeythatshouldbechanged"
    
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
