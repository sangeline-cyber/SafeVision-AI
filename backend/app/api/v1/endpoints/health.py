from fastapi import APIRouter, status, Response
from backend.app.schemas.health import HealthResponse, DatabaseHealthResponse
from backend.app.database.session import test_db_connection
from backend.app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Returns standard operational health status of the SafeVision AI service."
)
def get_health() -> dict:
    """
    Standard health check endpoint.
    Specification requirement format:
    {
      "status": "ok",
      "service": "SafeVision AI"
    }
    """
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME
    }


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    summary="Database Connectivity Health Check",
    description="Executes a live query against PostgreSQL database to verify connection health."
)
def get_database_health(response: Response) -> dict:
    """
    PostgreSQL connectivity health check endpoint.
    Performs real live connection test.
    """
    db_status = test_db_connection()
    if not db_status.get("connected"):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        response.status_code = status.HTTP_200_OK
    return db_status
