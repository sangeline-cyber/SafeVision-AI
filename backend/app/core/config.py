import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables and .env file.
    """
    PROJECT_NAME: str = "SafeVision AI"
    PROJECT_TITLE: str = "Context-Aware Autonomous Safety Event Detection and Evidence Verification System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "safevision_db"
    
    # Custom DATABASE_URL override if provided
    DATABASE_URL: Optional[str] = None

    # Security & JWT
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_SECRET_KEY_SAFEVISION_2026_HNX26PSI07"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]

    # Storage Paths
    STORAGE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
    VIDEO_STORAGE_PATH: str = os.path.join(STORAGE_DIR, "videos")
    EVIDENCE_CLIPS_PATH: str = os.path.join(STORAGE_DIR, "evidence_clips")
    THUMBNAILS_PATH: str = os.path.join(STORAGE_DIR, "thumbnails")

    @property
    def sync_database_uri(self) -> str:
        """
        Construct sync PostgreSQL database URI or use explicitly supplied DATABASE_URL.
        Uses postgresql+psycopg2:// for universal compatibility.
        """
        if self.DATABASE_URL:
            # Normalize postgres:// and postgresql:// to postgresql+psycopg2:// if not already qualified
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
            elif self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
