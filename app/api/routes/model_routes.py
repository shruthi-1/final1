"""
Model API Routes - ML Model Management
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from app.database.schemas import APIResponse
from app.services.model_service import ModelService
from app.utils.error_handlers import NotFoundException, ModelException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/user/{user_id}")
async def get_model_info(user_id: str) -> Dict[str, Any]:
    """
    Get ML model information for a user
    
    Returns model metadata including version, training samples, performance metrics
    """
    try:
        model_info = await ModelService.get_model_info(user_id)
        return model_info
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model info"
        )


@router.post("/initialize/{user_id}", response_model=APIResponse)
async def initialize_model(user_id: str):
    """
    Initialize ML model for a user
    
    Creates a new model instance for the user
    """
    try:
        model_weight = await ModelService.initialize_user_model(user_id)
        
        return APIResponse(
            status="success",
            message="Model initialized successfully",
            data={
                "user_id": user_id,
                "model_id": str(model_weight.id),
                "version": model_weight.version
            }
        )
    except Exception as e:
        logger.error(f"Error initializing model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize model"
        )


@router.post("/train/{user_id}")
async def train_model(user_id: str, force_retrain: bool = False) -> Dict[str, Any]:
    """
    Train or retrain user's ML model
    
    Requires at least 5 completed workouts for training
    Uses continuous learning (incremental updates)
    """
    try:
        result = await ModelService.train_user_model(user_id, force_retrain)
        return result
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ModelException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to train model"
        )
