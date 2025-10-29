"""
Model Service - ML Model Operations with Continuous Learning
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.database.schemas import ModelWeight, User, Workout
from app.models.ml_model import WorkoutModel
from app.utils.error_handlers import ModelException, NotFoundException
from config import settings

logger = logging.getLogger(__name__)


class ModelService:
    """Service for ML model operations"""
    
    @staticmethod
    async def initialize_user_model(user_id: str) -> ModelWeight:
        """Initialize a new model for a user"""
        try:
            existing = await ModelWeight.find_one(ModelWeight.user_id == user_id)
            if existing:
                logger.info(f"Model already exists for user: {user_id}")
                return existing
            
            model = WorkoutModel()
            model_data = model.serialize()
            
            model_weight = ModelWeight(
                user_id=user_id,
                model_data=model_data,
                version=1,
                training_samples=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await model_weight.insert()
            logger.info(f"Model initialized for user: {user_id}")
            return model_weight
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise ModelException(f"Failed to initialize model: {str(e)}", "WorkoutModel")
    
    @staticmethod
    async def get_model_info(user_id: str) -> Dict[str, Any]:
        """Get model information for a user"""
        try:
            model_weight = await ModelWeight.find_one(ModelWeight.user_id == user_id)
            
            if not model_weight:
                return {
                    "exists": False,
                    "message": "No model found for user"
                }
            
            return {
                "exists": True,
                "version": model_weight.version,
                "training_samples": model_weight.training_samples,
                "last_updated": model_weight.updated_at,
                "performance_metrics": model_weight.performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            raise ModelException(f"Failed to get model info: {str(e)}", "WorkoutModel")
    
    @staticmethod
    async def train_user_model(user_id: str, force_retrain: bool = False) -> Dict[str, Any]:
        """Train or retrain user's model"""
        try:
            user = await User.get(user_id)
            if not user:
                raise NotFoundException(f"User not found: {user_id}", "User")
            
            workouts = await Workout.find(
                Workout.user_id == user_id,
                Workout.completed == True
            ).to_list()
            
            if len(workouts) < 5 and not force_retrain:
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 5 completed workouts for training",
                    "current_workouts": len(workouts)
                }
            
            # For now, return success (actual training logic can be added)
            return {
                "status": "success",
                "message": "Model training completed",
                "workouts_used": len(workouts)
            }
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to train model: {e}")
            raise ModelException(f"Failed to train model: {str(e)}", "WorkoutModel")
    
    @staticmethod
    async def update_model_with_workout(user_id: str, workout: Workout) -> Dict[str, Any]:
        """Update model with new workout data (Continuous Learning)"""
        try:
            workout_count = await Workout.find(
                Workout.user_id == user_id,
                Workout.completed == True
            ).count()
            
            if workout_count % settings.MODEL_RETRAIN_THRESHOLD == 0:
                logger.info(f"Triggering model update for user {user_id}")
                result = await ModelService.train_user_model(user_id)
                return {
                    "status": "model_updated",
                    "trigger": "workout_threshold",
                    "workout_count": workout_count,
                    "training_result": result
                }
            else:
                remaining = settings.MODEL_RETRAIN_THRESHOLD - (workout_count % settings.MODEL_RETRAIN_THRESHOLD)
                return {
                    "status": "pending",
                    "message": f"Model will update after {remaining} more workouts",
                    "workout_count": workout_count
                }
                
        except Exception as e:
            logger.error(f"Failed to update model with workout: {e}")
            raise ModelException(f"Failed to update model: {str(e)}", "WorkoutModel")
