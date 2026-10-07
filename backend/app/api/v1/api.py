from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, videos

api_router = APIRouter()

# Mount health endpoints
api_router.include_router(health.router, tags=["Health"])

# Mount video processing and evidence endpoints under /api/v1/... and direct /api/...
api_router.include_router(videos.router, prefix="/v1", tags=["Video Processing & Fall Detection"])
api_router.include_router(videos.router, tags=["Video Processing Direct"])
