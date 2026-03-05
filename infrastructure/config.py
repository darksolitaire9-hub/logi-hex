# infrastructure/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_title: str = "logi-hex"
    app_version: str = "0.1.0"
    database_url: str = "sqlite+aiosqlite:///./logi.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = True


settings = Settings()
