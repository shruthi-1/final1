"""
NutriX FastAPI Application
Main entry point for the API
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.api.routes import user_routes, workout_routes, model_routes
from app.database.mongodb import connect_to_mongo, close_mongo_connection
from app.utils.logger import setup_logging
from app.utils.error_handlers import (
    ValidationException,
    DatabaseException,
    ModelException,
    NotFoundException,
    validation_exception_handler,
    database_exception_handler,
    model_exception_handler,
    not_found_exception_handler,
    general_exception_handler
)
from config import settings

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting NutriX API...")
    await connect_to_mongo()
    logger.info("MongoDB connected successfully")
    yield
    # Shutdown
    logger.info("Shutting down NutriX API...")
    await close_mongo_connection()
    logger.info("MongoDB connection closed")


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

# CORS Configuration for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(ValidationException, validation_exception_handler)
app.add_exception_handler(DatabaseException, database_exception_handler)
app.add_exception_handler(ModelException, model_exception_handler)
app.add_exception_handler(NotFoundException, not_found_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(user_routes.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(workout_routes.router, prefix="/api/v1/workouts", tags=["Workouts"])
app.include_router(model_routes.router, prefix="/api/v1/models", tags=["Models"])


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "success",
        "message": "NutriX API is running",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "api_version": settings.API_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
