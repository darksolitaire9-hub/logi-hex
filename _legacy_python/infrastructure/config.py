# infrastructure/config.py
from functools import cached_property

import bcrypt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_title: str = "logi-hex"
    app_version: str = "0.1.0"
    database_url: str = "sqlite+aiosqlite:///./logi.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = False

    admin_username: str = "admin"
    admin_password: str = ""  # plain text from env
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    @cached_property
    def admin_password_hash(self) -> bytes:
        return bcrypt.hashpw(self.admin_password.encode(), bcrypt.gensalt())


settings = Settings()
