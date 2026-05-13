from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TeamFlow"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "teamflow-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    DATABASE_URL: str = "sqlite:///./teamflow_app.db"

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB

    AI_API_KEY: Optional[str] = None
    AI_API_BASE: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        extra="ignore",
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return True

        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        return True


settings = Settings()
