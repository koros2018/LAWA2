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

    # CORS
    cors_origins: list[str] = ["*"]

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

    # ── LLM Provider 配置 ──
    # LongCat
    llm_longcat_key: str = ""
    llm_longcat_base_url: str = "https://api.longcat.com/v1"
    llm_longcat_model: str = "LongCat-2.0-Preview"

    # OpenCode
    llm_opencode_key: str = ""
    llm_opencode_base_url: str = "https://api.opencode.com/v1"
    llm_opencode_model: str = "kimi-k2.6"

    # DeepSeek
    llm_deepseek_key: str = ""
    llm_deepseek_base_url: str = "https://api.deepseek.com/v1"
    llm_deepseek_model: str = "deepseek-chat"

    # SenseNova (Sensetime 商汤)
    llm_sensenova_key: str = ""
    llm_sensenova_base_url: str = "https://token.sensenova.cn/v1"
    llm_sensenova_model: str = "deepseek-v4-flash"

    # Ollama (本地兜底)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # LLM 通用
    llm_timeout_seconds: int = 30
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048


settings = Settings()
