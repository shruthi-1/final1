"""
Exercise Recommendation System using Collaborative Filtering
Recommends exercises based on similar users' preferences
"""
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ExerciseRecommender:
    """Collaborative filtering for exercise recommendations."""
    
    def __init__(self, db):
        self.db = db
        self.user_exercise_matrix = None
        self.user_similarity_matrix = None
        self.user_ids = []
        self.exercise_ids = []
    
    def build_interaction_matrix(self) -> bool:
        """Build user-exercise interaction matrix from session logs."""
        try:
            # Get all sessions with exercise data
            sessions = list(self.db.session_logs.find({
                "exercises_completed": {"$exists": True, "$ne": []}
            }))
            
            if len(sessions) < 5:
                logger.warning("Not enough session data for recommendations")
                return False
            
            # Build interactions list
            interactions = []
            for session in sessions:
                user_id = session.get('user_id')
                satisfaction = session.get('satisfaction', 5)
                completion = session.get('completion_percent', 0.8)
                
                # Interaction score: satisfaction weighted by completion
                score = (satisfaction / 5.0) * completion
                
                for exercise_id in session.get('exercises_completed', []):
                    interactions.append({
                        'user_id': user_id,
                        'exercise_id': exercise_id,
                        'score': score
                    })
            
            if not interactions:
                return False
            
            # Create DataFrame and pivot
            df = pd.DataFrame(interactions)
            
            # Aggregate multiple interactions (take mean)
            df = df.groupby(['user_id', 'exercise_id'])['score'].mean().reset_index()
            
            # Pivot to create user-exercise matrix
            self.user_exercise_matrix = df.pivot(
                index='user_id',
                columns='exercise_id',
                values='score'
            ).fillna(0)
            
            self.user_ids = self.user_exercise_matrix.index.tolist()
            self.exercise_ids = self.user_exercise_matrix.columns.tolist()
            
            # Compute user similarity matrix
            self.user_similarity_matrix = cosine_similarity(self.user_exercise_matrix)
            
            logger.info(f"Built interaction matrix: {len(self.user_ids)} users, {len(self.exercise_ids)} exercises")
            return True
            
        except Exception as e:
            logger.error(f"Error building interaction matrix: {e}")
            return False
    
    def get_recommendations(self, user_id: str, n: int = 10) -> List[Dict[str, Any]]:
        """Get exercise recommendations for a user."""
        try:
            # Build matrix if not already built
            if self.user_exercise_matrix is None:
                if not self.build_interaction_matrix():
                    return self._fallback_recommendations(user_id, n)
            
            # Check if user exists in matrix
            if user_id not in self.user_ids:
                return self._fallback_recommendations(user_id, n)
            
            user_idx = self.user_ids.index(user_id)
            
            # Get similar users
            similarities = self.user_similarity_matrix[user_idx]
            similar_user_indices = np.argsort(similarities)[::-1][1:6]  # Top 5 similar users
            
            # Get exercises the user hasn't done
            user_exercises = set(
                self.user_exercise_matrix.loc[user_id]
                [self.user_exercise_matrix.loc[user_id] > 0].index
            )
            
            # Calculate weighted scores for unrated exercises
            exercise_scores = {}
            
            for sim_idx in similar_user_indices:
                similar_user_id = self.user_ids[sim_idx]
                similarity_score = similarities[sim_idx]
                
                # Get exercises this similar user liked
                liked_exercises = self.user_exercise_matrix.loc[similar_user_id]
                
                for exercise_id, score in liked_exercises.items():
                    if score > 0.6 and exercise_id not in user_exercises:
                        if exercise_id not in exercise_scores:
                            exercise_scores[exercise_id] = 0
                        exercise_scores[exercise_id] += similarity_score * score
            
            # Sort and get top N
            sorted_exercises = sorted(
                exercise_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:n]
            
            # Fetch exercise details
            recommendations = []
            for exercise_id, score in sorted_exercises:
                exercise = self.db.exercises.find_one({"exercise_id_clean": exercise_id})
                
                if exercise:
                    recommendations.append({
                        'exercise_id': exercise_id,
                        'name': exercise.get('Title', ''),
                        'body_part': exercise.get('BodyPart', ''),
                        'equipment': exercise.get('Equipment', ''),
                        'confidence_score': min(1.0, score / 5.0),
                        'reason': f"Users similar to you rated this highly"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _fallback_recommendations(self, user_id: str, n: int) -> List[Dict[str, Any]]:
        """Fallback recommendations based on user profile."""
        try:
            user = self.db.users.find_one({"user_id": user_id})
            if not user:
                return []
            
            # Get highly rated exercises matching user's goal
            goal = user.get('primary_goal', 'general_fitness')
            equipment = user.get('equipment_list', ['Bodyweight'])
            
            exercises = list(self.db.exercises.find({
                "Equipment": {"$in": equipment},
                "Rating": {"$gte": 4.0},
                "is_active": True
            }).sort("Rating", -1).limit(n))
            
            recommendations = []
            for exercise in exercises:
                recommendations.append({
                    'exercise_id': exercise.get('exercise_id_clean', ''),
                    'name': exercise.get('Title', ''),
                    'body_part': exercise.get('BodyPart', ''),
                    'equipment': exercise.get('Equipment', ''),
                    'confidence_score': 0.5,
                    'reason': f"Highly rated for {goal.replace('_', ' ')}"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in fallback recommendations: {e}")
            return []
