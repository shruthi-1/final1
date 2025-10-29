"""
Workout Service - Using NutriX Actual Database (2918 exercises)
Complete implementation with safety, muscle tracking, and warmup suggestions
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random
import pandas as pd
import os

from app.database.schemas import Workout, User, WorkoutCreate
from app.utils.error_handlers import DatabaseException, ValidationException, NotFoundException
from app.services.model_service import ModelService
from app.services.user_service import UserService
from config import settings

logger = logging.getLogger(__name__)

# Load actual NutriX exercise database
EXERCISE_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'nutrix_exercise_database.csv')
EXERCISE_DF = pd.read_csv(EXERCISE_DB_PATH)

# Muscle recovery requirements (days of rest needed)
RECOVERY_DAYS = {
    'Abdominals': 1,
    'Quadriceps': 2,
    'Hamstrings': 2,
    'Glutes': 2,
    'Chest': 2,
    'Shoulders': 1,
    'Biceps': 1,
    'Triceps': 1,
    'Lats': 2,
    'Middle Back': 2,
    'Lower Back': 2,
    'Calves': 1,
    'Forearms': 1,
    'Traps': 1,
    'Abductors': 1,
    'Adductors': 1,
    'Neck': 1
}

# Equipment mapping
MINIMAL_EQUIPMENT = ['Bodyweight', 'Other']
HOME_GYM = ['Bodyweight', 'Dumbbell', 'Kettlebells', 'Bands', 'Other']
FULL_GYM = list(EXERCISE_DF['Equipment'].unique())


class WorkoutService:
    """Service for workout-related operations with safety and muscle tracking"""
    
    @staticmethod
    async def create_workout(workout_data: WorkoutCreate) -> Workout:
        """Create and log a workout"""
        try:
            user = await UserService.get_user(workout_data.user_id)
            
            workout = Workout(
                user_id=workout_data.user_id,
                exercises=workout_data.exercises,
                duration=workout_data.duration,
                difficulty=workout_data.difficulty,
                performance_score=workout_data.performance_score,
                calories_burned=workout_data.calories_burned,
                heart_rate_avg=workout_data.heart_rate_avg,
                notes=workout_data.notes,
                date=datetime.utcnow(),
                completed=False
            )
            
            await workout.insert()
            await UserService.increment_workout_count(workout_data.user_id)
            
            logger.info(f"Workout created for user {workout_data.user_id}")
            return workout
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to create workout: {e}")
            raise DatabaseException(f"Failed to create workout: {str(e)}", "create_workout")
    
    @staticmethod
    async def get_workout(workout_id: str) -> Workout:
        """Get workout by ID"""
        try:
            workout = await Workout.get(workout_id)
            if not workout:
                raise NotFoundException(f"Workout not found: {workout_id}", "Workout")
            return workout
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get workout: {e}")
            raise DatabaseException(f"Failed to get workout: {str(e)}", "get_workout")
    
    @staticmethod
    async def get_user_workouts(
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        completed_only: bool = False
    ) -> List[Workout]:
        """Get user's workout history"""
        try:
            query = Workout.find(Workout.user_id == user_id)
            if completed_only:
                query = query.find(Workout.completed == True)
            workouts = await query.sort(-Workout.date).skip(skip).limit(limit).to_list()
            return workouts
        except Exception as e:
            logger.error(f"Failed to get user workouts: {e}")
            raise DatabaseException(f"Failed to get user workouts: {str(e)}", "get_user_workouts")
    
    @staticmethod
    async def complete_workout(workout_id: str, performance_score: Optional[float] = None) -> Workout:
        """Mark workout as completed and trigger ML update"""
        try:
            workout = await WorkoutService.get_workout(workout_id)
            workout.completed = True
            
            if performance_score is not None:
                workout.performance_score = performance_score
            
            await workout.save()
            await ModelService.update_model_with_workout(workout.user_id, workout)
            
            logger.info(f"Workout {workout_id} marked as completed")
            return workout
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to complete workout: {e}")
            raise DatabaseException(f"Failed to complete workout: {str(e)}", "complete_workout")
    
    @staticmethod
    async def get_last_worked_muscles(user_id: str, days: int = 7) -> Dict[str, datetime]:
        """Get last workout date for each muscle group"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            workouts = await Workout.find(
                Workout.user_id == user_id,
                Workout.completed == True,
                Workout.date >= cutoff_date
            ).sort(-Workout.date).to_list()
            
            muscle_last_worked = {}
            
            for workout in workouts:
                for exercise in workout.exercises:
                    exercise_id = exercise.get("exercise_id", None)
                    
                    if exercise_id is not None:
                        ex_data = EXERCISE_DF[EXERCISE_DF['exercise_id'] == exercise_id]
                        
                        if not ex_data.empty:
                            body_part = ex_data.iloc[0]['BodyPart']
                            
                            if body_part not in muscle_last_worked:
                                muscle_last_worked[body_part] = workout.date
            
            return muscle_last_worked
            
        except Exception as e:
            logger.error(f"Failed to get last worked muscles: {e}")
            return {}
    
    @staticmethod
    def _get_warmup_exercises(body_parts: List[str], count: int = 3) -> List[Dict[str, Any]]:
        """Get warmup/stretching exercises for given body parts"""
        warmups = []
        
        warmup_df = EXERCISE_DF[
            (EXERCISE_DF['Type'].isin(['Stretching', 'Cardio'])) &
            (EXERCISE_DF['BodyPart'].isin(body_parts + ['Abdominals'])) &
            (EXERCISE_DF['Equipment'].isin(['Bodyweight', 'Other']))
        ].dropna(subset=['Title'])
        
        if len(warmup_df) > 0:
            selected = warmup_df.sample(n=min(count, len(warmup_df)))
            
            for _, row in selected.iterrows():
                warmups.append({
                    'exercise_id': int(row['exercise_id']),
                    'name': row['Title'],
                    'type': 'warmup',
                    'duration': '30-60 seconds',
                    'body_part': row['BodyPart'],
                    'instructions': 'Light intensity to prepare muscles'
                })
        
        if len(warmups) < count:
            generic_warmups = [
                {'name': 'Jumping Jacks', 'type': 'warmup', 'duration': '60 seconds'},
                {'name': 'Arm Circles', 'type': 'warmup', 'duration': '30 seconds'},
                {'name': 'Leg Swings', 'type': 'warmup', 'duration': '30 seconds'}
            ]
            warmups.extend(generic_warmups[:count - len(warmups)])
        
        return warmups[:count]
    
    @staticmethod
    async def generate_workout(
        user_id: str,
        target_duration: int = 30,
        focus_areas: List[str] = None,
        equipment: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized AI-powered workout using YOUR 2918-exercise database
        """
        try:
            user = await UserService.get_user(user_id)
            muscle_last_worked = await WorkoutService.get_last_worked_muscles(user_id, days=7)
            
            # Determine muscles to avoid
            muscles_to_avoid = []
            for muscle, last_date in muscle_last_worked.items():
                days_since = (datetime.utcnow() - last_date).days
                recovery_needed = RECOVERY_DAYS.get(muscle, 2)
                
                if days_since < recovery_needed:
                    muscles_to_avoid.append(muscle)
            
            available_muscles = [m for m in RECOVERY_DAYS.keys() if m not in muscles_to_avoid]
            
            if not available_muscles:
                cooldown = WorkoutService._get_warmup_exercises(list(RECOVERY_DAYS.keys())[:5], 5)
                return {
                    'status': 'rest_day_recommended',
                    'message': 'All major muscle groups need rest.',
                    'recovery_exercises': cooldown
                }
            
            # Equipment setup
            if equipment is None:
                equipment = FULL_GYM
            elif 'minimal' in equipment:
                equipment = MINIMAL_EQUIPMENT
            elif 'home' in equipment:
                equipment = HOME_GYM
            
            # Target muscles
            if focus_areas:
                target_muscles = [m for m in focus_areas if m in available_muscles]
            else:
                target_muscles = random.sample(available_muscles, min(3, len(available_muscles)))
            
            # Filter exercises
            level_map = {
                'Beginner': ['Beginner'],
                'Intermediate': ['Beginner', 'Intermediate'],
                'Advanced': ['Beginner', 'Intermediate', 'Expert'],
                'Expert': ['Beginner', 'Intermediate', 'Expert']
            }
            allowed_levels = level_map.get(user.fitness_level.value, ['Beginner'])
            
            df = EXERCISE_DF[
                (EXERCISE_DF['Level'].isin(allowed_levels)) &
                (EXERCISE_DF['Equipment'].isin(equipment)) &
                (EXERCISE_DF['BodyPart'].isin(target_muscles)) &
                (~EXERCISE_DF['BodyPart'].isin(muscles_to_avoid))
            ].dropna(subset=['Title', 'BodyPart'])
            
            if len(df) == 0:
                raise ValidationException("No suitable exercises found", "exercise_selection")
            
            # Generate warmup
            warmup = WorkoutService._get_warmup_exercises(target_muscles, 3)
            
            # Select exercises
            warmup_time = 5
            available_time = target_duration - warmup_time
            exercise_count = max(4, min(8, available_time // 4))
            
            selected = []
            used_ids = set()
            
            for muscle in target_muscles:
                muscle_exs = df[df['BodyPart'] == muscle]
                if len(muscle_exs) > 0:
                    for _ in range(2):
                        available = muscle_exs[~muscle_exs['exercise_id'].isin(used_ids)]
                        if len(available) > 0:
                            ex = available.sample(n=1).iloc[0]
                            
                            if user.fitness_level.value == 'Beginner':
                                sets, reps = random.randint(2,3), random.randint(8,12)
                            else:
                                sets, reps = random.randint(3,4), random.randint(8,15)
                            
                            selected.append({
                                'exercise_id': int(ex['exercise_id']),
                                'name': ex['Title'],
                                'sets': sets,
                                'reps': reps,
                                'body_part': ex['BodyPart'],
                                'equipment': ex['Equipment']
                            })
                            used_ids.add(ex['exercise_id'])
                            
                            if len(selected) >= exercise_count:
                                break
                if len(selected) >= exercise_count:
                    break
            
            estimated_duration = warmup_time + (len(selected) * 4)
            estimated_calories = int(estimated_duration * 5)
            
            return {
                'status': 'success',
                'warmup': warmup,
                'exercises': selected,
                'duration': estimated_duration,
                'difficulty': 'Easy' if user.fitness_level.value == 'Beginner' else 'Medium',
                'estimated_calories': estimated_calories,
                'muscles_targeted': target_muscles,
                'muscles_avoided': muscles_to_avoid,
                'total_exercises': len(selected)
            }
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate workout: {e}")
            raise DatabaseException(f"Failed to generate workout: {str(e)}", "generate_workout")
