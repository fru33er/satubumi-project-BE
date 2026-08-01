import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Satubumi API Engine"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://satubumi.org"
    ]
    
    # Database (Default to SQLite for local development without Postgres container)
    POSTGRES_USER: str = "satubumi"
    POSTGRES_PASSWORD: str = "satubumipassword"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "satubumi_db"
    DATABASE_URL: str = "sqlite:///./satubumi.db"
    
    # JWT Auth
    SECRET_KEY: str = "supersecretjwtkeyforbackendauthenticationchangeinproduction"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # GEE
    GEE_PROJECT_ID: str = ""
    GEE_SERVICE_ACCOUNT_EMAIL: str = ""
    GEE_PRIVATE_KEY_FILE_PATH: str = ""
    USE_MOCK_GEE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
