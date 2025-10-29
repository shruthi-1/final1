"""
Workout API Routes - Complete Implementation
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
import logging

from app.database.schemas import (
    WorkoutCreate, WorkoutResponse, WorkoutGenerateRequest, APIResponse
)
from app.services.workout_service import WorkoutService
from app.utils.error_handlers import ValidationException, NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(workout_data: WorkoutCreate):
    """
    Create and log a workout
    
    **Request Body:**
    - user_id: User ID
    - exercises: List of exercises with exercise_id, sets, reps
    - duration: Duration in minutes
    - difficulty: Easy, Medium, or Hard
    - performance_score: Optional (0-10)
    """
    try:
        workout = await WorkoutService.create_workout(workout_data)
        
        return WorkoutResponse(
            id=str(workout.id),
            user_id=workout.user_id,
            exercises=workout.exercises,
            duration=workout.duration,
            difficulty=workout.difficulty,
            performance_score=workout.performance_score,
            date=workout.date,
            completed=workout.completed
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating workout: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create workout")


@router.post("/generate")
async def generate_workout(request: WorkoutGenerateRequest):
    """
    Generate AI-powered personalized workout using YOUR 2918-exercise database
    
    **Request Body:**
    - user_id: User ID
    - target_duration: Target duration in minutes (default: 30)
    - focus_areas: Optional list of body parts (e.g., ["Chest", "Shoulders"])
    - equipment: Optional list of equipment types
    
    **Safety Features:**
    - Checks muscle recovery times
    - Avoids overworked muscles
    - Recommends rest days when needed
    - Includes warmup exercises
    """
    try:
        equipment = getattr(request, 'equipment', None)
        
        workout_plan = await WorkoutService.generate_workout(
            user_id=request.user_id,
            target_duration=request.target_duration,
            focus_areas=request.focus_areas,
            equipment=equipment
        )
        
        return workout_plan
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating workout: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate workout")


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(workout_id: str):
    """Get workout by ID"""
    try:
        workout = await WorkoutService.get_workout(workout_id)
        
        return WorkoutResponse(
            id=str(workout.id),
            user_id=workout.user_id,
            exercises=workout.exercises,
            duration=workout.duration,
            difficulty=workout.difficulty,
            performance_score=workout.performance_score,
            date=workout.date,
            completed=workout.completed
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting workout: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get workout")


@router.get("/user/{user_id}", response_model=List[WorkoutResponse])
async def get_user_workouts(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    completed_only: bool = Query(False)
):
    """Get user's workout history"""
    try:
        workouts = await WorkoutService.get_user_workouts(user_id, skip, limit, completed_only)
        
        return [
            WorkoutResponse(
                id=str(workout.id),
                user_id=workout.user_id,
                exercises=workout.exercises,
                duration=workout.duration,
                difficulty=workout.difficulty,
                performance_score=workout.performance_score,
                date=workout.date,
                completed=workout.completed
            )
            for workout in workouts
        ]
    except Exception as e:
        logger.error(f"Error getting user workouts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user workouts")


@router.put("/{workout_id}/complete", response_model=APIResponse)
async def complete_workout(
    workout_id: str,
    performance_score: Optional[float] = Query(None, ge=0.0, le=10.0)
):
    """
    Mark workout as completed
    
    **Triggers continuous learning system to update ML model**
    """
    try:
        workout = await WorkoutService.complete_workout(workout_id, performance_score)
        
        return APIResponse(
            status="success",
            message="Workout completed successfully",
            data={"workout_id": str(workout.id), "triggers_ml_update": True}
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing workout: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete workout")
