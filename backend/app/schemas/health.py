from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Schema for standard health response.
    Exact specification requirement:
    {
      "status": "ok",
      "service": "SafeVision AI"
    }
    """
    status: str = Field(..., description="Service status, e.g. ok")
    service: str = Field(default="SafeVision AI", description="Name of the service")
    version: Optional[str] = Field(default=None, description="Current version")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp")


class DatabaseHealthResponse(BaseModel):
    """
    Schema for PostgreSQL database connectivity health response.
    """
    status: str = Field(..., description="Connection status: connected, unreachable, or error")
    database: str = Field(default="postgresql", description="Database engine type")
    connected: bool = Field(..., description="True if database answered ping query")
    server: Optional[str] = Field(default=None, description="Database host server")
    database_name: Optional[str] = Field(default=None, description="Database schema name")
    error: Optional[str] = Field(default=None, description="Error message if unreachable")
    details: Optional[str] = Field(default=None, description="Diagnostic details if available")
