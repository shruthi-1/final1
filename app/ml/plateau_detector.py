"""
Training Plateau Detection System
Identifies when user progress has stagnated
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from app.ml.constants_ml import PLATEAU_PARAMS

logger = logging.getLogger(__name__)


class PlateauDetector:
    """Detect training plateaus and suggest interventions."""
    
    def __init__(self, db):
        self.db = db
    
    def detect_plateau(self, user_id: str) -> Dict[str, Any]:
        """Detect if user has hit a training plateau."""
        try:
            # Get recent workout plans (last 6 weeks)
            cutoff_date = (datetime.utcnow() - timedelta(weeks=6)).isoformat()
            plans = list(self.db.user_weekly_plans.find({
                "user_id": user_id,
                "generated_at_iso": {"$gte": cutoff_date}
            }).sort("generated_at_iso", 1))
            
            if len(plans) < PLATEAU_PARAMS['min_stagnation_weeks']:
                return {
                    'has_plateau': False,
                    'confidence': 0.0,
                    'explanation': 'Not enough training history for plateau detection',
                    'recommendations': []
                }
            
            # Analyze multiple plateau indicators
            volume_stagnation = self._check_volume_stagnation(plans)
            performance_stagnation = self._check_performance_stagnation(user_id)
            variety_deficiency = self._check_exercise_variety(plans)
            
            # Determine overall plateau status
            plateau_score = np.mean([
                volume_stagnation['score'],
                performance_stagnation['score'],
                variety_deficiency['score']
            ])
            
            has_plateau = plateau_score >= 0.6
            
            # Generate recommendations
            recommendations = []
            if volume_stagnation['detected']:
                recommendations.extend(volume_stagnation['recommendations'])
            if performance_stagnation['detected']:
                recommendations.extend(performance_stagnation['recommendations'])
            if variety_deficiency['detected']:
                recommendations.extend(variety_deficiency['recommendations'])
            
            return {
                'has_plateau': has_plateau,
                'confidence': plateau_score,
                'weeks_stagnant': len(plans),
                'indicators': {
                    'volume_stagnation': volume_stagnation['detected'],
                    'performance_stagnation': performance_stagnation['detected'],
                    'variety_deficiency': variety_deficiency['detected']
                },
                'recommendations': recommendations,
                'explanation': self._generate_explanation(plateau_score, has_plateau)
            }
            
        except Exception as e:
            logger.error(f"Error detecting plateau: {e}")
            return {
                'has_plateau': False,
                'confidence': 0.0,
                'recommendations': []
            }
    
    def _check_volume_stagnation(self, plans: List[Dict]) -> Dict:
        """Check if training volume has stagnated."""
        try:
            # Extract total weekly volume from each plan
            volumes = []
            for plan in plans:
                weekly_volume = 0
                for day_plan in plan.get('days', {}).values():
                    for exercise in day_plan.get('main', []):
                        sets = exercise.get('sets', 0)
                        reps = exercise.get('reps', 0)
                        weekly_volume += sets * reps
                volumes.append(weekly_volume)
            
            if not volumes or len(volumes) < 3:
                return {'detected': False, 'score': 0.0, 'recommendations': []}
            
            # Calculate variance coefficient
            variance_coef = np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0
            
            # Check for stagnation
            detected = variance_coef < PLATEAU_PARAMS['performance_variance_threshold']
            score = 1.0 - (variance_coef / 0.2)  # Normalize to 0-1
            score = max(0.0, min(1.0, score))
            
            recommendations = []
            if detected:
                recommendations.append({
                    'action': f'Increase training volume by {int(PLATEAU_PARAMS["volume_increase_required"]*100)}%',
                    'reason': 'Volume has been stagnant - progressive overload needed',
                    'priority': 'high'
                })
                recommendations.append({
                    'action': 'Add 1-2 sets per exercise',
                    'reason': 'Gradual volume increase to stimulate adaptation',
                    'priority': 'medium'
                })
            
            return {
                'detected': detected,
                'score': score,
                'current_volume': volumes[-1] if volumes else 0,
                'variance_coefficient': variance_coef,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error checking volume stagnation: {e}")
            return {'detected': False, 'score': 0.0, 'recommendations': []}
    
    def _check_performance_stagnation(self, user_id: str) -> Dict:
        """Check if performance metrics have stagnated."""
        try:
            # Get session logs for last 4 weeks
            cutoff_date = (datetime.utcnow() - timedelta(weeks=4)).isoformat()
            sessions = list(self.db.session_logs.find({
                "user_id": user_id,
                "logged_at": {"$gte": cutoff_date}
            }).sort("logged_at", 1))
            
            if len(sessions) < PLATEAU_PARAMS['strength_plateau_weeks']:
                return {'detected': False, 'score': 0.0, 'recommendations': []}
            
            # Check completion rate trend
            completions = [s.get('completion_percent', 0.8) for s in sessions]
            
            # Check satisfaction trend
            satisfactions = [s.get('satisfaction', 5) for s in sessions]
            
            # Calculate trends (simple linear regression)
            completion_trend = self._calculate_trend(completions)
            satisfaction_trend = self._calculate_trend(satisfactions)
            
            # Stagnation if both trends are flat or declining
            completion_stagnant = abs(completion_trend) < 0.05
            satisfaction_stagnant = satisfaction_trend <= 0
            
            detected = completion_stagnant and satisfaction_stagnant
            score = 0.7 if detected else 0.2
            
            recommendations = []
            if detected:
                recommendations.append({
                    'action': 'Change training split (e.g., switch to Push/Pull/Legs)',
                    'reason': 'New stimulus needed to break through plateau',
                    'priority': 'high'
                })
                recommendations.append({
                    'action': 'Try different exercise variations',
                    'reason': 'Novel exercises can reignite progress',
                    'priority': 'medium'
                })
                recommendations.append({
                    'action': 'Implement periodization (3 weeks on, 1 week deload)',
                    'reason': 'Strategic variation prevents stagnation',
                    'priority': 'medium'
                })
            
            return {
                'detected': detected,
                'score': score,
                'completion_trend': completion_trend,
                'satisfaction_trend': satisfaction_trend,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error checking performance stagnation: {e}")
            return {'detected': False, 'score': 0.0, 'recommendations': []}
    
    def _check_exercise_variety(self, plans: List[Dict]) -> Dict:
        """Check if exercise selection lacks variety."""
        try:
            # Collect all exercises from recent plans
            all_exercises = []
            for plan in plans:
                for day_plan in plan.get('days', {}).values():
                    for exercise in day_plan.get('main', []):
                        all_exercises.append(exercise.get('id', ''))
            
            if not all_exercises:
                return {'detected': False, 'score': 0.0, 'recommendations': []}
            
            # Calculate variety metrics
            unique_exercises = len(set(all_exercises))
            total_exercises = len(all_exercises)
            variety_ratio = unique_exercises / total_exercises if total_exercises > 0 else 0
            
            # Low variety indicates stagnation
            detected = variety_ratio < 0.5  # Less than 50% unique exercises
            score = 1.0 - variety_ratio
            
            recommendations = []
            if detected:
                recommendations.append({
                    'action': 'Introduce 2-3 new exercises per week',
                    'reason': f'Current variety ratio: {variety_ratio:.1%} - too repetitive',
                    'priority': 'medium'
                })
                recommendations.append({
                    'action': 'Try unilateral variations (single-leg/arm exercises)',
                    'reason': 'Unilateral work provides new stimulus',
                    'priority': 'low'
                })
            
            return {
                'detected': detected,
                'score': score,
                'variety_ratio': variety_ratio,
                'unique_exercises': unique_exercises,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error checking exercise variety: {e}")
            return {'detected': False, 'score': 0.0, 'recommendations': []}
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend of values."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return slope
    
    def _generate_explanation(self, plateau_score: float, has_plateau: bool) -> str:
        """Generate human-readable explanation."""
        if not has_plateau:
            return "No plateau detected. Your training is progressing well!"
        
        if plateau_score < 0.7:
            return "Minor stagnation detected. Consider the recommendations to refresh your training."
        
        return f"Training plateau detected (confidence: {plateau_score:.0%}). Your body has adapted to current stimulus. Implement the recommendations to break through."
