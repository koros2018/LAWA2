"""
LAWA2 配置
"""
from pydantic_settings import BaseSettings
from typing import Optional
from loguru import logger
from urllib.parse import quote_plus


class Settings(BaseSettings):
    app_name: str = "LAWA2"
    app_version: str = "2.0.0"
    api_port: int = 6290

    # 数据库
    db_type: str = "sqlite"  # sqlite | postgresql
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "lawa2"
    db_user: str = "lawa"
    db_password: str = ""
    db_path: str = "./lawa2.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    debug: bool = False

    @property
    def db_use_sqlite(self) -> bool:
        return self.db_type == "sqlite"

    # 认证
    secret_key: str = "lawa2-dev-secret-key-change-in-production"
    token_expire_minutes: int = 1440  # 24h

    @property
    def database_url(self) -> str:
        if self.db_type == "sqlite":
            return f"sqlite+aiosqlite:///{self.db_path}"
        pw = quote_plus(self.db_password) if self.db_password else ""
        return f"postgresql+asyncpg://{self.db_user}:{pw}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
