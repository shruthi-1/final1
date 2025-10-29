"""
Error Handlers and Custom Exceptions
"""
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class ValidationException(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class DatabaseException(Exception):
    """Custom exception for database errors"""
    def __init__(self, message: str, operation: str = None):
        self.message = message
        self.operation = operation
        super().__init__(self.message)


class ModelException(Exception):
    """Custom exception for ML model errors"""
    def __init__(self, message: str, model_type: str = None):
        self.message = message
        self.model_type = model_type
        super().__init__(self.message)


class NotFoundException(Exception):
    """Custom exception for resource not found"""
    def __init__(self, message: str, resource: str = None):
        self.message = message
        self.resource = resource
        super().__init__(self.message)


async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions"""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error_type": "ValidationError",
            "message": exc.message,
            "field": exc.field
        }
    )


async def database_exception_handler(request: Request, exc: DatabaseException):
    """Handle database exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": "DatabaseError",
            "message": "A database error occurred",
            "operation": exc.operation
        }
    )


async def model_exception_handler(request: Request, exc: ModelException):
    """Handle ML model exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": "ModelError",
            "message": "An error occurred with the ML model"
        }
    )


async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions"""
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "error_type": "NotFoundError",
            "message": exc.message,
            "resource": exc.resource
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred"
        }
    )
