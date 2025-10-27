"""
Workout Completion Predictor
Predicts likelihood of workout completion
"""
import numpy as np
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class CompletionPredictor:
    """Predict workout completion probability."""
    
    def __init__(self, db):
        self.db = db
    
    def predict_completion(self, user_id: str, workout_duration: int, num_exercises: int) -> Dict[str, Any]:
        """Predict probability of completing a workout."""
        try:
            # Get user's historical completion data
            sessions = list(self.db.session_logs.find({
                "user_id": user_id
            }).sort("logged_at", -1).limit(20))
            
            if len(sessions) < 3:
                return {
                    'completion_probability': 0.80,  # Default optimistic
                    'confidence': 0.0,
                    'factors': [],
                    'recommendation': 'Not enough history for accurate prediction'
                }
            
            # Extract features
            historical_completions = [s.get('completion_percent', 0.8) for s in sessions]
            historical_durations = [s.get('actual_duration', 45) for s in sessions]
            
            # Calculate base completion rate
            base_completion = np.mean(historical_completions)
            
            # Adjust for workout characteristics
            avg_duration = np.mean(historical_durations)
            duration_factor = self._calculate_duration_factor(workout_duration, avg_duration)
            
            # Adjust for day of week
            day_factor = self._calculate_day_factor(user_id, datetime.now().weekday())
            
            # Adjust for recent trend
            trend_factor = self._calculate_trend_factor(historical_completions)
            
            # Combined prediction
            predicted_completion = base_completion * duration_factor * day_factor * trend_factor
            predicted_completion = max(0.0, min(1.0, predicted_completion))
            
            # Confidence based on data quantity
            confidence = min(1.0, len(sessions) / 20)
            
            # Generate factors explanation
            factors = [
                {
                    'name': 'Historical Performance',
                    'impact': f"{base_completion:.0%} average completion",
                    'weight': 0.4
                },
                {
                    'name': 'Workout Duration',
                    'impact': f"{'Longer' if duration_factor < 1 else 'Shorter'} than usual",
                    'weight': 0.3
                },
                {
                    'name': 'Day of Week',
                    'impact': self._get_day_impact_description(day_factor),
                    'weight': 0.2
                },
                {
                    'name': 'Recent Trend',
                    'impact': f"{'Improving' if trend_factor > 1 else 'Declining' if trend_factor < 1 else 'Stable'}",
                    'weight': 0.1
                }
            ]
            
            # Generate recommendation
            recommendation = self._generate_recommendation(predicted_completion, workout_duration, num_exercises)
            
            return {
                'completion_probability': predicted_completion,
                'confidence': confidence,
                'factors': factors,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error predicting completion: {e}")
            return {
                'completion_probability': 0.80,
                'confidence': 0.0,
                'factors': [],
                'recommendation': 'Unable to generate prediction'
            }
    
    def _calculate_duration_factor(self, planned_duration: int, avg_duration: float) -> float:
        """Calculate adjustment factor based on workout duration."""
        if avg_duration == 0:
            return 1.0
        
        ratio = planned_duration / avg_duration
        
        # Penalize significantly longer workouts
        if ratio > 1.2:
            return 0.85
        elif ratio > 1.1:
            return 0.95
        elif ratio < 0.8:
            return 1.05
        else:
            return 1.0
    
    def _calculate_day_factor(self, user_id: str, day_of_week: int) -> float:
        """Calculate adjustment based on day of week patterns."""
        try:
            # Get sessions by day of week
            sessions = list(self.db.session_logs.find({"user_id": user_id}))
            
            if len(sessions) < 5:
                return 1.0
            
            # Group by day of week
            day_completions = {}
            for session in sessions:
                session_date = datetime.fromisoformat(session.get('logged_at', ''))
                session_day = session_date.weekday()
                
                if session_day not in day_completions:
                    day_completions[session_day] = []
                day_completions[session_day].append(session.get('completion_percent', 0.8))
            
            # Calculate average for this day
            if day_of_week in day_completions:
                day_avg = np.mean(day_completions[day_of_week])
                overall_avg = np.mean([c for completions in day_completions.values() for c in completions])
                
                return day_avg / overall_avg if overall_avg > 0 else 1.0
            
            return 1.0
            
        except:
            return 1.0
    
    def _calculate_trend_factor(self, recent_completions: list) -> float:
        """Calculate trend adjustment factor."""
        if len(recent_completions) < 3:
            return 1.0
        
        # Compare most recent 3 to previous 3
        recent_avg = np.mean(recent_completions[:3])
        previous_avg = np.mean(recent_completions[3:6]) if len(recent_completions) >= 6 else recent_avg
        
        if previous_avg == 0:
            return 1.0
        
        ratio = recent_avg / previous_avg
        
        # Return trend factor
        if ratio > 1.1:
            return 1.05  # Improving
        elif ratio < 0.9:
            return 0.95  # Declining
        else:
            return 1.0  # Stable
    
    def _get_day_impact_description(self, factor: float) -> str:
        """Get description of day impact."""
        if factor > 1.05:
            return "Strong day for you"
        elif factor < 0.95:
            return "Historically challenging day"
        else:
            return "Typical performance expected"
    
    def _generate_recommendation(self, probability: float, duration: int, num_exercises: int) -> str:
        """Generate actionable recommendation."""
        if probability < 0.6:
            return f"⚠️  Low completion probability. Consider reducing to {int(duration*0.8)} min or {num_exercises-1} exercises."
        elif probability < 0.75:
            return "💡 Moderate completion probability. Stay focused and pace yourself."
        else:
            return "✅ High completion probability. You're likely to crush this workout!"
