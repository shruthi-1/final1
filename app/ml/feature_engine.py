"""
Feature engineering for ML models
Extracts and transforms features from user data
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Extract and engineer features from user workout data."""
    
    def __init__(self, db):
        self.db = db
    
    def extract_user_profile_features(self, user_id: str) -> Dict[str, Any]:
        """Extract features from user profile."""
        try:
            user = self.db.users.find_one({"user_id": user_id})
            if not user:
                return {}
            
            # Encode categorical variables
            fitness_level_map = {'Beginner': 1, 'Intermediate': 2, 'Expert': 3}
            goal_map = {
                'weight_loss': 1,
                'muscle_gain': 2,
                'strength': 3,
                'endurance': 4,
                'general_fitness': 5,
                'athletic': 6
            }
            
            features = {
                'age': user.get('age', 30),
                'bmi': user.get('bmi', 25.0),
                'bmi_category_encoded': self._encode_bmi_category(user.get('bmi_category', 'normal')),
                'fitness_level_encoded': fitness_level_map.get(user.get('fitness_level'), 2),
                'primary_goal_encoded': goal_map.get(user.get('primary_goal'), 5),
                'equipment_count': len(user.get('equipment_list', [])),
                'has_barbell': int('Barbell' in user.get('equipment_list', [])),
                'has_dumbbell': int('Dumbbell' in user.get('equipment_list', [])),
                'bodyweight_only': int(user.get('equipment_list') == ['Bodyweight'] or not user.get('equipment_list')),
                'has_injuries': int(len(user.get('injury_types', [])) > 0),
                'injury_count': len(user.get('injury_types', [])),
                'gender_encoded': self._encode_gender(user.get('gender', 'other'))
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting user profile features: {e}")
            return {}
    
    def extract_historical_features(self, user_id: str, lookback_days: int = 30) -> Dict[str, Any]:
        """Extract features from workout history."""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=lookback_days)).isoformat()
            
            sessions = list(self.db.session_logs.find({
                "user_id": user_id,
                "logged_at": {"$gte": cutoff_date}
            }).sort("logged_at", -1))
            
            if not sessions:
                return {
                    'total_sessions': 0,
                    'avg_completion_rate': 0.8,
                    'avg_satisfaction': 5.0,
                    'avg_rpe': 7.0,
                    'total_volume': 0,
                    'consistency_score': 0.0
                }
            
            # Calculate aggregate metrics
            completions = [s.get('completion_percent', 0.8) for s in sessions]
            satisfactions = [s.get('satisfaction', 5) for s in sessions]
            rpes = [s.get('avg_rpe', 7) for s in sessions if s.get('avg_rpe')]
            durations = [s.get('actual_duration', 45) for s in sessions]
            volumes = [s.get('total_volume', 0) for s in sessions if s.get('total_volume')]
            
            # Calculate consistency (sessions per week)
            if len(sessions) > 1:
                first_session = datetime.fromisoformat(sessions[-1].get('logged_at', ''))
                last_session = datetime.fromisoformat(sessions[0].get('logged_at', ''))
                days_span = (last_session - first_session).days + 1
                consistency = len(sessions) / max(1, days_span / 7)
            else:
                consistency = 0.0
            
            features = {
                'total_sessions': len(sessions),
                'avg_completion_rate': np.mean(completions),
                'std_completion_rate': np.std(completions),
                'avg_satisfaction': np.mean(satisfactions),
                'std_satisfaction': np.std(satisfactions),
                'avg_rpe': np.mean(rpes) if rpes else 7.0,
                'max_rpe': max(rpes) if rpes else 10.0,
                'min_rpe': min(rpes) if rpes else 4.0,
                'avg_duration': np.mean(durations),
                'total_volume': sum(volumes),
                'avg_volume_per_session': np.mean(volumes) if volumes else 0,
                'consistency_score': consistency,
                'completion_trend': self._calculate_trend(completions),
                'satisfaction_trend': self._calculate_trend(satisfactions),
                'days_since_last_session': (datetime.utcnow() - last_session).days if sessions else 999
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting historical features: {e}")
            return {}
    
    def extract_temporal_features(self, timestamp: datetime = None) -> Dict[str, Any]:
        """Extract time-based features."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        return {
            'day_of_week': timestamp.weekday(),  # 0=Monday, 6=Sunday
            'is_weekend': int(timestamp.weekday() >= 5),
            'week_of_year': timestamp.isocalendar()[1],
            'month': timestamp.month,
            'hour_of_day': timestamp.hour,
            'is_morning': int(6 <= timestamp.hour < 12),
            'is_afternoon': int(12 <= timestamp.hour < 18),
            'is_evening': int(18 <= timestamp.hour < 22)
        }
    
    def extract_exercise_features(self, exercise: Dict) -> Dict[str, Any]:
        """Extract features from an exercise."""
        try:
            body_part_map = self._get_body_part_encoding()
            equipment_map = self._get_equipment_encoding()
            
            features = {
                'body_part_encoded': body_part_map.get(exercise.get('BodyPart', ''), 0),
                'equipment_encoded': equipment_map.get(exercise.get('Equipment', ''), 0),
                'difficulty_encoded': self._encode_difficulty(exercise.get('Level', 'Intermediate')),
                'rating': exercise.get('Rating', 0),
                'is_compound': int(exercise.get('Type', '').lower() == 'compound'),
                'is_bodyweight': int(exercise.get('Equipment', '') == 'Bodyweight')
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting exercise features: {e}")
            return {}
    
    def create_feature_vector(self, user_id: str, include_temporal: bool = True) -> np.ndarray:
        """Create complete feature vector for ML models."""
        try:
            # Extract all feature groups
            profile_features = self.extract_user_profile_features(user_id)
            historical_features = self.extract_historical_features(user_id)
            
            # Combine features
            all_features = {**profile_features, **historical_features}
            
            if include_temporal:
                temporal_features = self.extract_temporal_features()
                all_features.update(temporal_features)
            
            # Convert to numpy array
            feature_vector = np.array(list(all_features.values()))
            
            return feature_vector
            
        except Exception as e:
            logger.error(f"Error creating feature vector: {e}")
            return np.array([])
    
    def _encode_bmi_category(self, category: str) -> int:
        """Encode BMI category as integer."""
        mapping = {
            'severe_underweight': 1,
            'moderate_underweight': 2,
            'mild_underweight': 3,
            'normal': 4,
            'overweight': 5,
            'obese': 6,
            'severe_obese': 7
        }
        return mapping.get(category, 4)
    
    def _encode_gender(self, gender: str) -> int:
        """Encode gender as integer."""
        mapping = {'male': 1, 'female': 2, 'other': 3}
        return mapping.get(gender.lower(), 3)
    
    def _encode_difficulty(self, level: str) -> int:
        """Encode difficulty level."""
        mapping = {'Beginner': 1, 'Intermediate': 2, 'Expert': 3}
        return mapping.get(level, 2)
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend (-1 declining, 0 stable, 1 improving)."""
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        # Normalize to -1, 0, 1
        if slope > 0.05:
            return 1.0
        elif slope < -0.05:
            return -1.0
        else:
            return 0.0
    
    def _get_body_part_encoding(self) -> Dict[str, int]:
        """Get body part encoding mapping."""
        return {
            'Chest': 1,
            'Back': 2,
            'Shoulders': 3,
            'Arms': 4,
            'Legs': 5,
            'Core': 6,
            'Cardio': 7,
            'Full Body': 8
        }
    
    def _get_equipment_encoding(self) -> Dict[str, int]:
        """Get equipment encoding mapping."""
        return {
            'Bodyweight': 1,
            'Dumbbell': 2,
            'Barbell': 3,
            'Machine': 4,
            'Cable': 5,
            'Bands': 6,
            'Kettlebells': 7,
            'Other': 8
        }
