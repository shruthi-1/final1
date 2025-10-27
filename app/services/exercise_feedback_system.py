"""
Exercise Feedback & Rating System
Tracks user feelings before/after workout and per-exercise ratings
Integrated with ML system for personalized recommendations
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PreWorkoutFeeling(str, Enum):
    """How user feels BEFORE workout."""
    ENERGIZED = "energized"
    NORMAL = "normal"
    TIRED = "tired"
    SORE = "sore"
    UNMOTIVATED = "unmotivated"
    STRESSED = "stressed"
    EXCELLENT = "excellent"

class PostWorkoutFeeling(str, Enum):
    """How user feels AFTER workout."""
    ACCOMPLISHED = "accomplished"
    ENERGIZED = "energized"
    EXHAUSTED = "exhausted"
    GREAT = "great"
    SATISFIED = "satisfied"
    DISAPPOINTED = "disappointed"
    SORE = "sore"
    PUMPED = "pumped"

class ExerciseDifficulty(str, Enum):
    """Perceived difficulty of exercise."""
    TOO_EASY = "too_easy"
    EASY = "easy"
    PERFECT = "perfect"
    CHALLENGING = "challenging"
    TOO_HARD = "too_hard"

class ExerciseFeedback:
    """Individual exercise feedback model."""

    def __init__(
        self,
        exercise_id: str,
        exercise_name: str,
        rating: int,  # 1-5 stars
        difficulty: ExerciseDifficulty,
        sets_completed: int,
        reps_completed: int,
        weight_used: Optional[float] = None,
        form_quality: Optional[int] = None,  # 1-5, optional
        enjoyment: Optional[int] = None,  # 1-5, optional
        would_repeat: bool = True,
        notes: str = ""
    ):
        self.exercise_id = exercise_id
        self.exercise_name = exercise_name
        self.rating = rating
        self.difficulty = difficulty
        self.sets_completed = sets_completed
        self.reps_completed = reps_completed
        self.weight_used = weight_used
        self.form_quality = form_quality
        self.enjoyment = enjoyment
        self.would_repeat = would_repeat
        self.notes = notes
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise_name,
            "rating": self.rating,
            "difficulty": self.difficulty.value,
            "sets_completed": self.sets_completed,
            "reps_completed": self.reps_completed,
            "weight_used": self.weight_used,
            "form_quality": self.form_quality,
            "enjoyment": self.enjoyment,
            "would_repeat": self.would_repeat,
            "notes": self.notes,
            "timestamp": self.timestamp.isoformat()
        }

class WorkoutSession:
    """Complete workout session with all feedback."""

    def __init__(
        self,
        user_id: str,
        workout_id: str,
        day_name: str,
        pre_workout_feeling: PreWorkoutFeeling,
        pre_workout_energy: int,  # 1-10 scale
        pre_workout_notes: str = ""
    ):
        self.user_id = user_id
        self.workout_id = workout_id
        self.day_name = day_name
        self.pre_workout_feeling = pre_workout_feeling
        self.pre_workout_energy = pre_workout_energy
        self.pre_workout_notes = pre_workout_notes
        self.started_at = datetime.utcnow()

        # Will be filled during/after workout
        self.exercise_feedback: List[ExerciseFeedback] = []
        self.post_workout_feeling: Optional[PostWorkoutFeeling] = None
        self.post_workout_energy: Optional[int] = None  # 1-10 scale
        self.overall_satisfaction: Optional[int] = None  # 1-5 stars
        self.overall_difficulty: Optional[ExerciseDifficulty] = None
        self.post_workout_notes: str = ""
        self.completed_at: Optional[datetime] = None
        self.duration_minutes: Optional[int] = None
        self.completion_percent: float = 0.0

    def add_exercise_feedback(self, feedback: ExerciseFeedback):
        """Add feedback for individual exercise."""
        self.exercise_feedback.append(feedback)
        logger.info(f"Added feedback for {feedback.exercise_name}: {feedback.rating}⭐")

    def complete_workout(
        self,
        post_workout_feeling: PostWorkoutFeeling,
        post_workout_energy: int,
        overall_satisfaction: int,
        overall_difficulty: ExerciseDifficulty,
        post_workout_notes: str = ""
    ):
        """Complete workout with post-workout feedback."""
        self.completed_at = datetime.utcnow()
        self.duration_minutes = int((self.completed_at - self.started_at).total_seconds() / 60)
        self.post_workout_feeling = post_workout_feeling
        self.post_workout_energy = post_workout_energy
        self.overall_satisfaction = overall_satisfaction
        self.overall_difficulty = overall_difficulty
        self.post_workout_notes = post_workout_notes

        # Calculate completion percentage
        if self.exercise_feedback:
            self.completion_percent = (len(self.exercise_feedback) / 
                                      len(self.exercise_feedback)) * 100  # Simplified

        logger.info(f"Workout completed: {self.duration_minutes} min, "
                   f"satisfaction {overall_satisfaction}⭐")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            "user_id": self.user_id,
            "workout_id": self.workout_id,
            "day_name": self.day_name,

            # Pre-workout data
            "pre_workout": {
                "feeling": self.pre_workout_feeling.value,
                "energy_level": self.pre_workout_energy,
                "notes": self.pre_workout_notes,
                "timestamp": self.started_at.isoformat()
            },

            # Exercise-level feedback
            "exercises": [fb.to_dict() for fb in self.exercise_feedback],

            # Post-workout data
            "post_workout": {
                "feeling": self.post_workout_feeling.value if self.post_workout_feeling else None,
                "energy_level": self.post_workout_energy,
                "overall_satisfaction": self.overall_satisfaction,
                "overall_difficulty": self.overall_difficulty.value if self.overall_difficulty else None,
                "notes": self.post_workout_notes,
                "timestamp": self.completed_at.isoformat() if self.completed_at else None
            },

            # Session metrics
            "session_metrics": {
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_minutes": self.duration_minutes,
                "completion_percent": self.completion_percent,
                "exercises_logged": len(self.exercise_feedback)
            },

            # Derived analytics
            "analytics": self._compute_analytics()
        }

    def _compute_analytics(self) -> Dict[str, Any]:
        """Compute analytics from feedback."""
        if not self.exercise_feedback:
            return {}

        ratings = [fb.rating for fb in self.exercise_feedback]
        enjoyments = [fb.enjoyment for fb in self.exercise_feedback if fb.enjoyment]
        form_qualities = [fb.form_quality for fb in self.exercise_feedback if fb.form_quality]

        return {
            "avg_exercise_rating": sum(ratings) / len(ratings) if ratings else 0,
            "avg_enjoyment": sum(enjoyments) / len(enjoyments) if enjoyments else None,
            "avg_form_quality": sum(form_qualities) / len(form_qualities) if form_qualities else None,
            "energy_delta": (self.post_workout_energy - self.pre_workout_energy) 
                           if self.post_workout_energy else None,
            "difficult_exercises": [
                fb.exercise_name for fb in self.exercise_feedback 
                if fb.difficulty in [ExerciseDifficulty.TOO_HARD, ExerciseDifficulty.CHALLENGING]
            ],
            "favorite_exercises": [
                fb.exercise_name for fb in self.exercise_feedback 
                if fb.rating >= 4 and fb.would_repeat
            ],
            "exercises_to_avoid": [
                fb.exercise_name for fb in self.exercise_feedback 
                if fb.rating <= 2 or not fb.would_repeat
            ]
        }


class FeedbackManager:
    """Manages workout session feedback and stores in MongoDB."""

    def __init__(self, main_db, history_db):
        """
        Args:
            main_db: Main nutrix database
            history_db: Workout history database
        """
        self.main_db = main_db
        self.history_db = history_db
        self.sessions_coll = history_db.workout_sessions  # New collection
        self.exercise_ratings_coll = history_db.exercise_ratings  # New collection
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes for feedback collections."""
        try:
            # Workout sessions indexes
            self.sessions_coll.create_index([
                ("user_id", 1),
                ("started_at", -1)
            ], name="user_sessions_idx")

            self.sessions_coll.create_index([
                ("workout_id", 1)
            ], name="workout_idx")

            # Exercise ratings indexes
            self.exercise_ratings_coll.create_index([
                ("user_id", 1),
                ("exercise_id", 1)
            ], name="user_exercise_idx")

            self.exercise_ratings_coll.create_index([
                ("exercise_id", 1),
                ("rating", -1)
            ], name="exercise_popularity_idx")

            logger.info("Feedback indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating feedback indexes: {e}")

    def save_session(self, session: WorkoutSession) -> str:
        """Save workout session with all feedback."""
        session_dict = session.to_dict()
        result = self.sessions_coll.insert_one(session_dict)

        # Update exercise ratings aggregation
        self._update_exercise_ratings(session)

        logger.info(f"Saved session {result.inserted_id} for user {session.user_id}")
        return str(result.inserted_id)

    def _update_exercise_ratings(self, session: WorkoutSession):
        """Update aggregated exercise ratings."""
        for feedback in session.exercise_feedback:
            self.exercise_ratings_coll.update_one(
                {
                    "user_id": session.user_id,
                    "exercise_id": feedback.exercise_id
                },
                {
                    "$push": {
                        "ratings": {
                            "rating": feedback.rating,
                            "difficulty": feedback.difficulty.value,
                            "enjoyment": feedback.enjoyment,
                            "would_repeat": feedback.would_repeat,
                            "timestamp": feedback.timestamp.isoformat()
                        }
                    },
                    "$inc": {"total_sessions": 1},
                    "$set": {
                        "exercise_name": feedback.exercise_name,
                        "last_performed": feedback.timestamp
                    }
                },
                upsert=True
            )

    def get_user_exercise_history(
        self,
        user_id: str,
        exercise_id: str
    ) -> Dict[str, Any]:
        """Get user's complete history with specific exercise."""
        rating_doc = self.exercise_ratings_coll.find_one({
            "user_id": user_id,
            "exercise_id": exercise_id
        })

        if not rating_doc:
            return {
                "total_sessions": 0,
                "avg_rating": 0,
                "ratings": []
            }

        ratings = rating_doc.get("ratings", [])
        avg_rating = sum(r["rating"] for r in ratings) / len(ratings) if ratings else 0

        return {
            "exercise_name": rating_doc.get("exercise_name"),
            "total_sessions": rating_doc.get("total_sessions", 0),
            "avg_rating": round(avg_rating, 2),
            "last_performed": rating_doc.get("last_performed"),
            "ratings": ratings[-10:]  # Last 10 ratings
        }

    def get_favorite_exercises(
        self,
        user_id: str,
        min_sessions: int = 3,
        min_rating: float = 4.0
    ) -> List[Dict[str, Any]]:
        """Get user's favorite exercises based on ratings."""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$addFields": {
                "avg_rating": {"$avg": "$ratings.rating"}
            }},
            {"$match": {
                "total_sessions": {"$gte": min_sessions},
                "avg_rating": {"$gte": min_rating}
            }},
            {"$sort": {"avg_rating": -1, "total_sessions": -1}},
            {"$limit": 20}
        ]

        favorites = list(self.exercise_ratings_coll.aggregate(pipeline))
        return favorites

    def get_exercises_to_avoid(
        self,
        user_id: str,
        min_sessions: int = 2,
        max_rating: float = 2.5
    ) -> List[Dict[str, Any]]:
        """Get exercises user dislikes."""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$addFields": {
                "avg_rating": {"$avg": "$ratings.rating"}
            }},
            {"$match": {
                "total_sessions": {"$gte": min_sessions},
                "avg_rating": {"$lte": max_rating}
            }},
            {"$sort": {"avg_rating": 1}},
            {"$limit": 20}
        ]

        to_avoid = list(self.exercise_ratings_coll.aggregate(pipeline))
        return to_avoid

    def get_user_feedback_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get summary of user's feedback over last N days."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        sessions = list(self.sessions_coll.find({
            "user_id": user_id,
            "started_at": {"$gte": cutoff.isoformat()}
        }))

        if not sessions:
            return {"total_sessions": 0}

        # Aggregate metrics
        pre_energies = [s["pre_workout"]["energy_level"] for s in sessions]
        post_energies = [
            s["post_workout"]["energy_level"] 
            for s in sessions 
            if s["post_workout"].get("energy_level")
        ]
        satisfactions = [
            s["post_workout"]["overall_satisfaction"]
            for s in sessions
            if s["post_workout"].get("overall_satisfaction")
        ]

        return {
            "total_sessions": len(sessions),
            "avg_pre_energy": sum(pre_energies) / len(pre_energies) if pre_energies else 0,
            "avg_post_energy": sum(post_energies) / len(post_energies) if post_energies else 0,
            "avg_satisfaction": sum(satisfactions) / len(satisfactions) if satisfactions else 0,
            "energy_improvement": (
                (sum(post_energies) / len(post_energies)) - 
                (sum(pre_energies) / len(pre_energies))
            ) if post_energies and pre_energies else 0,
            "completion_rate": sum(
                1 for s in sessions 
                if s.get("completed_at")
            ) / len(sessions) * 100
        }
