import os
from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.base import Base

from backend.app.models import (
    User, Camera, Zone, TrackedEntity, Incident, Evidence, Alert, EventRule
)

# Determine primary or fallback database URI
_configured_uri = settings.sync_database_uri
_active_uri = _configured_uri

if "postgresql" in _configured_uri:
    try:
        _test_eng = create_engine(_configured_uri, connect_args={"connect_timeout": 1})
        with _test_eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        _test_eng.dispose()
        logger.info(f"Connected to PostgreSQL database at {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
    except Exception as exc:
        logger.warning(f"PostgreSQL unreachable ({exc}). Falling back to local persistent SQLite database.")
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        sqlite_file = os.path.join(settings.STORAGE_DIR, "safevision.db")
        _active_uri = f"sqlite:///{sqlite_file}"

if "sqlite" in _active_uri:
    engine = create_engine(
        _active_uri,
        connect_args={"check_same_thread": False}
    )
    # Automatically ensure schema tables exist for SQLite
    Base.metadata.create_all(bind=engine)
else:
    engine = create_engine(
        _active_uri,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args={"connect_timeout": 5}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request with automatic teardown.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_db_connection() -> Dict[str, Any]:
    """
    Executes a direct connectivity check against the active database.
    """
    is_sqlite = "sqlite" in _active_uri
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            scalar = result.scalar()
            return {
                "connected": scalar == 1,
                "status": "connected" if scalar == 1 else "unreachable",
                "database": "sqlite" if is_sqlite else "postgresql",
                "server": "localhost" if is_sqlite else settings.POSTGRES_SERVER,
                "database_name": "safevision.db" if is_sqlite else settings.POSTGRES_DB,
                "ping": scalar == 1
            }
    except Exception as e:
        logger.warning(f"Database error during connectivity test: {e}")
        return {
            "connected": False,
            "status": "error",
            "database": "sqlite" if is_sqlite else "postgresql",
            "server": settings.POSTGRES_SERVER,
            "database_name": settings.POSTGRES_DB,
            "error": str(e),
            "details": str(e)
        }
