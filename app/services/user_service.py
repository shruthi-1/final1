"""
User Service - Business Logic for User Operations
"""
from typing import Optional, List
from datetime import datetime
import logging

from app.database.schemas import User, UserCreate, UserUpdate
from app.utils.error_handlers import DatabaseException, NotFoundException

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related operations"""
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            user = User(
                name=user_data.name,
                email=user_data.email,
                age=user_data.age,
                height=user_data.height,
                weight=user_data.weight,
                fitness_level=user_data.fitness_level,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await user.insert()
            logger.info(f"User created successfully: {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise DatabaseException(f"Failed to create user: {str(e)}", "create_user")
    
    @staticmethod
    async def get_user(user_id: str) -> User:
        """Get user by ID"""
        try:
            user = await User.get(user_id)
            if not user:
                raise NotFoundException(f"User not found: {user_id}", "User")
            return user
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise DatabaseException(f"Failed to get user: {str(e)}", "get_user")
    
    @staticmethod
    async def increment_workout_count(user_id: str) -> User:
        """Increment user's total workout count"""
        try:
            user = await UserService.get_user(user_id)
            user.total_workouts += 1
            user.updated_at = datetime.utcnow()
            await user.save()
            return user
        except Exception as e:
            logger.error(f"Failed to increment workout count: {e}")
            raise DatabaseException(f"Failed to increment workout count: {str(e)}", "increment_workout_count")
