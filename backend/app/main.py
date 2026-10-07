import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan event handler for startup and shutdown procedures.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} ({settings.ENVIRONMENT})")
    logger.info(f"Database URI configured: {settings.sync_database_uri.split('@')[-1] if '@' in settings.sync_database_uri else settings.sync_database_uri}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


# Initialize FastAPI Application with Lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_TITLE,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_log(request: Request, call_next):
    """
    HTTP Middleware for request logging and latency measurement.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} ({process_time:.1f}ms)"
    )
    return response


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database operational error occurred", "type": exc.__class__.__name__}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Mount API routers
# Both /api/health and /api/... will be available
app.include_router(api_router, prefix=settings.API_V1_STR)
