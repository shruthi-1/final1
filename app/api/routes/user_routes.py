"""
User API Routes
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List
import logging

from app.database.schemas import UserCreate, UserUpdate, UserResponse, APIResponse
from app.services.user_service import UserService
from app.services.model_service import ModelService
from app.utils.error_handlers import ValidationException, NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        user = await UserService.create_user(user_data)
        
        # Initialize ML model for new user
        await ModelService.initialize_user_model(str(user.id))
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            age=user.age,
            height=user.height,
            weight=user.weight,
            fitness_level=user.fitness_level.value,
            total_workouts=user.total_workouts,
            created_at=user.created_at
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    try:
        user = await UserService.get_user(user_id)
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            age=user.age,
            height=user.height,
            weight=user.weight,
            fitness_level=user.fitness_level.value,
            total_workouts=user.total_workouts,
            created_at=user.created_at
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user")
